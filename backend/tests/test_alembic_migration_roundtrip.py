"""迁移链回归护栏 — 把「一次性手工验证」固化为可自动发现的测试。

覆盖场景（缺一即不可信）：
1. 链单头（`alembic heads` 只有一个）
2. 空库 `upgrade head` 后结构与模型零差异
3. 往返（`downgrade base` → `upgrade head`）后结构不变
4. 老库升级（`downgrade` 到历史 revision → `upgrade head`）后结构与模型一致

另外覆盖 `_repair_dirty_tables` 脏库自愈（它会在库上执行 DDL，
一旦写错比迁移失败更严重）。

⚠️ 本文件在 SQLite 上运行，「结构跨版本升级」的验证强度有限，原因见
`test_legacy_db_upgrade_matches_models` 的 docstring。

为什么用 subprocess 而不是 `alembic.command` API：
- `alembic/env.py` 有模块级副作用（`import app.models`、初始化 settings / 日志）
- `app.core.engine` 是模块级单例，而同进程内 `env.py` 的 `engine_from_config`
  会建出第二个引擎对象 —— 二者可能指向不同的库，导致测试「升级了临时库，
  却检测了全局库」的错配 → 假绿
- subprocess 下子进程自行初始化 settings 与 engine，上述错配不存在

⚠️ 不得复用 `conftest.py` 的 session 级共享引擎做破坏性 DDL（见 MEMORY 4.6）。
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel

BACKEND_DIR = Path(__file__).resolve().parent.parent

# 全部历史 revision，用于「跳版本老库」场景
INITIAL_REVISION = "582670eaa9ea"


def _run_alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    """在子进程中执行 alembic 命令，返回 CompletedProcess。

    以 `python -m alembic` 调用而非 `uv run`，避免测试嵌套调用包管理器。
    """
    env = {**os.environ, "ALEMBIC_DB_URL": db_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return result


def _alembic_ok(db_url: str, *args: str) -> str:
    """执行 alembic 命令并在失败时抛出，附带 stdout / stderr 便于定位。"""
    result = _run_alembic(db_url, *args)
    if result.returncode != 0:
        raise AssertionError(
            f"alembic {' '.join(args)} 执行失败（exit={result.returncode}）\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    return result.stdout


@pytest.fixture
def tmp_db_url(tmp_path: Path) -> str:
    """每个测试独立的临时 SQLite 库 URL。"""
    return f"sqlite:///{tmp_path / f'{uuid.uuid4().hex}.sqlite'}"


def _snapshot_structure(db_url: str) -> dict[str, set[str]]:
    """快照库结构：{表名: 列名集合}。"""
    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        return {
            t: {c["name"] for c in inspector.get_columns(t)}
            for t in inspector.get_table_names()
            if t != "alembic_version"
        }
    finally:
        engine.dispose()


def _diff_against_models(snapshot: dict[str, set[str]]) -> list[dict]:
    """把结构快照与 SQLModel.metadata 逐表逐列比对，返回差异列表（空列表 = 一致）。

    必须比对全集（不能用抽查）：参考项目曾因只查 `user` 一张表就断言
    「结构与模型一致」，实际另有 2 张表缺列。
    """
    db_tables = set(snapshot)
    model_tables = set(SQLModel.metadata.tables.keys())
    if db_tables != model_tables:
        return [
            {
                "table": "<table-set>",
                "missing": sorted(model_tables - db_tables),
                "extra": sorted(db_tables - model_tables),
            }
        ]

    diffs = []
    for table_name in sorted(model_tables):
        model_cols = set(SQLModel.metadata.tables[table_name].columns.keys())
        if snapshot[table_name] != model_cols:
            diffs.append(
                {
                    "table": table_name,
                    "missing": sorted(model_cols - snapshot[table_name]),
                    "extra": sorted(snapshot[table_name] - model_cols),
                }
            )
    return diffs


def _assert_structure_matches_models(db_url: str) -> None:
    """逐表逐列 set 比对库结构与 SQLModel.metadata。"""
    diffs = _diff_against_models(_snapshot_structure(db_url))
    assert not diffs, f"库结构与模型不一致: {diffs}"


# ═══════════════════════════════════════════════════════════════════════
# 场景 1：链单头
# ═══════════════════════════════════════════════════════════════════════


def test_migration_chain_has_single_head(tmp_db_url: str) -> None:
    """判断分支数必须用 `alembic heads`；`alembic history` 的折行会产生多头假象。"""
    output = _alembic_ok(tmp_db_url, "heads")
    head_lines = [line for line in output.splitlines() if line.strip() and not line.startswith("INFO")]
    assert len(head_lines) == 1, f"期望单头，实际 {len(head_lines)} 个 head: {head_lines}"


# ═══════════════════════════════════════════════════════════════════════
# 场景 2：空库 upgrade head 结构与模型一致
# ═══════════════════════════════════════════════════════════════════════


def test_fresh_db_upgrade_head_matches_models(tmp_db_url: str) -> None:
    """空库从零升级到 head，结构与模型必须零差异。

    这条同时验证了「迁移链能独立建出完整库」—— 即 `create_all` 移除后
    新环境首次启动所依赖的路径。
    """
    _alembic_ok(tmp_db_url, "upgrade", "head")
    _assert_structure_matches_models(tmp_db_url)


# ═══════════════════════════════════════════════════════════════════════
# 场景 3：往返（downgrade base → upgrade head）
# ═══════════════════════════════════════════════════════════════════════


def test_downgrade_base_then_upgrade_head_restores_structure(tmp_db_url: str) -> None:
    """`downgrade base` 后表数归零，再 `upgrade head` 结构必须与模型一致。"""
    _alembic_ok(tmp_db_url, "upgrade", "head")
    at_head = _snapshot_structure(tmp_db_url)

    _alembic_ok(tmp_db_url, "downgrade", "base")
    assert not _snapshot_structure(tmp_db_url), "downgrade base 后仍有残留表"

    _alembic_ok(tmp_db_url, "upgrade", "head")
    _assert_structure_matches_models(tmp_db_url)

    # 往返必须对称：回到 head 后的结构应与首次升级结果逐列完全相同
    assert _snapshot_structure(tmp_db_url) == at_head, "往返后结构与首次升级结果不一致"


# ═══════════════════════════════════════════════════════════════════════
# 场景 4：老库升级
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "target_revision",
    [
        pytest.param("-1", id="adjacent"),
        pytest.param(INITIAL_REVISION, id="initial"),
    ],
)
def test_legacy_db_upgrade_matches_models(tmp_db_url: str, target_revision: str) -> None:
    """老库升级：downgrade 到历史 revision → `upgrade head` → 结构与模型一致。

    构造老库的方式是「先升到 head，再 downgrade 到目标 revision」——不拉取历史版本代码，
    `downgrade` 得到的库在结构上与「该版本代码建出的库」等价。

    ⚠️ **本测试在 SQLite 上无法验证「结构跨版本升级」**，这是被测对象的性质而非测试缺陷：

    | revision | 内容 | SQLite 上的结构效果 |
    |---|---|---|
    | `582670eaa9ea` | 建全部表 | 建出全部表 |
    | `1e99a7fcad44` | `upgrade()`/`downgrade()` 均为 `pass`（操作已并入基线） | 无 |
    | `f9c9610dbf51` | 纯 `UPDATE systemlog SET module=...` | 无（数据迁移） |
    | `30bcfbeddb70` | `alter_column` 改 timezone | **`bind.dialect.name == "sqlite"` 时直接 return** |

    即：**整条链的结构效果几乎全由第一个迁移完成**，故 downgrade 到任何非 base 版本结构都不变。
    真正的结构跨版本升级需在 PostgreSQL 上才有验证意义。因此本测试的断言是：
    「升级前后结构都必须与模型一致」，而**不假设 downgrade 一定改变了结构**。
    """
    _alembic_ok(tmp_db_url, "upgrade", "head")
    at_head = _snapshot_structure(tmp_db_url)

    _alembic_ok(tmp_db_url, "downgrade", target_revision)
    legacy = _snapshot_structure(tmp_db_url)

    # 升级前结构就必须是自洽的，否则被测的 `upgrade head` 是在一个非法起点上跑，结论无意义
    legacy_diffs = _diff_against_models(legacy)
    assert not legacy_diffs, f"downgrade 到 {target_revision} 后的结构非法（与模型不兼容）: {legacy_diffs}"

    _alembic_ok(tmp_db_url, "upgrade", "head")
    _assert_structure_matches_models(tmp_db_url)
    # 无论链上是否有空迁移，回到 head 后都必须与首次升级结果逐列一致
    assert _snapshot_structure(tmp_db_url) == at_head, f"从 {target_revision} 升级回 head 后结构不一致"


# ═══════════════════════════════════════════════════════════════════════
# 场景 5：老库带业务数据升级，数据必须保真
# ═══════════════════════════════════════════════════════════════════════


def test_legacy_db_upgrade_preserves_business_data(tmp_db_url: str) -> None:
    """在历史 revision 的库上插入业务数据，升级到 head 后数据必须完好。

    ⚠️ 这条是 SQLite 上**唯一有实战价值**的老库升级场景：结构跨版本升级在 SQLite 上
    是空转（见上一测试的说明），但「有数据的老库能否升级成功」不受此影响 ——
    而用户的真实场景恰恰是「手上有旧版库（有数据），装了新代码，执行迁移」。
    """
    _alembic_ok(tmp_db_url, "upgrade", "head")
    _alembic_ok(tmp_db_url, "downgrade", INITIAL_REVISION)

    engine = create_engine(tmp_db_url)
    try:
        with engine.begin() as conn:
            # 列名与 NOT NULL 约束以真实 schema 为准（先 inspect 确认，不凭字段名推测）
            conn.execute(
                text(
                    "INSERT INTO user "
                    "(id, created_at, username, email, password, status, is_superuser, sex, failed_login_count) "
                    "VALUES (:id, :created_at, :username, :email, :password, 1, 0, 1, 0)"
                ),
                {
                    "id": uuid.uuid4().bytes,
                    "created_at": "2026-01-01 00:00:00",
                    "username": "legacyuser",
                    "email": "legacy@example.com",
                    "password": "hashed",
                },
            )
            conn.execute(
                text(
                    "INSERT INTO systemlog (id, time, level, module, message) "
                    "VALUES (:id, :time, 'INFO', '系统管理', 'legacy log')"
                ),
                {"id": uuid.uuid4().bytes, "time": "2026-01-01 00:00:00"},
            )
    finally:
        engine.dispose()

    # 被测动作：在带数据的老库上执行升级
    _alembic_ok(tmp_db_url, "upgrade", "head")

    engine = create_engine(tmp_db_url)
    try:
        with engine.connect() as conn:
            user = conn.execute(text("SELECT username, email FROM user WHERE username = 'legacyuser'")).first()
            assert user is not None, "升级后业务数据（user 行）丢失"
            assert user[1] == "legacy@example.com", "升级后业务数据字段值被改动"

            # f9c9610dbf51 是数据迁移：中文字面量应被改写为英文常量
            module = conn.execute(text("SELECT module FROM systemlog LIMIT 1")).scalar()
            assert module == "system_management", f"数据迁移未生效，module 仍为 {module!r}"
    finally:
        engine.dispose()

    _assert_structure_matches_models(tmp_db_url)


# ═══════════════════════════════════════════════════════════════════════
# 脏库自愈 `_repair_dirty_tables`
# ═══════════════════════════════════════════════════════════════════════


class TestRepairDirtyTables:
    """自愈会在用户库上执行 DDL（`ALTER TABLE ADD COLUMN`），

    写错比迁移失败更严重 —— 迁移失败只是启动不了，自愈写错是库被改坏。
    因此在独立临时库上构造脏态并直接调用被测函数。
    """

    @staticmethod
    def _repair(db_url: str) -> None:
        """在指向指定库的独立引擎上执行 `_repair_dirty_tables`。"""
        import app.core.database as database_mod

        other_engine = create_engine(db_url)
        original_engine = database_mod.engine
        database_mod.engine = other_engine
        try:
            database_mod._repair_dirty_tables()
        finally:
            database_mod.engine = original_engine
            other_engine.dispose()

    def test_repairs_missing_column(self, tmp_db_url: str) -> None:
        """缺列应被补齐，且已有数据不受影响。"""
        _alembic_ok(tmp_db_url, "upgrade", "head")

        engine = create_engine(tmp_db_url)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO department (id, name, sort, status, created_at) "
                        "VALUES (:id, '老部门', 0, 1, '2026-01-01 00:00:00')"
                    ),
                    {"id": uuid.uuid4().bytes},
                )
                # 构造脏态：删掉一个模型里有、但库上缺的列
                conn.execute(text("ALTER TABLE department DROP COLUMN remark"))
        finally:
            engine.dispose()

        snapshot = _snapshot_structure(tmp_db_url)
        assert "remark" not in snapshot["department"], "脏态构造失败：remark 列仍存在"

        self._repair(tmp_db_url)

        snapshot = _snapshot_structure(tmp_db_url)
        assert "remark" in snapshot["department"], "自愈未补上缺失的列 remark"

        engine = create_engine(tmp_db_url)
        try:
            with engine.connect() as conn:
                name = conn.execute(text("SELECT name FROM department")).scalar()
                assert name == "老部门", "补列后已有数据丢失"
        finally:
            engine.dispose()

    def test_repairs_missing_table(self, tmp_db_url: str) -> None:
        """缺表应被补齐。"""
        _alembic_ok(tmp_db_url, "upgrade", "head")

        engine = create_engine(tmp_db_url)
        try:
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE notice"))
        finally:
            engine.dispose()

        assert "notice" not in _snapshot_structure(tmp_db_url), "脏态构造失败：notice 表仍存在"

        self._repair(tmp_db_url)

        assert "notice" in _snapshot_structure(tmp_db_url), "自愈未补上缺失的表 notice"

    def test_noop_on_healthy_db(self, tmp_db_url: str) -> None:
        """结构完好的库上自愈必须是零操作（幂等，不得改动任何结构）。"""
        _alembic_ok(tmp_db_url, "upgrade", "head")
        before = _snapshot_structure(tmp_db_url)

        self._repair(tmp_db_url)

        assert _snapshot_structure(tmp_db_url) == before, "自愈在完好的库上产生了结构改动"

    def test_repaired_column_loses_constraints(self, tmp_db_url: str) -> None:
        """⚠️ 补列语句**只带类型、不带约束**：补出来的列恒为可空、无默认值。

        实现是 `col_type = column.type.compile(dialect)` →
        `ALTER TABLE "t" ADD COLUMN "c" INTEGER`，模型上的 `nullable=False`
        与 default 都不会出现。**库结构因此静默偏离模型定义**。

        本测试锁定该现状，用途有二：
        1. 它是「自愈掩盖漏迁移」的**加强版论据** —— 不仅列会被悄悄补上，
           补出来的列**语义还与模型不符**；
        2. 若将来有人给补列加上 `nullable` / default，本测试会变红，
           提醒同步更新 `.codebuddy/rules/backend-architecture.md`「脏库自愈」一节。

        用的是 `department.status`（模型为 `Field(default=0)` → `nullable=False`），
        且其补列 SQL `ADD COLUMN "status" INTEGER` 在表非空时也**不会抛错**
        （NOT NULL 约束未被带出，故不触发 SQLite「不给非空表加无默认值 NOT NULL 列」的限制）。
        """
        _alembic_ok(tmp_db_url, "upgrade", "head")

        # 表非空：证明「有数据」也不影响补列成功（NOT NULL 未被带出，故不受 SQLite 限制）
        engine = create_engine(tmp_db_url)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO department (id, name, sort, status, created_at) "
                        "VALUES ('00000000-0000-0000-0000-000000000001', '老部门', 1, 1, '2024-01-01 00:00:00')"
                    )
                )
                conn.execute(text("ALTER TABLE department DROP COLUMN status"))
        finally:
            engine.dispose()

        assert "status" not in _snapshot_structure(tmp_db_url)["department"], "脏态构造失败：status 列仍存在"

        # 自愈不应抛错（先前「撞 NOT NULL 失败」的假设是错的）
        self._repair(tmp_db_url)

        engine = create_engine(tmp_db_url)
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("PRAGMA table_info(department)")).all()
        finally:
            engine.dispose()

        status_col = next((r for r in rows if r[1] == "status"), None)
        assert status_col is not None, "自愈未补上缺失的列 status"

        # PRAGMA table_info 列序：cid, name, type, notnull, dflt_value, pk
        notnull, dflt_value = status_col[3], status_col[4]
        assert notnull == 0, (
            f"补列意外带上了 NOT NULL（notnull={notnull}）——"
            "实现若已变更，请同步更新 .codebuddy/rules/backend-architecture.md"
        )
        assert dflt_value is None, (
            f"补列意外带上了默认值（dflt_value={dflt_value!r}）——"
            "实现若已变更，请同步更新 .codebuddy/rules/backend-architecture.md"
        )
