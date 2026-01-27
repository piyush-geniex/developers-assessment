"""Add work log and remittance tables

Revision ID: f1265a4b8c01
Revises: 1a31ce608336
Create Date: 2026-01-27 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f1265a4b8c01"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("total_remitted_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "work_log_segment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=False), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=False), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["work_log.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "work_log_adjustment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["work_log.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "remittance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="SUCCEEDED"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_work_log_user_id", "work_log", ["user_id"])
    op.create_index("ix_work_log_segment_worklog_id", "work_log_segment", ["worklog_id"])
    op.create_index("ix_work_log_adjustment_worklog_id", "work_log_adjustment", ["worklog_id"])
    op.create_index("ix_remittance_user_id", "remittance", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_remittance_user_id", table_name="remittance")
    op.drop_index("ix_work_log_adjustment_worklog_id", table_name="work_log_adjustment")
    op.drop_index("ix_work_log_segment_worklog_id", table_name="work_log_segment")
    op.drop_index("ix_work_log_user_id", table_name="work_log")
    op.drop_table("remittance")
    op.drop_table("work_log_adjustment")
    op.drop_table("work_log_segment")
    op.drop_table("work_log")
