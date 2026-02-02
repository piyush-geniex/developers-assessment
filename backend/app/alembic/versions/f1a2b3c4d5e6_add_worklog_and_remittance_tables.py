"""Add WorkLog, WorkLogSegment, WorkLogAdjustment and Remittance tables

Revision ID: f1a2b3c4d5e6
Revises: 1a31ce608336
Create Date: 2026-02-02 18:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worklog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_code", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "worklogsegment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Numeric(), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(), nullable=False),
        sa.Column("is_questioned", sa.Boolean(), nullable=False),
        sa.Column("is_settled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "worklogadjustment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("is_settled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"]),
        sa.ForeignKeyConstraint(["segment_id"], ["worklogsegment.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "remittance",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("remittance")
    op.drop_table("worklogadjustment")
    op.drop_table("worklogsegment")
    op.drop_table("worklog")
