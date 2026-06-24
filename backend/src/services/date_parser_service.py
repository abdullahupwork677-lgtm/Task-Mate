"""Date Parser Service for natural language date parsing with timezone awareness.

This service provides functions for parsing natural language dates like:
- "tomorrow at 5pm"
- "next Friday"
- "in 3 days"
- "Feb 15 at 2pm"

All dates are stored in UTC internally and converted to user timezones for display.
"""

import re
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
import dateparser
import pytz


# ========== CUSTOM EXCEPTIONS ==========

class InvalidDateError(ValueError):
    """Raised when a date string cannot be parsed."""
    pass


class InvalidTimezoneError(ValueError):
    """Raised when a timezone is invalid."""
    pass


# ========== CORE FUNCTIONS ==========

def parse_natural_date(text: Optional[str], user_timezone: str) -> datetime:
    """Parse natural language date string with timezone awareness.

    Args:
        text: Natural language date string (e.g., "tomorrow at 5pm", "next Friday")
        user_timezone: IANA timezone string (e.g., "America/New_York", "UTC")

    Returns:
        Timezone-aware datetime object in UTC

    Raises:
        InvalidDateError: If date string cannot be parsed or is empty
        InvalidTimezoneError: If timezone is invalid

    Examples:
        >>> parse_natural_date("tomorrow at 5pm", "America/New_York")
        datetime(2026, 2, 11, 22, 0, 0, tzinfo=ZoneInfo(key='UTC'))

        >>> parse_natural_date("next Friday", "UTC")
        datetime(2026, 2, 14, 9, 0, 0, tzinfo=ZoneInfo(key='UTC'))
    """
    # Validate input
    if not text or (isinstance(text, str) and text.strip() == ""):
        raise InvalidDateError("Empty date string provided")

    # Validate timezone
    validate_timezone(user_timezone)

    # Parse using dateparser with user's timezone
    # dateparser settings: prefer dates in the future, use user timezone
    settings = {
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': user_timezone,
        'RETURN_AS_TIMEZONE_AWARE': True,
        'TO_TIMEZONE': 'UTC',  # Convert result to UTC
    }

    parsed_date = dateparser.parse(text.strip(), settings=settings)

    if parsed_date is None:
        raise InvalidDateError(f"Could not parse date: '{text}'")

    # Ensure timezone-aware datetime in UTC
    if parsed_date.tzinfo is None:
        # If somehow not timezone-aware, assume user timezone and convert to UTC
        user_tz = ZoneInfo(user_timezone)
        parsed_date = parsed_date.replace(tzinfo=user_tz)
        parsed_date = parsed_date.astimezone(ZoneInfo("UTC"))

    # For relative phrases without specific time (e.g., "in 3 days", "yesterday"),
    # set time to midnight if no specific time was mentioned
    text_lower = text.lower()
    has_time_indicator = any(indicator in text_lower for indicator in [
        'am', 'pm', ':', 'morning', 'afternoon', 'evening', 'night', 'noon', 'midnight'
    ])

    if not has_time_indicator and any(phrase in text_lower for phrase in [
        'in ', 'yesterday', 'day', 'tomorrow', 'next ', 'last '
    ]):
        # Reset to midnight in the target date
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return parsed_date


def parse_interval(text: str) -> Optional[str]:
    """Parse natural language interval to standardized format.

    Args:
        text: Natural language interval (e.g., "3 days before", "24 hours before")

    Returns:
        Standardized interval string (e.g., "3d", "24h", "30m") or None if invalid

    Examples:
        >>> parse_interval("3 days before")
        '3d'

        >>> parse_interval("24 hours before")
        '24h'

        >>> parse_interval("30 minutes before")
        '30m'

        >>> parse_interval("invalid interval")
        None
    """
    # Pattern: extract number and unit from phrases like "3 days before", "24 hours before"
    pattern = r'(\d+)\s*(minute|minutes|min|hour|hours|hr|h|day|days|d|week|weeks|w)'
    match = re.search(pattern, text.lower())

    if not match:
        return None

    number = match.group(1)
    unit = match.group(2)

    # Normalize unit to single letter
    if unit in ['minute', 'minutes', 'min']:
        unit_letter = 'm'
    elif unit in ['hour', 'hours', 'hr', 'h']:
        unit_letter = 'h'
    elif unit in ['day', 'days', 'd']:
        unit_letter = 'd'
    elif unit in ['week', 'weeks', 'w']:
        unit_letter = 'w'
    else:
        return None

    return f"{number}{unit_letter}"


def parse_remind_before_natural(text: str) -> list[str]:
    """Parse natural language reminder intervals to standardized format.

    Args:
        text: Natural language reminder intervals (e.g., "24h and 1h before", "remind me 3 days and 1 hour before")

    Returns:
        List of standardized interval strings (e.g., ["24h", "1h"], ["3d", "1h"])

    Raises:
        ValueError: If no valid intervals found

    Examples:
        >>> parse_remind_before_natural("24h and 1h before")
        ['24h', '1h']

        >>> parse_remind_before_natural("remind me 3 days and 1 hour before")
        ['3d', '1h']

        >>> parse_remind_before_natural("30 minutes before")
        ['30m']
    """
    # Find all intervals in the text using parse_interval
    intervals = []

    # Pattern: find all number + unit combinations
    pattern = r'(\d+\s*(?:minute|minutes|min|hour|hours|hr|h|day|days|d|week|weeks|w))'
    matches = re.findall(pattern, text.lower())

    for match in matches:
        interval = parse_interval(match)
        if interval and interval not in intervals:  # Avoid duplicates
            intervals.append(interval)

    if not intervals:
        raise ValueError(f"No valid reminder intervals found in '{text}'")

    return intervals


def interval_to_timedelta(interval: str) -> timedelta:
    """Convert standardized interval string to timedelta object.

    Args:
        interval: Standardized interval (e.g., "24h", "3d", "30m", "1w")

    Returns:
        timedelta object representing the interval

    Raises:
        ValueError: If interval format is invalid

    Examples:
        >>> interval_to_timedelta("24h")
        timedelta(hours=24)

        >>> interval_to_timedelta("3d")
        timedelta(days=3)

        >>> interval_to_timedelta("30m")
        timedelta(minutes=30)
    """
    # Pattern: number followed by unit letter (m, h, d, w)
    pattern = r'^(\d+)([mhdw])$'
    match = re.match(pattern, interval)

    if not match:
        raise ValueError(f"Invalid interval format: '{interval}'. Expected format: '24h', '3d', '30m', '1w'")

    number = int(match.group(1))
    unit = match.group(2)

    if unit == 'm':
        return timedelta(minutes=number)
    elif unit == 'h':
        return timedelta(hours=number)
    elif unit == 'd':
        return timedelta(days=number)
    elif unit == 'w':
        return timedelta(weeks=number)
    else:
        raise ValueError(f"Invalid unit: '{unit}'")


def format_due_date(due_date: datetime, user_timezone: str) -> str:
    """Format due date as human-readable string in user's timezone.

    Args:
        due_date: Timezone-aware datetime in UTC
        user_timezone: IANA timezone for display

    Returns:
        Human-readable date string (e.g., "Saturday, February 15 at 9:00 AM")

    Examples:
        >>> due_date = datetime(2026, 2, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
        >>> format_due_date(due_date, "America/New_York")
        'Sunday, February 15 at 9:00 AM'
    """
    validate_timezone(user_timezone)

    # Convert UTC to user timezone
    user_tz = ZoneInfo(user_timezone)
    local_date = due_date.astimezone(user_tz)

    # Format: "Saturday, February 15 at 9:00 AM"
    hour_12 = local_date.hour % 12
    if hour_12 == 0:
        hour_12 = 12
    formatted = local_date.strftime(f"%A, %B %d at {hour_12}:%M %p")

    return formatted


def validate_timezone(timezone: str) -> bool:
    """Validate timezone string against IANA timezone database.

    Args:
        timezone: IANA timezone string (e.g., "America/New_York", "UTC")

    Returns:
        True if valid

    Raises:
        InvalidTimezoneError: If timezone is invalid

    Examples:
        >>> validate_timezone("America/New_York")
        True

        >>> validate_timezone("Invalid/Timezone")
        InvalidTimezoneError: Invalid timezone: 'Invalid/Timezone'
    """
    if timezone not in pytz.all_timezones:
        raise InvalidTimezoneError(f"Invalid timezone: '{timezone}'. Must be valid IANA timezone.")

    return True


# ========== HELPER FUNCTIONS ==========

def calculate_reminder_time(due_date: datetime, interval: str) -> datetime:
    """Calculate when a reminder should be sent based on due date and interval.

    Args:
        due_date: When task is due (UTC)
        interval: Reminder interval (e.g., "24h", "1h", "3d")

    Returns:
        Datetime when reminder should be sent (UTC)

    Examples:
        >>> due_date = datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        >>> calculate_reminder_time(due_date, "24h")
        datetime(2026, 2, 14, 17, 0, 0, tzinfo=ZoneInfo(key='UTC'))
    """
    delta = interval_to_timedelta(interval)
    reminder_time = due_date - delta
    return reminder_time


def is_reminder_due(reminder_time: datetime, current_time: datetime) -> bool:
    """Check if a reminder should be sent now.

    A reminder is due if current time >= reminder time and within 5-minute window.

    Args:
        reminder_time: When reminder should be sent
        current_time: Current datetime

    Returns:
        True if reminder should be sent now

    Examples:
        >>> reminder_time = datetime(2026, 2, 14, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        >>> current_time = datetime(2026, 2, 14, 17, 2, 0, tzinfo=ZoneInfo("UTC"))
        >>> is_reminder_due(reminder_time, current_time)
        True
    """
    # Allow 5-minute grace period after reminder time
    grace_period = timedelta(minutes=5)

    return reminder_time <= current_time <= (reminder_time + grace_period)
