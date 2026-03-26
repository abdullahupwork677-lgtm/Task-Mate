"""Unit tests for set_due_date MCP tool.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for set_due_date before implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from freezegun import freeze_time
from zoneinfo import ZoneInfo

# Import will fail initially (TDD RED phase) - this is expected
from src.mcp_tools.set_due_date import set_due_date
from src.services.date_parser_service import InvalidDateError


# ========== TEST FIXTURES ==========

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return Mock()


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    task = Mock()
    task.id = 42
    task.user_id = "user-123"
    task.title = "Submit quarterly report"
    task.due_date = None
    task.remind_before = ["24h", "1h"]
    task.reminder_sent = {}
    task.completed = False
    return task


@pytest.fixture
def user_timezone():
    """User timezone for testing."""
    return "America/New_York"


# ========== TEST CASE 1: Set due date with natural language ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_with_natural_language(mock_db_session, sample_task, user_timezone):
    """Test setting due date using natural language input."""
    # Mock database query
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute
    result = set_due_date(
        task_id=42,
        due_date_natural="tomorrow at 5pm",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    # Verify
    assert result["success"] is True
    assert result["task_id"] == 42
    assert result["due_date_formatted"] is not None
    assert "Tomorrow" in result["due_date_formatted"] or "February 11" in result["due_date_formatted"]
    assert sample_task.due_date is not None
    assert sample_task.reminder_sent == {}  # Reset when due date changes


# ========== TEST CASE 2: Task not found error ==========

def test_set_due_date_task_not_found(mock_db_session, user_timezone):
    """Test error when task doesn't exist."""
    # Mock database queries return None for both the user-isolated query and existence check
    mock_db_session.query().filter().filter().first.return_value = None
    mock_db_session.query().filter().first.return_value = None  # Also for existence check

    # Execute and expect error
    with pytest.raises(ValueError, match="Task .* not found"):
        set_due_date(
            task_id=999,
            due_date_natural="tomorrow",
            user_id="user-123",
            user_timezone=user_timezone,
            db=mock_db_session
        )


# ========== TEST CASE 3: Unauthorized access (wrong user) ==========

def test_set_due_date_unauthorized(mock_db_session, sample_task, user_timezone):
    """Test error when user tries to modify another user's task."""
    sample_task.user_id = "user-456"  # Different user

    # First query (with user isolation) returns None
    mock_db_session.query().filter().filter().first.return_value = None

    # Second query (existence check without user filter) returns the task
    mock_db_session.query().filter().first.return_value = sample_task

    # Execute and expect error
    with pytest.raises(PermissionError, match="Not authorized"):
        set_due_date(
            task_id=42,
            due_date_natural="tomorrow",
            user_id="user-123",  # Different from task owner
            user_timezone=user_timezone,
            db=mock_db_session
        )


# ========== TEST CASE 4: Invalid date string ==========

def test_set_due_date_invalid_date(mock_db_session, sample_task, user_timezone):
    """Test error when date string cannot be parsed."""
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute and expect error
    with pytest.raises(InvalidDateError, match="Could not parse date"):
        set_due_date(
            task_id=42,
            due_date_natural="invalid date xyz",
            user_id="user-123",
            user_timezone=user_timezone,
            db=mock_db_session
        )


# ========== TEST CASE 5: Reset reminder_sent when due_date changes ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_resets_reminder_sent(mock_db_session, sample_task, user_timezone):
    """Test that changing due date resets reminder_sent to empty object."""
    # Setup: Task already has reminders sent
    sample_task.due_date = datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    sample_task.reminder_sent = {"24h": "2026-02-14T17:00:00Z"}

    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute (use "Monday" instead of "next Monday" due to freezegun limitations)
    result = set_due_date(
        task_id=42,
        due_date_natural="Monday",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    # Verify reminder_sent was reset
    assert sample_task.reminder_sent == {}
    assert result["success"] is True


# ========== TEST CASE 6: Return human-readable due date ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_returns_formatted_date(mock_db_session, sample_task, user_timezone):
    """Test that response includes human-readable due date."""
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute
    result = set_due_date(
        task_id=42,
        due_date_natural="Feb 15 at 2pm",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    # Verify formatted date is returned
    assert "due_date_formatted" in result
    assert "February 15" in result["due_date_formatted"]
    assert "PM" in result["due_date_formatted"]


# ========== TEST CASE 7: Database commit is called ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_commits_to_database(mock_db_session, sample_task, user_timezone):
    """Test that database changes are committed."""
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute
    set_due_date(
        task_id=42,
        due_date_natural="tomorrow",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    # Verify commit was called
    mock_db_session.commit.assert_called_once()


# ========== TEST CASE 8: Set past due date (overdue task) ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_past_date_allowed(mock_db_session, sample_task, user_timezone):
    """Test that setting past due date is allowed (for overdue tasks)."""
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute with past date
    result = set_due_date(
        task_id=42,
        due_date_natural="yesterday",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    # Verify it succeeds
    assert result["success"] is True
    assert sample_task.due_date < datetime.now(ZoneInfo("UTC"))


# ========== TEST CASE 9: Timezone conversion works correctly ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_timezone_conversion(mock_db_session, sample_task):
    """Test that timezone conversion works for different timezones."""
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # User in New York says "tomorrow at 5pm"
    result = set_due_date(
        task_id=42,
        due_date_natural="tomorrow at 5pm",
        user_id="user-123",
        user_timezone="America/New_York",
        db=mock_db_session
    )

    # Due date should be stored in UTC (5pm EST = 10pm UTC)
    assert result["success"] is True
    # Stored in UTC but formatted for user's timezone
    assert "5:00 PM" in result["due_date_formatted"]


# ========== TEST CASE 10: Empty or None due_date_natural raises error ==========

def test_set_due_date_empty_string_raises_error(mock_db_session, sample_task, user_timezone):
    """Test that empty date string raises error."""
    mock_db_session.query().filter().filter().first.return_value = sample_task

    with pytest.raises(InvalidDateError, match="Empty date string"):
        set_due_date(
            task_id=42,
            due_date_natural="",
            user_id="user-123",
            user_timezone=user_timezone,
            db=mock_db_session
        )


# ========== EDGE CASES ==========

def test_set_due_date_for_completed_task_allowed(mock_db_session, sample_task, user_timezone):
    """Test that setting due date on completed task is allowed (for rescheduling)."""
    sample_task.completed = True
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Should succeed
    result = set_due_date(
        task_id=42,
        due_date_natural="tomorrow",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    assert result["success"] is True


@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_set_due_date_updates_existing_due_date(mock_db_session, sample_task, user_timezone):
    """Test updating an existing due date."""
    # Setup: Task already has a due date
    sample_task.due_date = datetime(2026, 2, 20, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
    mock_db_session.query().filter().filter().first.return_value = sample_task

    # Execute with new due date
    result = set_due_date(
        task_id=42,
        due_date_natural="tomorrow at 3pm",
        user_id="user-123",
        user_timezone=user_timezone,
        db=mock_db_session
    )

    # Verify due date was updated
    assert result["success"] is True
    assert sample_task.due_date != datetime(2026, 2, 20, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
