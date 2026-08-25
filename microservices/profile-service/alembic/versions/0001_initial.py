"""initial profile tables

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
        "creator_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("niches", sa.JSON(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("completion_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_creator_profiles_user_id", "creator_profiles", ["user_id"], unique=True
    )

    op.create_table(
        "brand_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_brand_profiles_user_id", "brand_profiles", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_table("brand_profiles")
    op.drop_table("creator_profiles")
