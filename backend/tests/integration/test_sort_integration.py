"""
Integration Tests: Task Sorting with MCP Tool (Feature 005-task-sort)

Tests list_tasks MCP tool with sort parameters, verifying user isolation,
parameter validation, and correct integration with TaskService sorting logic.

Phase: 005-task-sort (Phase V)
Task: T034 (Integration testing)
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session
from src.models import Task, User
from src.mcp_tools.list_tasks import list_tasks, ListTasksParams


@pytest.fixture
def user(db: Session) -> User:
    """Create test user."""
    user = User(
        id="test-user-integration",
        email="integration@example.com",
        hashed_password="hashed"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db: Session) -> User:
    """Create another user for isolation testing."""
    user = User(
        id="other-user-integration",
        email="other@example.com",
        hashed_password="hashed"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_tasks(db: Session, user: User, other_user: User) -> dict:
    """Create sample tasks for multiple users."""
    now = datetime.utcnow()

    # Tasks for test user
    user_tasks = [
        Task(
            user_id=user.id,
            title="Task A",
            due_date=now + timedelta(days=1),
            priority="high",
            created_at=now - timedelta(hours=3)
        ),
        Task(
            user_id=user.id,
            title="Task B",
            due_date=now + timedelta(days=2),
            priority="medium",
            created_at=now - timedelta(hours=2)
        ),
        Task(
            user_id=user.id,
            title="Task C",
            due_date=now + timedelta(days=3),
            priority="low",
            created_at=now - timedelta(hours=1)
        ),
    ]

    # Tasks for other user (should NOT appear in results)
    other_tasks = [
        Task(
            user_id=other_user.id,
            title="Other Task",
            due_date=now,
            priority="high",
            created_at=now
        ),
    ]

    for task in user_tasks + other_tasks:
        db.add(task)

    db.commit()

    for task in user_tasks + other_tasks:
        db.refresh(task)

    return {
        "user_tasks": user_tasks,
        "other_tasks": other_tasks
    }


class TestMCPToolSortIntegration:
    """Test MCP tool list_tasks with sort parameters."""

    def test_list_tasks_sort_by_due_date_asc(self, db: Session, user: User, sample_tasks: dict):
        """Test MCP tool with sort_by=due_date, sort_direction=asc."""
        params = ListTasksParams(
            user_id=user.id,
            sort_by="due_date",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should return only user's tasks, sorted by due_date ascending
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Task A"  # Day 1
        assert result["tasks"][1]["title"] == "Task B"  # Day 2
        assert result["tasks"][2]["title"] == "Task C"  # Day 3

    def test_list_tasks_sort_by_priority_asc(self, db: Session, user: User, sample_tasks: dict):
        """Test MCP tool with sort_by=priority, sort_direction=asc (high to low)."""
        params = ListTasksParams(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should be sorted: high, medium, low
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["priority"] == "high"
        assert result["tasks"][1]["priority"] == "medium"
        assert result["tasks"][2]["priority"] == "low"

    def test_list_tasks_sort_by_created_at_desc(self, db: Session, user: User, sample_tasks: dict):
        """Test MCP tool with sort_by=created_at, sort_direction=desc (newest first)."""
        params = ListTasksParams(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="desc"
        )

        result = list_tasks(params, db)

        # Should be sorted newest to oldest
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Task C"  # Most recent
        assert result["tasks"][1]["title"] == "Task B"
        assert result["tasks"][2]["title"] == "Task A"  # Oldest

    def test_list_tasks_sort_by_title_asc(self, db: Session, user: User, sample_tasks: dict):
        """Test MCP tool with sort_by=title, sort_direction=asc (A-Z)."""
        params = ListTasksParams(
            user_id=user.id,
            sort_by="title",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should be sorted alphabetically
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Task A"
        assert result["tasks"][1]["title"] == "Task B"
        assert result["tasks"][2]["title"] == "Task C"

    def test_list_tasks_default_sort(self, db: Session, user: User, sample_tasks: dict):
        """Test MCP tool with no sort parameters (should use default: created_at desc)."""
        params = ListTasksParams(user_id=user.id)

        result = list_tasks(params, db)

        # Default should be created_at desc (newest first)
        assert len(result["tasks"]) == 3
        assert result["tasks"][0]["title"] == "Task C"  # Newest
        assert result["tasks"][2]["title"] == "Task A"  # Oldest

    def test_list_tasks_user_isolation_with_sort(self, db: Session, user: User, other_user: User, sample_tasks: dict):
        """Test that sorting maintains user isolation (only returns user's tasks)."""
        params = ListTasksParams(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should only return user's tasks, NOT other_user's tasks
        assert len(result["tasks"]) == 3
        assert all(task["user_id"] == user.id for task in result["tasks"])

        # Verify other user's task is NOT included
        task_titles = [task["title"] for task in result["tasks"]]
        assert "Other Task" not in task_titles

    def test_list_tasks_invalid_sort_field(self, db: Session, user: User):
        """Test that invalid sort_by field raises validation error."""
        with pytest.raises(ValueError, match="sort_by must be one of"):
            params = ListTasksParams(
                user_id=user.id,
                sort_by="invalid_field"
            )

    def test_list_tasks_invalid_sort_direction(self, db: Session, user: User):
        """Test that invalid sort_direction raises validation error."""
        with pytest.raises(ValueError, match="sort_direction must be one of"):
            params = ListTasksParams(
                user_id=user.id,
                sort_by="created_at",
                sort_direction="invalid"
            )

    def test_list_tasks_sort_combined_with_status_filter(self, db: Session, user: User):
        """Test sorting combined with status filter."""
        now = datetime.utcnow()

        # Create tasks with different statuses
        tasks = [
            Task(user_id=user.id, title="Completed High", completed=True, priority="high", created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Incomplete Medium", completed=False, priority="medium", created_at=now - timedelta(hours=2)),
            Task(user_id=user.id, title="Completed Low", completed=True, priority="low", created_at=now - timedelta(hours=1)),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Filter completed + sort by priority
        params = ListTasksParams(
            user_id=user.id,
            status_filter="completed",
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should return only completed tasks, sorted by priority
        assert len(result["tasks"]) == 2
        assert all(task["completed"] for task in result["tasks"])
        assert result["tasks"][0]["priority"] == "high"
        assert result["tasks"][1]["priority"] == "low"

    def test_list_tasks_sort_combined_with_keyword_search(self, db: Session, user: User):
        """Test sorting combined with keyword search."""
        now = datetime.utcnow()

        # Create tasks with keyword
        tasks = [
            Task(user_id=user.id, title="Buy groceries", priority="high", created_at=now - timedelta(hours=3)),
            Task(user_id=user.id, title="Buy milk", priority="low", created_at=now - timedelta(hours=2)),
            Task(user_id=user.id, title="Buy bread", priority="medium", created_at=now - timedelta(hours=1)),
            Task(user_id=user.id, title="Call doctor", priority="high", created_at=now),
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Search "buy" + sort by priority
        params = ListTasksParams(
            user_id=user.id,
            keyword="buy",
            sort_by="priority",
            sort_direction="asc"
        )

        result = list_tasks(params, db)

        # Should return only "buy" tasks, sorted by priority
        assert len(result["tasks"]) == 3
        assert all("buy" in task["title"].lower() for task in result["tasks"])
        assert result["tasks"][0]["priority"] == "high"  # Buy groceries
        assert result["tasks"][1]["priority"] == "medium"  # Buy bread
        assert result["tasks"][2]["priority"] == "low"  # Buy milk

    def test_list_tasks_sort_direction_reversal(self, db: Session, user: User, sample_tasks: dict):
        """Test that reversing sort direction reverses results."""
        # Sort ascending
        params_asc = ListTasksParams(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="asc"
        )

        result_asc = list_tasks(params_asc, db)

        # Sort descending
        params_desc = ListTasksParams(
            user_id=user.id,
            sort_by="created_at",
            sort_direction="desc"
        )

        result_desc = list_tasks(params_desc, db)

        # Results should be reversed
        assert len(result_asc["tasks"]) == len(result_desc["tasks"])
        assert result_asc["tasks"][0]["title"] == result_desc["tasks"][-1]["title"]
        assert result_asc["tasks"][-1]["title"] == result_desc["tasks"][0]["title"]

    def test_list_tasks_pagination_with_sort(self, db: Session, user: User):
        """Test that sorting works correctly with pagination."""
        now = datetime.utcnow()

        # Create 10 tasks with different priorities
        tasks = [
            Task(user_id=user.id, title=f"Task {i}", priority="high" if i < 3 else "medium" if i < 7 else "low", created_at=now - timedelta(hours=i))
            for i in range(10)
        ]

        for task in tasks:
            db.add(task)
        db.commit()

        # Get page 1 sorted by priority
        params_page1 = ListTasksParams(
            user_id=user.id,
            sort_by="priority",
            sort_direction="asc",
            page=1,
            page_size=5
        )

        result_page1 = list_tasks(params_page1, db)

        # First page should have high priority tasks
        assert len(result_page1["tasks"]) == 5
        assert result_page1["tasks"][0]["priority"] == "high"
        assert result_page1["pagination"]["page"] == 1
        assert result_page1["pagination"]["totalPages"] == 2
