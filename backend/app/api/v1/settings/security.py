"""安全设置 API — 安全策略 + IP 黑白名单管理"""
import ipaddress
from uuid import UUID

from fastapi import APIRouter
from sqlmodel import select, col

from app.core.dependency import DependUser, SessionDep
from app.models.security import (
    SecurityPolicy, SecurityPolicyUpdate,
    IPRule, IPRuleCreate, IPRuleUpdate,
)
from app.models.base import Success, Fail
from app.core.redis import get_redis
from app.settings.log import logger


# ─── 认证接口 ──────────────────────────────────────────────────────────
securityProtectedRouter = APIRouter()


# ═══════════════════════════════════════════════════════════════════════
# 安全策略
# ═══════════════════════════════════════════════════════════════════════

@securityProtectedRouter.get("/policy", summary="获取安全策略")
async def get_security_policy(session: SessionDep):
    policy = session.exec(select(SecurityPolicy)).first()
    if not policy:
        return Fail(msg="安全策略未初始化")
    data = await policy.to_dict()
    return Success(data=data)


@securityProtectedRouter.post("/policy", summary="更新安全策略")
async def update_security_policy(
        session: SessionDep,
        current_user: DependUser,
        data: SecurityPolicyUpdate):
    policy = session.exec(select(SecurityPolicy)).first()
    if not policy:
        return Fail(msg="安全策略未初始化")

    update_data = data.model_dump(exclude_unset=True, exclude={"id"})
    for key, value in update_data.items():
        setattr(policy, key, value)

    session.add(policy)
    session.commit()
    session.refresh(policy)

    await logger.operationInfo(user=current_user.username, msg="更新安全策略")
    result = await policy.to_dict()
    return Success(data=result, msg="安全策略更新成功")


# ═══════════════════════════════════════════════════════════════════════
# IP 规则管理
# ═══════════════════════════════════════════════════════════════════════

@securityProtectedRouter.get("/ip-rules", summary="获取IP规则列表")
async def get_ip_rules(session: SessionDep):
    rules = session.exec(select(IPRule).order_by(col(IPRule.created_at).desc())).all()
    result = [await rule.to_dict() for rule in rules]
    return Success(data=result)


@securityProtectedRouter.post("/ip-rules/add", summary="新增IP规则")
async def add_ip_rule(session: SessionDep, current_user: DependUser, data: IPRuleCreate):
    # 校验 rule_type
    if data.rule_type not in ("whitelist", "blacklist"):
        return Fail(msg="rule_type 必须为 whitelist 或 blacklist")

    # 校验 IP/CIDR 格式
    try:
        if '/' in data.ip_cidr:
            ipaddress.ip_network(data.ip_cidr, strict=False)
        else:
            ipaddress.ip_address(data.ip_cidr)
    except ValueError:
        return Fail(msg="IP/CIDR 格式不正确")

    # 检查重复
    existing = session.exec(
        select(IPRule).where(
            IPRule.ip_cidr == data.ip_cidr,
            IPRule.rule_type == data.rule_type
        )
    ).first()
    if existing:
        return Fail(msg="该 IP 规则已存在")

    rule = IPRule.model_validate(data)
    session.add(rule)
    session.commit()
    session.refresh(rule)

    # 清除 Redis 缓存
    redis = get_redis()
    await redis.delete("ip_rules:cache")

    await logger.operationInfo(user=current_user.username, msg=f"新增IP规则: {data.ip_cidr} ({data.rule_type})")
    result = await rule.to_dict()
    return Success(data=result, msg="IP 规则添加成功")


@securityProtectedRouter.post("/ip-rules/update", summary="修改IP规则")
async def update_ip_rule(session: SessionDep, current_user: DependUser, data: IPRuleUpdate):
    rule = session.get(IPRule, data.id)
    if not rule:
        return Fail(msg="IP 规则不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"id"})

    # 校验 rule_type
    if "rule_type" in update_data and update_data["rule_type"] not in ("whitelist", "blacklist"):
        return Fail(msg="rule_type 必须为 whitelist 或 blacklist")

    # 校验 IP/CIDR 格式
    if "ip_cidr" in update_data:
        try:
            cidr = update_data["ip_cidr"]
            if '/' in cidr:
                ipaddress.ip_network(cidr, strict=False)
            else:
                ipaddress.ip_address(cidr)
        except ValueError:
            return Fail(msg="IP/CIDR 格式不正确")

    for key, value in update_data.items():
        setattr(rule, key, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)

    # 清除 Redis 缓存
    redis = get_redis()
    await redis.delete("ip_rules:cache")

    await logger.operationInfo(user=current_user.username, msg=f"修改IP规则: {data.id}")
    result = await rule.to_dict()
    return Success(data=result, msg="IP 规则更新成功")


@securityProtectedRouter.post("/ip-rules/delete", summary="删除IP规则")
async def delete_ip_rule(session: SessionDep, current_user: DependUser, data: list[UUID]):
    for rule_id in data:
        rule = session.get(IPRule, rule_id)
        if rule:
            session.delete(rule)
    session.commit()

    # 清除 Redis 缓存
    redis = get_redis()
    await redis.delete("ip_rules:cache")

    await logger.operationInfo(user=current_user.username, msg=f"删除IP规则: {[str(d) for d in data]}")
    return Success(msg="IP 规则删除成功")
