"""MCP Tool: set_reminder

Allows users to configure custom reminder intervals for tasks.

Phase V - Due Dates & Reminders
User Story 4: Custom Reminder Intervals
Tasks: T123-T130
"""

from typing import List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from sqlmodel import Session, select
import logging

from ..models import Task
from ..services.date_parser_service import parse_remind_before_natural, interval_to_timedelta, InvalidDateError

logger = logging.getLogger(__name__)


# ========== Custom Exceptions (T129) ==========

class NoDueDateError(Exception):
    """Raised when trying to set reminders for a task without a due date."""
    pass


class InvalidIntervalError(Exception):
    """Raised when an invalid interval format is provided."""
    pass


class TooManyIntervalsError(Exception):
    """Raised when more than 5 intervals are specified."""
    pass


# ========== Pydantic Models ==========

class SetReminderParams(BaseModel):
    """Parameters for set_reminder tool."""

    task_id: int = Field(description="Task ID to set reminders for")
    remind_before_natural: str = Field(
        description="Natural language reminder intervals (e.g., '3 days before and 1 hour before', '30 minutes before'). Use empty string to clear all reminders."
    )
    user_id: str = Field(description="User ID (for ownership verification)")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 42,
                "remind_before_natural": "3 days before and 1 hour before",
                "user_id": "user-123"
            }
        }


class SetReminderResult(BaseModel):
    """Result of set_reminder operation."""

    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Success or error message")
    intervals: List[str] = Field(default=[], description="Parsed reminder intervals (e.g., ['3d', '1h'])")
    reminder_times: List[str] = Field(default=[], description="Formatted reminder times with dates")
    warning: Optional[str] = Field(default=None, description="Warning message if any")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Reminders set successfully",
                "intervals": ["3d", "1h"],
                "reminder_times": [
                    "3d before (Feb 17 at 5:00 PM)",
                    "1h before (Feb 20 at 4:00 PM)"
                ],
                "warning": None
            }
        }


# ========== Main Function (T124) ==========

def set_reminder(params: SetReminderParams, db: Session) -> SetReminderResult:
    """Set custom reminder intervals for a task.

    Implements:
    - T124: Main set_reminder function
    - T125: Parse natural language intervals
    - T126: Validation (due date, max 5 intervals, intervals before due date)
    - T127: Update task.remind_before array
    - T128: Reset task.reminder_sent to {}
    - T129: Error handling with custom exceptions
    - T130: Return formatted reminder times

    Args:
        params: SetReminderParams with task_id, remind_before_natural, user_id
        db: Database session

    Returns:
        SetReminderResult with success status, intervals, and formatted times

    Raises:
        NoDueDateError: Task has no due date
        InvalidIntervalError: Invalid interval format
        TooManyIntervalsError: More than 5 intervals specified
        ValueError: Task not found or user doesn't own task
    """
    # Get task with user isolation (T127)
    task = db.exec(
        select(Task).where(
            Task.id == params.task_id,
            Task.user_id == params.user_id
        )
    ).first()

    if not task:
        raise ValueError(f"Task {params.task_id} not found for user {params.user_id}")

    # T126: Validate task has due date
    if not task.due_date:
        raise NoDueDateError(
            f"Task '{task.title}' must have a due date before setting reminders"
        )

    # Handle empty string = clear all reminders (T127)
    if not params.remind_before_natural or params.remind_before_natural.strip() == "":
        task.remind_before = []
        task.reminder_sent = {}  # T128: Reset reminder_sent
        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(f"Cleared all reminders for task_id={task.id}, user_id={params.user_id}")

        return SetReminderResult(
            success=True,
            message="All reminders cleared",
            intervals=[],
            reminder_times=[]
        )

    # T125: Parse natural language intervals
    try:
        intervals = parse_remind_before_natural(params.remind_before_natural)
    except ValueError as e:
        raise InvalidIntervalError(
            f"Invalid reminder interval format: {params.remind_before_natural}. {str(e)}"
        )

    # T126: Validate max 5 intervals
    if len(intervals) > 5:
        raise TooManyIntervalsError(
            f"Maximum 5 reminder intervals allowed. You specified {len(intervals)} intervals."
        )

    # T126: Validate intervals are before due date (warn if already passed)
    warning = None
    current_time = datetime.now(ZoneInfo("UTC"))
    passed_intervals = []

    for interval in intervals:
        try:
            delta = interval_to_timedelta(interval)
            reminder_time = task.due_date - delta

            # Ensure reminder_time is timezone-aware
            if reminder_time.tzinfo is None:
                reminder_time = reminder_time.replace(tzinfo=ZoneInfo("UTC"))

            if reminder_time < current_time:
                passed_intervals.append(interval)

        except Exception as e:
            logger.warning(f"Could not validate interval {interval}: {e}")

    if passed_intervals:
        warning = (
            f"Warning: Some reminder times have already passed: {', '.join(passed_intervals)}. "
            f"These reminders won't be sent."
        )

    # T127: Update task.remind_before array
    task.remind_before = intervals

    # T128: Reset reminder_sent to {} (user changed preferences)
    task.reminder_sent = {}

    # Commit changes
    db.add(task)
    db.commit()
    db.refresh(task)

    logger.info(
        f"Set reminders for task_id={task.id}, user_id={params.user_id}, "
        f"intervals={intervals}"
    )

    # T130: Return formatted reminder times
    reminder_times = _format_reminder_times(task.due_date, intervals)

    return SetReminderResult(
        success=True,
        message="Reminders set successfully",
        intervals=intervals,
        reminder_times=reminder_times,
        warning=warning
    )


# ========== Helper Functions ==========

def _format_reminder_times(due_date: datetime, intervals: List[str]) -> List[str]:
    """Format reminder times as human-readable strings (T130).

    Args:
        due_date: Task due date
        intervals: List of interval strings (e.g., ["3d", "1h"])

    Returns:
        List of formatted strings (e.g., ["3d before (Feb 17 at 5:00 PM UTC)"])
    """
    formatted_times = []

    for interval in intervals:
        try:
            delta = interval_to_timedelta(interval)
            reminder_time = due_date - delta

            # Ensure timezone-aware
            if reminder_time.tzinfo is None:
                reminder_time = reminder_time.replace(tzinfo=ZoneInfo("UTC"))

            # Format as "3d before (Feb 17 at 5:00 PM UTC)"
            formatted_date = reminder_time.strftime("%b %d at %I:%M %p %Z")
            formatted_str = f"{interval} before ({formatted_date})"

            formatted_times.append(formatted_str)

        except Exception as e:
            logger.warning(f"Could not format interval {interval}: {e}")
            formatted_times.append(f"{interval} before (formatting error)")

    return formatted_times
