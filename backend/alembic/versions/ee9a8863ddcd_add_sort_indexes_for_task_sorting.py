"""add_sort_indexes_for_task_sorting

Revision ID: ee9a8863ddcd
Revises: 03ff0d5d6905
Create Date: 2026-02-18 07:35:15.034913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee9a8863ddcd'
down_revision: Union[str, Sequence[str], None] = '03ff0d5d6905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for efficient task sorting.

    Creates 4 indexes to support sorting by:
    - due_date (with NULL handling)
    - priority (with tiebreaker)
    - created_at (default sort)
    - title (case-insensitive with tiebreaker)

    Note: Different index syntax for PostgreSQL vs SQLite
    PostgreSQL: Supports NULLS LAST, DESC in index
    SQLite: Simpler indexes (NULLS LAST handled in query ORDER BY)
    """
    # Get database dialect name
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == 'postgresql':
        # PostgreSQL: Full composite indexes with NULLS LAST and DESC
        # Index 1: Sort by due_date (NULLS LAST, tiebreaker: created_at DESC)
        op.execute(
            'CREATE INDEX idx_tasks_user_due_date ON tasks (user_id, due_date NULLS LAST, created_at DESC)'
        )

        # Index 2: Sort by priority (tiebreaker: created_at DESC)
        op.execute(
            'CREATE INDEX idx_tasks_user_priority ON tasks (user_id, priority, created_at DESC)'
        )

        # Index 3: Sort by created_at (default sort)
        op.execute(
            'CREATE INDEX idx_tasks_user_created ON tasks (user_id, created_at DESC)'
        )

        # Index 4: Sort by title case-insensitive (tiebreaker: created_at DESC)
        op.execute(
            'CREATE INDEX idx_tasks_user_title ON tasks (user_id, LOWER(title), created_at DESC)'
        )
    else:
        # SQLite: Simpler indexes (NULLS LAST handled in query)
        # Index 1: Sort by due_date (user_id + due_date + created_at)
        op.create_index(
            'idx_tasks_user_due_date',
            'tasks',
            ['user_id', 'due_date', 'created_at'],
            unique=False
        )

        # Index 2: Sort by priority (user_id + priority + created_at)
        op.create_index(
            'idx_tasks_user_priority',
            'tasks',
            ['user_id', 'priority', 'created_at'],
            unique=False
        )

        # Index 3: Sort by created_at (user_id + created_at)
        op.create_index(
            'idx_tasks_user_created',
            'tasks',
            ['user_id', 'created_at'],
            unique=False
        )

        # Index 4: Sort by title (user_id + title + created_at)
        # Note: SQLite doesn't support expression indexes (LOWER(title)) in CREATE INDEX
        # The LOWER() will be used in the query's ORDER BY clause
        op.create_index(
            'idx_tasks_user_title',
            'tasks',
            ['user_id', 'title', 'created_at'],
            unique=False
        )


def downgrade() -> None:
    """Remove sort indexes."""
    op.drop_index('idx_tasks_user_title', table_name='tasks')
    op.drop_index('idx_tasks_user_created', table_name='tasks')
    op.drop_index('idx_tasks_user_priority', table_name='tasks')
    op.drop_index('idx_tasks_user_due_date', table_name='tasks')
