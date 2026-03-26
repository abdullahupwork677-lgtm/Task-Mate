"""Unit tests for add_task MCP tool

Tests the add_task tool functionality including:
- Basic task creation
- Recurring task creation with recurrence_pattern parameter
- Input validation
- Edge cases

Phase V: Task Creation Extension (Phase 8)
"""

import pytest
from datetime import datetime, timedelta
from src.mcp_tools.add_task import AddTaskParams, add_task, AddTaskResult


class TestAddTaskBasic:
    """Test basic task creation without recurrence."""

    def test_add_task_with_title_only(self, db_session, test_user):
        """Test creating task with just a title."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Simple task"
        )

        result = add_task(db_session, params)

        assert result.task_id > 0
        assert result.title == "Simple task"
        assert result.completed is False
        assert result.priority == "medium"  # default
        assert result.due_date is None
        assert result.is_recurring is False
        assert result.recurrence_pattern is None

    def test_add_task_with_all_fields(self, db_session, test_user):
        """Test creating task with title, description, priority, due_date."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Complete task",
            description="With all fields",
            priority="high",
            due_date="tomorrow at 5pm"
        )

        result = add_task(db_session, params)

        assert result.task_id > 0
        assert result.title == "Complete task"
        assert result.description == "With all fields"
        assert result.priority == "high"
        assert result.due_date is not None
        assert result.is_recurring is False


class TestAddTaskRecurring:
    """Test recurring task creation (Phase 8 extension)."""

    def test_add_task_with_simple_recurrence_daily(self, db_session, test_user):
        """Test creating recurring task with 'daily' pattern."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Daily standup",
            recurrence_pattern="daily"
        )

        result = add_task(db_session, params)

        assert result.task_id > 0
        assert result.title == "Daily standup"
        assert result.is_recurring is True
        assert result.recurrence_pattern == "daily"
        assert result.recurrence_end_date is None

    def test_add_task_with_simple_recurrence_weekly(self, db_session, test_user):
        """Test creating recurring task with 'weekly' pattern."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Weekly review",
            recurrence_pattern="weekly"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "weekly"

    def test_add_task_with_simple_recurrence_monthly(self, db_session, test_user):
        """Test creating recurring task with 'monthly' pattern."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Monthly report",
            recurrence_pattern="monthly"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "monthly"

    def test_add_task_with_custom_recurrence(self, db_session, test_user):
        """Test creating recurring task with custom pattern 'every N days'."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Check server logs",
            recurrence_pattern="every 3 days"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "every 3 days"

    def test_add_task_with_recurrence_and_end_date(self, db_session, test_user):
        """Test creating recurring task with end date."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Q1 workout routine",
            recurrence_pattern="daily",
            recurrence_end_date="March 31, 2026"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "daily"
        assert result.recurrence_end_date is not None
        # Should be end of March 2026
        assert result.recurrence_end_date.year == 2026
        assert result.recurrence_end_date.month == 3

    def test_add_task_with_recurrence_due_date_and_end_date(self, db_session, test_user):
        """Test creating recurring task with due_date AND recurrence_end_date."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Daily exercise",
            description="Morning workout",
            priority="high",
            due_date="tomorrow at 7am",
            recurrence_pattern="daily",
            recurrence_end_date="next month"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is True
        assert result.recurrence_pattern == "daily"
        assert result.due_date is not None
        assert result.recurrence_end_date is not None
        assert result.recurrence_end_date > result.due_date


class TestAddTaskRecurringValidation:
    """Test validation for recurring task parameters."""

    def test_add_task_invalid_recurrence_pattern(self, db_session, test_user):
        """Test that invalid recurrence pattern raises ValueError."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Bad recurring task",
            recurrence_pattern="invalid pattern"
        )

        with pytest.raises(ValueError, match="Invalid recurrence pattern"):
            add_task(db_session, params)

    def test_add_task_recurrence_end_date_without_pattern(self, db_session, test_user):
        """Test that recurrence_end_date without pattern raises ValueError."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Task with end date but no pattern",
            recurrence_end_date="next month"
        )

        with pytest.raises(ValueError, match="recurrence_end_date requires recurrence_pattern"):
            add_task(db_session, params)

    def test_add_task_recurrence_end_date_in_past(self, db_session, test_user):
        """Test that recurrence_end_date in past raises ValueError."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Task with past end date",
            recurrence_pattern="daily",
            recurrence_end_date="yesterday"
        )

        with pytest.raises(ValueError, match="End date must be in the future"):
            add_task(db_session, params)

    def test_add_task_none_recurrence_pattern(self, db_session, test_user):
        """Test that 'none' as recurrence_pattern is treated as no recurrence."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="Non-recurring task",
            recurrence_pattern="none"
        )

        result = add_task(db_session, params)

        assert result.is_recurring is False
        assert result.recurrence_pattern is None


class TestAddTaskEdgeCases:
    """Test edge cases for add_task tool."""

    def test_add_task_empty_title_raises_error(self, db_session, test_user):
        """Test that empty title raises ValueError."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="   "  # whitespace only
        )

        with pytest.raises(ValueError, match="Title cannot be empty"):
            add_task(db_session, params)

    def test_add_task_title_too_long_raises_error(self, db_session, test_user):
        """Test that title > 200 chars raises ValueError."""
        params = AddTaskParams(
            user_id=test_user.id,
            title="x" * 201
        )

        with pytest.raises(ValueError, match="Title must be 200 characters or less"):
            add_task(db_session, params)

    def test_add_task_invalid_priority_raises_error(self, db_session, test_user):
        """Test that invalid priority raises ValueError."""
        with pytest.raises(ValueError, match="Invalid priority"):
            params = AddTaskParams(
                user_id=test_user.id,
                title="Task",
                priority="urgent"  # not in [high, medium, low]
            )
