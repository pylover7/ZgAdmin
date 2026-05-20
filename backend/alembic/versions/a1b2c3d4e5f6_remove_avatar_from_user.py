"""remove avatar column from user table

Revision ID: a1b2c3d4e5f6
Revises: ec209d42800e
Create Date: 2026-05-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'ec209d42800e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated ###
    op.drop_column('user', 'avatar')
    # ### end auto generated ###


def downgrade() -> None:
    # ### commands auto generated ###
    op.add_column('user', sa.Column('avatar', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    # ### end auto generated ###
