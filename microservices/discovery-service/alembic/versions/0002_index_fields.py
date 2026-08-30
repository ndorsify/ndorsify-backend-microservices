"""creator_index: handle, platforms, rate_per_post, verified

Adds the fields the marketplace card and its filters need (platform, rate,
verification) on top of the P0 index.

Revision ID: 0002_index_fields
Revises: 0001_initial
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_index_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("creator_index", sa.Column("handle", sa.String(), nullable=True))
    op.add_column(
        "creator_index",
        sa.Column("platforms", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "creator_index",
        sa.Column("platforms_text", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "creator_index",
        sa.Column("rate_per_post", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "creator_index",
        sa.Column(
            "verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_creator_index_handle", "creator_index", ["handle"])


def downgrade() -> None:
    op.drop_index("ix_creator_index_handle", table_name="creator_index")
    op.drop_column("creator_index", "verified")
    op.drop_column("creator_index", "rate_per_post")
    op.drop_column("creator_index", "platforms_text")
    op.drop_column("creator_index", "platforms")
    op.drop_column("creator_index", "handle")
