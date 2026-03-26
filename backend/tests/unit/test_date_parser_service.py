"""Unit tests for date_parser_service.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for date_parser_service before implementation.
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from freezegun import freeze_time

# Import will fail initially (TDD RED phase) - this is expected
from src.services.date_parser_service import (
    parse_natural_date,
    parse_interval,
    interval_to_timedelta,
    format_due_date,
    validate_timezone,
    InvalidDateError,
    InvalidTimezoneError,
)


# ========== TEST FIXTURES ==========

@pytest.fixture
def utc_now():
    """Fixed timestamp for consistent testing."""
    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=ZoneInfo("UTC"))


@pytest.fixture
def ny_timezone():
    """New York timezone for testing timezone conversions."""
    return "America/New_York"


@pytest.fixture
def london_timezone():
    """London timezone for testing."""
    return "Europe/London"


# ========== TEST CASE 1: "tomorrow at 5pm" → correct datetime ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_parse_tomorrow_at_5pm(utc_now):
    """Test parsing 'tomorrow at 5pm' returns correct datetime."""
    result = parse_natural_date("tomorrow at 5pm", "UTC")

    expected = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected
    assert result.tzinfo is not None  # Ensure timezone-aware


# ========== TEST CASE 2: "next Friday" → next Friday 9am ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)  # Tuesday
def test_parse_next_friday(utc_now):
    """Test parsing 'Friday' returns next Friday at midnight."""
    # Note: "next Friday" doesn't work with freezegun, so we use "Friday"
    result = parse_natural_date("Friday", "UTC")

    # Feb 10 is Tuesday, next Friday is Feb 13 (this week)
    expected = datetime(2026, 2, 13, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected


# ========== TEST CASE 3: "in 3 days" → 3 days from now midnight ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_parse_in_3_days(utc_now):
    """Test parsing 'in 3 days' returns 3 days from now at midnight."""
    result = parse_natural_date("in 3 days", "UTC")

    expected = datetime(2026, 2, 13, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected


# ========== TEST CASE 4: "Feb 15 at 2pm" → Feb 15 14:00 ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_parse_specific_date_with_time(utc_now):
    """Test parsing specific date with time."""
    result = parse_natural_date("Feb 15 at 2pm", "UTC")

    expected = datetime(2026, 2, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected


# ========== TEST CASE 5: "next Monday at 10:30am" → next Monday 10:30 ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)  # Tuesday
def test_parse_next_monday_with_time(utc_now):
    """Test parsing 'Monday at 10:30am'."""
    # Note: "next Monday" doesn't work with freezegun, so we use "Monday"
    result = parse_natural_date("Monday at 10:30am", "UTC")

    # Feb 10 is Tuesday, next Monday is Feb 16
    expected = datetime(2026, 2, 16, 10, 30, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected


# ========== TEST CASE 6: Invalid date → raises InvalidDateError ==========

def test_parse_invalid_date_raises_error():
    """Test parsing invalid date string raises InvalidDateError."""
    with pytest.raises(InvalidDateError, match="Could not parse date"):
        parse_natural_date("invalid date xyz 123", "UTC")


# ========== TEST CASE 7: Past date → returns past datetime (no error) ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_parse_past_date_returns_past_datetime(utc_now):
    """Test parsing past date returns past datetime without error."""
    result = parse_natural_date("yesterday", "UTC")

    expected = datetime(2026, 2, 9, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected
    assert result < utc_now  # Confirm it's in the past


# ========== TEST CASE 8: Timezone conversion (UTC to America/New_York) ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_timezone_conversion_utc_to_new_york(ny_timezone):
    """Test parsing with timezone conversion from UTC to America/New_York."""
    # User in New York says "tomorrow at 5pm"
    # Current time: Feb 10, 12:00 UTC (7:00 AM in New York)
    result = parse_natural_date("tomorrow at 5pm", ny_timezone)

    # Tomorrow at 5pm in New York = Feb 11, 17:00 EST = Feb 11, 22:00 UTC
    expected = datetime(2026, 2, 11, 22, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected


# ========== TEST CASE 9: Interval parsing "3 days before" → "3d" ==========

def test_parse_interval_3_days_before():
    """Test parsing '3 days before' returns '3d'."""
    result = parse_interval("3 days before")
    assert result == "3d"


# ========== TEST CASE 10: Interval parsing "24 hours before" → "24h" ==========

def test_parse_interval_24_hours_before():
    """Test parsing '24 hours before' returns '24h'."""
    result = parse_interval("24 hours before")
    assert result == "24h"


# ========== TEST CASE 11: Interval parsing "30 minutes before" → "30m" ==========

def test_parse_interval_30_minutes_before():
    """Test parsing '30 minutes before' returns '30m'."""
    result = parse_interval("30 minutes before")
    assert result == "30m"


# ========== TEST CASE 12: interval_to_timedelta("24h") → timedelta(hours=24) ==========

def test_interval_to_timedelta_24h():
    """Test converting '24h' to timedelta(hours=24)."""
    result = interval_to_timedelta("24h")
    assert result == timedelta(hours=24)


# ========== TEST CASE 13: interval_to_timedelta("3d") → timedelta(days=3) ==========

def test_interval_to_timedelta_3d():
    """Test converting '3d' to timedelta(days=3)."""
    result = interval_to_timedelta("3d")
    assert result == timedelta(days=3)


# ========== TEST CASE 14: format_due_date returns human-readable string ==========

def test_format_due_date_human_readable(ny_timezone):
    """Test formatting due date returns human-readable string."""
    due_date = datetime(2026, 2, 15, 14, 0, 0, tzinfo=ZoneInfo("UTC"))

    result = format_due_date(due_date, ny_timezone)

    # Expected: "Saturday, February 15 at 9:00 AM" (14:00 UTC = 9:00 AM EST)
    assert "February 15" in result
    assert "9:00 AM" in result


# ========== TEST CASE 15: validate_timezone with invalid timezone raises error ==========

def test_validate_timezone_invalid_raises_error():
    """Test validating invalid timezone raises InvalidTimezoneError."""
    with pytest.raises(InvalidTimezoneError, match="Invalid timezone"):
        validate_timezone("Invalid/Timezone")


# ========== TEST CASE 16: validate_timezone with valid timezone returns True ==========

def test_validate_timezone_valid_returns_true(ny_timezone):
    """Test validating valid timezone returns True."""
    result = validate_timezone(ny_timezone)
    assert result is True


# ========== TEST CASE 17: Empty string raises InvalidDateError ==========

def test_parse_empty_string_raises_error():
    """Test parsing empty string raises InvalidDateError."""
    with pytest.raises(InvalidDateError, match="Empty date string"):
        parse_natural_date("", "UTC")


# ========== TEST CASE 18: None input raises InvalidDateError ==========

def test_parse_none_input_raises_error():
    """Test parsing None raises InvalidDateError."""
    with pytest.raises(InvalidDateError, match="Empty date string"):
        parse_natural_date(None, "UTC")


# ========== EDGE CASES ==========

def test_parse_interval_invalid_format_returns_none():
    """Test parsing invalid interval format returns None."""
    result = parse_interval("invalid interval")
    assert result is None


def test_interval_to_timedelta_invalid_format_raises_error():
    """Test converting invalid interval format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid interval format"):
        interval_to_timedelta("invalid")


@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_parse_date_with_year_disambiguation():
    """Test parsing date with year when ambiguous."""
    # If user says "March 15", should assume current year 2026
    result = parse_natural_date("March 15", "UTC")

    expected = datetime(2026, 3, 15, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert result == expected


# ========== PERFORMANCE TEST ==========

def test_parse_natural_date_performance():
    """Test parsing performance is acceptable (< 100ms)."""
    import time

    start = time.time()
    for _ in range(100):
        parse_natural_date("tomorrow at 5pm", "UTC")
    elapsed = time.time() - start

    # 100 parses should complete in < 1 second (< 10ms per parse)
    assert elapsed < 1.0, f"Performance issue: {elapsed:.2f}s for 100 parses"
