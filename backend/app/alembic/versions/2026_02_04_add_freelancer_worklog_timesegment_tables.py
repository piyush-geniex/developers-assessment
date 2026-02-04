"""add freelancer worklog timesegment tables

Revision ID: 2026_02_04_worklog
Revises: 1a31ce608336
Create Date: 2026-02-04 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_02_04_worklog'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Create freelancer table
    op.create_table('freelancer',
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_freelancer_created_at'), 'freelancer', ['created_at'], unique=False)
    op.create_index(op.f('ix_freelancer_user_id'), 'freelancer', ['user_id'], unique=False)

    # Create worklog table
    op.create_table('worklog',
        sa.Column('task_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('task_description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('payment_status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('freelancer_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['freelancer_id'], ['freelancer.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worklog_created_at'), 'worklog', ['created_at'], unique=False)
    op.create_index(op.f('ix_worklog_freelancer_id'), 'worklog', ['freelancer_id'], unique=False)
    op.create_index(op.f('ix_worklog_paid_at'), 'worklog', ['paid_at'], unique=False)

    # Create timesegment table
    op.create_table('timesegment',
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('segment_date', sa.DateTime(), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('worklog_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['worklog_id'], ['worklog.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timesegment_worklog_id'), 'timesegment', ['worklog_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_timesegment_worklog_id'), table_name='timesegment')
    op.drop_table('timesegment')
    
    op.drop_index(op.f('ix_worklog_paid_at'), table_name='worklog')
    op.drop_index(op.f('ix_worklog_freelancer_id'), table_name='worklog')
    op.drop_index(op.f('ix_worklog_created_at'), table_name='worklog')
    op.drop_table('worklog')
    
    op.drop_index(op.f('ix_freelancer_user_id'), table_name='freelancer')
    op.drop_index(op.f('ix_freelancer_created_at'), table_name='freelancer')
    op.drop_table('freelancer')
