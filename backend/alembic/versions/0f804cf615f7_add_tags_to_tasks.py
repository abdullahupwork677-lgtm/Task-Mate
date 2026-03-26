"""add_tags_to_tasks

Revision ID: 0f804cf615f7
Revises: d7e4e2b4589b
Create Date: 2026-02-14 18:20:24.517282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f804cf615f7'
down_revision: Union[str, Sequence[str], None] = 'd7e4e2b4589b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tags JSONB/JSON column to tasks table with index."""
    # Check if we're using PostgreSQL or SQLite
    connection = op.get_bind()
    dialect_name = connection.dialect.name

    if dialect_name == "postgresql":
        # PostgreSQL: Use JSONB with GIN index
        op.execute("""
            ALTER TABLE tasks
            ADD COLUMN tags JSONB NOT NULL DEFAULT '[]'::jsonb
        """)

        # Create GIN index for efficient tag filtering
        op.execute("""
            CREATE INDEX idx_tasks_tags ON tasks USING gin(tags)
        """)
    else:
        # SQLite: Use JSON (same storage, different API)
        op.add_column(
            'tasks',
            sa.Column(
                'tags',
                sa.JSON,
                nullable=False,
                server_default='[]'
            )
        )

        # Create regular index (SQLite doesn't support GIN)
        op.create_index('idx_tasks_tags', 'tasks', ['tags'])


def downgrade() -> None:
    """Remove tags column and index."""
    op.drop_index('idx_tasks_tags', table_name='tasks')
    op.drop_column('tasks', 'tags')
