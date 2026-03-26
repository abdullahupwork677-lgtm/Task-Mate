"""Integration Tests for Listing Recurring Tasks

Tests the recurring filter functionality in list_tasks tool.
Following TDD approach - tests written FIRST before implementation.
"""

import pytest
from datetime import datetime
from sqlmodel import Session
from src.models import Task, User
from src.mcp_tools.list_tasks import list_tasks, ListTasksParams
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
        id="test-user-list-recurring",
        email="list.recurring@example.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mixed_tasks(db_session: Session, test_user: User):
    """Create a mix of recurring and non-recurring tasks."""
    tasks = [
        # Recurring tasks
        Task(
            user_id=test_user.id,
            title="Daily standup",
            is_recurring=True,
            recurrence_pattern="daily",
            due_date=datetime(2026, 2, 10, 10, 0, 0)
        ),
        Task(
            user_id=test_user.id,
            title="Weekly report",
            is_recurring=True,
            recurrence_pattern="weekly",
            due_date=datetime(2026, 2, 16, 10, 0, 0)
        ),
        # Non-recurring tasks
        Task(
            user_id=test_user.id,
            title="One-time meeting",
            is_recurring=False,
            due_date=datetime(2026, 2, 11, 10, 0, 0)
        ),
        Task(
            user_id=test_user.id,
            title="Buy groceries",
            is_recurring=False,
            due_date=datetime(2026, 2, 12, 10, 0, 0)
        )
    ]

    for task in tasks:
        db_session.add(task)
    db_session.commit()

    for task in tasks:
        db_session.refresh(task)

    return tasks


class TestListRecurringTasks:
    """Integration tests for listing recurring tasks."""

    def test_filter_recurring_only(self, db_session: Session, test_user: User, mixed_tasks):
        """Test filtering to show only recurring tasks."""
        params = ListTasksParams(
            user_id=test_user.id,
            status="all",
            priority="all",
            recurring="recurring"
        )

        result = list_tasks(db_session, params)

        # Should return only 2 recurring tasks
        assert result.count == 2
        assert len(result.tasks) == 2

        # All returned tasks should be recurring
        for task in result.tasks:
            assert task["is_recurring"] is True
            assert task["recurrence_pattern"] is not None
            assert task["recurrence_pattern"] in ["daily", "weekly"]

    def test_filter_non_recurring_only(self, db_session: Session, test_user: User, mixed_tasks):
        """Test filtering to show only non-recurring tasks."""
        params = ListTasksParams(
            user_id=test_user.id,
            status="all",
            priority="all",
            recurring="non-recurring"
        )

        result = list_tasks(db_session, params)

        # Should return only 2 non-recurring tasks
        assert result.count == 2
        assert len(result.tasks) == 2

        # All returned tasks should be non-recurring
        for task in result.tasks:
            assert task["is_recurring"] is False
            assert task["recurrence_pattern"] is None

    def test_filter_all_returns_both(self, db_session: Session, test_user: User, mixed_tasks):
        """Test filtering with 'all' returns both recurring and non-recurring."""
        params = ListTasksParams(
            user_id=test_user.id,
            status="all",
            priority="all",
            recurring="all"
        )

        result = list_tasks(db_session, params)

        # Should return all 4 tasks
        assert result.count == 4
        assert len(result.tasks) == 4

        # Should have both recurring and non-recurring
        recurring_count = sum(1 for t in result.tasks if t["is_recurring"])
        non_recurring_count = sum(1 for t in result.tasks if not t["is_recurring"])
        assert recurring_count == 2
        assert non_recurring_count == 2

    def test_recurring_tasks_include_pattern_info(self, db_session: Session, test_user: User, mixed_tasks):
        """Test that recurring tasks include recurrence_pattern in response."""
        params = ListTasksParams(
            user_id=test_user.id,
            status="all",
            priority="all",
            recurring="recurring"
        )

        result = list_tasks(db_session, params)

        # Find the daily task
        daily_task = next(t for t in result.tasks if t["title"] == "Daily standup")
        assert daily_task["recurrence_pattern"] == "daily"
        assert daily_task["is_recurring"] is True

        # Find the weekly task
        weekly_task = next(t for t in result.tasks if t["title"] == "Weekly report")
        assert weekly_task["recurrence_pattern"] == "weekly"
        assert weekly_task["is_recurring"] is True

    def test_empty_recurring_tasks_list(self, db_session: Session, test_user: User):
        """Test filtering recurring tasks when none exist."""
        # Create only non-recurring tasks
        task = Task(
            user_id=test_user.id,
            title="One-time task",
            is_recurring=False
        )
        db_session.add(task)
        db_session.commit()

        params = ListTasksParams(
            user_id=test_user.id,
            status="all",
            priority="all",
            recurring="recurring"
        )

        result = list_tasks(db_session, params)

        # Should return empty list
        assert result.count == 0
        assert len(result.tasks) == 0

    def test_combine_filters_recurring_and_pending(self, db_session: Session, test_user: User):
        """Test combining recurring filter with status filter."""
        # Create mix of tasks
        tasks = [
            Task(
                user_id=test_user.id,
                title="Pending recurring",
                is_recurring=True,
                recurrence_pattern="daily",
                completed=False
            ),
            Task(
                user_id=test_user.id,
                title="Completed recurring",
                is_recurring=True,
                recurrence_pattern="weekly",
                completed=True
            ),
            Task(
                user_id=test_user.id,
                title="Pending non-recurring",
                is_recurring=False,
                completed=False
            )
        ]

        for task in tasks:
            db_session.add(task)
        db_session.commit()

        params = ListTasksParams(
            user_id=test_user.id,
            status="pending",
            priority="all",
            recurring="recurring"
        )

        result = list_tasks(db_session, params)

        # Should return only pending recurring task
        assert result.count == 1
        assert result.tasks[0]["title"] == "Pending recurring"
        assert result.tasks[0]["is_recurring"] is True
        assert result.tasks[0]["completed"] is False
