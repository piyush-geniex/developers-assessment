"""Add worklog payment models (Freelancer, WorkLog, TimeEntry, PaymentBatch)

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2024-10-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Create worklogstatus enum
    worklogstatus_enum = postgresql.ENUM(
        'pending', 'approved', 'paid', 'rejected',
        name='worklogstatus',
        create_type=False
    )
    worklogstatus_enum.create(op.get_bind(), checkfirst=True)

    # Create paymentbatchstatus enum
    paymentbatchstatus_enum = postgresql.ENUM(
        'draft', 'processing', 'completed', 'failed',
        name='paymentbatchstatus',
        create_type=False
    )
    paymentbatchstatus_enum.create(op.get_bind(), checkfirst=True)

    # Create freelancer table
    op.create_table(
        'freelancer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=False, server_default='50.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_freelancer_email', 'freelancer', ['email'], unique=True)

    # Create paymentbatch table
    op.create_table(
        'paymentbatch',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', postgresql.ENUM('draft', 'processing', 'completed', 'failed', name='paymentbatchstatus', create_type=False), nullable=False, server_default='completed'),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.ForeignKeyConstraint(['processed_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create worklog table
    op.create_table(
        'worklog',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('freelancer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'paid', 'rejected', name='worklogstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('payment_batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['freelancer_id'], ['freelancer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_batch_id'], ['paymentbatch.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_worklog_freelancer_id', 'worklog', ['freelancer_id'])
    op.create_index('ix_worklog_status', 'worklog', ['status'])
    op.create_index('ix_worklog_created_at', 'worklog', ['created_at'])
    op.create_index('ix_worklog_status_created_at', 'worklog', ['status', 'created_at'])

    # Create timeentry table
    op.create_table(
        'timeentry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_log_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['work_log_id'], ['worklog.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_timeentry_work_log_id', 'timeentry', ['work_log_id'])


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_timeentry_work_log_id', table_name='timeentry')
    op.drop_table('timeentry')

    op.drop_index('ix_worklog_status_created_at', table_name='worklog')
    op.drop_index('ix_worklog_created_at', table_name='worklog')
    op.drop_index('ix_worklog_status', table_name='worklog')
    op.drop_index('ix_worklog_freelancer_id', table_name='worklog')
    op.drop_table('worklog')

    op.drop_table('paymentbatch')

    op.drop_index('ix_freelancer_email', table_name='freelancer')
    op.drop_table('freelancer')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS worklogstatus')
    op.execute('DROP TYPE IF EXISTS paymentbatchstatus')
