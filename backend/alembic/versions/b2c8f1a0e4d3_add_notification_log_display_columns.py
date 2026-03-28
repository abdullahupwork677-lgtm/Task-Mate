"""add_notification_log_display_columns

Revision ID: b2c8f1a0e4d3
Revises: ee9a8863ddcd
Create Date: 2026-03-28

In-app notifications API expects title, message, is_read, created_at on notification_logs.
Original Phase V migration only had audit columns; this aligns DB with reminders INSERT + GET.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c8f1a0e4d3"
down_revision: Union[str, Sequence[str], None] = "ee9a8863ddcd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IF NOT EXISTS: safe if columns were added manually on some deployments
    op.execute(
        sa.text(
            "ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS title VARCHAR(500)"
        )
    )
    op.execute(
        sa.text("ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS message TEXT")
    )
    op.execute(
        sa.text(
            "ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS is_read BOOLEAN "
            "NOT NULL DEFAULT false"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS created_at "
            "TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        )
    )


def downgrade() -> None:
    op.drop_column("notification_logs", "created_at")
    op.drop_column("notification_logs", "is_read")
    op.drop_column("notification_logs", "message")
    op.drop_column("notification_logs", "title")
