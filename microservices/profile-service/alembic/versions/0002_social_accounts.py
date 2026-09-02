"""add social_accounts

Revision ID: 0002_social_accounts
Revises: 0001_initial
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_social_accounts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("external_account_id", sa.String(), nullable=False),
        sa.Column("handle", sa.String(), nullable=True),
        sa.Column("follower_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("engagement_rate", sa.Float(), server_default="0", nullable=False),
        sa.Column("connected_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "platform", name="uq_social_account_platform"),
    )
    op.create_index("ix_social_accounts_user_id", "social_accounts", ["user_id"])


def downgrade() -> None:
    op.drop_table("social_accounts")
