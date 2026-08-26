"""initial discovery tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "creator_index",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("niches", sa.JSON(), nullable=False),
        sa.Column("niches_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("follower_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("engagement_rate", sa.Float(), server_default="0", nullable=False),
        sa.Column("avg_rating", sa.Float(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_creator_index_user_id", "creator_index", ["user_id"], unique=True)
    op.create_index("ix_creator_index_display_name", "creator_index", ["display_name"])
    op.create_index("ix_creator_index_location", "creator_index", ["location"])

    op.create_table(
        "shortlists",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_shortlists_brand_id", "shortlists", ["brand_id"])

    op.create_table(
        "shortlist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "shortlist_id",
            sa.Integer(),
            sa.ForeignKey("shortlists.id"),
            nullable=False,
        ),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("shortlist_id", "creator_id", name="uq_shortlist_creator"),
    )
    op.create_index("ix_shortlist_items_shortlist_id", "shortlist_items", ["shortlist_id"])


def downgrade() -> None:
    op.drop_table("shortlist_items")
    op.drop_table("shortlists")
    op.drop_table("creator_index")
