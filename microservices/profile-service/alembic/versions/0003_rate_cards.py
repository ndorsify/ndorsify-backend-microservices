"""add rate_cards and rate_card_packages

Revision ID: 0003_rate_cards
Revises: 0002_social_accounts
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_rate_cards"
down_revision = "0002_social_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rate_cards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hidden", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_rate_cards_user_id", "rate_cards", ["user_id"], unique=True)
    op.create_table(
        "rate_card_packages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "rate_card_id",
            sa.Integer(),
            sa.ForeignKey("rate_cards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("turnaround_days", sa.Integer(), nullable=False),
        sa.Column("visible", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_rate_card_packages_rate_card_id", "rate_card_packages", ["rate_card_id"]
    )


def downgrade() -> None:
    op.drop_table("rate_card_packages")
    op.drop_table("rate_cards")
