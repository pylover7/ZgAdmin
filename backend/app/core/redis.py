"""
Redis 抽象层 — 生产环境使用真实 Redis，开发环境使用内存适配器

用法:
    from app.core.redis import get_redis, RedisClient

    redis = get_redis()
    await redis.set("key", "value", ex=300)
    val = await redis.get("key")
"""

import asyncio
import time
from typing import Any, Protocol, runtime_checkable

from app.settings import settings
from app.settings.log import logger

_SET_CMD_MIN_LEN = 3


@runtime_checkable
class RedisClient(Protocol):
    """Redis 客户端协议 — 真实 Redis 和内存实现都需满足此接口"""

    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> None: ...
    async def delete(self, *keys: str) -> int: ...
    async def exists(self, key: str) -> bool: ...
    async def expire(self, key: str, seconds: int) -> bool: ...
    async def incr(self, key: str) -> int: ...
    async def ttl(self, key: str) -> int: ...
    async def zadd(self, key: str, mapping: dict[str, float]) -> int: ...
    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int: ...
    async def zcard(self, key: str) -> int: ...
    async def pipeline_exec(self, commands: list[tuple]) -> list[Any]: ...
    async def close(self) -> None: ...


class MemoryRedis:
    """内存 Redis 适配器 — 用于开发环境，功能完全等价"""

    def __init__(self):
        self._data: dict[str, tuple[str, float | None]] = {}  # key -> (value, expire_at)
        self._sorted_sets: dict[str, dict[str, float]] = {}  # key -> {member: score}
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        if key not in self._data:
            return True
        _, expire_at = self._data[key]
        if expire_at is not None and time.monotonic() > expire_at:
            del self._data[key]
            return True
        return False

    async def get(self, key: str) -> str | None:
        async with self._lock:
            if self._is_expired(key):
                return None
            return self._data[key][0]

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        async with self._lock:
            expire_at = time.monotonic() + ex if ex else None
            self._data[key] = (value, expire_at)

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for key in keys:
                if key in self._data:
                    del self._data[key]
                    count += 1
                if key in self._sorted_sets:
                    del self._sorted_sets[key]
                    count += 1
            return count

    async def exists(self, key: str) -> bool:
        async with self._lock:
            return not self._is_expired(key)

    async def expire(self, key: str, seconds: int) -> bool:
        async with self._lock:
            if self._is_expired(key):
                return False
            value, _ = self._data[key]
            self._data[key] = (value, time.monotonic() + seconds)
            return True

    async def incr(self, key: str) -> int:
        async with self._lock:
            if self._is_expired(key):
                self._data[key] = ("1", None)
                return 1
            value, expire_at = self._data[key]
            new_val = int(value) + 1
            self._data[key] = (str(new_val), expire_at)
            return new_val

    async def ttl(self, key: str) -> int:
        async with self._lock:
            if self._is_expired(key):
                return -2
            _, expire_at = self._data[key]
            if expire_at is None:
                return -1
            remaining = int(expire_at - time.monotonic())
            return max(0, remaining)

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        async with self._lock:
            if key not in self._sorted_sets:
                self._sorted_sets[key] = {}
            added = 0
            for member, score in mapping.items():
                if member not in self._sorted_sets[key]:
                    added += 1
                self._sorted_sets[key][member] = score
            return added

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        async with self._lock:
            if key not in self._sorted_sets:
                return 0
            to_remove = [member for member, score in self._sorted_sets[key].items() if min_score <= score <= max_score]
            for member in to_remove:
                del self._sorted_sets[key][member]
            return len(to_remove)

    async def zcard(self, key: str) -> int:
        async with self._lock:
            return len(self._sorted_sets.get(key, {}))

    async def pipeline_exec(self, commands: list[tuple]) -> list[Any]:
        """简化版 pipeline — 顺序执行命令并收集结果"""
        results = []
        for cmd in commands:
            op = cmd[0]
            if op == "zremrangebyscore":
                results.append(await self.zremrangebyscore(cmd[1], cmd[2], cmd[3]))
            elif op == "zcard":
                results.append(await self.zcard(cmd[1]))
            elif op == "zadd":
                results.append(await self.zadd(cmd[1], cmd[2]))
            elif op == "expire":
                results.append(await self.expire(cmd[1], cmd[2]))
            elif op == "incr":
                results.append(await self.incr(cmd[1]))
            elif op == "get":
                results.append(await self.get(cmd[1]))
            elif op == "set":
                await self.set(cmd[1], cmd[2], cmd[3] if len(cmd) > _SET_CMD_MIN_LEN else None)
                results.append(None)
            elif op == "delete":
                results.append(await self.delete(cmd[1]))
            elif op == "exists":
                results.append(await self.exists(cmd[1]))
            else:
                results.append(None)
        return results

    async def close(self) -> None:
        self._data.clear()
        self._sorted_sets.clear()


class RealRedis:
    """真实 Redis 客户端封装 — 生产环境使用"""

    def __init__(self, url: str):
        try:
            import redis.asyncio as aioredis
        except ImportError as exc:
            raise ImportError("生产环境需要 redis 包，请运行: uv add redis") from exc
        self._pool = aioredis.ConnectionPool.from_url(url, decode_responses=True)
        self._redis = aioredis.Redis(connection_pool=self._pool)

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self._redis.set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        return await self._redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def expire(self, key: str, seconds: int) -> bool:
        return await self._redis.expire(key, seconds)

    async def incr(self, key: str) -> int:
        return await self._redis.incr(key)

    async def ttl(self, key: str) -> int:
        return await self._redis.ttl(key)

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        return await self._redis.zadd(key, mapping)

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        return await self._redis.zremrangebyscore(key, min_score, max_score)

    async def zcard(self, key: str) -> int:
        return await self._redis.zcard(key)

    async def pipeline_exec(self, commands: list[tuple]) -> list[Any]:
        pipe = self._redis.pipeline(transaction=False)
        for cmd in commands:
            op = cmd[0]
            if op == "zremrangebyscore":
                pipe.zremrangebyscore(cmd[1], cmd[2], cmd[3])
            elif op == "zcard":
                pipe.zcard(cmd[1])
            elif op == "zadd":
                pipe.zadd(cmd[1], cmd[2])
            elif op == "expire":
                pipe.expire(cmd[1], cmd[2])
            elif op == "incr":
                pipe.incr(cmd[1])
            elif op == "get":
                pipe.get(cmd[1])
            elif op == "set":
                pipe.set(cmd[1], cmd[2], ex=cmd[3] if len(cmd) > _SET_CMD_MIN_LEN else None)
            elif op == "delete":
                pipe.delete(cmd[1])
            elif op == "exists":
                pipe.exists(cmd[1])
        return await pipe.execute()

    async def close(self) -> None:
        await self._redis.close()
        await self._pool.disconnect()


# ─── 全局单例 ──────────────────────────────────────────────────────────

_redis_instance: RedisClient | None = None


def _create_redis() -> RedisClient:
    """根据配置创建 Redis 实例"""
    redis_url = getattr(settings, "REDIS_URL", "") or ""

    if redis_url:
        logger.info(f"Redis: 使用真实连接 ({redis_url.split('@')[-1]})")
        return RealRedis(redis_url)

    if settings.ENVIRONMENT == "local":
        logger.info("Redis: 使用内存适配器（开发模式）")
        return MemoryRedis()

    # 非本地环境没有 REDIS_URL 时，降级到内存模式并警告
    logger.warning("⚠ 生产环境未配置 REDIS_URL，降级使用内存适配器（多进程不可用）")
    return MemoryRedis()


def get_redis() -> RedisClient:
    """获取 Redis 全局单例"""
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = _create_redis()
    return _redis_instance


async def init_redis() -> None:
    """应用启动时调用 — 初始化 Redis 连接"""
    global _redis_instance
    _redis_instance = _create_redis()

    # 测试连接
    if isinstance(_redis_instance, RealRedis):
        try:
            await _redis_instance.set("redis:ping", "pong", ex=10)
            pong = await _redis_instance.get("redis:ping")
            if pong != "pong":
                raise ConnectionError("Redis ping 失败")
            logger.info("Redis 连接测试成功")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            raise


async def close_redis() -> None:
    """应用关闭时调用 — 关闭 Redis 连接"""
    global _redis_instance
    if _redis_instance is not None:
        await _redis_instance.close()
        _redis_instance = None
        logger.info("Redis 连接已关闭")
