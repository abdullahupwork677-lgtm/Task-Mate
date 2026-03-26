"""Integration tests for tag filtering functionality.

Tests the tag filtering feature:
1. Single tag filtering
2. Multiple tag filtering with OR logic
3. Combination with status filters
4. Case-insensitive tag matching
5. Empty and invalid tag filters
6. Performance with large tag datasets

Phase V - Task Tags & Categories (003-task-tags) - User Story 3
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.models import User, Task
from src.mcp_tools.list_tasks import list_tasks, ListTasksParams


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    return user.id


@pytest.fixture(name="test_tasks")
def test_tasks_fixture(session: Session, test_user: str):
    """Create test tasks with various tag combinations."""
    tasks = [
        Task(
            title="Work task 1",
            user_id=test_user,
            priority="high",
            completed=False,
            tags=["work", "urgent"]
        ),
        Task(
            title="Work task 2",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["work", "important"]
        ),
        Task(
            title="Shopping task",
            user_id=test_user,
            priority="low",
            completed=False,
            tags=["shopping", "groceries"]
        ),
        Task(
            title="Personal task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=["personal", "home"]
        ),
        Task(
            title="Urgent shopping",
            user_id=test_user,
            priority="high",
            completed=False,
            tags=["urgent", "shopping"]
        ),
        Task(
            title="Completed work",
            user_id=test_user,
            priority="high",
            completed=True,
            tags=["work", "done"]
        ),
        Task(
            title="No tags task",
            user_id=test_user,
            priority="medium",
            completed=False,
            tags=[]
        ),
    ]

    for task in tasks:
        session.add(task)
    session.commit()

    return tasks


class TestSingleTagFiltering:
    """Test filtering by a single tag."""

    def test_filter_by_work_tag(self, session: Session, test_user: str, test_tasks: list):
        """Filter tasks by 'work' tag."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should return 3 tasks with 'work' tag (including completed)
        assert result.count == 3
        assert all("work" in task["tags"] for task in result.tasks)
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Work task 2", "Completed work"}

    def test_filter_by_shopping_tag(self, session: Session, test_user: str, test_tasks: list):
        """Filter tasks by 'shopping' tag."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["shopping"]
        )

        result = list_tasks(session, params)

        # Should return 2 tasks with 'shopping' tag
        assert result.count == 2
        assert all("shopping" in task["tags"] for task in result.tasks)
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Shopping task", "Urgent shopping"}

    def test_filter_by_urgent_tag(self, session: Session, test_user: str, test_tasks: list):
        """Filter tasks by 'urgent' tag."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["urgent"]
        )

        result = list_tasks(session, params)

        # Should return 2 tasks with 'urgent' tag
        assert result.count == 2
        assert all("urgent" in task["tags"] for task in result.tasks)
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Urgent shopping"}

    def test_filter_by_nonexistent_tag(self, session: Session, test_user: str, test_tasks: list):
        """Filter by a tag that doesn't exist on any task."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["nonexistent"]
        )

        result = list_tasks(session, params)

        # Should return 0 tasks
        assert result.count == 0
        assert result.tasks == []


class TestMultipleTagFilteringORLogic:
    """Test filtering by multiple tags with OR logic."""

    def test_filter_by_work_or_shopping(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'work' OR 'shopping' tags."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work", "shopping"]
        )

        result = list_tasks(session, params)

        # Should return 5 tasks: 3 work + 2 shopping (no overlap)
        assert result.count == 5
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Work task 2", "Shopping task", "Urgent shopping", "Completed work"}

    def test_filter_by_urgent_or_important(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'urgent' OR 'important' tags."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["urgent", "important"]
        )

        result = list_tasks(session, params)

        # Should return 3 tasks
        assert result.count == 3
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Work task 2", "Urgent shopping"}

    def test_filter_by_three_tags(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'work' OR 'shopping' OR 'personal' tags."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work", "shopping", "personal"]
        )

        result = list_tasks(session, params)

        # Should return 6 tasks
        assert result.count == 6
        titles = {task["title"] for task in result.tasks}
        assert "No tags task" not in titles  # Task with no tags should not appear

    def test_filter_with_overlapping_tags(self, session: Session, test_user: str, test_tasks: list):
        """Filter by tags where some tasks have both tags."""
        # Urgent shopping has both 'urgent' and 'shopping' tags
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["urgent", "shopping"]
        )

        result = list_tasks(session, params)

        # Should return 3 unique tasks:
        # - Work task 1 (urgent)
        # - Shopping task (shopping)
        # - Urgent shopping (both urgent and shopping)
        assert result.count == 3
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Shopping task", "Urgent shopping"}


class TestCombinedFiltering:
    """Test tag filtering combined with other filters."""

    def test_filter_by_tag_and_status_pending(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'work' tag AND pending status."""
        params = ListTasksParams(
            user_id=test_user,
            status="pending",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should return 2 pending work tasks (excludes completed work)
        assert result.count == 2
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Work task 2"}
        assert all(not task["completed"] for task in result.tasks)

    def test_filter_by_tag_and_status_completed(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'work' tag AND completed status."""
        params = ListTasksParams(
            user_id=test_user,
            status="completed",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should return 1 completed work task
        assert result.count == 1
        assert result.tasks[0]["title"] == "Completed work"
        assert result.tasks[0]["completed"] is True

    def test_filter_by_tag_and_priority(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'work' tag AND 'high' priority."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            priority="high",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should return 2 high-priority work tasks
        assert result.count == 2
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Completed work"}
        assert all(task["priority"] == "high" for task in result.tasks)

    def test_filter_by_multiple_tags_and_status(self, session: Session, test_user: str, test_tasks: list):
        """Filter by multiple tags AND pending status."""
        params = ListTasksParams(
            user_id=test_user,
            status="pending",
            tag_filter=["work", "shopping"]
        )

        result = list_tasks(session, params)

        # Should return 4 pending tasks (work or shopping, excludes completed work)
        assert result.count == 4
        titles = {task["title"] for task in result.tasks}
        assert "Completed work" not in titles


class TestCaseInsensitiveTagFiltering:
    """Test case-insensitive tag matching."""

    def test_filter_with_uppercase_tag(self, session: Session, test_user: str, test_tasks: list):
        """Filter by 'WORK' should match 'work' tags."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["WORK"]
        )

        result = list_tasks(session, params)

        # Should return 3 tasks with 'work' tag (case-insensitive)
        assert result.count == 3
        titles = {task["title"] for task in result.tasks}
        assert titles == {"Work task 1", "Work task 2", "Completed work"}

    def test_filter_with_mixed_case_tags(self, session: Session, test_user: str, test_tasks: list):
        """Filter by mixed case tags."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["Work", "SHOPPING", "Urgent"]
        )

        result = list_tasks(session, params)

        # Should match tasks with work, shopping, or urgent (case-insensitive)
        assert result.count >= 4


class TestEdgeCases:
    """Test edge cases for tag filtering."""

    def test_filter_with_empty_tag_list(self, session: Session, test_user: str, test_tasks: list):
        """Filter with empty tag_filter list."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=[]
        )

        result = list_tasks(session, params)

        # Should return all tasks (no filtering)
        assert result.count == len(test_tasks)

    def test_filter_with_none_tag_filter(self, session: Session, test_user: str, test_tasks: list):
        """Filter with None tag_filter."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=None
        )

        result = list_tasks(session, params)

        # Should return all tasks (no filtering)
        assert result.count == len(test_tasks)

    def test_filter_with_whitespace_tags(self, session: Session, test_user: str, test_tasks: list):
        """Filter with tags containing whitespace."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["  work  ", " shopping "]
        )

        result = list_tasks(session, params)

        # Whitespace should be stripped, should match work and shopping
        assert result.count == 5

    def test_filter_no_match_returns_empty_list(self, session: Session, test_user: str, test_tasks: list):
        """Filter that matches no tasks returns empty list."""
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["xyz", "abc"]
        )

        result = list_tasks(session, params)

        assert result.count == 0
        assert result.tasks == []


class TestUserIsolation:
    """Test user isolation with tag filtering."""

    def test_tag_filter_respects_user_isolation(self, session: Session):
        """Tag filtering should only return tasks for the authenticated user."""
        # Create two users
        user1 = User(
            id="user-1",
            email="user1@example.com",
            name="User 1",
            password_hash="hash1"
        )
        user2 = User(
            id="user-2",
            email="user2@example.com",
            name="User 2",
            password_hash="hash2"
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # Create tasks for both users with same tags
        task1 = Task(
            title="User 1 work task",
            user_id="user-1",
            priority="medium",
            completed=False,
            tags=["work"]
        )
        task2 = Task(
            title="User 2 work task",
            user_id="user-2",
            priority="medium",
            completed=False,
            tags=["work"]
        )
        session.add(task1)
        session.add(task2)
        session.commit()

        # User 1 filters by 'work' tag
        params = ListTasksParams(
            user_id="user-1",
            status="all",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should only return user 1's task
        assert result.count == 1
        assert result.tasks[0]["title"] == "User 1 work task"

        # User 2 filters by 'work' tag
        params = ListTasksParams(
            user_id="user-2",
            status="all",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should only return user 2's task
        assert result.count == 1
        assert result.tasks[0]["title"] == "User 2 work task"


class TestPerformance:
    """Test performance with large tag datasets."""

    def test_filter_with_many_matching_tasks(self, session: Session, test_user: str):
        """Filter should work efficiently with many matching tasks."""
        # Create 100 tasks with 'work' tag
        tasks = [
            Task(
                title=f"Work task {i}",
                user_id=test_user,
                priority="medium",
                completed=False,
                tags=["work", f"tag{i % 10}"]
            )
            for i in range(100)
        ]

        for task in tasks:
            session.add(task)
        session.commit()

        # Filter by 'work' tag
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work"]
        )

        result = list_tasks(session, params)

        # Should return all 100 tasks
        assert result.count == 100

    def test_filter_by_multiple_tags_with_many_tasks(self, session: Session, test_user: str):
        """Filter by multiple tags with large dataset."""
        # Create 50 tasks with tag1, 50 with tag2
        tasks1 = [
            Task(
                title=f"Tag1 task {i}",
                user_id=test_user,
                priority="medium",
                completed=False,
                tags=["tag1"]
            )
            for i in range(50)
        ]
        tasks2 = [
            Task(
                title=f"Tag2 task {i}",
                user_id=test_user,
                priority="medium",
                completed=False,
                tags=["tag2"]
            )
            for i in range(50)
        ]

        for task in tasks1 + tasks2:
            session.add(task)
        session.commit()

        # Filter by tag1 OR tag2
        params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["tag1", "tag2"]
        )

        result = list_tasks(session, params)

        # Should return all 100 tasks
        assert result.count == 100
