"""update worklog add item_id hours

Revision ID: 2026_02_04_wl_item
Revises: 2026_02_04_worklog
Create Date: 2026-02-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_02_04_wl_item'
down_revision = '2026_02_04_worklog'
branch_labels = None
depends_on = None


def upgrade():
    # Add item_id column
    op.add_column('worklog', sa.Column('item_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_worklog_item_id'), 'worklog', ['item_id'], unique=False)
    op.create_foreign_key(None, 'worklog', 'item', ['item_id'], ['id'])
    
    # Add hours column
    op.add_column('worklog', sa.Column('hours', sa.Float(), nullable=False, server_default='0.0'))
    
    # Drop old columns
    op.drop_column('worklog', 'task_description')
    op.drop_column('worklog', 'task_name')


def downgrade():
    # Add back old columns
    op.add_column('worklog', sa.Column('task_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.add_column('worklog', sa.Column('task_description', sa.VARCHAR(), autoincrement=False, nullable=True))
    
    # Drop new columns
    op.drop_constraint(None, 'worklog', type_='foreignkey')
    op.drop_index(op.f('ix_worklog_item_id'), table_name='worklog')
    op.drop_column('worklog', 'hours')
    op.drop_column('worklog', 'item_id')
