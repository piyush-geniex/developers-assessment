"""Add worklog payment models

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2024-07-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    userrole_enum = postgresql.ENUM('ADMIN', 'FREELANCER', name='userrole', create_type=False)
    userrole_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('user', sa.Column('role', userrole_enum, nullable=False, server_default='FREELANCER'))
    op.add_column('user', sa.Column('hourly_rate', sa.Float(), nullable=True))

    op.create_table(
        'task',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'timeentry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('freelancer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['freelancer_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_timeentry_task_id', 'timeentry', ['task_id'])
    op.create_index('ix_timeentry_freelancer_id', 'timeentry', ['freelancer_id'])
    op.create_index('ix_timeentry_start_time', 'timeentry', ['start_time'])

    paymentbatchstatus_enum = postgresql.ENUM('DRAFT', 'CONFIRMED', name='paymentbatchstatus', create_type=False)
    paymentbatchstatus_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'paymentbatch',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date_from', sa.DateTime(), nullable=False),
        sa.Column('date_to', sa.DateTime(), nullable=False),
        sa.Column('status', paymentbatchstatus_enum, nullable=False, server_default='DRAFT'),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_paymentbatch_created_by_id', 'paymentbatch', ['created_by_id'])
    op.create_index('ix_paymentbatch_status', 'paymentbatch', ['status'])

    op.create_table(
        'payment',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('freelancer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('time_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['paymentbatch.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['freelancer_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['time_entry_id'], ['timeentry.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_batch_id', 'payment', ['batch_id'])
    op.create_index('ix_payment_freelancer_id', 'payment', ['freelancer_id'])
    op.create_index('ix_payment_time_entry_id', 'payment', ['time_entry_id'])


def downgrade():
    op.drop_index('ix_payment_time_entry_id', 'payment')
    op.drop_index('ix_payment_freelancer_id', 'payment')
    op.drop_index('ix_payment_batch_id', 'payment')
    op.drop_table('payment')

    op.drop_index('ix_paymentbatch_status', 'paymentbatch')
    op.drop_index('ix_paymentbatch_created_by_id', 'paymentbatch')
    op.drop_table('paymentbatch')

    op.drop_index('ix_timeentry_start_time', 'timeentry')
    op.drop_index('ix_timeentry_freelancer_id', 'timeentry')
    op.drop_index('ix_timeentry_task_id', 'timeentry')
    op.drop_table('timeentry')

    op.drop_table('task')

    op.drop_column('user', 'hourly_rate')
    op.drop_column('user', 'role')

    postgresql.ENUM(name='paymentbatchstatus').drop(op.get_bind())
    postgresql.ENUM(name='userrole').drop(op.get_bind())
