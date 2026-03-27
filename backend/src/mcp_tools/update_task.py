"""MCP Tool: update_task

Updates task title, description, or priority for the authenticated user.

This tool enables AI agents to modify task details based on
natural language input.

Phase V Extension (US1):
- Support due_date as natural language string
- Support clear_due_date flag to remove due dates
- Reset reminder_sent when due date changes
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from sqlmodel import Session, select
import logging

from ..models import Task
from ..services.date_parser_service import (
    parse_natural_date,
    format_due_date,
    InvalidDateError,
    InvalidTimezoneError
)

logger = logging.getLogger(__name__)


class UpdateTaskParams(BaseModel):
    """Input parameters for update_task tool.

    Attributes:
        user_id: ID of the authenticated user (for isolation)
        task_id: ID of the task to update
        title: New task title (optional)
        description: New task description (optional)
        priority: New task priority level (optional)
        due_date: New task due date in natural language (Phase V - optional)
        clear_due_date: Flag to clear due date (Phase V - optional)
        user_timezone: User's IANA timezone for date parsing (Phase V - defaults to UTC)
        completed: Mark as completed (True) or incomplete (False) (optional)
    """

    user_id: str = Field(..., description="User ID for task ownership")
    task_id: int = Field(..., description="ID of the task to update")
    title: Optional[str] = Field(None, description="New task title")
    description: Optional[str] = Field(None, description="New task description")
    priority: Optional[str] = Field(
        None,
        description="New task priority level (high, medium, low)"
    )
    due_date: Optional[str] = Field(
        None,
        description=(
            "New task due date in natural language (Phase V - US1). "
            "Examples: 'tomorrow at 5pm', 'next Friday', 'Feb 15 at 2pm'"
        )
    )
    clear_due_date: Optional[bool] = Field(
        None,
        description=(
            "Set to True to clear the due date (Phase V - US1). "
            "When True, sets due_date=NULL, remind_before=NULL, reminder_sent=NULL"
        )
    )
    user_timezone: str = Field(
        default="UTC",
        description="User's IANA timezone for parsing due dates (e.g., 'America/New_York', 'Europe/London')"
    )
    completed: Optional[bool] = Field(
        None,
        description="Mark task as completed (True) or incomplete (False)"
    )

    @validator("priority")
    def validate_priority(cls, v):
        """Validate priority is one of the allowed values."""
        if v is None:
            return v
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
                "task_id": 3,
                "title": "Buy milk and eggs",
                "priority": "high"
            }
        }


class UpdateTaskResult(BaseModel):
    """Result from update_task tool execution.

    Attributes:
        task_id: ID of the updated task
        title: Updated task title
        description: Updated task description
        completed: Task completion status
        priority: Task priority level
        due_date: Task due date
        due_date_formatted: Human-readable due date in user's timezone (Phase V - US1)
        updated_at: Timestamp when task was updated
    """

    task_id: int = Field(..., description="ID of the task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    completed: bool = Field(..., description="Task completion status")
    priority: str = Field(..., description="Task priority level")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    due_date_formatted: Optional[str] = Field(
        None, description="Human-readable due date in user's timezone (Phase V)"
    )
    updated_at: datetime = Field(..., description="Timestamp of update")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "task_id": 3,
                "title": "Buy milk and eggs",
                "description": "From grocery store",
                "completed": False,
                "priority": "high",
                "updated_at": "2025-12-30T16:30:00Z"
            }
        }


def update_task(db: Session, params: UpdateTaskParams) -> UpdateTaskResult:
    """Update task title, description, or priority.

    This is the core MCP tool function that AI agents call to update tasks.

    Args:
        db: Database session
        params: Task update parameters

    Returns:
        UpdateTaskResult with updated task details

    Raises:
        ValueError: If task not found, doesn't belong to user, or no fields provided

    Security:
        - Enforces user isolation: query filters by both user_id AND task_id
        - Returns generic "not found" error (doesn't reveal if task exists for other user)

    Validation:
        - At least one field (title, description, or priority) must be provided

    Example:
        >>> params = UpdateTaskParams(
        ...     user_id="user-123",
        ...     task_id=3,
        ...     title="Buy milk and eggs",
        ...     priority="high"
        ... )
        >>> result = update_task(db, params)
        >>> assert result.title == "Buy milk and eggs"
        >>> assert result.priority == "high"
    """
    # Validate at least one field provided (T128)
    # Check if any field was explicitly set (using __fields_set__)
    updateable_fields = {'title', 'description', 'priority', 'due_date', 'clear_due_date', 'completed'}
    if not any(field in params.__fields_set__ for field in updateable_fields):
        raise ValueError(
            "At least one field (title, description, priority, due_date, clear_due_date, or completed) "
            "must be provided"
        )

    logger.info(
        f"update_task: Querying task {params.task_id} for user {params.user_id}",
        extra={
            "user_id": params.user_id,
            "task_id": params.task_id,
            "fields_to_update": {
                "title": params.title,
                "description": params.description,
                "priority": params.priority,
                "due_date": params.due_date,
                "completed": params.completed
            }
        }
    )

    # Query task with user_id AND task_id (T129)
    # This enforces user isolation
    query = select(Task).where(
        Task.id == params.task_id,
        Task.user_id == params.user_id
    )

    try:
        result = db.exec(query).first()
    except Exception as e:
        logger.error(f"update_task: Query failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to query task: {str(e)}") from e

    # Handle task not found
    if not result:
        logger.warning(
            f"update_task: Task {params.task_id} not found for user {params.user_id}",
            extra={"user_id": params.user_id, "task_id": params.task_id}
        )
        raise ValueError("Task not found")

    task = result

    logger.info(
        f"update_task: Found task - id={task.id}, title={task.title}",
        extra={"user_id": params.user_id, "task_id": task.id, "old_title": task.title}
    )

    # Update provided fields (T130)
    # Use __fields_set__ to detect which fields were explicitly provided
    # This allows us to distinguish between "not provided" vs "provided as None"
    fields_set = params.__fields_set__

    # Phase V - US1: Track if due date will change (for reminder_sent reset)
    old_due_date = task.due_date
    parsed_due_date = None
    due_date_formatted = None

    if 'title' in fields_set:
        task.title = params.title
    if 'description' in fields_set:
        task.description = params.description
    if 'priority' in fields_set:
        task.priority = params.priority

    # Phase V - US1: Handle clear_due_date flag (T046)
    if 'clear_due_date' in fields_set and params.clear_due_date is True:
        logger.info(f"Clearing due date for task {task.id}")
        task.due_date = None
        task.reminder_sent = {}
        parsed_due_date = None
        due_date_formatted = None

    # Phase V - US1: Handle due_date as natural language (T045)
    elif 'due_date' in fields_set:
        if params.due_date is None:
            # Explicit null from chat/API means remove due date.
            logger.info(f"Clearing due date for task {task.id} via due_date=None")
            task.due_date = None
            task.reminder_sent = {}
            parsed_due_date = None
            due_date_formatted = None
        elif params.due_date and params.due_date.strip():
            try:
                parsed_due_date = parse_natural_date(params.due_date, params.user_timezone)
                due_date_formatted = format_due_date(parsed_due_date, params.user_timezone)
                task.due_date = parsed_due_date
                logger.info(
                    f"Updated due date for task {task.id}: '{params.due_date}' → {parsed_due_date} "
                    f"(formatted: {due_date_formatted})"
                )
            except InvalidDateError as e:
                logger.error(f"Invalid date '{params.due_date}': {e}")
                raise  # Re-raise for proper error handling
            except InvalidTimezoneError as e:
                logger.error(f"Invalid timezone '{params.user_timezone}': {e}")
                raise  # Re-raise for proper error handling
        else:
            # Empty string - treat as no change (backward compatibility)
            parsed_due_date = task.due_date
            if parsed_due_date:
                due_date_formatted = format_due_date(parsed_due_date, params.user_timezone)

    # Phase V - US1: Reset reminder_sent if due date changed (T039)
    if old_due_date != task.due_date:
        task.reminder_sent = {}
        logger.debug(f"Reset reminder_sent for task {task.id} (due date changed)")

    if 'completed' in fields_set:
        task.completed = params.completed

    # Always update timestamp (T022)
    task.updated_at = datetime.utcnow()

    # Format due_date for response if it exists but wasn't just updated
    if task.due_date and not due_date_formatted:
        due_date_formatted = format_due_date(task.due_date, params.user_timezone)

    # Persist changes
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(
            f"update_task: Successfully committed task {task.id} to database",
            extra={
                "user_id": params.user_id,
                "task_id": task.id,
                "new_title": task.title,
                "new_priority": task.priority
            }
        )
    except Exception as e:
        logger.error(
            f"update_task: Commit failed for task {params.task_id}: {str(e)}",
            extra={"user_id": params.user_id, "task_id": params.task_id},
            exc_info=True
        )
        db.rollback()
        raise RuntimeError(f"Failed to update task: {str(e)}") from e

    # Return result (T131)
    return UpdateTaskResult(
        task_id=task.id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        priority=task.priority,
        due_date=task.due_date,
        due_date_formatted=due_date_formatted,  # Phase V - US1
        updated_at=task.updated_at
    )
