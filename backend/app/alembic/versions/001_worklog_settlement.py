"""Add worklog settlement tables

Revision ID: 001_worklog_settlement
Revises: 1a31ce608336
Create Date: 2026-01-30 15:50:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy import DECIMAL
from alembic import op

# revision identifiers, used by Alembic.
revision = "001_worklog_settlement"
down_revision = "1a31ce608336"  # Latest existing migration
branch_labels = None
depends_on = None


def upgrade():
    """Create all worklog settlement system tables."""

    # WorkLog table
    op.create_table(
        "worklog",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worker_user_id", sa.Uuid(), nullable=False),
        sa.Column("task_identifier", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["worker_user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worklog_worker_user_id"), "worklog", ["worker_user_id"])

    # TimeSegment table
    op.create_table(
        "time_segment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worklog_id", sa.Uuid(), nullable=False),
        sa.Column("hours_worked", DECIMAL(10, 2), nullable=False),
        sa.Column("hourly_rate", DECIMAL(10, 2), nullable=False),
        sa.Column("segment_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["worklog_id"],
            ["worklog.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_time_segment_worklog_id"), "time_segment", ["worklog_id"]
    )
    op.create_index(
        op.f("ix_time_segment_segment_date"), "time_segment", ["segment_date"]
    )

    # Adjustment table
    op.create_table(
        "adjustment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worklog_id", sa.Uuid(), nullable=False),
        sa.Column(
            "adjustment_type",
            sa.Enum("DEDUCTION", "ADDITION", name="adjustmenttype"),
            nullable=False,
        ),
        sa.Column("amount", DECIMAL(10, 2), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["worklog_id"],
            ["worklog.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_adjustment_worklog_id"), "adjustment", ["worklog_id"])

    # Settlement table
    op.create_table(
        "settlement",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("run_at", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("COMPLETED", "FAILED", name="settlementstatus"),
            nullable=False,
        ),
        sa.Column("total_remittances_generated", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Remittance table
    op.create_table(
        "remittance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("settlement_id", sa.Uuid(), nullable=False),
        sa.Column("worker_user_id", sa.Uuid(), nullable=False),
        sa.Column("gross_amount", DECIMAL(10, 2), nullable=False),
        sa.Column("adjustments_amount", DECIMAL(10, 2), nullable=False),
        sa.Column("net_amount", DECIMAL(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PAID", "FAILED", "CANCELLED", name="remittancestatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["settlement_id"],
            ["settlement.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["worker_user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_remittance_worker_user_id"), "remittance", ["worker_user_id"]
    )
    op.create_index(op.f("ix_remittance_status"), "remittance", ["status"])
    op.create_index(
        op.f("ix_remittance_settlement_id"), "remittance", ["settlement_id"]
    )

    # RemittanceLine table
    op.create_table(
        "remittance_line",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("remittance_id", sa.Uuid(), nullable=False),
        sa.Column("time_segment_id", sa.Uuid(), nullable=True),
        sa.Column("adjustment_id", sa.Uuid(), nullable=True),
        sa.Column("amount", DECIMAL(10, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["remittance_id"],
            ["remittance.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["time_segment_id"],
            ["time_segment.id"],
        ),
        sa.ForeignKeyConstraint(
            ["adjustment_id"],
            ["adjustment.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_remittance_line_remittance_id"),
        "remittance_line",
        ["remittance_id"],
    )
    op.create_index(
        op.f("ix_remittance_line_time_segment_id"),
        "remittance_line",
        ["time_segment_id"],
    )
    op.create_index(
        op.f("ix_remittance_line_adjustment_id"),
        "remittance_line",
        ["adjustment_id"],
    )


def downgrade():
    """Drop all worklog settlement system tables."""
    op.drop_table("remittance_line")
    op.drop_table("remittance")
    op.drop_table("settlement")
    op.drop_table("adjustment")
    op.drop_table("time_segment")
    op.drop_table("worklog")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS adjustmenttype")
    op.execute("DROP TYPE IF EXISTS settlementstatus")
    op.execute("DROP TYPE IF EXISTS remittancestatus")
