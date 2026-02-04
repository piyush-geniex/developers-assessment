"""Add worklog payment tables

Revision ID: a1b2c3d4e5f6
Revises: d98dd8ec85a3
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd98dd8ec85a3'
branch_labels = None
depends_on = None


def upgrade():
    # Create worklog table
    op.create_table(
        'worklog',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('freelancer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_hours', sa.Float(), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['freelancer_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worklog_created_at'), 'worklog', ['created_at'], unique=False)

    # Create timeentry table
    op.create_table(
        'timeentry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('worklog_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['worklog_id'], ['worklog.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create payment table
    op.create_table(
        'payment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_created_at'), 'payment', ['created_at'], unique=False)

    # Create paymentworklog table (junction)
    op.create_table(
        'paymentworklog',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('worklog_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worklog_id'], ['worklog.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('paymentworklog')
    op.drop_index(op.f('ix_payment_created_at'), table_name='payment')
    op.drop_table('payment')
    op.drop_table('timeentry')
    op.drop_index(op.f('ix_worklog_created_at'), table_name='worklog')
    op.drop_table('worklog')
