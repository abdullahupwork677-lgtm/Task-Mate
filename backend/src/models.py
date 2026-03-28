"""SQLModel database models for User and Task entities."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import Column, Enum, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlmodel import Field, Relationship, SQLModel


class PriorityLevel(str, PyEnum):
    """Task priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class User(SQLModel, table=True):
    """
    User account with authentication support.
    
    Supports both:
    - Backend email/password auth (password_hash field)
    - Better Auth providers (password_hash can be null for OAuth users)
    """
    
    __tablename__ = "users"
    
    id: str = Field(
        primary_key=True,
        description="UUID (generated on signup or from Better Auth)"
    )
    email: str = Field(
        unique=True,
        index=True,
        max_length=255,
        description="User email address (stored in lowercase)"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="User display name"
    )
    password_hash: Optional[str] = Field(
        default=None,
        max_length=255,
        description="bcrypt hashed password (null for OAuth users)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Account creation timestamp"
    )

    # Phase V - Due Dates & Reminders Fields
    timezone: str = Field(
        default="UTC",
        max_length=50,
        description="User's IANA timezone (e.g., 'America/New_York', 'Europe/London') for displaying due dates (Phase V)"
    )
    notification_preferences: Dict[str, Any] = Field(
        default={"email": True, "push": False, "in_app": True},
        sa_column=Column(JSON),
        description="Notification channel preferences: email, push, in_app (Phase V)"
    )

    # Relationships
    tasks: List["Task"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    conversations: List["Conversation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    messages: List["Message"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    notification_logs: List["NotificationLog"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Task(SQLModel, table=True):
    """
    Todo task belonging to a user.
    
    Supports full CRUD operations via REST API.
    """
    
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Auto-incrementing task ID"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner user ID"
    )
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Task title (required)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Task description (optional)"
    )
    completed: bool = Field(
        default=False,
        index=True,
        description="Completion status"
    )
    priority: str = Field(
        default="medium",
        sa_column=Column(
            Enum("high", "medium", "low", name="priority_enum"),
            nullable=False,
            server_default="medium"
        ),
        description="Task priority level (high, medium, low)"
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date and time (optional)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )

    # Phase V - Recurring Tasks Fields
    is_recurring: bool = Field(
        default=False,
        index=True,
        description="Whether this task repeats on completion (Phase V)"
    )
    recurrence_pattern: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Recurrence pattern: daily, weekly, monthly, yearly, 'every N days/weeks/months' (Phase V)"
    )
    recurrence_end_date: Optional[datetime] = Field(
        default=None,
        description="Optional end date for recurrence (None = infinite) (Phase V)"
    )
    parent_task_id: Optional[int] = Field(
        default=None,
        foreign_key="tasks.id",
        description="Links to parent recurring task if this is an auto-created occurrence (Phase V)"
    )

    # Phase V - Due Dates & Reminders Fields
    remind_before: Optional[List[str]] = Field(
        default=["24h", "1h"],
        sa_column=Column(JSON),
        description="Array of reminder intervals before due date (e.g., ['24h', '1h', '3d']) (Phase V)"
    )
    reminder_sent: Optional[Dict[str, Any]] = Field(
        default={},
        sa_column=Column(JSON),
        description="Tracking object for sent reminders: {'24h': '2026-02-09T10:00:00Z', '1h': '...'} (Phase V)"
    )

    # Phase V - Task Tags & Categories Fields
    tags: List[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Array of tags for task categorization (e.g., ['work', 'urgent', 'shopping']) - stored as lowercase (Phase V)"
    )

    # Relationships
    user: Optional[User] = Relationship(back_populates="tasks")
    notification_logs: List["NotificationLog"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    parent_task: Optional["Task"] = Relationship(
        back_populates="child_occurrences",
        sa_relationship_kwargs={"remote_side": "Task.id", "foreign_keys": "[Task.parent_task_id]"}
    )
    child_occurrences: List["Task"] = Relationship(
        back_populates="parent_task",
        sa_relationship_kwargs={"foreign_keys": "[Task.parent_task_id]"}
    )


class Conversation(SQLModel, table=True):
    """
    Chat conversation between user and AI assistant.

    Stores conversation metadata, state tracking, and timestamps for stateless architecture.
    Messages are stored separately in the Message table.

    State Fields (Phase 3 - Robust AI Assistant):
    - current_intent: Tracks conversation flow state (NEUTRAL, ADDING_TASK, etc.)
    - state_data: Stores collected information during multi-turn workflows
    - target_task_id: References task being updated/deleted/completed
    """

    __tablename__ = "conversations"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Auto-incrementing conversation ID"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner user ID"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Conversation creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last message timestamp"
    )

    # Phase 3: Conversation State Tracking
    current_intent: str = Field(
        default="NEUTRAL",
        max_length=50,
        description="Current conversation state: NEUTRAL, ADDING_TASK, UPDATING_TASK, DELETING_TASK, COMPLETING_TASK, LISTING_TASKS"
    )
    state_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Collected information for current operation (e.g., partial task details)"
    )
    target_task_id: Optional[int] = Field(
        default=None,
        description="ID of task being updated/deleted/completed in current workflow"
    )

    # Relationships
    user: Optional[User] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Message(SQLModel, table=True):
    """
    Individual message within a conversation.

    Can be from user (role='user') or AI assistant (role='assistant').
    Messages are ordered by created_at within a conversation.
    """

    __tablename__ = "messages"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Auto-incrementing message ID"
    )
    conversation_id: int = Field(
        foreign_key="conversations.id",
        index=True,
        description="Parent conversation ID"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Owner user ID (matches conversation.user_id)"
    )
    role: str = Field(
        max_length=20,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        description="Message text content"
    )
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Tool calls associated with this message (for assistant messages)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="Message timestamp"
    )

    # Relationships
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    user: Optional[User] = Relationship(back_populates="messages")

    def validate_role(self) -> None:
        """Validate that role is either 'user' or 'assistant'."""
        if self.role not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")


class NotificationLog(SQLModel, table=True):
    """
    Audit trail for sent notifications.

    Tracks notification delivery status for debugging, analytics, and idempotency.
    Each notification attempt is logged with delivery status and optional error message.

    Phase V - Due Dates & Reminders
    """

    __tablename__ = "notification_logs"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Auto-incrementing log ID"
    )
    task_id: int = Field(
        foreign_key="tasks.id",
        index=True,
        description="Task that triggered notification"
    )
    user_id: str = Field(
        foreign_key="users.id",
        index=True,
        description="Recipient user ID"
    )
    reminder_type: str = Field(
        max_length=50,
        description="Reminder interval (e.g., '24h', '1h', '3d')"
    )
    channel: str = Field(
        max_length=50,
        description="Delivery channel: email, push, in_app"
    )
    status: str = Field(
        max_length=20,
        description="Delivery status: success, failed, pending"
    )
    sent_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="When notification was sent (UTC)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if status=failed"
    )
    event_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), unique=True, nullable=False),
        description="Kafka event UUID for idempotency"
    )
    title: Optional[str] = Field(default=None, max_length=500)
    message: Optional[str] = Field(default=None)
    is_read: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default=None)

    # Relationships
    task: Optional[Task] = Relationship(back_populates="notification_logs")
    user: Optional[User] = Relationship(back_populates="notification_logs")

