"""Add worklog and payment tables

Revision ID: a7f3b2c1d4e8
Revises: 1a31ce608336
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = "a7f3b2c1d4e8"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # Add hourly_rate to user
    op.add_column("user", sa.Column("hourly_rate", sa.Float(), nullable=True))

    # Create worklog table
    op.create_table(
        "worklog",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column("hourly_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["freelancer_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_worklog_freelancer_id", "worklog", ["freelancer_id"])
    op.create_index("ix_worklog_created_at", "worklog", ["created_at"])

    # Create time_entry table
    op.create_table(
        "time_entry",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("worklog_id", sa.UUID(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("hours", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_time_entry_worklog_id", "time_entry", ["worklog_id"])
    op.create_index("ix_time_entry_start_time", "time_entry", ["start_time"])

    # Create payment_batch table
    op.create_table(
        "payment_batch",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="draft"),
        sa.Column("created_by_id", sa.UUID(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_batch_date_from", "payment_batch", ["date_from"])
    op.create_index("ix_payment_batch_created_by_id", "payment_batch", ["created_by_id"])
    op.create_index("ix_payment_batch_created_at", "payment_batch", ["created_at"])

    # Create payment table
    op.create_table(
        "payment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("batch_id", sa.UUID(), nullable=False),
        sa.Column("time_entry_id", sa.UUID(), nullable=False),
        sa.Column("worklog_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("hourly_rate", sa.Float(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["payment_batch.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["time_entry_id"], ["time_entry.id"]),
        sa.ForeignKeyConstraint(["worklog_id"], ["worklog.id"]),
        sa.ForeignKeyConstraint(["freelancer_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_batch_id", "payment", ["batch_id"])
    op.create_index("ix_payment_time_entry_id", "payment", ["time_entry_id"])
    op.create_index("ix_payment_worklog_id", "payment", ["worklog_id"])
    op.create_index("ix_payment_freelancer_id", "payment", ["freelancer_id"])


def downgrade():
    op.drop_table("payment")
    op.drop_table("payment_batch")
    op.drop_table("time_entry")
    op.drop_table("worklog")
    op.drop_column("user", "hourly_rate")
