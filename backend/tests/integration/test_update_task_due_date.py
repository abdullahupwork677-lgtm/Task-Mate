"""Integration tests for update_task MCP tool with due date support.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for update_task due date extension before implementation.

Phase V - Due Dates & Reminders
User Story 1: Basic Due Date Assignment
"""

import pytest
from datetime import datetime
from freezegun import freeze_time
from zoneinfo import ZoneInfo

# Import will initially work (update_task exists) but tests will fail (new params not implemented)
from src.mcp_tools.update_task import update_task, UpdateTaskParams
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
        id="test-user-456",
        email="updateuser@example.com",
        name="Update User",
        password_hash="hashed_password",
        timezone="America/New_York",
        notification_preferences={"email": True, "push": False, "in_app": True}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_task(db_session, test_user):
    """Create a sample task for testing updates."""
    task = Task(
        user_id=test_user.id,
        title="Original task title",
        description="Original description",
        priority="medium",
        due_date=None,
        remind_before=["24h", "1h"],
        reminder_sent={},
        completed=False
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


# ========== TEST CASE 1: Update task to add due date ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_update_task_add_due_date(db_session, test_user, sample_task):
    """Test adding a due date to an existing task without one."""
    # Execute
    params = UpdateTaskParams(
        task_id=sample_task.id,
        user_id=test_user.id,
        due_date="tomorrow at 3pm",
        user_timezone="America/New_York"
    )
    result = update_task(db=db_session, params=params)

    # Verify response
    assert result.task_id == sample_task.id
    assert result.due_date is not None
    assert result.due_date_formatted is not None
    assert "3:00 PM" in result.due_date_formatted

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.due_date is not None
    # Tomorrow at 3pm EST = Feb 11, 2026 20:00 UTC
    expected = datetime(2026, 2, 11, 20, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert task.due_date == expected
    assert task.reminder_sent == {}  # Reset when due date changes


# ========== TEST CASE 2: Update existing due date ==========

@freeze_time("2026-02-10 12:00:00", tz_offset=0)
def test_update_task_change_due_date(db_session, test_user, sample_task):
    """Test changing an existing due date."""
    # Setup: Task already has a due date and sent reminders
    sample_task.due_date = datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    sample_task.reminder_sent = {"24h": "2026-02-14T17:00:00Z"}
    db_session.add(sample_task)
    db_session.commit()

    # Execute - change due date
    params = UpdateTaskParams(
        task_id=sample_task.id,
        user_id=test_user.id,
        due_date="Friday at 5pm",
        user_timezone="America/New_York"
    )
    result = update_task(db=db_session, params=params)

    # Verify response
    assert result.task_id == sample_task.id
    assert result.due_date is not None

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.due_date is not None
    # Due date should be different from original
    assert task.due_date != datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    # Reminder sent should be reset
    assert task.reminder_sent == {}


# ========== TEST CASE 3: Clear due date with clear_due_date flag ==========

def test_update_task_clear_due_date(db_session, test_user, sample_task):
    """Test clearing a due date using clear_due_date flag."""
    # Setup: Task has a due date
    sample_task.due_date = datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    sample_task.reminder_sent = {"24h": "2026-02-14T17:00:00Z", "1h": "2026-02-15T16:00:00Z"}
    db_session.add(sample_task)
    db_session.commit()

    # Execute - clear due date
    params = UpdateTaskParams(
        task_id=sample_task.id,
        user_id=test_user.id,
        clear_due_date=True
    )
    result = update_task(db=db_session, params=params)

    # Verify response
    assert result.task_id == sample_task.id
    assert result.due_date is None
    assert result.due_date_formatted is None

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.due_date is None
    # Reminder tracking should be reset
    assert task.reminder_sent == {}


# ========== TEST CASE 4: Update task with invalid due date raises error ==========

def test_update_task_with_invalid_due_date_raises_error(db_session, test_user, sample_task):
    """Test that invalid date string raises InvalidDateError."""
    # Execute and expect error
    with pytest.raises(InvalidDateError, match="Could not parse date"):
        params = UpdateTaskParams(
            task_id=sample_task.id,
            user_id=test_user.id,
            due_date="invalid date xyz",
            user_timezone="America/New_York"
        )
        update_task(db=db_session, params=params)

    # Verify task was not modified
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.due_date is None  # Still None (original state)


# ========== TEST CASE 5: Update only title, due date unchanged ==========

def test_update_task_title_only_preserves_due_date(db_session, test_user, sample_task):
    """Test updating title only doesn't affect due date."""
    # Setup: Task has a due date
    original_due_date = datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    sample_task.due_date = original_due_date
    sample_task.reminder_sent = {"24h": "2026-02-14T17:00:00Z"}
    db_session.add(sample_task)
    db_session.commit()

    # Execute - update title only
    params = UpdateTaskParams(
        task_id=sample_task.id,
        user_id=test_user.id,
        title="Updated title"
    )
    result = update_task(db=db_session, params=params)

    # Verify response
    assert result.task_id == sample_task.id
    assert result.title == "Updated title"
    assert result.due_date == original_due_date

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.title == "Updated title"
    assert task.due_date == original_due_date
    # Reminder sent should NOT be reset (due date unchanged)
    assert task.reminder_sent == {"24h": "2026-02-14T17:00:00Z"}


# ========== TEST CASE 6: Unauthorized user cannot update task ==========

def test_update_task_unauthorized(db_session, test_user, sample_task):
    """Test that user cannot update another user's task."""
    # Execute - try to update with different user_id
    with pytest.raises(PermissionError, match="Not authorized"):
        params = UpdateTaskParams(
            task_id=sample_task.id,
            user_id="different-user-789",
            title="Hacked title"
        )
        update_task(db=db_session, params=params)

    # Verify task was not modified
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.title == "Original task title"  # Unchanged


# ========== EDGE CASE: Empty due_date string treated as no change ==========

def test_update_task_with_empty_due_date_string(db_session, test_user, sample_task):
    """Test that empty due_date string is treated as no change (backward compatibility)."""
    # Setup: Task has a due date
    original_due_date = datetime(2026, 2, 15, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
    sample_task.due_date = original_due_date
    db_session.add(sample_task)
    db_session.commit()

    # Execute with empty string
    params = UpdateTaskParams(
        task_id=sample_task.id,
        user_id=test_user.id,
        due_date="",
        title="Updated title"
    )
    result = update_task(db=db_session, params=params)

    # Verify due date unchanged
    assert result.task_id == sample_task.id
    assert result.due_date == original_due_date

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == sample_task.id)
    ).first()

    assert task is not None
    assert task.due_date == original_due_date  # Unchanged
