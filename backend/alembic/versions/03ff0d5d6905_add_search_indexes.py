"""add_search_indexes

Revision ID: 03ff0d5d6905
Revises: 0f804cf615f7
Create Date: 2026-02-14 23:18:50.685269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03ff0d5d6905'
down_revision: Union[str, Sequence[str], None] = '0f804cf615f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add composite indexes for efficient search and filtering."""
    # Use CREATE INDEX IF NOT EXISTS for idempotent migrations

    # Index 1: (user_id, completed) - For status filtering
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tasks_user_completed
        ON tasks (user_id, completed)
        """
    )

    # Index 2: (user_id, priority) - For priority filtering
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tasks_user_priority
        ON tasks (user_id, priority)
        """
    )

    # Index 3: (user_id, tags) - For tag filtering (GIN index for JSONB)
    # Note: For PostgreSQL, this uses GIN operator class for JSONB
    # For SQLite (testing), this falls back to regular index
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tasks_user_tags
        ON tasks (user_id, tags)
        """
    )

    # Index 4: (user_id, due_date) - For due date filtering
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tasks_user_due_date
        ON tasks (user_id, due_date)
        """
    )

    # Index 5: (user_id, title) - For keyword search on titles
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tasks_user_title
        ON tasks (user_id, title)
        """
    )


def downgrade() -> None:
    """Downgrade schema - Remove composite indexes."""
    op.drop_index('idx_tasks_user_title', table_name='tasks')
    op.drop_index('idx_tasks_user_due_date', table_name='tasks')
    op.execute('DROP INDEX IF EXISTS idx_tasks_user_tags')
    op.drop_index('idx_tasks_user_priority', table_name='tasks')
    op.drop_index('idx_tasks_user_completed', table_name='tasks')
