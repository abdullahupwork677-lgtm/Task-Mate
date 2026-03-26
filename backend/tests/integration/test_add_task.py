"""Integration tests for add_task MCP tool

Tests add_task with real database operations including:
- Task persistence to database
- Recurring task creation
- User isolation
- Database constraints

Phase V: Task Creation Extension (Phase 8)
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select
from src.models import Task, User
from src.mcp_tools.add_task import AddTaskParams, add_task


class TestAddTaskIntegration:
    """Integration tests for add_task tool with database."""

    def test_add_task_persists_to_database(self, db_session: Session, test_user: User):
        """Test that task is actually saved to database."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Test task persistence"
        )

        result = add_task(db_session, params)

        # Query database directly to verify
        statement = select(Task).where(Task.id == result.task_id)
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.id == result.task_id
        assert task.title == "Test task persistence"
        assert task.user_id == test_user.id
        assert task.completed is False

    def test_add_recurring_task_persists_with_pattern(self, db_session: Session, test_user: User):
        """Test that recurring task is saved with recurrence fields."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Daily recurring task",
            recurrence_pattern="daily"
        )

        result = add_task(db_session, params)

        # Query database
        statement = select(Task).where(Task.id == result.task_id)
        task = db_session.exec(statement).first()

        assert task.is_recurring is True
        assert task.recurrence_pattern == "daily"
        assert task.recurrence_end_date is None

    def test_add_recurring_task_with_end_date_persists(self, db_session: Session, test_user: User):
        """Test that recurring task with end_date is saved correctly."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Limited recurring task",
            recurrence_pattern="weekly",
            recurrence_end_date="next month"
        )

        result = add_task(db_session, params)

        # Query database
        statement = select(Task).where(Task.id == result.task_id)
        task = db_session.exec(statement).first()

        assert task.is_recurring is True
        assert task.recurrence_pattern == "weekly"
        assert task.recurrence_end_date is not None

    def test_add_task_user_isolation(self, db_session: Session):
        """Test that tasks are isolated by user_id."""
        # Create two users
        user1 = User(id="user-1", email="user1@example.com", hashed_password="hash1")
        user2 = User(id="user-2", email="user2@example.com", hashed_password="hash2")
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        # User 1 creates a task
        params1 = AddTaskParams(user_id=user1.id, title="User 1 task")
        result1 = add_task(db_session, params1)

        # User 2 creates a task
        params2 = AddTaskParams(user_id=user2.id, title="User 2 task")
        result2 = add_task(db_session, params2)

        # Query tasks for user 1
        statement = select(Task).where(Task.user_id == user1.id)
        user1_tasks = db_session.exec(statement).all()

        assert len(user1_tasks) == 1
        assert user1_tasks[0].id == result1.task_id
        assert user1_tasks[0].title == "User 1 task"

        # Query tasks for user 2
        statement = select(Task).where(Task.user_id == user2.id)
        user2_tasks = db_session.exec(statement).all()

        assert len(user2_tasks) == 1
        assert user2_tasks[0].id == result2.task_id
        assert user2_tasks[0].title == "User 2 task"

    def test_add_multiple_recurring_tasks_for_same_user(self, db_session: Session, test_user: User):
        """Test creating multiple recurring tasks for same user."""
        # Create 3 recurring tasks
        patterns = ["daily", "weekly", "monthly"]
        task_ids = []

        for pattern in patterns:
            params = AddTaskParams(
                user_id=test_user.id,
                title=f"{pattern.capitalize()} task",
                recurrence_pattern=pattern
            )
            result = add_task(db_session, params)
            task_ids.append(result.task_id)

        # Query all recurring tasks for user
        statement = select(Task).where(
            Task.user_id == test_user.id,
            Task.is_recurring == True
        )
        recurring_tasks = db_session.exec(statement).all()

        assert len(recurring_tasks) == 3
        assert set(t.id for t in recurring_tasks) == set(task_ids)
        assert set(t.recurrence_pattern for t in recurring_tasks) == set(patterns)

    def test_add_task_with_due_date_and_recurrence(self, db_session: Session, test_user: User):
        """Test creating recurring task with due_date."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Morning exercise",
            due_date="tomorrow at 7am",
            recurrence_pattern="daily",
            recurrence_end_date="in 30 days"
        )

        result = add_task(db_session, params)

        # Query database
        statement = select(Task).where(Task.id == result.task_id)
        task = db_session.exec(statement).first()

        assert task.due_date is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "daily"
        assert task.recurrence_end_date is not None
        assert task.recurrence_end_date > task.due_date

    def test_add_task_rollback_on_error(self, db_session: Session, test_user: User):
        """Test that database transaction is rolled back on error."""
        # Get initial task count
        statement = select(Task).where(Task.user_id == test_user.id)
        initial_count = len(db_session.exec(statement).all())

        # Try to create task with invalid pattern (should fail)
        params = AddTaskParams(
            user_id=test_user.id,
            title="Task that will fail",
            recurrence_pattern="invalid"
        )

        with pytest.raises(ValueError):
            add_task(db_session, params)

        # Verify no task was created
        statement = select(Task).where(Task.user_id == test_user.id)
        final_count = len(db_session.exec(statement).all())

        assert final_count == initial_count


class TestAddTaskNaturalLanguage:
    """Test natural language parsing for recurring tasks."""

    def test_add_daily_task_natural_language(self, db_session: Session, test_user: User):
        """Test 'Add a daily task' natural language command."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Morning standup",
            recurrence_pattern="daily"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "daily"

    def test_add_recurring_task_every_month(self, db_session: Session, test_user: User):
        """Test 'Add recurring task every month' natural language command."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Pay rent",
            recurrence_pattern="monthly"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "monthly"

    def test_add_recurring_task_every_3_days(self, db_session: Session, test_user: User):
        """Test 'Add task every 3 days' natural language command."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Water plants",
            recurrence_pattern="every 3 days"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "every 3 days"
