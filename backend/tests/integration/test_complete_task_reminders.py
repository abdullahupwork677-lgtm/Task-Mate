"""Integration tests for complete_task MCP tool with reminder tracking.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for complete_task reminder extension before implementation.

Phase V - Due Dates & Reminders
User Story 1: Basic Due Date Assignment
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Import will initially work (complete_task exists) but tests will fail (reminder_sent clear not implemented)
from src.mcp_tools.complete_task import complete_task, CompleteTaskParams
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
        id="test-user-complete",
        email="completeuser@example.com",
        name="Complete User",
        password_hash="hashed_password",
        timezone="America/New_York",
        notification_preferences={"email": True, "push": False, "in_app": True}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def task_with_reminders(db_session, test_user):
    """Create a task with reminders sent."""
    now = datetime.now(ZoneInfo("UTC"))

    task = Task(
        user_id=test_user.id,
        title="Task with reminders",
        priority="high",
        due_date=now + timedelta(hours=2),
        remind_before=["24h", "1h"],
        reminder_sent={
            "24h": (now - timedelta(days=1)).isoformat(),
            "1h": (now - timedelta(hours=1)).isoformat()
        },
        completed=False
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


# ========== TEST CASE 1: Complete task clears reminder_sent ==========

def test_complete_task_clears_reminder_sent(db_session, test_user, task_with_reminders):
    """Test that completing a task clears the reminder_sent tracking object."""
    # Verify reminder_sent is populated before completion
    assert task_with_reminders.reminder_sent == {
        "24h": pytest.approx(
            (datetime.now(ZoneInfo("UTC")) - timedelta(days=1)).isoformat(),
            abs=timedelta(seconds=5)
        ),
        "1h": pytest.approx(
            (datetime.now(ZoneInfo("UTC")) - timedelta(hours=1)).isoformat(),
            abs=timedelta(seconds=5)
        )
    }

    # Execute - complete the task
    params = CompleteTaskParams(
        user_id=test_user.id,
        task_id=task_with_reminders.id
    )
    result = complete_task(db=db_session, params=params)

    # Verify result
    assert result.task_id == task_with_reminders.id
    assert result.completed is True

    # Verify task in database
    task = db_session.exec(
        select(Task).where(Task.id == task_with_reminders.id)
    ).first()

    assert task is not None
    assert task.completed is True
    # Phase V - US1: reminder_sent should be cleared (T052)
    assert task.reminder_sent == {}


# ========== TEST CASE 2: Complete task without reminders (backward compatibility) ==========

def test_complete_task_without_reminders_backward_compatibility(db_session, test_user):
    """Test that completing a task without reminders still works."""
    # Create task without reminders
    task = Task(
        user_id=test_user.id,
        title="Simple task",
        priority="medium",
        completed=False
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Execute - complete the task
    params = CompleteTaskParams(
        user_id=test_user.id,
        task_id=task.id
    )
    result = complete_task(db=db_session, params=params)

    # Verify result
    assert result.task_id == task.id
    assert result.completed is True

    # Verify task in database
    task_updated = db_session.exec(
        select(Task).where(Task.id == task.id)
    ).first()

    assert task_updated is not None
    assert task_updated.completed is True
    # reminder_sent should be empty dict (default)
    assert task_updated.reminder_sent == {}


# ========== TEST CASE 3: Complete task with due date but no reminders sent ==========

def test_complete_task_with_due_date_no_reminders_sent(db_session, test_user):
    """Test completing a task with due date but no reminders sent yet."""
    now = datetime.now(ZoneInfo("UTC"))

    # Create task with due date but no reminders sent
    task = Task(
        user_id=test_user.id,
        title="Task with due date, no reminders",
        priority="medium",
        due_date=now + timedelta(days=1),
        remind_before=["24h", "1h"],
        reminder_sent={},
        completed=False
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Execute - complete the task
    params = CompleteTaskParams(
        user_id=test_user.id,
        task_id=task.id
    )
    result = complete_task(db=db_session, params=params)

    # Verify result
    assert result.task_id == task.id
    assert result.completed is True

    # Verify task in database
    task_updated = db_session.exec(
        select(Task).where(Task.id == task.id)
    ).first()

    assert task_updated is not None
    assert task_updated.completed is True
    # reminder_sent should still be empty dict
    assert task_updated.reminder_sent == {}
