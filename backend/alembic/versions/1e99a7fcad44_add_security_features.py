"""add_security_features

Revision ID: 1e99a7fcad44
Revises: 582670eaa9ea
Create Date: 2026-05-23 04:12:13.233109

Note: This migration's original operations (add security columns to user,
modify foreign key CASCADE) are now included in the initial_create_all_tables
baseline migration. The upgrade/downgrade functions are intentionally empty
to preserve the migration chain history.

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '1e99a7fcad44'
down_revision: str | Sequence[str] | None = '582670eaa9ea'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema — operations absorbed into initial_create_all_tables baseline."""
    pass


def downgrade() -> None:
    """Downgrade schema — operations absorbed into initial_create_all_tables baseline."""
    pass
