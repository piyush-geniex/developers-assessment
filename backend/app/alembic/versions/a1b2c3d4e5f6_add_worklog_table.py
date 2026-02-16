"""Add worklog table

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2026-02-14 02:27:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "worklog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("freelancer_id", sa.Integer(), nullable=False),
        sa.Column("task_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("time_entries", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("total_hours", sa.Float(), nullable=False),
        sa.Column("hourly_rate", sa.Float(), nullable=False),
        sa.Column("total_earned", sa.Float(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worklog_freelancer_id"), "worklog", ["freelancer_id"], unique=False)
    op.create_index(op.f("ix_worklog_status"), "worklog", ["status"], unique=False)
    op.create_index(op.f("ix_worklog_created_at"), "worklog", ["created_at"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_worklog_created_at"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_status"), table_name="worklog")
    op.drop_index(op.f("ix_worklog_freelancer_id"), table_name="worklog")
    op.drop_table("worklog")
