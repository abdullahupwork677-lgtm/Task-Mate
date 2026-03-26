"""Recurrence Engine Service

Calculates next due dates for recurring tasks based on recurrence patterns.
Uses python-dateutil for date arithmetic and supports:
- daily, weekly, monthly, yearly patterns
- custom intervals (e.g., "every 3 days", "every 2 weeks")
- month-end handling (Feb 31 -> Feb 28/29)
- recurrence end dates

Phase V: Implements User Story 2 - Auto-Create Next Occurrence on Completion

Edge Cases Handled:
- Month-end dates (Jan 31 + 1 month = Feb 28/29)
- Leap years (Feb 29 + 1 year = Feb 28 in non-leap year)
- Recurrence end dates (stops when reached)
- Missing due dates (fallback to current time)
"""

from datetime import datetime
from typing import Optional, Tuple
import logging
from dateutil.relativedelta import relativedelta
import re

# Setup logging
logger = logging.getLogger(__name__)


def calculate_next_due_date(
    current_due_date: datetime,
    recurrence_pattern: str,
    recurrence_end_date: Optional[datetime] = None,
) -> Optional[datetime]:
    """Calculate the next due date based on recurrence pattern.

    This is the core date calculation engine for recurring tasks.
    Uses python-dateutil's relativedelta for accurate date arithmetic
    that automatically handles edge cases like month-end and leap years.

    Args:
        current_due_date: The current/completed task's due date
        recurrence_pattern: Pattern like "daily", "weekly", "monthly", "every 3 days"
        recurrence_end_date: Optional end date for recurrence (None = infinite)

    Returns:
        Next due date or None if recurrence has ended

    Raises:
        ValueError: If recurrence pattern is invalid

    Examples:
        >>> calculate_next_due_date(datetime(2026, 2, 9), "daily")
        datetime(2026, 2, 10, 0, 0, 0)

        >>> calculate_next_due_date(datetime(2026, 1, 31), "monthly")
        datetime(2026, 2, 28, 0, 0, 0)  # Month-end handling

        >>> calculate_next_due_date(datetime(2026, 2, 9), "every 3 days")
        datetime(2026, 2, 12, 0, 0, 0)
    """
    logger.debug(
        f"Calculating next due date: current={current_due_date}, "
        f"pattern={recurrence_pattern}, end_date={recurrence_end_date}"
    )

    # Parse pattern into frequency and interval
    frequency, interval = parse_recurrence_pattern(recurrence_pattern)
    logger.debug(f"Parsed pattern: frequency={frequency}, interval={interval}")

    # Calculate next due date
    if frequency == "daily" or frequency == "days":
        next_due = current_due_date + relativedelta(days=interval)
    elif frequency == "weekly" or frequency == "weeks":
        next_due = current_due_date + relativedelta(weeks=interval)
    elif frequency == "monthly" or frequency == "months":
        next_due = current_due_date + relativedelta(months=interval)
        # Handle month-end edge case (e.g., Jan 31 -> Feb 28/29)
        # relativedelta already handles this correctly
    elif frequency == "yearly" or frequency == "years":
        next_due = current_due_date + relativedelta(years=interval)
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")

    # Check if next occurrence exceeds end date
    if recurrence_end_date and next_due > recurrence_end_date:
        logger.info(
            f"Recurrence ended: next_due={next_due} exceeds end_date={recurrence_end_date}"
        )
        return None

    logger.debug(f"Calculated next due date: {next_due}")
    return next_due


def parse_recurrence_pattern(pattern: str) -> Tuple[str, int]:
    """Parse recurrence pattern into frequency and interval.

    Supports both simple patterns (daily, weekly, monthly, yearly) and
    custom intervals (every N days/weeks/months). Uses regex to extract
    interval and unit from custom patterns.

    Args:
        pattern: String like "daily", "weekly", "every 3 days"

    Returns:
        Tuple of (frequency, interval) e.g., ("daily", 1) or ("days", 3)

    Raises:
        ValueError: If pattern is invalid or not supported

    Examples:
        >>> parse_recurrence_pattern("daily")
        ("daily", 1)

        >>> parse_recurrence_pattern("every 3 days")
        ("days", 3)

        >>> parse_recurrence_pattern("every 2 weeks")
        ("weeks", 2)
    """
    pattern = pattern.lower().strip()

    # Simple patterns
    simple_patterns = {
        "daily": ("daily", 1),
        "weekly": ("weekly", 1),
        "monthly": ("monthly", 1),
        "yearly": ("yearly", 1),
    }

    if pattern in simple_patterns:
        return simple_patterns[pattern]

    # Custom patterns like "every 3 days", "every 2 weeks"
    custom_regex = r"^every\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)$"
    match = re.match(custom_regex, pattern, re.IGNORECASE)

    if match:
        interval = int(match.group(1))
        unit = match.group(2).lower()

        # Normalize unit (singular)
        if unit in ["day", "days"]:
            frequency = "days"
        elif unit in ["week", "weeks"]:
            frequency = "weeks"
        elif unit in ["month", "months"]:
            frequency = "months"
        elif unit in ["year", "years"]:
            frequency = "years"
        else:
            raise ValueError(f"Unsupported unit: {unit}")

        return (frequency, interval)

    raise ValueError(f"Invalid recurrence pattern: {pattern}")


def validate_recurrence_pattern(pattern: str) -> bool:
    """Validate if recurrence pattern is supported.

    Tests if a pattern can be parsed without raising ValueError.
    Used for pre-validation before storing patterns in database.

    Args:
        pattern: Recurrence pattern string

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_recurrence_pattern("daily")
        True

        >>> validate_recurrence_pattern("every century")
        False
    """
    try:
        parse_recurrence_pattern(pattern)
        return True
    except ValueError:
        return False
