"""Add payment_batch_id to worklog

Revision ID: 20250218_wl_pay
Revises: 20250218_worklog
Create Date: 2025-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20250218_wl_pay"
down_revision = "20250218_worklog"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "worklog",
        sa.Column("payment_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "worklog_payment_batch_id_fkey",
        "worklog",
        "payment_batch",
        ["payment_batch_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_worklog_payment_batch_id"),
        "worklog",
        ["payment_batch_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_worklog_payment_batch_id"), table_name="worklog")
    op.drop_constraint("worklog_payment_batch_id_fkey", "worklog", type_="foreignkey")
    op.drop_column("worklog", "payment_batch_id")
