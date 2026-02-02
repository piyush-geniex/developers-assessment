"""Add worklog and remittance models

Revision ID: f2a1b2c3d4e5
Revises: 1a31ce608336
Create Date: 2025-02-02

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

revision = "f2a1b2c3d4e5"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE remittancestatus AS ENUM ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')")

    op.create_table(
        "task",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "remittance",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("period_end", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "COMPLETED", "FAILED", "CANCELLED",
                name="remittancestatus", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("total_amount_cents", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "worklog",
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("remittance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["remittance_id"], ["remittance.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "timeentry",
        sa.Column("work_log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_date", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["work_log_id"], ["worklog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("timeentry")
    op.drop_table("worklog")
    op.drop_table("remittance")
    op.drop_table("task")
    op.execute("DROP TYPE IF EXISTS remittancestatus")
