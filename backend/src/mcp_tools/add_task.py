"""MCP Tool: add_task

Creates a new task for the authenticated user.

This tool enables AI agents to add tasks to a user's todo list based on
natural language input.

Phase V Extensions:
- US1: Support due_date_natural and remind_before_natural parameters
- Phase 8: Support recurring tasks at creation time
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from sqlmodel import Session
import logging

from ..models import Task
from ..services.date_parser_service import (
    parse_natural_date,
    format_due_date,
    parse_remind_before_natural,
    InvalidDateError,
    InvalidTimezoneError
)
from ..services.tag_service import TagService
from .set_recurring import _validate_pattern, _parse_end_date

logger = logging.getLogger(__name__)


class AddTaskParams(BaseModel):
    """Input parameters for add_task tool.

    Attributes:
        user_id: ID of the authenticated user (for isolation)
        title: Task title (1-200 characters)
        description: Optional task description
        priority: Task priority level (high, medium, low) - defaults to medium
        due_date: Optional due date in natural language (e.g., 'tomorrow', 'next Friday at 3pm', '2026-01-15')
        remind_before_natural: Optional reminder intervals in natural language (e.g., '24 hours before, 1 hour before')
        user_timezone: User's IANA timezone for date parsing (defaults to UTC)
        recurrence_pattern: Optional recurrence pattern (daily/weekly/monthly/yearly/every N days/weeks/months/none)
        recurrence_end_date: Optional end date for recurrence (requires recurrence_pattern)
    """

    user_id: str = Field(..., description="User ID for task ownership")
    title: str = Field(..., description="Task title (1-200 characters)")
    description: Optional[str] = Field(None, description="Optional task description")
    priority: str = Field(
        default="medium", description="Task priority level (high, medium, low)"
    )
    due_date: Optional[str] = Field(
        None,
        description=(
            "Due date in natural language (e.g., 'tomorrow', 'next Friday at 3pm', "
            "'January 15', '2026-01-15T14:30:00')"
        ),
    )
    remind_before_natural: Optional[str] = Field(
        None,
        description=(
            "Reminder intervals in natural language (Phase V - US1). "
            "Examples: '24 hours before', '1 day before and 1 hour before', '3 days before, 1 hour before'. "
            "Defaults to ['24h', '1h'] if due_date is set"
        ),
    )
    user_timezone: str = Field(
        default="Asia/Karachi",
        description="User's IANA timezone for parsing due dates (e.g., 'America/New_York', 'Asia/Karachi')"
    )
    recurrence_pattern: Optional[str] = Field(
        None,
        description=(
            "Recurrence pattern: daily, weekly, monthly, yearly, 'every N days', "
            "'every N weeks', 'every N months', or 'none' for non-recurring"
        ),
    )
    recurrence_end_date: Optional[str] = Field(
        None,
        description="End date for recurrence in natural language (e.g., 'next year', 'March 31', '2026-12-31')",
    )
    tags: Optional[List[str]] = Field(
        None,
        description=(
            "Optional tags for task categorization (e.g., ['work', 'urgent', 'shopping']). "
            "Tags are normalized to lowercase and duplicates are removed."
        ),
    )

    @validator("priority")
    def validate_priority(cls, v):
        """Validate priority is one of the allowed values."""
        allowed = ["high", "medium", "low"]
        if v not in allowed:
            raise ValueError(
                f"Invalid priority: {v}. Must be one of: {', '.join(allowed)}"
            )
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "title": "Buy milk",
                "description": "Get 2% milk from grocery store",
                "priority": "high",
                "due_date": "tomorrow at 5pm",
                "tags": ["shopping", "urgent"],
            }
        }


class AddTaskResult(BaseModel):
    """Result from add_task tool execution.

    Attributes:
        task_id: ID of the created task
        title: Task title
        description: Task description (if provided)
        completed: Task completion status (always False for new tasks)
        priority: Task priority level (high, medium, low)
        due_date: Task due date and time (if provided)
        due_date_formatted: Human-readable due date in user's timezone (Phase V - US1)
        remind_before: Array of reminder intervals (Phase V - US1)
        is_recurring: Whether task is recurring (Phase 8 extension)
        recurrence_pattern: Recurrence pattern if recurring (Phase 8 extension)
        recurrence_end_date: End date for recurrence if set (Phase 8 extension)
        created_at: Timestamp when task was created
    """

    task_id: int = Field(..., description="ID of the created task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    completed: bool = Field(False, description="Task completion status")
    priority: str = Field(..., description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Task due date and time")
    due_date_formatted: Optional[str] = Field(
        None, description="Human-readable due date in user's timezone (Phase V)"
    )
    remind_before: Optional[List[str]] = Field(
        None, description="Array of reminder intervals (e.g., ['24h', '1h']) (Phase V)"
    )
    is_recurring: bool = Field(False, description="Whether task is recurring")
    recurrence_pattern: Optional[str] = Field(None, description="Recurrence pattern")
    recurrence_end_date: Optional[datetime] = Field(
        None, description="Recurrence end date"
    )
    tags: List[str] = Field(
        default=[], description="Task tags (normalized lowercase, no duplicates)"
    )
    created_at: datetime = Field(..., description="Task creation timestamp")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "task_id": 42,
                "title": "Buy milk",
                "description": "Get 2% milk from grocery store",
                "completed": False,
                "priority": "high",
                "due_date": "2026-01-10T17:00:00Z",
                "tags": ["shopping", "urgent"],
                "created_at": "2025-12-30T10:30:00Z",
            }
        }


def add_task(db: Session, params: AddTaskParams) -> AddTaskResult:
    """Create a new task for the user.

    This is the core MCP tool function that AI agents call to add tasks.

    Phase V Extension: Now supports creating recurring tasks at creation time.
    Users can specify recurrence_pattern and optionally recurrence_end_date.

    Args:
        db: Database session
        params: Task creation parameters

    Returns:
        AddTaskResult with created task details

    Raises:
        ValueError: If validation fails (empty title, title too long, invalid pattern)

    Example:
        >>> # Non-recurring task
        >>> params = AddTaskParams(
        ...     user_id="user-123",
        ...     title="Buy milk",
        ...     description="Get 2% milk"
        ... )
        >>> result = add_task(db, params)
        >>> assert result.task_id > 0
        >>> assert result.is_recurring is False

        >>> # Recurring task
        >>> params = AddTaskParams(
        ...     user_id="user-123",
        ...     title="Morning standup",
        ...     recurrence_pattern="daily"
        ... )
        >>> result = add_task(db, params)
        >>> assert result.is_recurring is True
        >>> assert result.recurrence_pattern == "daily"
    """
    # Validate title
    title = params.title.strip() if params.title else ""

    if not title:
        raise ValueError("Title cannot be empty")

    if len(title) > 200:
        raise ValueError("Title must be 200 characters or less")

    # Phase V - US1: Parse due_date with timezone support
    parsed_due_date = None
    due_date_formatted = None

    if params.due_date and params.due_date.strip():
        try:
            parsed_due_date = parse_natural_date(params.due_date, params.user_timezone)
            due_date_formatted = format_due_date(parsed_due_date, params.user_timezone)
            logger.info(
                f"Parsed due date '{params.due_date}' to {parsed_due_date} "
                f"(formatted: {due_date_formatted})"
            )
        except InvalidDateError as e:
            logger.error(f"Invalid date '{params.due_date}': {e}")
            raise  # Re-raise for proper error handling
        except InvalidTimezoneError as e:
            logger.error(f"Invalid timezone '{params.user_timezone}': {e}")
            raise  # Re-raise for proper error handling
        except Exception as e:
            logger.error(f"Unexpected error parsing due date '{params.due_date}': {e}")
            # Continue without due_date for backward compatibility with legacy code
            parsed_due_date = None
            due_date_formatted = None

    # Phase V - US1: Parse remind_before_natural or use defaults
    remind_before = ["24h", "1h"]  # Default reminder intervals

    if params.remind_before_natural and params.remind_before_natural.strip():
        try:
            remind_before = parse_remind_before_natural(params.remind_before_natural)
            logger.info(
                f"Parsed reminder intervals '{params.remind_before_natural}' to {remind_before}"
            )
        except ValueError as e:
            logger.error(f"Invalid reminder intervals '{params.remind_before_natural}': {e}")
            raise  # Re-raise for proper error handling

    # Phase 8: Handle recurrence parameters
    is_recurring = False
    recurrence_pattern = None
    recurrence_end_date = None

    if params.recurrence_pattern:
        pattern = params.recurrence_pattern.lower().strip()

        # Handle "none" as explicit non-recurring
        if pattern == "none":
            is_recurring = False
            recurrence_pattern = None
            logger.info("Task explicitly set as non-recurring (pattern='none')")
        else:
            # Validate recurrence pattern
            try:
                _validate_pattern(pattern)
                is_recurring = True
                recurrence_pattern = pattern
                logger.info(f"Task set as recurring with pattern: {pattern}")
            except ValueError as e:
                raise ValueError(f"Invalid recurrence pattern: {str(e)}") from e

            # Parse recurrence_end_date if provided
            if params.recurrence_end_date:
                try:
                    recurrence_end_date = _parse_end_date(params.recurrence_end_date)
                    logger.info(f"Recurrence end date set to: {recurrence_end_date}")
                except ValueError as e:
                    raise ValueError(f"Invalid recurrence end date: {str(e)}") from e

    # Validate: recurrence_end_date requires recurrence_pattern
    if params.recurrence_end_date and not is_recurring:
        raise ValueError("recurrence_end_date requires recurrence_pattern to be set")

    # Phase V - US1 (003-task-tags): Normalize tags
    tag_service = TagService()
    normalized_tags = []
    if params.tags:
        normalized_tags = tag_service.validate_and_normalize_tags(params.tags)
        logger.info(f"Normalized tags: {params.tags} -> {normalized_tags}")

    # Create task with user isolation
    task = Task(
        user_id=params.user_id,
        title=title,
        description=params.description,
        priority=params.priority,
        due_date=parsed_due_date,
        remind_before=remind_before,  # Phase V - US1: Reminder intervals
        reminder_sent={},  # Phase V - US1: Empty reminder tracking object
        is_recurring=is_recurring,
        recurrence_pattern=recurrence_pattern,
        recurrence_end_date=recurrence_end_date,
        tags=normalized_tags,  # Phase V - US1 (003-task-tags): Normalized tags
        completed=False,
        created_at=datetime.utcnow(),
    )

    # Persist to database
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(
            f"Created task {task.id} (recurring={is_recurring}, pattern={recurrence_pattern})"
        )
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to create task: {str(e)}") from e

    # Return result
    return AddTaskResult(
        task_id=task.id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        priority=task.priority,
        due_date=task.due_date,
        due_date_formatted=due_date_formatted,  # Phase V - US1
        remind_before=task.remind_before,  # Phase V - US1
        is_recurring=task.is_recurring,
        recurrence_pattern=task.recurrence_pattern,
        recurrence_end_date=task.recurrence_end_date,
        tags=task.tags,  # Phase V - US1 (003-task-tags)
        created_at=task.created_at,
    )
