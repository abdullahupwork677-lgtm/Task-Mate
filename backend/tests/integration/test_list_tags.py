"""Integration tests for list_tags MCP tool.

Tests the tag listing functionality:
1. List all unique tags with counts
2. Tags sorted by count then alphabetically
3. Color generation consistency
4. Empty tag list handling
5. User isolation enforcement
6. Tag statistics accuracy
7. Performance with large datasets

Phase V - Task Tags & Categories (003-task-tags) - User Story 5
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.models import User, Task
from src.mcp_tools.list_tags import list_tags, ListTagsParams


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


@pytest.fixture(name="test_tasks_with_tags")
def test_tasks_with_tags_fixture(session: Session, test_user: str):
    """Create test tasks with various tags."""
    tasks = [
        # work tag: 5 tasks
        Task(title="Work task 1", user_id=test_user, priority="high", completed=False, tags=["work", "urgent"]),
        Task(title="Work task 2", user_id=test_user, priority="medium", completed=False, tags=["work", "important"]),
        Task(title="Work task 3", user_id=test_user, priority="low", completed=False, tags=["work"]),
        Task(title="Work task 4", user_id=test_user, priority="high", completed=True, tags=["work", "done"]),
        Task(title="Work task 5", user_id=test_user, priority="medium", completed=False, tags=["work", "project-a"]),

        # urgent tag: 3 tasks (2 overlap with work)
        Task(title="Urgent task 1", user_id=test_user, priority="high", completed=False, tags=["urgent"]),
        Task(title="Urgent task 2", user_id=test_user, priority="high", completed=False, tags=["urgent", "critical"]),
        # work + urgent already counted above (2 tasks)

        # shopping tag: 4 tasks
        Task(title="Shopping task 1", user_id=test_user, priority="low", completed=False, tags=["shopping", "groceries"]),
        Task(title="Shopping task 2", user_id=test_user, priority="medium", completed=False, tags=["shopping"]),
        Task(title="Shopping task 3", user_id=test_user, priority="low", completed=False, tags=["shopping", "home"]),
        Task(title="Shopping task 4", user_id=test_user, priority="high", completed=False, tags=["shopping", "urgent"]),

        # personal tag: 2 tasks
        Task(title="Personal task 1", user_id=test_user, priority="medium", completed=False, tags=["personal", "health"]),
        Task(title="Personal task 2", user_id=test_user, priority="low", completed=False, tags=["personal"]),

        # Unique tags (1 task each)
        Task(title="Important task", user_id=test_user, priority="high", completed=False, tags=["important"]),  # +1 (1 from work overlap)
        Task(title="Done task", user_id=test_user, priority="medium", completed=True, tags=["done"]),  # +1 (1 from work overlap)
        Task(title="Critical task", user_id=test_user, priority="high", completed=False, tags=["critical"]),  # +1 (1 from urgent overlap)
        Task(title="Groceries task", user_id=test_user, priority="low", completed=False, tags=["groceries"]),  # +1 (1 from shopping overlap)
        Task(title="Home task", user_id=test_user, priority="medium", completed=False, tags=["home"]),  # +1 (1 from shopping overlap)
        Task(title="Health task", user_id=test_user, priority="high", completed=False, tags=["health"]),  # +1 (1 from personal overlap)
        Task(title="Project A task", user_id=test_user, priority="medium", completed=False, tags=["project-a"]),  # +1 (1 from work overlap)

        # Task with no tags
        Task(title="No tags task", user_id=test_user, priority="low", completed=False, tags=[]),
    ]

    for task in tasks:
        session.add(task)
    session.commit()

    return tasks


class TestListTagsBasic:
    """Test basic list_tags functionality."""

    def test_list_all_tags(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """List all tags returns all unique tags."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Should have multiple unique tags
        assert result.total_tags > 0
        assert len(result.tags) == result.total_tags

        # Verify work is most popular (5 tasks)
        assert result.tags[0].name == "work"
        assert result.tags[0].count == 5

    def test_tags_sorted_by_count_then_name(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """Tags should be sorted by count (descending) then alphabetically."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Verify sorting: count DESC, then name ASC
        for i in range(len(result.tags) - 1):
            current = result.tags[i]
            next_tag = result.tags[i + 1]

            # If counts are equal, names should be in alphabetical order
            if current.count == next_tag.count:
                assert current.name <= next_tag.name, f"{current.name} should come before {next_tag.name}"
            # Otherwise, current should have higher count
            else:
                assert current.count >= next_tag.count

    def test_tag_counts_accurate(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """Tag counts should match actual task count."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Find work tag (should have 5 tasks)
        work_tag = next((tag for tag in result.tags if tag.name == "work"), None)
        assert work_tag is not None
        assert work_tag.count == 5

        # Find shopping tag (should have 4 tasks)
        shopping_tag = next((tag for tag in result.tags if tag.name == "shopping"), None)
        assert shopping_tag is not None
        assert shopping_tag.count == 4

        # Find urgent tag (should have 4 tasks: 2 overlap + 2 unique)
        urgent_tag = next((tag for tag in result.tags if tag.name == "urgent"), None)
        assert urgent_tag is not None
        assert urgent_tag.count == 4

    def test_total_tasks_accurate(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """Total tasks should be sum of all tag counts."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Sum of all tag counts
        calculated_total = sum(tag.count for tag in result.tags)
        assert result.total_tasks == calculated_total


class TestColorGeneration:
    """Test color generation for tags."""

    def test_color_is_hex_code(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """Each tag should have a valid hex color code."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        for tag in result.tags:
            # Should be a hex color (#RRGGBB)
            assert tag.color.startswith("#")
            assert len(tag.color) == 7
            # Try to parse as hex
            int(tag.color[1:], 16)  # Will raise if not valid hex

    def test_color_consistency(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """Same tag should always generate the same color."""
        params = ListTagsParams(user_id=test_user)

        # Call list_tags multiple times
        result1 = list_tags(session, params)
        result2 = list_tags(session, params)
        result3 = list_tags(session, params)

        # Find work tag in all results
        work_color_1 = next((tag.color for tag in result1.tags if tag.name == "work"), None)
        work_color_2 = next((tag.color for tag in result2.tags if tag.name == "work"), None)
        work_color_3 = next((tag.color for tag in result3.tags if tag.name == "work"), None)

        assert work_color_1 == work_color_2 == work_color_3

    def test_different_tags_different_colors(self, session: Session, test_user: str, test_tasks_with_tags: list):
        """Different tags should generate different colors."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Collect all colors
        colors = [tag.color for tag in result.tags]

        # Most tags should have different colors (some collisions possible)
        unique_colors = set(colors)
        collision_rate = 1 - (len(unique_colors) / len(colors))

        # Allow some collisions but should be mostly unique
        assert collision_rate < 0.3  # Less than 30% collision rate


class TestEmptyAndEdgeCases:
    """Test edge cases for list_tags."""

    def test_list_tags_no_tasks(self, session: Session, test_user: str):
        """List tags when user has no tasks."""
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        assert result.total_tags == 0
        assert result.total_tasks == 0
        assert result.tags == []

    def test_list_tags_tasks_without_tags(self, session: Session, test_user: str):
        """List tags when all tasks have no tags."""
        # Create tasks without tags
        tasks = [
            Task(title="Task 1", user_id=test_user, priority="medium", completed=False, tags=[]),
            Task(title="Task 2", user_id=test_user, priority="low", completed=False, tags=[]),
            Task(title="Task 3", user_id=test_user, priority="high", completed=False, tags=[]),
        ]
        for task in tasks:
            session.add(task)
        session.commit()

        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        assert result.total_tags == 0
        assert result.total_tasks == 0
        assert result.tags == []

    def test_list_tags_one_tag(self, session: Session, test_user: str):
        """List tags when only one unique tag exists."""
        # Create tasks with single tag
        tasks = [
            Task(title="Task 1", user_id=test_user, priority="medium", completed=False, tags=["work"]),
            Task(title="Task 2", user_id=test_user, priority="low", completed=False, tags=["work"]),
        ]
        for task in tasks:
            session.add(task)
        session.commit()

        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        assert result.total_tags == 1
        assert result.total_tasks == 2
        assert result.tags[0].name == "work"
        assert result.tags[0].count == 2


class TestUserIsolation:
    """Test user isolation in list_tags."""

    def test_list_tags_only_returns_user_tags(self, session: Session):
        """List tags should only return tags for the authenticated user."""
        # Create two users
        user1 = User(id="user-1", email="user1@example.com", name="User 1", password_hash="hash1")
        user2 = User(id="user-2", email="user2@example.com", name="User 2", password_hash="hash2")
        session.add(user1)
        session.add(user2)
        session.commit()

        # User 1 tasks with tags
        user1_tasks = [
            Task(title="User 1 task 1", user_id="user-1", priority="medium", completed=False, tags=["work", "user1"]),
            Task(title="User 1 task 2", user_id="user-1", priority="low", completed=False, tags=["work"]),
        ]
        # User 2 tasks with different tags
        user2_tasks = [
            Task(title="User 2 task 1", user_id="user-2", priority="high", completed=False, tags=["personal", "user2"]),
            Task(title="User 2 task 2", user_id="user-2", priority="medium", completed=False, tags=["personal"]),
        ]
        for task in user1_tasks + user2_tasks:
            session.add(task)
        session.commit()

        # List tags for user 1
        params = ListTagsParams(user_id="user-1")
        result = list_tags(session, params)

        # Should only see user 1's tags
        tag_names = {tag.name for tag in result.tags}
        assert "work" in tag_names
        assert "user1" in tag_names
        assert "personal" not in tag_names  # User 2's tag
        assert "user2" not in tag_names  # User 2's tag

        # List tags for user 2
        params = ListTagsParams(user_id="user-2")
        result = list_tags(session, params)

        # Should only see user 2's tags
        tag_names = {tag.name for tag in result.tags}
        assert "personal" in tag_names
        assert "user2" in tag_names
        assert "work" not in tag_names  # User 1's tag
        assert "user1" not in tag_names  # User 1's tag


class TestPerformance:
    """Test performance with large datasets."""

    def test_list_tags_large_dataset(self, session: Session, test_user: str):
        """List tags should handle large numbers of tasks and tags efficiently."""
        # Create 100 tasks with 20 unique tags
        tag_pool = [f"tag{i}" for i in range(20)]

        tasks = []
        for i in range(100):
            # Each task has 2-3 tags
            task_tags = [tag_pool[i % 20], tag_pool[(i + 1) % 20]]
            if i % 3 == 0:
                task_tags.append(tag_pool[(i + 2) % 20])

            tasks.append(
                Task(
                    title=f"Task {i}",
                    user_id=test_user,
                    priority="medium",
                    completed=False,
                    tags=task_tags
                )
            )

        for task in tasks:
            session.add(task)
        session.commit()

        # List tags
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Should have 20 unique tags
        assert result.total_tags == 20

        # All tags should have counts
        assert all(tag.count > 0 for tag in result.tags)

        # Should be sorted by count then name
        for i in range(len(result.tags) - 1):
            current = result.tags[i]
            next_tag = result.tags[i + 1]
            if current.count == next_tag.count:
                assert current.name <= next_tag.name

    def test_list_tags_many_unique_tags(self, session: Session, test_user: str):
        """List tags with many unique tags (each used once)."""
        # Create 50 tasks, each with a unique tag
        tasks = [
            Task(
                title=f"Task {i}",
                user_id=test_user,
                priority="medium",
                completed=False,
                tags=[f"unique-tag-{i}"]
            )
            for i in range(50)
        ]

        for task in tasks:
            session.add(task)
        session.commit()

        # List tags
        params = ListTagsParams(user_id=test_user)
        result = list_tags(session, params)

        # Should have 50 unique tags
        assert result.total_tags == 50
        assert result.total_tasks == 50

        # All tags should have count = 1
        assert all(tag.count == 1 for tag in result.tags)

        # Should be sorted alphabetically (all counts are 1)
        tag_names = [tag.name for tag in result.tags]
        assert tag_names == sorted(tag_names)
