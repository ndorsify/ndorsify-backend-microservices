"""add campaigns.funded_at

Revision ID: 0002_add_funded_at
Revises: 0001_initial
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_funded_at"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("campaigns", sa.Column("funded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("campaigns", "funded_at")
