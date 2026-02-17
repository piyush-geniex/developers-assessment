"""Add worklog payment models

Revision ID: 2024_12_20_worklog
Revises: 1a31ce608336
Create Date: 2024-12-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel.sql.sqltypes as sqltypes

# revision identifiers, used by Alembic.
revision = "2024_12_20_worklog"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure uuid-ossp extension is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create task table
    op.create_table(
        "task",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_created_at"), "task", ["created_at"], unique=False)

    # Create worklog table
    op.create_table(
        "worklog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("freelancer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["freelancer_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worklog_created_at"), "worklog", ["created_at"], unique=False)
    op.create_index(op.f("ix_worklog_task_id"), "worklog", ["task_id"], unique=False)
    op.create_index(op.f("ix_worklog_freelancer_id"), "worklog", ["freelancer_id"], unique=False)

    # Create timeentry table
    op.create_table(
        "timeentry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("description", sqltypes.AutoString(), nullable=True),
        sa.Column("entry_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["worklog_id"],
            ["worklog.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_timeentry_created_at"), "timeentry", ["created_at"], unique=False)
    op.create_index(op.f("ix_timeentry_worklog_id"), "timeentry", ["worklog_id"], unique=False)

    # Create paymentbatch table
    op.create_table(
        "paymentbatch",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sqltypes.AutoString(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("notes", sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_paymentbatch_created_at"), "paymentbatch", ["created_at"], unique=False)

    # Create payment table
    op.create_table(
        "payment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["worklog_id"],
            ["worklog.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["payment_batch_id"],
            ["paymentbatch.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_created_at"), "payment", ["created_at"], unique=False)
    op.create_index(op.f("ix_payment_worklog_id"), "payment", ["worklog_id"], unique=False)
    op.create_index(op.f("ix_payment_payment_batch_id"), "payment", ["payment_batch_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_payment_payment_batch_id"), table_name="payment")
    op.drop_index(op.f("ix_payment_worklog_id"), table_name="payment")
    op.drop_index(op.f("ix_payment_created_at"), table_name="payment")
    op.drop_table("payment")
    op.drop_index(op.f("ix_paymentbatch_created_at"), table_name="paymentbatch")
    op.drop_table("paymentbatch")
    op.drop_index(op.f("ix_timeentry_worklog_id"), table_name="timeentry")
    op.drop_index(op.f("ix_timeentry_created_at"), table_name="timeentry")
    op.drop_table("timeentry")
    op.drop_index(op.f("ix_worklog_freelancer_id"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_task_id"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_created_at"), table_name="worklog")
    op.drop_table("worklog")
    op.drop_index(op.f("ix_task_created_at"), table_name="task")
    op.drop_table("task")

