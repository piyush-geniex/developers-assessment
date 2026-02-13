"""Add worklog settlement tables

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2024-12-20 00:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        "remittance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_remittance_user_id"), "remittance", ["user_id"])
    op.create_index(op.f("ix_remittance_status"), "remittance", ["status"])
    op.create_index(op.f("ix_remittance_period_start"), "remittance", ["period_start"])
    op.create_index(op.f("ix_remittance_period_end"), "remittance", ["period_end"])
    op.create_index(op.f("ix_remittance_created_at"), "remittance", ["created_at"])
    op.create_index(op.f("ix_remittance_updated_at"), "remittance", ["updated_at"])

    op.create_table(
        "worklog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_worklog_user_id"), "worklog", ["user_id"])
    op.create_index(op.f("ix_worklog_task_id"), "worklog", ["task_id"])
    op.create_index(op.f("ix_worklog_created_at"), "worklog", ["created_at"])
    op.create_index(op.f("ix_worklog_updated_at"), "worklog", ["updated_at"])

    op.create_table(
        "timesegment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_timesegment_worklog_id"), "timesegment", ["worklog_id"])
    op.create_index(op.f("ix_timesegment_created_at"), "timesegment", ["created_at"])

    op.create_table(
        "adjustment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("worklog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_adjustment_worklog_id"), "adjustment", ["worklog_id"])
    op.create_index(op.f("ix_adjustment_created_at"), "adjustment", ["created_at"])


def downgrade():
    op.drop_index(op.f("ix_adjustment_created_at"), table_name="adjustment")
    op.drop_index(op.f("ix_adjustment_worklog_id"), table_name="adjustment")
    op.drop_table("adjustment")

    op.drop_index(op.f("ix_timesegment_created_at"), table_name="timesegment")
    op.drop_index(op.f("ix_timesegment_worklog_id"), table_name="timesegment")
    op.drop_table("timesegment")

    op.drop_index(op.f("ix_worklog_updated_at"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_created_at"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_task_id"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_user_id"), table_name="worklog")
    op.drop_table("worklog")

    op.drop_index(op.f("ix_remittance_updated_at"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_created_at"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_period_end"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_period_start"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_status"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_user_id"), table_name="remittance")
    op.drop_table("remittance")

