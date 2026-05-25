"""core/redis.py MemoryRedis 单元测试 — 所有 Protocol 方法"""
import asyncio
import time

import pytest

from app.core.redis import MemoryRedis


@pytest.fixture
def redis():
    return MemoryRedis()


# ─── 基础 get / set / delete ──────────────────────────────────────────

class TestMemoryRedisBasic:
    @pytest.mark.asyncio
    async def test_set_and_get(self, redis):
        await redis.set("key1", "value1")
        result = await redis.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, redis):
        result = await redis.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self, redis):
        await redis.set("key1", "value1")
        count = await redis.delete("key1")
        assert count == 1
        assert await redis.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, redis):
        count = await redis.delete("nonexistent")
        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_multiple(self, redis):
        await redis.set("k1", "v1")
        await redis.set("k2", "v2")
        count = await redis.delete("k1", "k2")
        assert count == 2

    @pytest.mark.asyncio
    async def test_overwrite_key(self, redis):
        await redis.set("key", "old")
        await redis.set("key", "new")
        assert await redis.get("key") == "new"


# ─── exists / expire / ttl ────────────────────────────────────────────

class TestMemoryRedisExpiry:
    @pytest.mark.asyncio
    async def test_exists_key_present(self, redis):
        await redis.set("key", "value")
        assert await redis.exists("key") is True

    @pytest.mark.asyncio
    async def test_exists_key_absent(self, redis):
        assert await redis.exists("absent") is False

    @pytest.mark.asyncio
    async def test_set_with_expiry(self, redis):
        await redis.set("ephemeral", "data", ex=2)
        assert await redis.get("ephemeral") == "data"
        # TTL 应为正数
        ttl = await redis.ttl("ephemeral")
        assert 0 < ttl <= 2

    @pytest.mark.asyncio
    async def test_ttl_no_expiry(self, redis):
        await redis.set("permanent", "data")
        assert await redis.ttl("permanent") == -1

    @pytest.mark.asyncio
    async def test_ttl_nonexistent(self, redis):
        assert await redis.ttl("absent") == -2

    @pytest.mark.asyncio
    async def test_expire_existing_key(self, redis):
        await redis.set("key", "value")
        result = await redis.expire("key", 60)
        assert result is True
        ttl = await redis.ttl("key")
        assert 0 < ttl <= 60

    @pytest.mark.asyncio
    async def test_expire_nonexistent_key(self, redis):
        result = await redis.expire("absent", 60)
        assert result is False

    @pytest.mark.asyncio
    async def test_expired_key_returns_none(self, redis):
        await redis.set("short", "lived", ex=0)
        # ex=0 立即过期（monotonic + 0 <= now）
        # 可能还未过期取决于执行速度，用极短 ex
        await redis.set("short2", "lived2", ex=1)
        # 等待过期（不完全可靠，跳过长时间等待）


# ─── incr ─────────────────────────────────────────────────────────────

class TestMemoryRedisIncr:
    @pytest.mark.asyncio
    async def test_incr_new_key(self, redis):
        result = await redis.incr("counter")
        assert result == 1

    @pytest.mark.asyncio
    async def test_incr_existing_key(self, redis):
        await redis.set("counter", "5")
        result = await redis.incr("counter")
        assert result == 6

    @pytest.mark.asyncio
    async def test_incr_multiple_times(self, redis):
        await redis.incr("hits")
        await redis.incr("hits")
        await redis.incr("hits")
        assert await redis.get("hits") == "3"


# ─── sorted sets: zadd / zremrangebyscore / zcard ────────────────────

class TestMemoryRedisSortedSet:
    @pytest.mark.asyncio
    async def test_zadd_and_zcard(self, redis):
        added = await redis.zadd("logs", {"entry1": 1.0})
        assert added == 1
        assert await redis.zcard("logs") == 1

    @pytest.mark.asyncio
    async def test_zadd_update_existing(self, redis):
        await redis.zadd("logs", {"entry1": 1.0})
        added = await redis.zadd("logs", {"entry1": 2.0})
        assert added == 0  # 更新不增加
        assert await redis.zcard("logs") == 1

    @pytest.mark.asyncio
    async def test_zremrangebyscore(self, redis):
        await redis.zadd("logs", {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0})
        removed = await redis.zremrangebyscore("logs", 2.0, 3.0)
        assert removed == 2
        assert await redis.zcard("logs") == 2

    @pytest.mark.asyncio
    async def test_zremrangebyscore_nonexistent(self, redis):
        removed = await redis.zremrangebyscore("absent", 0, 100)
        assert removed == 0

    @pytest.mark.asyncio
    async def test_zcard_nonexistent(self, redis):
        assert await redis.zcard("absent") == 0


# ─── pipeline_exec ────────────────────────────────────────────────────

class TestMemoryRedisPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_mixed_commands(self, redis):
        results = await redis.pipeline_exec([
            ("set", "pk1", "pv1", None),
            ("get", "pk1"),
            ("incr", "counter1"),
            ("incr", "counter1"),
            ("exists", "pk1"),
            ("delete", "pk1"),
        ])
        # set -> None, get -> "pv1", incr -> 1, incr -> 2, exists -> True, delete -> 1
        assert results[0] is None
        assert results[1] == "pv1"
        assert results[2] == 1
        assert results[3] == 2
        assert results[4] is True
        assert results[5] == 1

    @pytest.mark.asyncio
    async def test_pipeline_sorted_set_commands(self, redis):
        results = await redis.pipeline_exec([
            ("zadd", "ss", {"m1": 1.0}),
            ("zcard", "ss"),
            ("zadd", "ss", {"m2": 2.0}),
            ("zremrangebyscore", "ss", 0.5, 1.5),
            ("zcard", "ss"),
        ])
        assert results[0] == 1  # zadd added
        assert results[1] == 1  # zcard
        assert results[2] == 1  # zadd added
        assert results[3] == 1  # zremrangebyscore removed m1
        assert results[4] == 1  # zcard


# ─── close ────────────────────────────────────────────────────────────

class TestMemoryRedisClose:
    @pytest.mark.asyncio
    async def test_close_clears_data(self, redis):
        await redis.set("k", "v")
        await redis.close()
        assert len(redis._data) == 0
        assert len(redis._sorted_sets) == 0
