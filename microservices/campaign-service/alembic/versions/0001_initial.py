"""initial campaign tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("deliverables", sa.JSON(), nullable=False),
        sa.Column("platforms", sa.JSON(), nullable=False),
        sa.Column("budget_amount", sa.Float(), nullable=True),
        sa.Column("budget_currency", sa.String(), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("target_audience", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
    )
    op.create_index("ix_campaigns_brand_id", "campaigns", ["brand_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("campaign_id", "creator_id", name="uq_invitation_pair"),
    )
    op.create_index("ix_invitations_campaign_id", "invitations", ["campaign_id"])
    op.create_index("ix_invitations_creator_id", "invitations", ["creator_id"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("proposal", sa.Text(), nullable=True),
        sa.Column("proposed_rate", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), server_default="submitted", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("campaign_id", "creator_id", name="uq_application_pair"),
    )
    op.create_index("ix_applications_campaign_id", "applications", ["campaign_id"])
    op.create_index("ix_applications_creator_id", "applications", ["creator_id"])


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("invitations")
    op.drop_table("campaigns")
