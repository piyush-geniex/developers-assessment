"""Add worklog settlement tables

Revision ID: 4b7c2f13a901
Revises: 1a31ce608336
Create Date: 2026-02-13 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4b7c2f13a901"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settlement_run",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("period_from", sa.Date(), nullable=False),
        sa.Column("period_to", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("meta_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_settlement_run_idempotency_key",
        "settlement_run",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_settlement_run_status", "settlement_run", ["status"], unique=False
    )
    op.create_index(
        "ix_settlement_run_period_from", "settlement_run", ["period_from"], unique=False
    )
    op.create_index(
        "ix_settlement_run_period_to", "settlement_run", ["period_to"], unique=False
    )
    op.create_index(
        "ix_settlement_run_created_at", "settlement_run", ["created_at"], unique=False
    )
    op.create_index(
        "ix_settlement_run_updated_at", "settlement_run", ["updated_at"], unique=False
    )

    op.create_table(
        "worklog",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_ref", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_worklog_user_id", "worklog", ["user_id"], unique=False)
    op.create_index("ix_worklog_task_ref", "worklog", ["task_ref"], unique=False)
    op.create_index("ix_worklog_created_at", "worklog", ["created_at"], unique=False)

    op.create_table(
        "worklog_entry",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("worklog_id", sa.BigInteger(), nullable=False),
        sa.Column("entry_type", sa.String(length=32), nullable=False),
        sa.Column("hours", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("rate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("amount_signed", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_worklog_entry_worklog_id", "worklog_entry", ["worklog_id"], unique=False
    )
    op.create_index(
        "ix_worklog_entry_entry_type", "worklog_entry", ["entry_type"], unique=False
    )
    op.create_index(
        "ix_worklog_entry_created_at", "worklog_entry", ["created_at"], unique=False
    )

    op.create_table(
        "remittance",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["settlement_run.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_remittance_user_idempotency_key",
        ),
    )
    op.create_index("ix_remittance_run_id", "remittance", ["run_id"], unique=False)
    op.create_index("ix_remittance_user_id", "remittance", ["user_id"], unique=False)
    op.create_index("ix_remittance_status", "remittance", ["status"], unique=False)
    op.create_index(
        "ix_remittance_idempotency_key", "remittance", ["idempotency_key"], unique=False
    )
    op.create_index(
        "ix_remittance_created_at", "remittance", ["created_at"], unique=False
    )
    op.create_index(
        "ix_remittance_updated_at", "remittance", ["updated_at"], unique=False
    )

    op.create_table(
        "remittance_line",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("remittance_id", sa.BigInteger(), nullable=False),
        sa.Column("worklog_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("snapshot_note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["remittance_id"], ["remittance.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_remittance_line_remittance_id",
        "remittance_line",
        ["remittance_id"],
        unique=False,
    )
    op.create_index(
        "ix_remittance_line_worklog_id", "remittance_line", ["worklog_id"], unique=False
    )
    op.create_index(
        "ix_remittance_line_created_at", "remittance_line", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_remittance_line_created_at", table_name="remittance_line")
    op.drop_index("ix_remittance_line_worklog_id", table_name="remittance_line")
    op.drop_index("ix_remittance_line_remittance_id", table_name="remittance_line")
    op.drop_table("remittance_line")

    op.drop_index("ix_remittance_updated_at", table_name="remittance")
    op.drop_index("ix_remittance_created_at", table_name="remittance")
    op.drop_index("ix_remittance_idempotency_key", table_name="remittance")
    op.drop_index("ix_remittance_status", table_name="remittance")
    op.drop_index("ix_remittance_user_id", table_name="remittance")
    op.drop_index("ix_remittance_run_id", table_name="remittance")
    op.drop_table("remittance")

    op.drop_index("ix_worklog_entry_created_at", table_name="worklog_entry")
    op.drop_index("ix_worklog_entry_entry_type", table_name="worklog_entry")
    op.drop_index("ix_worklog_entry_worklog_id", table_name="worklog_entry")
    op.drop_table("worklog_entry")

    op.drop_index("ix_worklog_created_at", table_name="worklog")
    op.drop_index("ix_worklog_task_ref", table_name="worklog")
    op.drop_index("ix_worklog_user_id", table_name="worklog")
    op.drop_table("worklog")

    op.drop_index("ix_settlement_run_updated_at", table_name="settlement_run")
    op.drop_index("ix_settlement_run_created_at", table_name="settlement_run")
    op.drop_index("ix_settlement_run_status", table_name="settlement_run")
    op.drop_index("ix_settlement_run_period_to", table_name="settlement_run")
    op.drop_index("ix_settlement_run_period_from", table_name="settlement_run")
    op.drop_index("ix_settlement_run_idempotency_key", table_name="settlement_run")
    op.drop_table("settlement_run")
