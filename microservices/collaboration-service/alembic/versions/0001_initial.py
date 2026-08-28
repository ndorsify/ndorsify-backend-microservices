"""initial collaboration tables

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
        "collaborations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), server_default="accepted", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_collaborations_campaign_id", "collaborations", ["campaign_id"])
    op.create_index("ix_collaborations_brand_id", "collaborations", ["brand_id"])
    op.create_index("ix_collaborations_creator_id", "collaborations", ["creator_id"])

    op.create_table(
        "deliverables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("collaboration_id", sa.Integer(), sa.ForeignKey("collaborations.id"), nullable=False),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), server_default="todo", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deliverables_collaboration_id", "deliverables", ["collaboration_id"])

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("deliverable_id", sa.Integer(), sa.ForeignKey("deliverables.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("file_refs", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("submitted_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_submissions_deliverable_id", "submissions", ["deliverable_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reviews_submission_id", "reviews", ["submission_id"])


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("submissions")
    op.drop_table("deliverables")
    op.drop_table("collaborations")
