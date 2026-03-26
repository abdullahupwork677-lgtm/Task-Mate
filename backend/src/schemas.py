"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class TaskCreate(BaseModel):
    """Request schema for creating a new task."""

    title: str = Field(min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Task description"
    )
    priority: str = Field(
        default="medium",
        description="Task priority (high, medium, low)"
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date and time (optional)"
    )

    # Phase V - Due Dates & Reminders Fields
    due_date_natural: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Natural language due date (e.g., 'tomorrow at 5pm', 'next Friday') - Phase V"
    )
    remind_before_natural: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Natural language reminder intervals (e.g., '24 hours before and 1 hour before') - Phase V"
    )

    # Phase V - Task Tags & Categories Fields
    tags: List[str] = Field(
        default=[],
        max_length=100,
        description="Array of tags for categorization (e.g., ['work', 'urgent']) - Phase V"
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate title is not empty or whitespace only."""
        if not v or v.strip() == "":
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_length(cls, v: Optional[str]) -> Optional[str]:
        """Validate description length if provided."""
        if v and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is one of allowed values."""
        allowed = ["high", "medium", "low"]
        if v not in allowed:
            raise ValueError(f"Priority must be one of {allowed}, got '{v}'")
        return v


class TaskUpdate(BaseModel):
    """Request schema for updating an existing task."""

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated task title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated task description"
    )
    priority: Optional[str] = Field(
        default=None,
        description="Updated task priority (high, medium, low)"
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Updated task due date and time (optional)"
    )
    completed: Optional[bool] = Field(
        default=None,
        description="Task completion status"
    )

    # Phase V - Due Dates & Reminders Fields
    due_date_natural: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Natural language due date (e.g., 'tomorrow at 5pm') - Phase V"
    )
    clear_due_date: Optional[bool] = Field(
        default=None,
        description="Set to True to clear the due date - Phase V"
    )

    # Phase V - Task Tags & Categories Fields
    tags: Optional[List[str]] = Field(
        default=None,
        max_length=100,
        description="Array of tags for categorization (replaces existing tags if provided) - Phase V"
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate title is not empty if provided."""
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip() if v else v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority is one of allowed values if provided."""
        if v is not None:
            allowed = ["high", "medium", "low"]
            if v not in allowed:
                raise ValueError(f"Priority must be one of {allowed}, got '{v}'")
        return v


class TaskResponse(BaseModel):
    """Response schema for task data."""

    id: int
    user_id: str
    title: str
    description: Optional[str]
    completed: bool
    priority: str = Field(default="medium", description="Task priority (high, medium, low)")
    due_date: Optional[datetime] = Field(default=None, description="Task due date and time")
    created_at: datetime
    updated_at: datetime
    tags: List[str] = Field(default=[], description="Task tags for categorization (Phase V)")

    model_config = {
        "from_attributes": True,
        # Serialize datetime WITHOUT "Z" suffix - times are stored as local time, not UTC
        # This allows frontend to interpret them correctly without timezone conversion
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }


# Phase V - Task Sorting Schemas (Feature 005)

class SortField(str, Enum):
    """Sortable task fields."""
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    CREATED_AT = "created_at"
    TITLE = "title"


class SortDirection(str, Enum):
    """Sort direction (ascending or descending)."""
    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """
    Query parameters for task sorting.

    Used in list_tasks endpoint to enable sorting tasks by different criteria:
    - due_date: Sort by task due date (earliest/latest first, nulls last)
    - priority: Sort by priority (high → medium → low, or reverse)
    - created_at: Sort by creation date (newest/oldest first)
    - title: Sort alphabetically by title (A-Z or Z-A, case-insensitive)

    Default sort: created_at descending (newest tasks first)
    """

    sort_by: SortField = Field(
        default=SortField.CREATED_AT,
        description="Field to sort tasks by (due_date, priority, created_at, title)"
    )
    sort_direction: Optional[SortDirection] = Field(
        default=None,
        description="Sort direction (asc/desc). If not provided, uses field-specific default."
    )


class SimpleHealthResponse(BaseModel):
    """Simple response schema for liveness probe."""

    status: str = Field(description="Service status")


class HealthResponse(BaseModel):
    """Response schema for readiness check endpoint."""

    status: str = Field(description="Overall system status")
    database: str = Field(description="Database connection status")
    version: str = Field(description="API version")
    timestamp: datetime = Field(description="Health check timestamp")
    pool_status: str | None = Field(default=None, description="Database connection pool status")


# Authentication Schemas (Feature 2)

class SignupRequest(BaseModel):
    """Request schema for user registration."""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(
        min_length=8,
        max_length=100,
        description="User password (min 8 characters)"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="User display name (optional)"
    )


class LoginRequest(BaseModel):
    """Request schema for user login."""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")


class UserResponse(BaseModel):
    """Response schema for user data (no password)."""
    
    id: str
    email: str
    name: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Response schema for successful login."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiry in seconds")
    user: UserResponse = Field(description="Authenticated user data")


# Phase V - Kafka Event Schemas

class ReminderEventSchema(BaseModel):
    """
    Schema for reminder events published to Kafka.

    These events are consumed by the notification microservice to send
    reminders before task due dates.

    Phase V - Due Dates & Reminders
    """

    event_id: UUID = Field(
        description="Unique event ID for idempotency (prevents duplicate notifications)"
    )
    task_id: int = Field(
        description="Task being reminded about",
        gt=0
    )
    user_id: str = Field(
        description="Task owner (recipient of notification)",
        min_length=1,
        max_length=100
    )
    task_title: str = Field(
        description="Human-readable task description for notification",
        min_length=1,
        max_length=500
    )
    due_date: datetime = Field(
        description="When task is due (UTC)"
    )
    reminder_type: str = Field(
        description="Interval before due date (e.g., '24h', '1h', '3d')",
        pattern=r"^\d+(m|h|d|w)$"
    )
    priority: str = Field(
        default="medium",
        description="Task priority level (high, medium, low)"
    )
    channels: List[str] = Field(
        description="Notification channels to use (email, push, in_app)",
        min_length=1
    )
    user_timezone: str = Field(
        description="User's IANA timezone for displaying dates in notifications",
        min_length=1,
        max_length=50
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When event was created (UTC)"
    )

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v: List[str]) -> List[str]:
        """Validate notification channels."""
        allowed = ["email", "push", "in_app"]
        for channel in v:
            if channel not in allowed:
                raise ValueError(f"Invalid channel '{channel}'. Must be one of: {allowed}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is one of allowed values."""
        allowed = ["high", "medium", "low"]
        if v not in allowed:
            raise ValueError(f"Priority must be one of {allowed}, got '{v}'")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": 123,
                "user_id": "user-abc-123",
                "task_title": "Submit quarterly report",
                "due_date": "2026-02-15T17:00:00Z",
                "reminder_type": "24h",
                "priority": "high",
                "channels": ["email", "push", "in_app"],
                "user_timezone": "America/New_York",
                "timestamp": "2026-02-14T17:00:00Z"
            }
        }
    }

