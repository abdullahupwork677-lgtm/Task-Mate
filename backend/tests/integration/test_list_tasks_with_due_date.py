"""Integration tests for list_tasks MCP tool with due date display.

Test-Driven Development (TDD) approach:
1. Write tests FIRST (RED - tests fail)
2. Implement minimal code to pass (GREEN - tests pass)
3. Refactor code (REFACTOR - maintain tests passing)

These tests define the contract for list_tasks due date extension before implementation.

Phase V - Due Dates & Reminders
User Story 1: Basic Due Date Assignment
"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from zoneinfo import ZoneInfo

# Import will initially work (list_tasks exists) but tests will fail (new fields not implemented)
from src.mcp_tools.list_tasks import list_tasks, ListTasksParams
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
        id="test-user-789",
        email="listuser@example.com",
        name="List User",
        password_hash="hashed_password",
        timezone="America/New_York",
        notification_preferences={"email": True, "push": False, "in_app": True}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tasks_with_due_dates(db_session, test_user):
    """Create sample tasks with various due date scenarios."""
    now = datetime.now(ZoneInfo("UTC"))

    tasks = [
        # Task 1: No due date
        Task(
            user_id=test_user.id,
            title="Task without due date",
            priority="medium",
            due_date=None,
            completed=False
        ),
        # Task 2: Due in future (tomorrow)
        Task(
            user_id=test_user.id,
            title="Task due tomorrow",
            priority="high",
            due_date=now + timedelta(days=1),
            remind_before=["24h", "1h"],
            reminder_sent={},
            completed=False
        ),
        # Task 3: Overdue (2 days ago)
        Task(
            user_id=test_user.id,
            title="Overdue task",
            priority="high",
            due_date=now - timedelta(days=2),
            remind_before=["24h"],
            reminder_sent={"24h": (now - timedelta(days=3)).isoformat()},
            completed=False
        ),
        # Task 4: Overdue (3 hours ago)
        Task(
            user_id=test_user.id,
            title="Task overdue by hours",
            priority="medium",
            due_date=now - timedelta(hours=3),
            completed=False
        ),
        # Task 5: Completed task with past due date (not overdue)
        Task(
            user_id=test_user.id,
            title="Completed task",
            priority="low",
            due_date=now - timedelta(days=1),
            completed=True
        ),
    ]

    for task in tasks:
        db_session.add(task)
    db_session.commit()

    for task in tasks:
        db_session.refresh(task)

    return tasks


# ========== TEST CASE 1: List tasks shows due_date_formatted ==========

def test_list_tasks_includes_due_date_formatted(db_session, test_user, tasks_with_due_dates):
    """Test that list_tasks includes formatted due dates in user's timezone."""
    # Execute
    params = ListTasksParams(
        user_id=test_user.id,
        user_timezone="America/New_York"
    )
    result = list_tasks(db=db_session, params=params)

    # Verify
    assert len(result.tasks) == 5

    # Find task with due date
    task_with_due_date = next(
        (t for t in result.tasks if t.title == "Task due tomorrow"),
        None
    )

    assert task_with_due_date is not None
    assert task_with_due_date.due_date is not None
    assert task_with_due_date.due_date_formatted is not None
    # Should be formatted in user's timezone (America/New_York)
    assert "Tomorrow" in task_with_due_date.due_date_formatted or "AM" in task_with_due_date.due_date_formatted or "PM" in task_with_due_date.due_date_formatted


# ========== TEST CASE 2: List tasks calculates is_overdue correctly ==========

def test_list_tasks_calculates_is_overdue(db_session, test_user, tasks_with_due_dates):
    """Test that is_overdue is True for tasks past due date and not completed."""
    # Execute
    params = ListTasksParams(
        user_id=test_user.id
    )
    result = list_tasks(db=db_session, params=params)

    # Verify overdue task
    overdue_task = next(
        (t for t in result.tasks if t.title == "Overdue task"),
        None
    )
    assert overdue_task is not None
    assert overdue_task.is_overdue is True
    assert overdue_task.overdue_by is not None

    # Verify future task (not overdue)
    future_task = next(
        (t for t in result.tasks if t.title == "Task due tomorrow"),
        None
    )
    assert future_task is not None
    assert future_task.is_overdue is False
    assert future_task.overdue_by is None

    # Verify completed task (not overdue even if past due date)
    completed_task = next(
        (t for t in result.tasks if t.title == "Completed task"),
        None
    )
    assert completed_task is not None
    assert completed_task.is_overdue is False
    assert completed_task.overdue_by is None

    # Verify task without due date (not overdue)
    no_due_date_task = next(
        (t for t in result.tasks if t.title == "Task without due date"),
        None
    )
    assert no_due_date_task is not None
    assert no_due_date_task.is_overdue is False
    assert no_due_date_task.overdue_by is None


# ========== TEST CASE 3: List tasks calculates overdue_by human-readable ==========

def test_list_tasks_calculates_overdue_by(db_session, test_user, tasks_with_due_dates):
    """Test that overdue_by shows human-readable duration."""
    # Execute
    params = ListTasksParams(
        user_id=test_user.id
    )
    result = list_tasks(db=db_session, params=params)

    # Verify overdue task (2 days)
    overdue_task = next(
        (t for t in result.tasks if t.title == "Overdue task"),
        None
    )
    assert overdue_task is not None
    assert overdue_task.is_overdue is True
    assert overdue_task.overdue_by is not None
    assert "2 days" in overdue_task.overdue_by or "2d" in overdue_task.overdue_by.lower()

    # Verify overdue task (3 hours)
    overdue_hours_task = next(
        (t for t in result.tasks if t.title == "Task overdue by hours"),
        None
    )
    assert overdue_hours_task is not None
    assert overdue_hours_task.is_overdue is True
    assert overdue_hours_task.overdue_by is not None
    assert "3 hours" in overdue_hours_task.overdue_by or "3h" in overdue_hours_task.overdue_by.lower()


# ========== TEST CASE 4: List tasks with no due dates (backward compatibility) ==========

def test_list_tasks_backward_compatibility_no_due_dates(db_session, test_user):
    """Test that list_tasks works when tasks have no due dates."""
    # Create task without due date
    task = Task(
        user_id=test_user.id,
        title="Simple task",
        priority="medium",
        completed=False
    )
    db_session.add(task)
    db_session.commit()

    # Execute
    params = ListTasksParams(
        user_id=test_user.id
    )
    result = list_tasks(db=db_session, params=params)

    # Verify
    assert len(result.tasks) == 1
    assert result.tasks[0].title == "Simple task"
    assert result.tasks[0].due_date is None
    assert result.tasks[0].due_date_formatted is None
    assert result.tasks[0].is_overdue is False
    assert result.tasks[0].overdue_by is None
