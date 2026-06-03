"""feat: migrate datetime columns to timezone-aware

Revision ID: 30bcfbeddb70
Revises: f9c9610dbf51
Create Date: 2026-06-03 15:39:45.091487

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "30bcfbeddb70"
down_revision: str | Sequence[str] | None = "f9c9610dbf51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 所有需要从 timestamp without tz → timestamp with tz 的列
_TIMEZONE_COLUMNS = [
    ("user", "created_at"),
    ("user", "last_login"),
    ("user", "locked_until"),
    ("role", "created_at"),
    ("menu", "created_at"),
    ("api", "created_at"),
    ("notice", "created_at"),
    ("noticeread", "created_at"),
    ("file", "created_at"),
    ("department", "created_at"),
    ("securitypolicy", "created_at"),
    ("iprule", "created_at"),
    ("siteconfig", "created_at"),
    ("oauthconfig", "created_at"),
    ("emailconfig", "created_at"),
    ("loginlog", "time"),
    ("operationlog", "time"),
    ("systemlog", "time"),
]


def upgrade() -> None:
    """将所有 datetime 列从 timestamp without time zone 迁移为 timestamp with time zone。"""
    # SQLite 不支持 timezone 修饰符，跳过
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    insp = inspect(bind)
    for table_name, column_name in _TIMEZONE_COLUMNS:
        if insp.has_table(table_name):
            op.alter_column(
                table_name,
                column_name,
                type_=sa.DateTime(timezone=True),
                existing_type=sa.DateTime(),
                existing_nullable=True,
            )


def downgrade() -> None:
    """将 timestamp with time zone 回退为 timestamp without time zone。"""
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return

    insp = inspect(bind)
    for table_name, column_name in _TIMEZONE_COLUMNS:
        if insp.has_table(table_name):
            op.alter_column(
                table_name,
                column_name,
                type_=sa.DateTime(),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=True,
            )
