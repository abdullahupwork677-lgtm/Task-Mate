"""add_due_date_reminder_fields

Revision ID: d7e4e2b4589b
Revises: czrecan0aykx
Create Date: 2026-02-10 00:24:26.084150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd7e4e2b4589b'
down_revision: Union[str, Sequence[str], None] = 'czrecan0aykx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add due date reminder fields and notification logs table."""

    # ========== TASKS TABLE EXTENSIONS ==========

    # Add remind_before column (JSONB array of intervals)
    op.add_column(
        'tasks',
        sa.Column(
            'remind_before',
            postgresql.JSONB(),
            nullable=True,
            server_default='["24h", "1h"]'
        )
    )

    # Add reminder_sent column (JSONB object tracking sent reminders)
    op.add_column(
        'tasks',
        sa.Column(
            'reminder_sent',
            postgresql.JSONB(),
            nullable=True,
            server_default='{}'
        )
    )

    # ========== USERS TABLE EXTENSIONS ==========

    # Add timezone column
    op.add_column(
        'users',
        sa.Column(
            'timezone',
            sa.String(length=50),
            nullable=False,
            server_default='UTC'
        )
    )

    # Add notification_preferences column (JSONB)
    op.add_column(
        'users',
        sa.Column(
            'notification_preferences',
            postgresql.JSONB(),
            nullable=False,
            server_default='{"email": true, "push": false, "in_app": true}'
        )
    )

    # ========== NOTIFICATION_LOGS TABLE (NEW) ==========

    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('reminder_type', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # ========== INDEXES ==========

    # Partial index for efficient reminder queries
    # Only indexes incomplete tasks with due dates
    op.execute(
        """
        CREATE INDEX idx_tasks_reminders
        ON tasks(user_id, due_date)
        WHERE due_date IS NOT NULL AND completed = FALSE
        """
    )

    # Index for due date sorting and filtering
    op.execute(
        """
        CREATE INDEX idx_tasks_due_date
        ON tasks(due_date)
        WHERE due_date IS NOT NULL
        """
    )

    # Index on notification_logs.task_id for querying notifications by task
    op.create_index(
        'idx_notification_logs_task',
        'notification_logs',
        ['task_id']
    )

    # Index on notification_logs.user_id for querying notifications by user
    op.create_index(
        'idx_notification_logs_user',
        'notification_logs',
        ['user_id']
    )

    # Unique index on notification_logs.event_id for idempotency
    op.create_index(
        'idx_notification_logs_event_id',
        'notification_logs',
        ['event_id'],
        unique=True
    )


def downgrade() -> None:
    """Remove due date reminder fields and notification logs table."""

    # Drop indexes
    op.drop_index('idx_notification_logs_event_id', table_name='notification_logs')
    op.drop_index('idx_notification_logs_user', table_name='notification_logs')
    op.drop_index('idx_notification_logs_task', table_name='notification_logs')
    op.drop_index('idx_tasks_due_date', table_name='tasks')
    op.drop_index('idx_tasks_reminders', table_name='tasks')

    # Drop notification_logs table
    op.drop_table('notification_logs')

    # Drop users table columns
    op.drop_column('users', 'notification_preferences')
    op.drop_column('users', 'timezone')

    # Drop tasks table columns
    op.drop_column('tasks', 'reminder_sent')
    op.drop_column('tasks', 'remind_before')
