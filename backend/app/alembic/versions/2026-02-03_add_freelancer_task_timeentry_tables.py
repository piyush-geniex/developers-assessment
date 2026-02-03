"""Add freelancer task timeentry tables

Revision ID: b2c3d4e5f6g7
Revises: 1a31ce608336
Create Date: 2026-02-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6g7"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "freelancer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hourly_rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_freelancer_email"), "freelancer", ["email"], unique=True)
    op.create_index(
        op.f("ix_freelancer_created_at"), "freelancer", ["created_at"], unique=False
    )

    op.create_table(
        "task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_created_at"), "task", ["created_at"], unique=False)

    op.create_table(
        "timeentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("freelancer_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("hours", sa.Float(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("logged_at", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["freelancer_id"],
            ["freelancer.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_timeentry_freelancer_id"), "timeentry", ["freelancer_id"], unique=False
    )
    op.create_index(
        op.f("ix_timeentry_task_id"), "timeentry", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_timeentry_logged_at"), "timeentry", ["logged_at"], unique=False
    )
    op.create_index(
        op.f("ix_timeentry_created_at"), "timeentry", ["created_at"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_timeentry_created_at"), table_name="timeentry")
    op.drop_index(op.f("ix_timeentry_logged_at"), table_name="timeentry")
    op.drop_index(op.f("ix_timeentry_task_id"), table_name="timeentry")
    op.drop_index(op.f("ix_timeentry_freelancer_id"), table_name="timeentry")
    op.drop_table("timeentry")

    op.drop_index(op.f("ix_task_created_at"), table_name="task")
    op.drop_table("task")

    op.drop_index(op.f("ix_freelancer_created_at"), table_name="freelancer")
    op.drop_index(op.f("ix_freelancer_email"), table_name="freelancer")
    op.drop_table("freelancer")
