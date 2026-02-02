"""Give all current users superuser access

Revision ID: g3b4c5d6e7f8
Revises: f2a1b2c3d4e5
Create Date: 2025-02-02

"""
from alembic import op

revision = "g3b4c5d6e7f8"
down_revision = "f2a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute('UPDATE "user" SET is_superuser = true')


def downgrade():
    # Revert: set is_superuser = false for all except the first superuser (cannot know which)
    op.execute('UPDATE "user" SET is_superuser = false')
