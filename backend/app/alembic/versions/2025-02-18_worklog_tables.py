"""Add task, worklog, time_entry, payment_batch tables

Revision ID: 20250218_worklog
Revises: 1a31ce608336
Create Date: 2025-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250218_worklog"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        "task",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_name"), "task", ["name"], unique=False)
    op.create_index(op.f("ix_task_created_at"), "task", ["created_at"], unique=False)

    op.create_table(
        "worklog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_earned", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worklog_task_id"), "worklog", ["task_id"], unique=False)
    op.create_index(op.f("ix_worklog_owner_id"), "worklog", ["owner_id"], unique=False)
    op.create_index(op.f("ix_worklog_status"), "worklog", ["status"], unique=False)
    op.create_index(op.f("ix_worklog_created_at"), "worklog", ["created_at"], unique=False)

    op.create_table(
        "time_entry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("logged_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_time_entry_worklog_id"), "time_entry", ["worklog_id"], unique=False)
    op.create_index(op.f("ix_time_entry_logged_at"), "time_entry", ["logged_at"], unique=False)

    op.create_table(
        "payment_batch",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("worklog_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_batch_created_at"), "payment_batch", ["created_at"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_payment_batch_created_at"), table_name="payment_batch")
    op.drop_table("payment_batch")
    op.drop_index(op.f("ix_time_entry_logged_at"), table_name="time_entry")
    op.drop_index(op.f("ix_time_entry_worklog_id"), table_name="time_entry")
    op.drop_table("time_entry")
    op.drop_index(op.f("ix_worklog_created_at"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_status"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_owner_id"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_task_id"), table_name="worklog")
    op.drop_table("worklog")
    op.drop_index(op.f("ix_task_created_at"), table_name="task")
    op.drop_index(op.f("ix_task_name"), table_name="task")
    op.drop_table("task")
