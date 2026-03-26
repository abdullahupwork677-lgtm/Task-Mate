"""add_due_date_to_tasks

Revision ID: 1c17986ce493
Revises: 8d62d630f4cb
Create Date: 2026-01-08 13:29:12.569806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1c17986ce493'
down_revision: Union[str, Sequence[str], None] = '8d62d630f4cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add due_date column
    op.add_column('tasks', sa.Column('due_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove due_date column
    op.drop_column('tasks', 'due_date')
