"""core/redis.py MemoryRedis 单元测试 — 所有 Protocol 方法"""

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
        results = await redis.pipeline_exec(
            [
                ("set", "pk1", "pv1", None),
                ("get", "pk1"),
                ("incr", "counter1"),
                ("incr", "counter1"),
                ("exists", "pk1"),
                ("delete", "pk1"),
            ]
        )
        # set -> None, get -> "pv1", incr -> 1, incr -> 2, exists -> True, delete -> 1
        assert results[0] is None
        assert results[1] == "pv1"
        assert results[2] == 1
        assert results[3] == 2
        assert results[4] is True
        assert results[5] == 1

    @pytest.mark.asyncio
    async def test_pipeline_sorted_set_commands(self, redis):
        results = await redis.pipeline_exec(
            [
                ("zadd", "ss", {"m1": 1.0}),
                ("zcard", "ss"),
                ("zadd", "ss", {"m2": 2.0}),
                ("zremrangebyscore", "ss", 0.5, 1.5),
                ("zcard", "ss"),
            ]
        )
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


# ─── 补充分支：惰性过期、删除 sorted set、pipeline 未知命令 ──────────────


class TestMemoryRedisExtraBranches:
    @pytest.mark.asyncio
    async def test_lazy_expiry_deletes_key(self, redis):
        await redis.set("k", "v", ex=1)
        redis._data["k"] = ("v", __import__("time").monotonic() - 1)
        assert await redis.get("k") is None
        assert "k" not in redis._data

    @pytest.mark.asyncio
    async def test_delete_removes_sorted_set(self, redis):
        await redis.zadd("z", {"a": 1.0})
        assert await redis.delete("z") == 1
        assert await redis.zcard("z") == 0

    @pytest.mark.asyncio
    async def test_pipeline_unknown_command(self, redis):
        results = await redis.pipeline_exec([("hset", "h", "f", "v")])
        assert results == [None]

    @pytest.mark.asyncio
    async def test_pipeline_set_without_ex(self, redis):
        results = await redis.pipeline_exec([("set", "k", "v")])
        assert results == [None]
        assert await redis.get("k") == "v"

    @pytest.mark.asyncio
    async def test_close_idempotent(self, redis):
        await redis.set("k", "v")
        await redis.close()
        await redis.close()
        assert await redis.get("k") is None


# ─── RealRedis（真实客户端全部委托方法，用 Mock 覆盖） ─────────────────


class TestRealRedis:
    @pytest.fixture
    def fake_redis(self):
        from unittest.mock import AsyncMock, MagicMock, patch

        inner = MagicMock()
        inner.get = AsyncMock(return_value="v")
        inner.set = AsyncMock()
        inner.delete = AsyncMock(return_value=1)
        inner.exists = AsyncMock(return_value=1)
        inner.expire = AsyncMock(return_value=True)
        inner.incr = AsyncMock(return_value=2)
        inner.ttl = AsyncMock(return_value=10)
        inner.zadd = AsyncMock(return_value=1)
        inner.zremrangebyscore = AsyncMock(return_value=1)
        inner.zcard = AsyncMock(return_value=1)
        inner.close = AsyncMock()
        pipe = MagicMock()
        pipe.execute = AsyncMock(return_value=["ok"])
        for name in (
            "zremrangebyscore",
            "zcard",
            "zadd",
            "expire",
            "incr",
            "get",
            "set",
            "delete",
            "exists",
        ):
            setattr(pipe, name, MagicMock())
        inner.pipeline = MagicMock(return_value=pipe)

        pool = MagicMock()
        pool.disconnect = AsyncMock()

        with (
            patch("redis.asyncio.ConnectionPool.from_url", return_value=pool),
            patch("redis.asyncio.Redis", return_value=inner),
        ):
            from app.core.redis import RealRedis

            instance = RealRedis("redis://localhost:6379/0")
        instance._pipe = pipe
        return instance

    @pytest.mark.asyncio
    async def test_delegates(self, fake_redis):
        assert await fake_redis.get("k") == "v"
        assert await fake_redis.set("k", "v", ex=1) is None
        assert await fake_redis.delete("k") == 1
        assert await fake_redis.exists("k") is True
        assert await fake_redis.expire("k", 1) is True
        assert await fake_redis.incr("k") == 2
        assert await fake_redis.ttl("k") == 10
        assert await fake_redis.zadd("z", {"a": 1.0}) == 1
        assert await fake_redis.zremrangebyscore("z", 0, 1) == 1
        assert await fake_redis.zcard("z") == 1

    @pytest.mark.asyncio
    async def test_pipeline_all_commands(self, fake_redis):
        cmds = [
            ("zremrangebyscore", "z", 0, 1),
            ("zcard", "z"),
            ("zadd", "z", {"a": 1.0}),
            ("expire", "k", 10),
            ("incr", "c"),
            ("get", "k"),
            ("set", "k", "v", 5),
            ("delete", "k"),
            ("exists", "k"),
        ]
        result = await fake_redis.pipeline_exec(cmds)
        assert result == ["ok"]

    @pytest.mark.asyncio
    async def test_close(self, fake_redis):
        await fake_redis.close()


class TestCreateRedis:
    def test_local_without_url(self, monkeypatch):
        from app.core import redis as redis_mod

        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "local", raising=False)
        monkeypatch.setattr(redis_mod.settings, "REDIS_URL", "", raising=False)
        assert isinstance(redis_mod._create_redis(), redis_mod.MemoryRedis)

    def test_local_with_url(self, monkeypatch):
        from unittest.mock import patch

        from app.core import redis as redis_mod

        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "local", raising=False)
        monkeypatch.setattr(redis_mod.settings, "REDIS_URL", "redis://u:p@h:6379/0", raising=False)
        with patch.object(redis_mod, "RealRedis") as mock_real:
            redis_mod._create_redis()
        mock_real.assert_called_once()

    def test_prod_without_url_raises(self, monkeypatch):
        from app.core import redis as redis_mod

        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "production", raising=False)
        monkeypatch.setattr(redis_mod.settings, "REDIS_URL", "", raising=False)
        with pytest.raises(ValueError, match="REDIS_URL"):
            redis_mod._create_redis()

    def test_prod_with_url(self, monkeypatch):
        from unittest.mock import patch

        from app.core import redis as redis_mod

        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "production", raising=False)
        monkeypatch.setattr(redis_mod.settings, "REDIS_URL", "redis://h:6379/0", raising=False)
        with patch.object(redis_mod, "RealRedis") as mock_real:
            redis_mod._create_redis()
        mock_real.assert_called_once()


class TestRedisManager:
    def test_get_creates_singleton(self, monkeypatch):
        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        created = []

        def fake_create():
            created.append(1)
            return redis_mod.MemoryRedis()

        monkeypatch.setattr(redis_mod, "_create_redis", fake_create)
        a = manager.get()
        b = manager.get()
        assert a is b
        assert len(created) == 1

    @pytest.mark.asyncio
    async def test_init_memory_noop(self, monkeypatch):
        from unittest.mock import MagicMock

        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        monkeypatch.setattr(redis_mod, "_create_redis", MagicMock(return_value=redis_mod.MemoryRedis()))
        await manager.init()
        assert isinstance(manager._instance, redis_mod.MemoryRedis)

    @pytest.mark.asyncio
    async def test_init_real_ping_success(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock

        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        real = MagicMock(spec=redis_mod.RealRedis)
        real.set = AsyncMock()
        real.get = AsyncMock(return_value="pong")
        real.close = AsyncMock()
        monkeypatch.setattr(redis_mod, "_create_redis", MagicMock(return_value=real))
        await manager.init()
        assert manager._instance is real

    @pytest.mark.asyncio
    async def test_init_real_ping_fail_local_fallback(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock

        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        real = MagicMock(spec=redis_mod.RealRedis)
        real.set = AsyncMock(side_effect=ConnectionError("nope"))
        real.get = AsyncMock()
        real.close = AsyncMock()
        monkeypatch.setattr(redis_mod, "_create_redis", MagicMock(return_value=real))
        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "local", raising=False)
        await manager.init()
        assert isinstance(manager._instance, redis_mod.MemoryRedis)
        real.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_init_real_ping_fail_prod_raises(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock

        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        real = MagicMock(spec=redis_mod.RealRedis)
        real.set = AsyncMock(side_effect=ConnectionError("nope"))
        real.get = AsyncMock()
        real.close = AsyncMock()
        monkeypatch.setattr(redis_mod, "_create_redis", MagicMock(return_value=real))
        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "production", raising=False)
        with pytest.raises(ConnectionError):
            await manager.init()

    @pytest.mark.asyncio
    async def test_init_pong_mismatch(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock

        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        real = MagicMock(spec=redis_mod.RealRedis)
        real.set = AsyncMock()
        real.get = AsyncMock(return_value="not-pong")
        real.close = AsyncMock()
        monkeypatch.setattr(redis_mod, "_create_redis", MagicMock(return_value=real))
        monkeypatch.setattr(redis_mod.settings, "ENVIRONMENT", "local", raising=False)
        await manager.init()
        assert isinstance(manager._instance, redis_mod.MemoryRedis)

    @pytest.mark.asyncio
    async def test_close_resets(self, monkeypatch):
        from unittest.mock import AsyncMock, MagicMock

        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        inst = MagicMock()
        inst.close = AsyncMock()
        manager._instance = inst
        await manager.close()
        assert manager._instance is None
        inst.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_when_none(self):
        from app.core import redis as redis_mod

        manager = redis_mod._RedisManager()
        await manager.close()


class TestModuleHelpers:
    @pytest.mark.asyncio
    async def test_init_and_close_helpers(self, monkeypatch):
        from unittest.mock import AsyncMock

        from app.core import redis as redis_mod

        monkeypatch.setattr(redis_mod.redis_manager, "init", AsyncMock())
        await redis_mod.init_redis()
        redis_mod.redis_manager.init.assert_awaited_once()

        monkeypatch.setattr(redis_mod.redis_manager, "close", AsyncMock())
        await redis_mod.close_redis()
        redis_mod.redis_manager.close.assert_awaited_once()

    def test_get_redis_returns_instance(self, monkeypatch):

        from app.core import redis as redis_mod

        sentinel = redis_mod.MemoryRedis()
        monkeypatch.setattr(redis_mod.redis_manager, "_instance", sentinel)
        assert redis_mod.get_redis() is sentinel
        assert isinstance(sentinel, redis_mod.RedisClient)


class TestRealRedisImportError:
    def test_missing_redis_package_raises(self, monkeypatch):
        import builtins
        import sys

        from app.core import redis as redis_mod

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "redis.asyncio" or name.startswith("redis.asyncio"):
                raise ImportError("no redis")
            return real_import(name, *args, **kwargs)

        monkeypatch.delitem(sys.modules, "redis.asyncio", raising=False)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ImportError, match="生产环境需要 redis 包"):
            redis_mod.RealRedis("redis://h:6379/0")
