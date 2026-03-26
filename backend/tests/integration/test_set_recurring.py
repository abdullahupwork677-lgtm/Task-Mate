"""Integration Tests for set_recurring MCP Tool

Tests the set_recurring tool with database interactions.
Following TDD approach - tests written FIRST before implementation.
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select
from src.models import Task, User
from src.mcp_tools.set_recurring import set_recurring
from src.db import engine


@pytest.fixture
def db_session():
    """Create a test database session."""
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        id="test-user-recurring-1", email="recurring.test@example.com", name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_task(db_session: Session, test_user: User):
    """Create a test task."""
    task = Task(
        user_id=test_user.id,
        title="Weekly standup",
        description="Team meeting every week",
        due_date=datetime(2026, 2, 10, 10, 0, 0),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.mark.asyncio
class TestSetRecurringIntegration:
    """Integration tests for set_recurring tool."""

    async def test_set_existing_task_as_recurring(
        self, db_session: Session, test_user: User, test_task: Task
    ):
        """Test setting an existing task as recurring."""
        result = await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="weekly",
            end_date=None,
        )

        # Verify result
        assert result["task_id"] == test_task.id
        assert result["title"] == "Weekly standup"
        assert result["is_recurring"] is True
        assert result["recurrence_pattern"] == "weekly"
        assert result["recurrence_end_date"] is None

        # Verify database update
        db_session.refresh(test_task)
        assert test_task.is_recurring is True
        assert test_task.recurrence_pattern == "weekly"
        assert test_task.recurrence_end_date is None

    async def test_set_recurring_with_end_date(
        self, db_session: Session, test_user: User, test_task: Task
    ):
        """Test setting recurring with an end date."""
        result = await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="daily",
            end_date="2026-12-31",
        )

        # Verify result
        assert result["is_recurring"] is True
        assert result["recurrence_pattern"] == "daily"
        assert result["recurrence_end_date"] is not None
        assert result["recurrence_end_date"].year == 2026
        assert result["recurrence_end_date"].month == 12
        assert result["recurrence_end_date"].day == 31

    async def test_user_isolation_cannot_set_another_users_task(
        self, db_session: Session, test_task: Task
    ):
        """Test user isolation - user cannot set another user's task as recurring."""
        # Create a different user
        other_user = User(
            id="test-user-recurring-2",
            email="other.user@example.com",
            name="Other User",
        )
        db_session.add(other_user)
        db_session.commit()

        # Try to set another user's task as recurring
        with pytest.raises(ValueError, match="Task not found or access denied"):
            await set_recurring(
                user_id=int(other_user.id.replace("test-user-recurring-", "")),
                task_id=test_task.id,
                pattern="weekly",
                end_date=None,
            )

    async def test_invalid_task_id_raises_error(self, test_user: User):
        """Test that invalid task_id raises ValueError."""
        with pytest.raises(ValueError, match="Task not found"):
            await set_recurring(
                user_id=int(test_user.id.replace("test-user-recurring-", "")),
                task_id=999999,
                pattern="weekly",
                end_date=None,
            )

    async def test_cancel_recurrence_with_pattern_none(
        self, db_session: Session, test_user: User, test_task: Task
    ):
        """Test canceling recurrence by setting pattern to 'none'."""
        # First make it recurring
        await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="weekly",
            end_date=None,
        )

        # Then cancel
        result = await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="none",
            end_date=None,
        )

        # Verify cancellation
        assert result["is_recurring"] is False
        assert result["recurrence_pattern"] is None
        assert result["recurrence_end_date"] is None

        # Verify database update
        db_session.refresh(test_task)
        assert test_task.is_recurring is False
        assert test_task.recurrence_pattern is None
        assert test_task.recurrence_end_date is None

    async def test_change_recurrence_pattern(
        self, db_session: Session, test_user: User, test_task: Task
    ):
        """Test changing recurrence pattern from weekly to daily."""
        # Set as weekly
        await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="weekly",
            end_date=None,
        )

        # Change to daily
        result = await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="daily",
            end_date=None,
        )

        # Verify change
        assert result["recurrence_pattern"] == "daily"
        db_session.refresh(test_task)
        assert test_task.recurrence_pattern == "daily"

    async def test_natural_language_end_date_parsing(
        self, db_session: Session, test_user: User, test_task: Task
    ):
        """Test natural language end date parsing like 'next year'."""
        result = await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=test_task.id,
            pattern="monthly",
            end_date="next year",
        )

        # Verify end_date was parsed (should be sometime in 2027)
        assert result["recurrence_end_date"] is not None
        assert result["recurrence_end_date"].year >= 2027

    # User Story 3 tests: Cancellation
    async def test_cancel_recurrence_prevents_next_occurrence(
        self, db_session: Session, test_user: User
    ):
        """Test that cancelling recurrence prevents next occurrence on completion."""
        # Create a recurring task
        task = Task(
            user_id=test_user.id,
            title="Cancellation test",
            is_recurring=True,
            recurrence_pattern="daily",
            due_date=datetime(2026, 2, 9, 10, 0, 0),
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Cancel recurrence
        await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=task.id,
            pattern="none",
            end_date=None,
        )

        # Verify task is no longer recurring
        db_session.refresh(task)
        assert task.is_recurring is False
        assert task.recurrence_pattern is None

        # Complete the task
        from backend.src.mcp_tools.complete_task import (
            complete_task,
            CompleteTaskParams,
        )

        complete_params = CompleteTaskParams(user_id=test_user.id, task_id=task.id)
        result = complete_task(db_session, complete_params)

        # Verify NO next occurrence was created
        assert result.next_occurrence is None

        # Verify no child tasks exist
        statement = select(Task).where(Task.parent_task_id == task.id)
        child_tasks = db_session.exec(statement).all()
        assert len(child_tasks) == 0

    async def test_cancel_non_recurring_task_error(
        self, db_session: Session, test_user: User
    ):
        """Test cancelling a non-recurring task returns informative message."""
        # Create a non-recurring task
        task = Task(
            user_id=test_user.id,
            title="Non-recurring task",
            is_recurring=False,
            due_date=datetime(2026, 2, 9, 10, 0, 0),
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Try to cancel (should succeed but have no effect)
        result = await set_recurring(
            user_id=int(test_user.id.replace("test-user-recurring-", "")),
            task_id=task.id,
            pattern="none",
            end_date=None,
        )

        # Should return is_recurring=False
        assert result["is_recurring"] is False

        # Task should remain non-recurring
        db_session.refresh(task)
        assert task.is_recurring is False
