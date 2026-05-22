import ipaddress
import json

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .bgtask import BgTasks
from .redis import get_redis


class SimpleBaseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        response = await self.before_request(request) or self.app
        await response(request.scope, request.receive, send)
        await self.after_request(request)

    async def before_request(self, _request: Request):
        return self.app

    async def after_request(self, _request: Request):
        return None


class BackGroundTaskMiddleware(SimpleBaseMiddleware):
    async def before_request(self, _request):
        await BgTasks.init_bg_tasks_obj()

    async def after_request(self, _request):
        await BgTasks.execute_tasks()


class IPFilterMiddleware(SimpleBaseMiddleware):
    """IP 黑白名单过滤中间件"""

    # Redis 缓存 key & TTL
    CACHE_KEY = "ip_rules:cache"
    CACHE_TTL = 30  # 30秒缓存

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP（支持代理头）"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    def _ip_matches_cidr(self, ip: str, cidr: str) -> bool:
        """检查 IP 是否匹配 CIDR 规则"""
        try:
            if '/' in cidr:
                return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
            return ip == cidr
        except (ValueError, TypeError):
            return ip == cidr

    async def _get_rules(self) -> list[dict]:
        """从 Redis 缓存获取 IP 规则，过期则从数据库重新加载"""
        redis = get_redis()
        cached = await redis.get(self.CACHE_KEY)

        if cached is not None:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                pass

        # 从数据库加载
        from sqlmodel import Session, select
        from app.models.security import IPRule
        from app.core import engine

        rules = []
        with Session(engine) as session:
            db_rules = session.exec(
                select(IPRule).where(IPRule.is_active.is_(True))  # noqa: E712
            ).all()
            for rule in db_rules:
                rules.append({
                    "ip_cidr": rule.ip_cidr,
                    "rule_type": rule.rule_type,
                })

        # 缓存到 Redis
        await redis.set(self.CACHE_KEY, json.dumps(rules), ex=self.CACHE_TTL)
        return rules

    async def before_request(self, request: Request):
        client_ip = self._get_client_ip(request)

        # 白名单路径放行（健康检查、验证码等）
        path = request.url.path
        if path.startswith(
                "/api/v1/base/health") or path == "/openapi.json" or path.startswith("/docs"):
            return self.app

        try:
            rules = await self._get_rules()
        except Exception:
            # 规则加载失败时放行，避免阻塞服务
            return self.app

        if not rules:
            return self.app

        whitelist_rules = [r for r in rules if r["rule_type"] == "whitelist"]
        blacklist_rules = [r for r in rules if r["rule_type"] == "blacklist"]

        # 白名单优先：如果存在白名单规则，则 IP 必须匹配白名单才放行
        if whitelist_rules:
            matched = any(
                self._ip_matches_cidr(client_ip, r["ip_cidr"])
                for r in whitelist_rules
            )
            if not matched:
                return JSONResponse(
                    status_code=403,
                    content={"code": 403, "msg": "访问被拒绝"}
                )

        # 黑名单检查
        for rule in blacklist_rules:
            if self._ip_matches_cidr(client_ip, rule["ip_cidr"]):
                return JSONResponse(
                    status_code=403,
                    content={"code": 403, "msg": "IP 已被封禁"}
                )

        return self.app
