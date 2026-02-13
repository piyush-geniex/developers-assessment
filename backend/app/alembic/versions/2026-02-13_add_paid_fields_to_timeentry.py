"""Add paid fields to timeentry

Revision ID: 2026_02_13_add_paid_fields
Revises: fe24a9f2f2e2
Create Date: 2026-02-13

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_02_13_add_paid_fields"
down_revision = "fe24a9f2f2e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "timeentry",
        sa.Column("is_paid", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("timeentry", sa.Column("paid_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_timeentry_is_paid"), "timeentry", ["is_paid"], unique=False)
    op.create_index(op.f("ix_timeentry_paid_at"), "timeentry", ["paid_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_timeentry_paid_at"), table_name="timeentry")
    op.drop_index(op.f("ix_timeentry_is_paid"), table_name="timeentry")
    op.drop_column("timeentry", "paid_at")
    op.drop_column("timeentry", "is_paid")

