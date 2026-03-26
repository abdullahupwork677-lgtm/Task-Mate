"""Database Models for Notification Service

Defines SQLModel models for notification storage.

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class InAppNotification(SQLModel, table=True):
    """In-app notification stored in database for frontend display.

    Used by: in_app_handler.py
    Consumed by: Frontend GET /api/notifications endpoint
    """

    __tablename__ = "in_app_notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="User to display notification to")
    task_id: int = Field(description="Task this notification is about")
    title: str = Field(description="Notification title (e.g., 'Reminder: Submit report')")
    message: str = Field(description="Notification message body")
    reminder_type: str = Field(description="Reminder interval (e.g., '24h', '1h', '3d')")
    is_read: bool = Field(default=False, description="Whether user has read this notification")
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    event_id: str = Field(unique=True, index=True, description="Unique event ID for idempotency")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": "user-123",
                "task_id": 42,
                "title": "Reminder: Submit project report",
                "message": "Your task 'Submit project report' is due in 24 hours at Feb 20, 2026 5:00 PM",
                "reminder_type": "24h",
                "is_read": False,
                "created_at": "2026-02-19T17:00:00+00:00",
                "event_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
