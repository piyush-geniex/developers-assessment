"""Add worklog settlement system

Revision ID: abc123def456
Revises: 1a31ce608336
Create Date: 2026-02-03 15:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "abc123def456"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # Create worklog table
    op.create_table(
        "worklog",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_worklog_user_id"), "worklog", ["user_id"], unique=False)
    op.create_index(op.f("ix_worklog_created_at"), "worklog", ["created_at"], unique=False)
    
    # Create time_segment table
    op.create_table(
        "timesegment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worklog_id", sa.Uuid(), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("is_removed", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_timesegment_worklog_id"), "timesegment", ["worklog_id"], unique=False)
    op.create_index(op.f("ix_timesegment_recorded_at"), "timesegment", ["recorded_at"], unique=False)
    
    # Create adjustment table
    op.create_table(
        "adjustment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worklog_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_adjustment_worklog_id"), "adjustment", ["worklog_id"], unique=False)
    op.create_index(op.f("ix_adjustment_created_at"), "adjustment", ["created_at"], unique=False)
    
    # Create remittance table
    op.create_table(
        "remittance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_remittance_user_id"), "remittance", ["user_id"], unique=False)
    op.create_index(op.f("ix_remittance_period_start"), "remittance", ["period_start"], unique=False)
    op.create_index(op.f("ix_remittance_period_end"), "remittance", ["period_end"], unique=False)
    op.create_index(op.f("ix_remittance_status"), "remittance", ["status"], unique=False)
    op.create_index(op.f("ix_remittance_created_at"), "remittance", ["created_at"], unique=False)
    
    # Create worklog_settlement table
    op.create_table(
        "worklogsettlement",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worklog_id", sa.Uuid(), nullable=False),
        sa.Column("remittance_id", sa.Uuid(), nullable=False),
        sa.Column("amount_settled", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["remittance_id"], ["remittance.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_worklogsettlement_worklog_id"), "worklogsettlement", ["worklog_id"], unique=False)
    op.create_index(op.f("ix_worklogsettlement_remittance_id"), "worklogsettlement", ["remittance_id"], unique=False)
    op.create_index(op.f("ix_worklogsettlement_created_at"), "worklogsettlement", ["created_at"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_worklogsettlement_created_at"), table_name="worklogsettlement")
    op.drop_index(op.f("ix_worklogsettlement_remittance_id"), table_name="worklogsettlement")
    op.drop_index(op.f("ix_worklogsettlement_worklog_id"), table_name="worklogsettlement")
    op.drop_table("worklogsettlement")
    
    op.drop_index(op.f("ix_remittance_created_at"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_status"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_period_end"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_period_start"), table_name="remittance")
    op.drop_index(op.f("ix_remittance_user_id"), table_name="remittance")
    op.drop_table("remittance")
    
    op.drop_index(op.f("ix_adjustment_created_at"), table_name="adjustment")
    op.drop_index(op.f("ix_adjustment_worklog_id"), table_name="adjustment")
    op.drop_table("adjustment")
    
    op.drop_index(op.f("ix_timesegment_recorded_at"), table_name="timesegment")
    op.drop_index(op.f("ix_timesegment_worklog_id"), table_name="timesegment")
    op.drop_table("timesegment")
    
    op.drop_index(op.f("ix_worklog_created_at"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_user_id"), table_name="worklog")
    op.drop_table("worklog")
