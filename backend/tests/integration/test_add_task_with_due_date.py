"""Integration tests for add_task MCP tool with due date support.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for add_task due date extension before implementation.

Phase V - Due Dates & Reminders
User Story 1: Basic Due Date Assignment
"""

import pytest
from datetime import datetime
from freezegun import freeze_time
from zoneinfo import ZoneInfo

# Import will initially work (add_task exists) but tests will fail (new params not implemented)
from src.mcp_tools.add_task import add_task, AddTaskParams
from src.services.date_parser_service import InvalidDateError
from src.db import engine
from src.models import Task, User
from sqlmodel import Session, select


# ========== TEST FIXTURES ==========

@pytest.fixture
def db_session():
    """Real database session for integration tests."""
    with Session(engine) as session:
        yield session
        session.rollback()  # Rollback after each test


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        id="test-user-123",
        email="testuser@example.com",
        name="Test User",
        password_hash="hashed_password",
        timezone="America/New_York",
        notification_preferences={"email": True, "push": False, "in_app": True}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ========== TEST CASE 1: Create task with due_date_natural ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_add_task_with_due_date_natural(db_session, test_user):
    """Test creating a task with natural language due date."""
    # Execute (this will FAIL until add_task is extended)
    params = AddTaskParams(
        user_id=test_user.id,
        title="Submit quarterly report",
        description="Q4 2025 financial report",
        due_date="tomorrow at 5pm",
        user_timezone="America/New_York"
    )
    result = add_task(db=db_session, params=params)

    # Verify
    assert result.task_id > 0
    assert result.title == "Submit quarterly report"
    assert result.due_date is not None
    assert result.due_date_formatted is not None

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == result.task_id)
    ).first()

    assert task is not None
    assert task.due_date is not None
    # Due date should be tomorrow at 5pm EST = Feb 11, 2026 22:00 UTC
    expected = datetime(2026, 2, 11, 22, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert task.due_date == expected

    # Verify default reminder intervals set
    assert task.remind_before == ["24h", "1h"]
    assert task.reminder_sent == {}


# ========== TEST CASE 2: Backward compatibility (no due date) ==========

def test_add_task_without_due_date_backward_compatibility(db_session, test_user):
    """Test that add_task still works without due_date_natural (backward compatibility)."""
    # Execute (should work even without new params)
    params = AddTaskParams(
        user_id=test_user.id,
        title="Buy groceries",
        description="Milk, eggs, bread"
    )
    result = add_task(db=db_session, params=params)

    # Verify
    assert result.task_id > 0
    assert result.title == "Buy groceries"
    assert result.due_date is None
    assert result.due_date_formatted is None

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == result.task_id)
    ).first()

    assert task is not None
    assert task.due_date is None
    assert task.remind_before == ["24h", "1h"]  # Default even without due date


# ========== TEST CASE 3: Invalid date string raises error ==========

def test_add_task_with_invalid_due_date_raises_error(db_session, test_user):
    """Test that invalid date string raises InvalidDateError."""
    # Execute and expect error
    with pytest.raises(InvalidDateError, match="Could not parse date"):
        params = AddTaskParams(
            user_id=test_user.id,
            title="Invalid date task",
            due_date="invalid date xyz",
            user_timezone="America/New_York"
        )
        add_task(db=db_session, params=params)

    # Verify no task was created
    tasks = db_session.exec(
        select(Task).where(Task.user_id == test_user.id)
    ).all()

    assert len(tasks) == 0


# ========== TEST CASE 4: Create task with custom remind_before_natural ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_add_task_with_custom_reminder_intervals(db_session, test_user):
    """Test creating a task with custom reminder intervals."""
    # Execute (use "Friday" instead of "next Friday" for freezegun compatibility)
    params = AddTaskParams(
        user_id=test_user.id,
        title="Important meeting",
        description="Board meeting",
        due_date="Friday at 2pm",
        remind_before_natural="3 days before, 1 day before, 1 hour before",
        user_timezone="America/New_York"
    )
    result = add_task(db=db_session, params=params)

    # Verify
    assert result.task_id > 0
    assert result.title == "Important meeting"
    assert result.due_date is not None

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == result.task_id)
    ).first()

    assert task is not None
    assert task.due_date is not None
    # Verify custom reminder intervals
    assert task.remind_before == ["3d", "1d", "1h"]
    assert task.reminder_sent == {}


# ========== TEST CASE 5: Timezone conversion works correctly ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_add_task_timezone_conversion(db_session, test_user):
    """Test that due dates are stored in UTC regardless of user timezone."""
    # Execute with Tokyo timezone (UTC+9)
    params = AddTaskParams(
        user_id=test_user.id,
        title="Tokyo meeting",
        due_date="tomorrow at 9am",
        user_timezone="Asia/Tokyo"
    )
    result = add_task(db=db_session, params=params)

    # Verify
    assert result.task_id > 0

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == result.task_id)
    ).first()

    assert task is not None
    assert task.due_date is not None

    # Tomorrow at 9am Tokyo time = Feb 11 9:00 JST = Feb 11 00:00 UTC
    expected = datetime(2026, 2, 11, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert task.due_date == expected

    # Verify formatted date is in user's timezone (Tokyo)
    assert result.due_date_formatted is not None
    assert "9:00 AM" in result.due_date_formatted


# ========== EDGE CASE: Empty due_date_natural string ==========

def test_add_task_with_empty_due_date_string(db_session, test_user):
    """Test that empty due_date_natural is treated as None (backward compatibility)."""
    # Execute with empty string
    params = AddTaskParams(
        user_id=test_user.id,
        title="Task with empty date",
        due_date=""
    )
    result = add_task(db=db_session, params=params)

    # Verify task created without due date
    assert result.task_id > 0
    assert result.due_date is None

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == result.task_id)
    ).first()

    assert task is not None
    assert task.due_date is None
