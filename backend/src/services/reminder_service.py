"""Reminder Service

Calculates when reminders should be sent and queries tasks needing reminders.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo
from sqlmodel import Session, select, and_

from src.models import Task

logger = logging.getLogger(__name__)

# Grace period for sending reminders (allows for cron schedule drift)
GRACE_PERIOD_MINUTES = 60  # 1 hour grace period


def parse_interval_to_timedelta(interval: str) -> timedelta:
    """Parse interval string to timedelta.

    Args:
        interval: Interval string (e.g., "24h", "1d", "30m", "1w")

    Returns:
        timedelta object

    Raises:
        ValueError: If interval format is invalid

    Examples:
        >>> parse_interval_to_timedelta("24h")
        timedelta(hours=24)
        >>> parse_interval_to_timedelta("3d")
        timedelta(days=3)
        >>> parse_interval_to_timedelta("30m")
        timedelta(minutes=30)
    """
    # Pattern: number followed by unit (m/h/d/w)
    pattern = r'^(\d+)([mhdw])$'
    match = re.match(pattern, interval)

    if not match:
        raise ValueError(
            f"Invalid interval format: '{interval}'. "
            f"Expected format: <number><unit> where unit is m/h/d/w "
            f"(e.g., '24h', '3d', '30m', '1w')"
        )

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == 'm':
        return timedelta(minutes=amount)
    elif unit == 'h':
        return timedelta(hours=amount)
    elif unit == 'd':
        return timedelta(days=amount)
    elif unit == 'w':
        return timedelta(weeks=amount)
    else:
        raise ValueError(f"Invalid interval unit: '{unit}'")


def calculate_reminder_time(due_date: datetime, interval: str) -> datetime:
    """Calculate when a reminder should be sent.

    Args:
        due_date: Task due date (timezone-aware)
        interval: Reminder interval (e.g., "24h", "1h", "3d")

    Returns:
        Reminder time (timezone-aware)

    Examples:
        >>> due = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        >>> calculate_reminder_time(due, "24h")
        datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    """
    delta = parse_interval_to_timedelta(interval)
    reminder_time = due_date - delta

    # Ensure reminder_time is timezone-aware (inherit from due_date or default to UTC)
    if reminder_time.tzinfo is None:
        from zoneinfo import ZoneInfo
        reminder_time = reminder_time.replace(tzinfo=ZoneInfo("UTC"))

    logger.debug(
        f"Calculated reminder time: due_date={due_date}, interval={interval}, "
        f"reminder_time={reminder_time}"
    )

    return reminder_time


def should_send_reminder(
    task: Task,
    interval: str,
    current_time: datetime
) -> bool:
    """Determine if a reminder should be sent for a task.

    Logic:
    1. Skip if task is completed
    2. Skip if reminder already sent for this interval
    3. Skip if no due date
    4. Check if current time is within reminder window (with grace period)

    Args:
        task: Task to check
        interval: Reminder interval (e.g., "24h", "1h")
        current_time: Current time (timezone-aware)

    Returns:
        True if reminder should be sent, False otherwise

    Examples:
        >>> task = Task(due_date=..., remind_before=["24h"], reminder_sent={}, completed=False)
        >>> should_send_reminder(task, "24h", current_time)
        True
    """
    # Skip completed tasks (T068)
    if task.completed:
        logger.debug(f"Task {task.id}: Skip (completed)")
        return False

    # Skip if reminder already sent for this interval (T068)
    if task.reminder_sent and interval in task.reminder_sent:
        logger.debug(
            f"Task {task.id}: Skip (reminder already sent for {interval} "
            f"at {task.reminder_sent[interval]})"
        )
        return False

    # Skip if no due date
    if not task.due_date:
        logger.debug(f"Task {task.id}: Skip (no due date)")
        return False

    # Calculate reminder time
    reminder_time = calculate_reminder_time(task.due_date, interval)

    # Check if current time is within reminder window
    # We use a grace period to account for cron schedule drift
    grace_period = timedelta(minutes=GRACE_PERIOD_MINUTES)

    # Reminder window: [reminder_time, reminder_time + grace_period]
    is_within_window = (
        reminder_time <= current_time <= (reminder_time + grace_period)
    )

    if is_within_window:
        logger.info(
            f"Task {task.id}: Reminder due (interval={interval}, "
            f"reminder_time={reminder_time}, current_time={current_time})"
        )
    else:
        logger.debug(
            f"Task {task.id}: Not within reminder window "
            f"(reminder_time={reminder_time}, current_time={current_time}, "
            f"grace_period={grace_period})"
        )

    return is_within_window


def get_tasks_needing_reminders(
    db: Session,
    current_time: datetime
) -> List[Task]:
    """Query tasks that need reminders sent now.

    Optimized query using idx_tasks_reminders index for performance.

    Filters:
    - Has due_date (NOT NULL)
    - Not completed (completed = False)
    - Due date is in the future (due_date > current_time)

    Performance:
    - Uses composite index: idx_tasks_reminders (completed, due_date)
    - Target: < 50ms for 10,000 tasks

    Args:
        db: Database session
        current_time: Current time (timezone-aware)

    Returns:
        List of tasks needing reminders

    Examples:
        >>> tasks = get_tasks_needing_reminders(db, datetime.now(ZoneInfo("UTC")))
        >>> assert all(not task.completed for task in tasks)
        >>> assert all(task.due_date is not None for task in tasks)
    """
    # Query tasks with due dates that are not completed (T067, T069)
    # Uses idx_tasks_reminders index: CREATE INDEX idx_tasks_reminders ON tasks (completed, due_date)
    query = (
        select(Task)
        .where(
            and_(
                Task.completed == False,  # Index column 1
                Task.due_date.is_not(None),  # Filter NULL due dates
                Task.due_date > current_time,  # Only future tasks
            )
        )
        .order_by(Task.due_date)  # Order by due date for efficient processing
    )

    try:
        tasks = db.exec(query).all()
        logger.info(
            f"Found {len(tasks)} tasks with due dates (not completed, due in future)"
        )
        return list(tasks)
    except Exception as e:
        logger.error(f"Failed to query tasks needing reminders: {e}", exc_info=True)
        raise RuntimeError(f"Failed to query tasks: {str(e)}") from e
