"""Integration Tests for Completing Recurring Tasks

Tests the auto-creation of next occurrence when completing recurring tasks.
Following TDD approach - tests written FIRST before implementation.
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select
from src.models import Task, User
from src.mcp_tools.complete_task import complete_task
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
        id="test-user-complete-recurring",
        email="complete.recurring@example.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
class TestCompleteRecurringTask:
    """Integration tests for completing recurring tasks and auto-creating next occurrence."""

    async def test_complete_daily_recurring_creates_next_occurrence(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test completing a daily recurring task creates next occurrence."""
        # Create a daily recurring task
        task = Task(
            user_id=test_user.id,
            title="Daily standup",
            description="Team meeting",
            is_recurring=True,
            recurrence_pattern="daily",
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Complete the task
        result = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Verify original task is completed
        db_session.refresh(task)
        assert task.completed is True

        # Verify next occurrence was created
        assert "next_occurrence" in result
        next_occurrence_id = result["next_occurrence"]["task_id"]

        # Fetch next occurrence from database
        statement = select(Task).where(Task.id == next_occurrence_id)
        next_task = db_session.exec(statement).first()

        assert next_task is not None
        assert next_task.user_id == test_user.id
        assert next_task.title == "Daily standup"
        assert next_task.description == "Team meeting"
        assert next_task.is_recurring is True
        assert next_task.recurrence_pattern == "daily"
        assert next_task.due_date == datetime(2026, 2, 10, 10, 0, 0)  # +1 day
        assert next_task.parent_task_id == task.id
        assert next_task.completed is False

    async def test_complete_weekly_recurring_creates_next_occurrence(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test completing a weekly recurring task creates next occurrence."""
        task = Task(
            user_id=test_user.id,
            title="Weekly report",
            is_recurring=True,
            recurrence_pattern="weekly",
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        result = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Verify next occurrence due date is +7 days
        next_task_id = result["next_occurrence"]["task_id"]
        statement = select(Task).where(Task.id == next_task_id)
        next_task = db_session.exec(statement).first()

        assert next_task.due_date == datetime(2026, 2, 16, 10, 0, 0)  # +7 days
        assert next_task.recurrence_pattern == "weekly"

    async def test_idempotency_completing_twice_no_duplicates(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test completing the same recurring task twice rapidly doesn't create duplicates."""
        task = Task(
            user_id=test_user.id,
            title="Idempotency test",
            is_recurring=True,
            recurrence_pattern="daily",
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Complete task first time
        result1 = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Try to complete again (should be idempotent due to unique constraint)
        # This should either return the same next_occurrence or handle gracefully
        try:
            result2 = await complete_task(
                user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
                task_id=task.id
            )
            # If it succeeds, it should return same next occurrence
            if "next_occurrence" in result2:
                assert result1["next_occurrence"]["task_id"] == result2["next_occurrence"]["task_id"]
        except Exception as e:
            # Or it should raise a meaningful error (already completed)
            assert "already completed" in str(e).lower() or "duplicate" in str(e).lower()

        # Verify only ONE next occurrence was created
        statement = select(Task).where(
            Task.parent_task_id == task.id,
            Task.due_date == datetime(2026, 2, 10, 10, 0, 0)
        )
        next_occurrences = db_session.exec(statement).all()
        assert len(next_occurrences) == 1

    async def test_next_occurrence_inherits_all_fields(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test next occurrence inherits title, description, priority, recurrence fields."""
        task = Task(
            user_id=test_user.id,
            title="Important meeting",
            description="Quarterly review with stakeholders",
            priority="high",
            is_recurring=True,
            recurrence_pattern="monthly",
            recurrence_end_date=datetime(2026, 12, 31, 23, 59, 59),
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        result = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Fetch next occurrence
        next_task_id = result["next_occurrence"]["task_id"]
        statement = select(Task).where(Task.id == next_task_id)
        next_task = db_session.exec(statement).first()

        # Verify ALL fields are inherited
        assert next_task.title == "Important meeting"
        assert next_task.description == "Quarterly review with stakeholders"
        assert next_task.priority == "high"
        assert next_task.is_recurring is True
        assert next_task.recurrence_pattern == "monthly"
        assert next_task.recurrence_end_date == datetime(2026, 12, 31, 23, 59, 59)
        assert next_task.user_id == test_user.id

    async def test_parent_task_id_linkage(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test parent_task_id links child to parent correctly."""
        task = Task(
            user_id=test_user.id,
            title="Parent task",
            is_recurring=True,
            recurrence_pattern="weekly",
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        result = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Fetch next occurrence
        next_task_id = result["next_occurrence"]["task_id"]
        statement = select(Task).where(Task.id == next_task_id)
        next_task = db_session.exec(statement).first()

        # Verify parent_task_id linkage
        assert next_task.parent_task_id == task.id

        # Verify relationship works both ways
        db_session.refresh(task)
        assert len(task.child_occurrences) == 1
        assert task.child_occurrences[0].id == next_task_id
        assert next_task.parent_task.id == task.id

    async def test_recurrence_end_date_prevents_next_occurrence(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test that recurrence stops when end_date is reached."""
        task = Task(
            user_id=test_user.id,
            title="Limited recurrence",
            is_recurring=True,
            recurrence_pattern="weekly",
            recurrence_end_date=datetime(2026, 2, 15, 23, 59, 59),
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        result = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Next occurrence would be Feb 16, but end_date is Feb 15
        # So no next occurrence should be created
        assert "next_occurrence" not in result or result["next_occurrence"] is None

        # Verify no child tasks were created
        statement = select(Task).where(Task.parent_task_id == task.id)
        child_tasks = db_session.exec(statement).all()
        assert len(child_tasks) == 0

    async def test_complete_non_recurring_task_no_next_occurrence(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test completing a non-recurring task does NOT create next occurrence."""
        task = Task(
            user_id=test_user.id,
            title="One-time task",
            is_recurring=False,
            due_date=datetime(2026, 2, 9, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        result = await complete_task(
            user_id=int(test_user.id.replace("test-user-complete-recurring", "")),
            task_id=task.id
        )

        # Verify no next occurrence was created
        assert "next_occurrence" not in result or result["next_occurrence"] is None

        # Verify no child tasks exist
        statement = select(Task).where(Task.parent_task_id == task.id)
        child_tasks = db_session.exec(statement).all()
        assert len(child_tasks) == 0
