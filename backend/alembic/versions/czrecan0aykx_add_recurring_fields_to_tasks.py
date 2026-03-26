"""Add recurring fields to tasks

Revision ID: czrecan0aykx
Revises: 3b7378ec255f
Create Date: 2026-02-09 05:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'czrecan0aykx'
down_revision: Union[str, Sequence[str], None] = '3b7378ec255f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add recurring task fields and indexes."""

    # Add is_recurring column (boolean, default False, indexed)
    op.add_column(
        'tasks',
        sa.Column(
            'is_recurring',
            sa.Boolean(),
            nullable=False,
            server_default='false'
        )
    )

    # Add recurrence_pattern column (varchar, nullable)
    op.add_column(
        'tasks',
        sa.Column(
            'recurrence_pattern',
            sa.String(length=50),
            nullable=True
        )
    )

    # Add recurrence_end_date column (datetime, nullable)
    op.add_column(
        'tasks',
        sa.Column(
            'recurrence_end_date',
            sa.DateTime(),
            nullable=True
        )
    )

    # Add parent_task_id column (integer, nullable, foreign key)
    op.add_column(
        'tasks',
        sa.Column(
            'parent_task_id',
            sa.Integer(),
            nullable=True
        )
    )

    # Add foreign key constraint for parent_task_id
    op.create_foreign_key(
        'fk_tasks_parent_task_id',
        'tasks',
        'tasks',
        ['parent_task_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create composite index on (user_id, is_recurring) for filtering recurring tasks
    # Partial index: only indexes rows where is_recurring = TRUE
    op.execute(
        """
        CREATE INDEX ix_tasks_user_recurring
        ON tasks (user_id, is_recurring)
        WHERE is_recurring = TRUE
        """
    )

    # Create index on parent_task_id for efficient lookups
    op.create_index(
        'ix_tasks_parent_task_id',
        'tasks',
        ['parent_task_id']
    )

    # Create unique partial index to prevent duplicate next occurrences
    # Ensures only ONE incomplete occurrence per parent task per due date
    op.execute(
        """
        CREATE UNIQUE INDEX ix_tasks_parent_due_unique
        ON tasks (parent_task_id, due_date)
        WHERE parent_task_id IS NOT NULL AND completed = FALSE
        """
    )


def downgrade() -> None:
    """Remove recurring task fields and indexes."""

    # Drop indexes
    op.drop_index('ix_tasks_parent_due_unique', table_name='tasks')
    op.drop_index('ix_tasks_parent_task_id', table_name='tasks')
    op.drop_index('ix_tasks_user_recurring', table_name='tasks')

    # Drop foreign key constraint
    op.drop_constraint('fk_tasks_parent_task_id', 'tasks', type_='foreignkey')

    # Drop columns
    op.drop_column('tasks', 'parent_task_id')
    op.drop_column('tasks', 'recurrence_end_date')
    op.drop_column('tasks', 'recurrence_pattern')
    op.drop_column('tasks', 'is_recurring')
