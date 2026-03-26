"""Unit Tests for set_reminder MCP Tool

Tests for the set_reminder tool that allows users to configure custom reminder intervals.

Following TDD approach - tests written FIRST before implementation.

Phase V - Due Dates & Reminders
User Story 4: Custom Reminder Intervals
Task: T122
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

from src.models import Task, User
from src.mcp_tools.set_reminder import (
    set_reminder,
    SetReminderParams,
    SetReminderResult,
    NoDueDateError,
    InvalidIntervalError,
    TooManyIntervalsError
)


# In-memory SQLite for testing
@pytest.fixture(name="test_db")
def test_db_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    user = User(
        id="test-user-set-reminder",
        email="setreminder@example.com",
        name="Set Reminder Test User",
        password_hash="$2b$12$dummy.hash",
        timezone="America/New_York"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def task_with_due_date(test_db: Session, test_user: User):
    """Create a task with a due date."""
    due_date = datetime(2026, 2, 20, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    task = Task(
        user_id=test_user.id,
        title="Test task",
        due_date=due_date,
        remind_before=["24h", "1h"],  # Default reminders
        reminder_sent={},
        completed=False
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


# ========== TEST CASE 1: Set custom reminder intervals ==========

def test_set_reminder_with_custom_intervals(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: Set custom reminder intervals (T123, T124, T125)"""
    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="3 days before and 1 hour before",
        user_id=test_user.id
    )

    result = set_reminder(params, test_db)

    # Verify success
    assert result.success is True
    assert result.message == "Reminders set successfully"

    # Verify intervals were parsed correctly
    assert result.intervals == ["3d", "1h"]

    # Verify task was updated
    test_db.refresh(task_with_due_date)
    assert task_with_due_date.remind_before == ["3d", "1h"]


# ========== TEST CASE 2: Reset reminder_sent when intervals change ==========

def test_set_reminder_resets_reminder_sent(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: reminder_sent reset to {} when user changes intervals (T128)"""
    # Set some previous reminders as sent
    task_with_due_date.reminder_sent = {"24h": "2026-02-19T17:00:00Z"}
    test_db.add(task_with_due_date)
    test_db.commit()

    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="2 days before",
        user_id=test_user.id
    )

    result = set_reminder(params, test_db)

    # Verify reminder_sent was reset
    test_db.refresh(task_with_due_date)
    assert task_with_due_date.reminder_sent == {}
    assert result.success is True


# ========== TEST CASE 3: Error - Task has no due date ==========

def test_set_reminder_no_due_date_error(
    test_db: Session,
    test_user: User
):
    """Test: Error when task has no due date (T126, T129)"""
    # Create task without due date
    task = Task(
        user_id=test_user.id,
        title="No due date task",
        due_date=None,
        completed=False
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)

    params = SetReminderParams(
        task_id=task.id,
        remind_before_natural="24h before",
        user_id=test_user.id
    )

    with pytest.raises(NoDueDateError) as exc_info:
        set_reminder(params, test_db)

    assert "must have a due date" in str(exc_info.value)


# ========== TEST CASE 4: Error - Too many intervals ==========

def test_set_reminder_too_many_intervals_error(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: Error when more than 5 intervals specified (T126, T129)"""
    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="7 days, 5 days, 3 days, 2 days, 1 day, 12 hours before",
        user_id=test_user.id
    )

    with pytest.raises(TooManyIntervalsError) as exc_info:
        set_reminder(params, test_db)

    assert "Maximum 5 reminder intervals" in str(exc_info.value)


# ========== TEST CASE 5: Error - Invalid interval format ==========

def test_set_reminder_invalid_interval_error(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: Error when interval format is invalid (T125, T129)"""
    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="tomorrow at 5pm",  # Not a valid interval
        user_id=test_user.id
    )

    with pytest.raises(InvalidIntervalError) as exc_info:
        set_reminder(params, test_db)

    assert "Invalid reminder interval" in str(exc_info.value)


# ========== TEST CASE 6: Return formatted reminder times ==========

def test_set_reminder_returns_formatted_times(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: Return formatted reminder times in response (T130)"""
    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="3 days before and 6 hours before",
        user_id=test_user.id
    )

    result = set_reminder(params, test_db)

    # Verify formatted times are returned
    assert len(result.reminder_times) == 2

    # Verify format includes interval and human-readable time
    # Due date: 2026-02-20 17:00:00 UTC
    # 3 days before: 2026-02-17 17:00:00 UTC
    # 6 hours before: 2026-02-20 11:00:00 UTC
    assert "3d" in result.reminder_times[0]
    assert "Feb" in result.reminder_times[0]  # Human-readable date
    assert "6h" in result.reminder_times[1]


# ========== TEST CASE 7: User isolation ==========

def test_set_reminder_user_isolation(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: Cannot set reminders for another user's task (T127)"""
    # Create another user
    other_user = User(
        id="other-user",
        email="other@example.com",
        name="Other User",
        password_hash="$2b$12$dummy.hash",
        timezone="UTC"
    )
    test_db.add(other_user)
    test_db.commit()

    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="24h before",
        user_id=other_user.id  # Different user!
    )

    with pytest.raises(ValueError) as exc_info:
        set_reminder(params, test_db)

    assert "not found" in str(exc_info.value).lower()


# ========== TEST CASE 8: Clear all reminders ==========

def test_set_reminder_clear_all(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: User can clear all reminders by passing empty string (T127)"""
    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="",  # Empty = clear all
        user_id=test_user.id
    )

    result = set_reminder(params, test_db)

    # Verify reminders were cleared
    test_db.refresh(task_with_due_date)
    assert task_with_due_date.remind_before == []
    assert result.success is True
    assert result.message == "All reminders cleared"


# ========== TEST CASE 9: Support multiple time units ==========

def test_set_reminder_multiple_time_units(
    test_db: Session,
    test_user: User,
    task_with_due_date: Task
):
    """Test: Support days, hours, minutes, weeks (T125)"""
    params = SetReminderParams(
        task_id=task_with_due_date.id,
        remind_before_natural="1 week, 3 days, 12 hours, 30 minutes before",
        user_id=test_user.id
    )

    result = set_reminder(params, test_db)

    # Verify all intervals were parsed
    assert result.intervals == ["1w", "3d", "12h", "30m"]
    assert result.success is True


# ========== TEST CASE 10: Validate intervals are before due date ==========

def test_set_reminder_interval_after_due_date_warning(
    test_db: Session,
    test_user: User
):
    """Test: Warning if interval is after task due date (T126)"""
    # Create task due tomorrow
    due_date = datetime.now(ZoneInfo("UTC")) + timedelta(hours=12)
    task = Task(
        user_id=test_user.id,
        title="Soon task",
        due_date=due_date,
        completed=False
    )
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)

    # Try to set reminder for 3 days before (but task is due in 12 hours!)
    params = SetReminderParams(
        task_id=task.id,
        remind_before_natural="3 days before",
        user_id=test_user.id
    )

    # Should still succeed but with warning
    result = set_reminder(params, test_db)

    assert result.success is True
    assert result.warning is not None
    assert "already passed" in result.warning.lower()
