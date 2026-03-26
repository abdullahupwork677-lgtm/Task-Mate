"""Event Schemas for Notification Service

Defines the structure of events consumed from Kafka.

Phase V - Due Dates & Reminders
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReminderEvent(BaseModel):
    """Event published to Kafka 'reminders' topic.

    Published by: backend/src/routes/reminders.py
    Consumed by: notification service
    """

    event_id: str = Field(
        description="Unique event ID (UUID) for idempotency"
    )
    task_id: int = Field(
        description="Task ID that triggered the reminder"
    )
    task_title: str = Field(
        description="Task title for notification content"
    )
    task_description: Optional[str] = Field(
        default=None,
        description="Task description for notification context"
    )
    user_id: str = Field(
        description="User to send notification to"
    )
    due_date: str = Field(
        description="Task due date (ISO 8601 format)"
    )
    reminder_type: str = Field(
        description="Reminder interval (e.g., '24h', '1h', '3d')"
    )
    channels: List[str] = Field(
        description="Notification channels to use (email, push, in_app)"
    )
    priority: str = Field(
        default="medium",
        description="Task priority (high, medium, low)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": 42,
                "task_title": "Submit project report",
                "task_description": "Q4 financial report",
                "user_id": "user-123",
                "due_date": "2026-02-20T17:00:00+00:00",
                "reminder_type": "24h",
                "channels": ["email", "push", "in_app"],
                "priority": "high"
            }
        }


class NotificationLogEntry(BaseModel):
    """Notification log entry for tracking delivery status.

    Maps to: backend/src/models.py::NotificationLog
    """

    task_id: int
    user_id: str
    reminder_type: str
    channel: str
    status: str  # success, failed, skipped
    sent_at: datetime
    error_message: Optional[str] = None
    event_id: str  # For idempotency

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 42,
                "user_id": "user-123",
                "reminder_type": "24h",
                "channel": "push",
                "status": "success",
                "sent_at": "2026-02-19T17:00:00+00:00",
                "error_message": None,
                "event_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
