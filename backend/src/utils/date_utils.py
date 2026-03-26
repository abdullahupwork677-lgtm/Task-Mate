"""Date utility functions for due date filtering and calculations.

This module provides helper functions for calculating date ranges used in
due date filtering (overdue, today, this week, this month).

Phase: 004-search-filter
Task: T031 (US5)
"""

from datetime import datetime, timedelta
from typing import Tuple


def get_today_range(timezone_offset: int = 0) -> Tuple[datetime, datetime]:
    """Get start and end of today (UTC).

    Args:
        timezone_offset: UTC offset in hours (default: 0)

    Returns:
        Tuple of (today_start, today_end) as datetime objects

    Examples:
        >>> start, end = get_today_range()
        >>> assert start.hour == 0
        >>> assert end.hour == 0
        >>> assert (end - start).days == 1
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    return today_start, today_end


def get_week_range() -> Tuple[datetime, datetime]:
    """Get start and end of current week (Monday to Sunday).

    Returns:
        Tuple of (week_start, week_end) as datetime objects

    Examples:
        >>> start, end = get_week_range()
        >>> assert start.weekday() == 0  # Monday
        >>> assert (end - start).days == 7
    """
    now = datetime.utcnow()
    # Get Monday of current week (weekday() returns 0 for Monday)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


def get_month_range() -> Tuple[datetime, datetime]:
    """Get start and end of current month.

    Returns:
        Tuple of (month_start, month_end) as datetime objects

    Examples:
        >>> start, end = get_month_range()
        >>> assert start.day == 1
        >>> assert end.day == 1  # First day of next month
    """
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate first day of next month
    if now.month == 12:
        month_end = month_start.replace(year=now.year + 1, month=1)
    else:
        month_end = month_start.replace(month=now.month + 1)

    return month_start, month_end


def is_overdue(due_date: datetime, completed: bool = False) -> bool:
    """Check if a task is overdue.

    A task is overdue if:
    - It has a due date
    - The due date is in the past (< now)
    - The task is not completed

    Args:
        due_date: Task due date
        completed: Whether task is completed

    Returns:
        True if task is overdue, False otherwise

    Examples:
        >>> past_date = datetime.utcnow() - timedelta(days=1)
        >>> assert is_overdue(past_date, completed=False) == True
        >>> assert is_overdue(past_date, completed=True) == False
        >>>
        >>> future_date = datetime.utcnow() + timedelta(days=1)
        >>> assert is_overdue(future_date, completed=False) == False
    """
    if completed:
        return False

    now = datetime.utcnow()
    return due_date < now


def calculate_overdue_duration(due_date: datetime) -> str:
    """Calculate human-readable overdue duration.

    Args:
        due_date: Task due date (must be in the past)

    Returns:
        Human-readable duration like "2 days", "3 hours", "45 minutes"

    Examples:
        >>> past = datetime.utcnow() - timedelta(days=2, hours=3)
        >>> duration = calculate_overdue_duration(past)
        >>> assert "day" in duration
    """
    now = datetime.utcnow()
    delta = now - due_date

    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return "less than a minute"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif total_seconds < 86400:  # Less than 1 day
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:  # Days
        days = total_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"


def format_date_range(filter_type: str) -> Tuple[datetime, datetime]:
    """Get date range for a due date filter type.

    Args:
        filter_type: One of 'today', 'this_week', 'this_month'

    Returns:
        Tuple of (range_start, range_end) as datetime objects

    Raises:
        ValueError: If filter_type is not recognized

    Examples:
        >>> start, end = format_date_range('today')
        >>> assert start.hour == 0
        >>> assert (end - start).days == 1
        >>>
        >>> start, end = format_date_range('this_week')
        >>> assert (end - start).days == 7
    """
    if filter_type == "today":
        return get_today_range()
    elif filter_type == "this_week":
        return get_week_range()
    elif filter_type == "this_month":
        return get_month_range()
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")


def is_date_in_range(
    date: datetime,
    range_start: datetime,
    range_end: datetime
) -> bool:
    """Check if a date falls within a range (inclusive start, exclusive end).

    Args:
        date: Date to check
        range_start: Start of range (inclusive)
        range_end: End of range (exclusive)

    Returns:
        True if date is in range, False otherwise

    Examples:
        >>> now = datetime.utcnow()
        >>> yesterday = now - timedelta(days=1)
        >>> tomorrow = now + timedelta(days=2)
        >>> assert is_date_in_range(now, yesterday, tomorrow) == True
        >>> assert is_date_in_range(yesterday, now, tomorrow) == False
    """
    return range_start <= date < range_end
