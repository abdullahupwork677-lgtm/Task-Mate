"""Set Recurring MCP Tool

Allows users to set a task as recurring or modify/cancel existing recurrence.
Validates patterns, parses natural language dates, and enforces user isolation.

Phase V: Recurring Tasks
Implements User Story 1 - Set a Task as Recurring via Chat
"""

from typing import Optional
from datetime import datetime
import logging
from sqlmodel import Session, select
from src.models import Task
from src.db import engine
import dateparser
import re

# Setup logging
logger = logging.getLogger(__name__)


# Supported recurrence patterns
SIMPLE_PATTERNS = ["daily", "weekly", "monthly", "yearly", "none"]
CUSTOM_PATTERN_REGEX = r"^every\s+(\d+)\s+(day|days|week|weeks|month|months)$"


async def set_recurring(
    user_id: int, task_id: int, pattern: str, end_date: Optional[str] = None
) -> dict:
    """Set a task as recurring with specified pattern.

    Phase V: This tool enables users to set tasks as recurring via natural language.
    Supports simple patterns (daily, weekly, monthly, yearly), custom intervals
    (every N days/weeks/months), and recurrence end dates.

    Args:
        user_id: User ID (for user isolation)
        task_id: Task ID to set as recurring
        pattern: Recurrence pattern (daily/weekly/monthly/yearly/every N days/none)
        end_date: Optional end date for recurrence (natural language or ISO format)

    Returns:
        Dict with task_id, title, is_recurring, recurrence_pattern, recurrence_end_date

    Raises:
        ValueError: If task not found, doesn't belong to user, or invalid pattern

    Examples:
        >>> await set_recurring(1, 5, "weekly")
        >>> await set_recurring(1, 7, "every 3 days", "next year")
        >>> await set_recurring(1, 8, "none")  # Cancel recurrence
    """
    logger.info(
        f"Setting recurring pattern for task {task_id}, user {user_id}: {pattern}"
    )

    # Normalize pattern
    pattern = pattern.lower().strip()

    # Validate pattern
    _validate_pattern(pattern)
    logger.debug(f"Pattern validated: {pattern}")

    # Parse end_date if provided
    parsed_end_date = None
    if end_date:
        parsed_end_date = _parse_end_date(end_date)
        logger.debug(f"End date parsed: {parsed_end_date}")

    # Database operations
    with Session(engine) as session:
        # Fetch task with user isolation
        statement = select(Task).where(Task.id == task_id, Task.user_id == str(user_id))
        task = session.exec(statement).first()

        if not task:
            raise ValueError("Task not found or access denied")

        # Handle recurrence cancellation (pattern="none")
        if pattern == "none":
            task.is_recurring = False
            task.recurrence_pattern = None
            task.recurrence_end_date = None
        else:
            # Set as recurring
            task.is_recurring = True
            task.recurrence_pattern = pattern
            task.recurrence_end_date = parsed_end_date

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Commit changes
        session.add(task)
        session.commit()
        session.refresh(task)

        # Log success
        if pattern == "none":
            logger.info(f"Cancelled recurrence for task {task_id}")
        else:
            logger.info(
                f"Set task {task_id} as recurring: pattern={pattern}, "
                f"end_date={parsed_end_date}"
            )

        # Return updated task info
        return {
            "task_id": task.id,
            "title": task.title,
            "is_recurring": task.is_recurring,
            "recurrence_pattern": task.recurrence_pattern,
            "recurrence_end_date": (
                task.recurrence_end_date.isoformat()
                if task.recurrence_end_date
                else None
            ),
        }


def _validate_pattern(pattern: str) -> None:
    """Validate recurrence pattern is supported.

    Raises:
        ValueError: If pattern is invalid
    """
    # Normalize pattern to lowercase for case-insensitive matching
    pattern = pattern.lower().strip()

    # Check simple patterns
    if pattern in SIMPLE_PATTERNS:
        return

    # Check custom patterns like "every 3 days", "every 2 weeks"
    match = re.match(CUSTOM_PATTERN_REGEX, pattern, re.IGNORECASE)
    if match:
        interval = int(match.group(1))
        # Unit (match.group(2)) is validated by regex pattern

        # Validate interval
        if interval <= 0:
            raise ValueError("Interval must be positive")
        if interval > 365:
            raise ValueError("Interval too large (max 365)")

        return

    # Pattern not recognized
    raise ValueError(
        f"Invalid recurrence pattern: '{pattern}'. "
        f"Supported patterns: daily, weekly, monthly, yearly, 'every N days', 'every N weeks', 'every N months', 'none'"
    )


def _parse_end_date(end_date_str: str) -> datetime:
    """Parse end date from natural language or ISO format.

    Args:
        end_date_str: Date string like "next year" or "2026-12-31"

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date cannot be parsed
    """
    # Try parsing with dateparser (supports natural language)
    parsed = dateparser.parse(
        end_date_str,
        settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False},
    )

    if not parsed:
        raise ValueError(f"Could not parse end date: '{end_date_str}'")

    # Ensure end date is in the future
    if parsed <= datetime.utcnow():
        raise ValueError("End date must be in the future")

    return parsed
