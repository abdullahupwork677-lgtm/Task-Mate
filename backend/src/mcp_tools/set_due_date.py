"""Set Due Date MCP Tool

Allows users to set or update a task's due date using natural language.
Validates dates, handles timezone conversion, and enforces user isolation.

Phase V: Due Dates & Reminders
Implements User Story 1 - Basic Due Date Assignment
"""

from typing import Optional
from datetime import datetime
import logging
from sqlmodel import Session

from src.models import Task
from src.services.date_parser_service import (
    parse_natural_date,
    format_due_date,
    InvalidDateError,
    InvalidTimezoneError
)

# Setup logging
logger = logging.getLogger(__name__)


def set_due_date(
    task_id: int,
    due_date_natural: str,
    user_id: str,
    user_timezone: str = "UTC",
    db: Optional[Session] = None
) -> dict:
    """Set or update a task's due date using natural language.

    Phase V: Enables users to set task due dates via natural language input.
    Automatically resets reminder_sent field when due date changes.

    Args:
        task_id: Task ID to update
        due_date_natural: Natural language date (e.g., "tomorrow at 5pm", "next Friday")
        user_id: User ID (for user isolation)
        user_timezone: User's IANA timezone (default: "UTC")
        db: Optional database session (for testing)

    Returns:
        Dict with success, task_id, due_date, due_date_formatted

    Raises:
        ValueError: If task not found or doesn't belong to user
        PermissionError: If user tries to modify another user's task
        InvalidDateError: If date string cannot be parsed
        InvalidTimezoneError: If timezone is invalid

    Examples:
        >>> await set_due_date(42, "tomorrow at 5pm", "user-123", "America/New_York")
        {"success": True, "task_id": 42, "due_date": "2026-02-11T22:00:00Z", ...}

        >>> await set_due_date(42, "next Friday", "user-123")
        {"success": True, "task_id": 42, "due_date": "2026-02-13T00:00:00Z", ...}
    """
    logger.info(
        f"Setting due date for task {task_id}, user {user_id}: '{due_date_natural}' "
        f"(timezone: {user_timezone})"
    )

    # Validate inputs
    if not due_date_natural or due_date_natural.strip() == "":
        raise InvalidDateError("Empty date string provided")

    # Parse natural language date
    try:
        parsed_due_date = parse_natural_date(due_date_natural.strip(), user_timezone)
        logger.debug(f"Parsed due date (UTC): {parsed_due_date}")
    except InvalidDateError as e:
        logger.error(f"Failed to parse date '{due_date_natural}': {e}")
        raise
    except InvalidTimezoneError as e:
        logger.error(f"Invalid timezone '{user_timezone}': {e}")
        raise

    # Database operations
    should_close = False
    if db is None:
        from src.db import engine
        db = Session(engine)
        should_close = True

    try:
        # Fetch task with user isolation
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .filter(Task.user_id == user_id)
            .first()
        )

        if not task:
            # Check if task exists but belongs to different user
            task_exists = db.query(Task).filter(Task.id == task_id).first()
            if task_exists:
                raise PermissionError(
                    f"Not authorized to modify task {task_id}. "
                    f"Task belongs to user {task_exists.user_id}"
                )
            else:
                raise ValueError(f"Task {task_id} not found")

        # Update due date
        old_due_date = task.due_date
        task.due_date = parsed_due_date

        # Reset reminder_sent when due date changes
        # This ensures reminders will be sent again for the new due date
        if old_due_date != parsed_due_date:
            task.reminder_sent = {}
            logger.debug(f"Reset reminder_sent for task {task_id} (due date changed)")

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Commit changes
        db.commit()
        db.refresh(task)

        # Format due date for response (in user's timezone)
        formatted_due_date = format_due_date(parsed_due_date, user_timezone)

        logger.info(
            f"Successfully set due date for task {task_id}: "
            f"{formatted_due_date} (UTC: {parsed_due_date})"
        )

        return {
            "success": True,
            "task_id": task_id,
            "task_title": task.title,
            "due_date": parsed_due_date.isoformat(),
            "due_date_formatted": formatted_due_date,
            "reminder_sent_reset": old_due_date != parsed_due_date,
        }

    finally:
        if should_close:
            db.close()




# MCP Tool Metadata (for agent registration)
TOOL_METADATA = {
    "name": "set_due_date",
    "description": (
        "Set or update a task's due date using natural language. "
        "Examples: 'tomorrow at 5pm', 'next Friday', 'Feb 15 at 2pm'. "
        "Automatically resets reminder tracking when due date changes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "integer",
                "description": "Task ID to update"
            },
            "due_date_natural": {
                "type": "string",
                "description": "Natural language due date (e.g., 'tomorrow at 5pm', 'next Friday')"
            },
            "user_id": {
                "type": "string",
                "description": "User ID (for authentication)"
            },
            "user_timezone": {
                "type": "string",
                "description": "User's IANA timezone (default: UTC)",
                "default": "UTC"
            }
        },
        "required": ["task_id", "due_date_natural", "user_id"]
    }
}
