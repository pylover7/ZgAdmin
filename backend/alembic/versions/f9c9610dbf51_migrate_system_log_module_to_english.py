"""migrate_system_log_module_to_english

Revision ID: f9c9610dbf51
Revises: 1e99a7fcad44
Create Date: 2026-05-26 11:33:28.114988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'f9c9610dbf51'
down_revision: Union[str, Sequence[str], None] = '1e99a7fcad44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """将 system_log 表中 module 字段的中文值迁移为英文常量。"""
    op.execute(
        "UPDATE systemlog SET module = 'system_management' WHERE module = '系统管理'"
    )
    op.execute(
        "UPDATE systemlog SET module = 'system' WHERE module = '系统'"
    )
    op.execute(
        "UPDATE systemlog SET module = 'database' WHERE module = '数据库'"
    )


def downgrade() -> None:
    """将英文常量回滚为中文值。"""
    op.execute(
        "UPDATE systemlog SET module = '系统管理' WHERE module = 'system_management'"
    )
    op.execute(
        "UPDATE systemlog SET module = '系统' WHERE module = 'system'"
    )
    op.execute(
        "UPDATE systemlog SET module = '数据库' WHERE module = 'database'"
    )
