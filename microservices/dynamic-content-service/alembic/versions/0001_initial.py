"""initial content table

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("lookup_text1", sa.String(), nullable=True),
        sa.Column("lookup_value1", sa.String(), nullable=True),
        sa.Column("lookup_text2", sa.String(), nullable=True),
        sa.Column("lookup_value2", sa.String(), nullable=True),
        sa.Column("lookup_text3", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("modified_by", sa.String(), nullable=True),
        sa.Column("created_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("modified_date", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("content")
