"""Add worklog, time_entry, payment_batch tables

Revision ID: b4e8f2a1c9d7
Revises: 1a31ce608336
Create Date: 2025-02-12

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b4e8f2a1c9d7"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "payment_batch",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payment_batch_status"), "payment_batch", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_payment_batch_created_at"),
        "payment_batch",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "worklog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sqlmodel.sql.sqltypes.AutoString(length=32),
            nullable=False,
        ),
        sa.Column("payment_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["payment_batch_id"], ["payment_batch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worklog_item_id"), "worklog", ["item_id"], unique=False)
    op.create_index(op.f("ix_worklog_user_id"), "worklog", ["user_id"], unique=False)
    op.create_index(op.f("ix_worklog_status"), "worklog", ["status"], unique=False)
    op.create_index(
        op.f("ix_worklog_payment_batch_id"),
        "worklog",
        ["payment_batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_worklog_created_at"), "worklog", ["created_at"], unique=False
    )

    op.create_table(
        "time_entry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column(
            "description",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_time_entry_worklog_id"),
        "time_entry",
        ["worklog_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_time_entry_entry_date"),
        "time_entry",
        ["entry_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_time_entry_created_at"),
        "time_entry",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_table("time_entry")
    op.drop_table("worklog")
    op.drop_table("payment_batch")
