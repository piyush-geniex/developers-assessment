"""Add hashed_password to freelancer table for freelancer authentication

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2024-10-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add hashed_password column to freelancer table (nullable for existing records)
    op.add_column('freelancer', sa.Column('hashed_password', sa.String(), nullable=True))


def downgrade():
    # Remove hashed_password column
    op.drop_column('freelancer', 'hashed_password')
