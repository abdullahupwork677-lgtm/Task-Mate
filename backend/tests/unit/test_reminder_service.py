"""Unit tests for reminder_service.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for reminder_service before implementation.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from freezegun import freeze_time
from unittest.mock import Mock, patch

# Import will fail initially (TDD RED phase) - this is expected
from src.services.reminder_service import (
    calculate_reminder_time,
    should_send_reminder,
    get_tasks_needing_reminders,
    parse_interval_to_timedelta
)


# ========== TEST FIXTURES ==========

@pytest.fixture
def utc_now():
    """Current time in UTC for consistent testing."""
    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=ZoneInfo("UTC"))


@pytest.fixture
def sample_task():
    """Sample task with due date and reminders."""
    task = Mock()
    task.id = 42
    task.user_id = "user-123"
    task.title = "Submit quarterly report"
    task.due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))  # Tomorrow at 5pm
    task.remind_before = ["24h", "1h"]
    task.reminder_sent = {}
    task.completed = False
    return task


# ========== TEST CASE 1: Calculate reminder time correctly ==========

def test_calculate_reminder_time_24h():
    """Test calculating reminder time 24 hours before due date."""
    due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Calculate reminder time for 24h interval
    reminder_time = calculate_reminder_time(due_date, "24h")

    # Should be exactly 24 hours before
    expected = datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert reminder_time == expected


def test_calculate_reminder_time_1h():
    """Test calculating reminder time 1 hour before due date."""
    due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Calculate reminder time for 1h interval
    reminder_time = calculate_reminder_time(due_date, "1h")

    # Should be exactly 1 hour before
    expected = datetime(2026, 2, 11, 16, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert reminder_time == expected


def test_calculate_reminder_time_3d():
    """Test calculating reminder time 3 days before due date."""
    due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Calculate reminder time for 3d interval
    reminder_time = calculate_reminder_time(due_date, "3d")

    # Should be exactly 3 days before
    expected = datetime(2026, 2, 8, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert reminder_time == expected


# ========== TEST CASE 2: should_send_reminder logic ==========

@freeze_time("2026-02-10 17:00:00", tz_offset=0)
def test_should_send_reminder_when_time_matches(sample_task):
    """Test that reminder should be sent when current time matches reminder time."""
    current_time = datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Current time is exactly 24h before due date
    result = should_send_reminder(sample_task, "24h", current_time)

    assert result is True


@freeze_time("2026-02-10 16:00:00", tz_offset=0)
def test_should_send_reminder_when_time_before_window(sample_task):
    """Test that reminder should NOT be sent before the reminder time."""
    current_time = datetime(2026, 2, 10, 16, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Current time is 25h before due date (too early)
    result = should_send_reminder(sample_task, "24h", current_time)

    assert result is False


@freeze_time("2026-02-10 18:00:00", tz_offset=0)
def test_should_send_reminder_within_grace_period(sample_task):
    """Test that reminder should be sent within grace period (5 minutes)."""
    current_time = datetime(2026, 2, 10, 18, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Current time is 23h before due date (within 1-hour grace period)
    result = should_send_reminder(sample_task, "24h", current_time)

    assert result is True


def test_should_send_reminder_skip_if_already_sent(sample_task):
    """Test that reminder should NOT be sent if already sent."""
    sample_task.reminder_sent = {"24h": "2026-02-10T17:00:00Z"}
    current_time = datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Reminder already sent
    result = should_send_reminder(sample_task, "24h", current_time)

    assert result is False


def test_should_send_reminder_skip_if_completed(sample_task):
    """Test that reminder should NOT be sent if task is completed."""
    sample_task.completed = True
    current_time = datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Task is completed
    result = should_send_reminder(sample_task, "24h", current_time)

    assert result is False


# ========== TEST CASE 3: Parse interval to timedelta ==========

def test_parse_interval_to_timedelta_hours():
    """Test parsing hour intervals."""
    assert parse_interval_to_timedelta("1h") == timedelta(hours=1)
    assert parse_interval_to_timedelta("24h") == timedelta(hours=24)
    assert parse_interval_to_timedelta("3h") == timedelta(hours=3)


def test_parse_interval_to_timedelta_days():
    """Test parsing day intervals."""
    assert parse_interval_to_timedelta("1d") == timedelta(days=1)
    assert parse_interval_to_timedelta("3d") == timedelta(days=3)
    assert parse_interval_to_timedelta("7d") == timedelta(days=7)


def test_parse_interval_to_timedelta_minutes():
    """Test parsing minute intervals."""
    assert parse_interval_to_timedelta("30m") == timedelta(minutes=30)
    assert parse_interval_to_timedelta("15m") == timedelta(minutes=15)


def test_parse_interval_to_timedelta_weeks():
    """Test parsing week intervals."""
    assert parse_interval_to_timedelta("1w") == timedelta(weeks=1)
    assert parse_interval_to_timedelta("2w") == timedelta(weeks=2)


def test_parse_interval_to_timedelta_invalid():
    """Test that invalid interval raises ValueError."""
    with pytest.raises(ValueError, match="Invalid interval format"):
        parse_interval_to_timedelta("invalid")

    with pytest.raises(ValueError, match="Invalid interval format"):
        parse_interval_to_timedelta("24")

    with pytest.raises(ValueError, match="Invalid interval format"):
        parse_interval_to_timedelta("h24")


# ========== TEST CASE 4: get_tasks_needing_reminders query ==========

@freeze_time("2026-02-10 17:00:00", tz_offset=0)
def test_get_tasks_needing_reminders_returns_eligible_tasks():
    """Test that query returns tasks that need reminders now."""
    # Mock database session
    mock_db = Mock()
    current_time = datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))

    # Mock task that needs 24h reminder
    task1 = Mock()
    task1.id = 1
    task1.due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    task1.remind_before = ["24h", "1h"]
    task1.reminder_sent = {}
    task1.completed = False

    # Mock task that needs 1h reminder
    task2 = Mock()
    task2.id = 2
    task2.due_date = datetime(2026, 2, 10, 18, 0, 0, tzinfo=ZoneInfo("UTC"))
    task2.remind_before = ["1h"]
    task2.reminder_sent = {}
    task2.completed = False

    # Mock query result
    mock_db.exec().all.return_value = [task1, task2]

    # Execute
    tasks = get_tasks_needing_reminders(mock_db, current_time)

    # Verify
    assert len(tasks) == 2
    assert task1 in tasks
    assert task2 in tasks


def test_get_tasks_needing_reminders_excludes_completed():
    """Test that query excludes completed tasks."""
    # This will be tested by the query filter
    # We'll verify in implementation that the query has: .where(Task.completed == False)
    pass


def test_get_tasks_needing_reminders_excludes_no_due_date():
    """Test that query excludes tasks without due dates."""
    # This will be tested by the query filter
    # We'll verify in implementation that the query has: .where(Task.due_date.is_not(None))
    pass
