"""Integration tests for add_tag and remove_tag MCP tools.

Tests the tag modification operations:
1. add_tag MCP tool - Adding tags to existing tasks
2. remove_tag MCP tool - Removing tags from existing tasks
3. Tag modification via TaskService methods
4. User isolation enforcement
5. Error handling for invalid operations

Phase V - Task Tags & Categories (003-task-tags)
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.models import User, Task
from src.mcp_tools.add_tag import add_tag, AddTagParams
from src.mcp_tools.remove_tag import remove_tag, RemoveTagParams


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


@pytest.fixture(name="test_task")
def test_task_fixture(session: Session, test_user: str):
    """Create a test task with existing tags."""
    task = Task(
        title="Buy groceries",
        description="Get milk and bread",
        user_id=test_user,
        priority="medium",
        completed=False,
        tags=["shopping", "urgent"]
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


class TestAddTagMCPTool:
    """Test add_tag MCP tool functionality."""

    def test_add_single_tag(self, session: Session, test_user: str, test_task: Task):
        """Add a single tag to a task."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["important"]
        )

        result = add_tag(session, params)

        assert result.task_id == test_task.id
        assert result.title == "Buy groceries"
        assert set(result.tags) == {"shopping", "urgent", "important"}
        assert result.tags_added == ["important"]
        assert result.tags_already_present == []
        assert "Added 1 tag(s)" in result.message

    def test_add_multiple_tags(self, session: Session, test_user: str, test_task: Task):
        """Add multiple tags to a task."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["work", "deadline", "high-priority"]
        )

        result = add_tag(session, params)

        assert set(result.tags) == {"shopping", "urgent", "work", "deadline", "high-priority"}
        assert set(result.tags_added) == {"work", "deadline", "high-priority"}
        assert len(result.tags_added) == 3
        assert "Added 3 tag(s)" in result.message

    def test_add_existing_tag(self, session: Session, test_user: str, test_task: Task):
        """Adding an existing tag should report it as already present."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["shopping"]  # Already exists
        )

        result = add_tag(session, params)

        assert set(result.tags) == {"shopping", "urgent"}  # No change
        assert result.tags_added == []
        assert result.tags_already_present == ["shopping"]
        assert "already present" in result.message

    def test_add_mixed_new_and_existing_tags(self, session: Session, test_user: str, test_task: Task):
        """Adding mix of new and existing tags."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["urgent", "work", "shopping"]  # urgent and shopping exist, work is new
        )

        result = add_tag(session, params)

        assert set(result.tags) == {"shopping", "urgent", "work"}
        assert result.tags_added == ["work"]
        assert set(result.tags_already_present) == {"urgent", "shopping"}
        assert "Added 1 tag(s)" in result.message
        assert "already present" in result.message

    def test_add_tags_with_uppercase(self, session: Session, test_user: str, test_task: Task):
        """Tags should be normalized to lowercase."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["WORK", "Important", "high-PRIORITY"]
        )

        result = add_tag(session, params)

        assert "work" in result.tags
        assert "important" in result.tags
        assert "high-priority" in result.tags
        # No uppercase versions
        assert "WORK" not in result.tags
        assert "Important" not in result.tags

    def test_add_invalid_tags_filters_them_out(self, session: Session, test_user: str, test_task: Task):
        """Invalid tags should be filtered out."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["valid-tag", "invalid!", "", "   ", "a" * 51, "also-valid"]
        )

        result = add_tag(session, params)

        assert "valid-tag" in result.tags
        assert "also-valid" in result.tags
        # Invalid tags should not be present
        assert "invalid!" not in result.tags

    def test_add_tag_to_nonexistent_task(self, session: Session, test_user: str):
        """Adding tag to non-existent task should raise error."""
        params = AddTagParams(
            user_id=test_user,
            task_id=9999,
            tags=["work"]
        )

        with pytest.raises(ValueError) as exc_info:
            add_tag(session, params)

        assert "not found" in str(exc_info.value)

    def test_add_tag_wrong_user(self, session: Session, test_task: Task):
        """Cannot add tags to another user's task."""
        params = AddTagParams(
            user_id="wrong-user-id",
            task_id=test_task.id,
            tags=["work"]
        )

        with pytest.raises(ValueError) as exc_info:
            add_tag(session, params)

        assert "not found or you don't have access" in str(exc_info.value)

    def test_add_all_invalid_tags_raises_error(self, session: Session, test_user: str, test_task: Task):
        """If all tags are invalid, should raise error."""
        params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["!!!", "???", ""]
        )

        with pytest.raises(ValueError) as exc_info:
            add_tag(session, params)

        assert "All provided tags are invalid" in str(exc_info.value)


class TestRemoveTagMCPTool:
    """Test remove_tag MCP tool functionality."""

    def test_remove_single_tag(self, session: Session, test_user: str, test_task: Task):
        """Remove a single tag from a task."""
        params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["urgent"]
        )

        result = remove_tag(session, params)

        assert result.task_id == test_task.id
        assert result.title == "Buy groceries"
        assert result.tags == ["shopping"]  # Only shopping remains
        assert result.tags_removed == ["urgent"]
        assert result.tags_not_found == []
        assert "Removed 1 tag(s)" in result.message

    def test_remove_multiple_tags(self, session: Session, test_user: str, test_task: Task):
        """Remove multiple tags from a task."""
        params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["shopping", "urgent"]
        )

        result = remove_tag(session, params)

        assert result.tags == []  # All tags removed
        assert set(result.tags_removed) == {"shopping", "urgent"}
        assert len(result.tags_removed) == 2
        assert "Removed 2 tag(s)" in result.message

    def test_remove_nonexistent_tag(self, session: Session, test_user: str, test_task: Task):
        """Removing a tag that doesn't exist should report it as not found."""
        params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["work"]  # Doesn't exist on task
        )

        result = remove_tag(session, params)

        assert set(result.tags) == {"shopping", "urgent"}  # No change
        assert result.tags_removed == []
        assert result.tags_not_found == ["work"]
        assert "not found" in result.message

    def test_remove_mixed_existing_and_nonexistent_tags(self, session: Session, test_user: str, test_task: Task):
        """Removing mix of existing and non-existing tags."""
        params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["shopping", "work", "urgent"]  # shopping and urgent exist, work doesn't
        )

        result = remove_tag(session, params)

        assert result.tags == []  # shopping and urgent removed
        assert set(result.tags_removed) == {"shopping", "urgent"}
        assert result.tags_not_found == ["work"]
        assert "Removed 2 tag(s)" in result.message
        assert "not found" in result.message

    def test_remove_tags_case_insensitive(self, session: Session, test_user: str, test_task: Task):
        """Tag removal should be case-insensitive."""
        params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["SHOPPING", "Urgent"]  # Different case
        )

        result = remove_tag(session, params)

        assert result.tags == []  # Both removed despite case mismatch
        assert set(result.tags_removed) == {"shopping", "urgent"}

    def test_remove_tag_from_nonexistent_task(self, session: Session, test_user: str):
        """Removing tag from non-existent task should raise error."""
        params = RemoveTagParams(
            user_id=test_user,
            task_id=9999,
            tags=["work"]
        )

        with pytest.raises(ValueError) as exc_info:
            remove_tag(session, params)

        assert "not found" in str(exc_info.value)

    def test_remove_tag_wrong_user(self, session: Session, test_task: Task):
        """Cannot remove tags from another user's task."""
        params = RemoveTagParams(
            user_id="wrong-user-id",
            task_id=test_task.id,
            tags=["shopping"]
        )

        with pytest.raises(ValueError) as exc_info:
            remove_tag(session, params)

        assert "not found or you don't have access" in str(exc_info.value)

    def test_remove_tags_from_task_with_no_tags(self, session: Session, test_user: str):
        """Removing tags from a task that has no tags."""
        # Create task with no tags
        task = Task(
            title="Empty task",
            user_id=test_user,
            priority="low",
            completed=False,
            tags=[]
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        params = RemoveTagParams(
            user_id=test_user,
            task_id=task.id,
            tags=["work"]
        )

        result = remove_tag(session, params)

        assert result.tags == []
        assert result.tags_removed == []
        assert result.tags_not_found == ["work"]


class TestTagModificationWorkflow:
    """Test complete tag modification workflows."""

    def test_add_then_remove_tag(self, session: Session, test_user: str, test_task: Task):
        """Add a tag and then remove it."""
        # Add tag
        add_params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["work"]
        )
        add_result = add_tag(session, add_params)
        assert "work" in add_result.tags

        # Remove tag
        remove_params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["work"]
        )
        remove_result = remove_tag(session, remove_params)
        assert "work" not in remove_result.tags
        assert remove_result.tags_removed == ["work"]

    def test_remove_then_add_tag(self, session: Session, test_user: str, test_task: Task):
        """Remove a tag and then add it back."""
        # Remove tag
        remove_params = RemoveTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["urgent"]
        )
        remove_result = remove_tag(session, remove_params)
        assert "urgent" not in remove_result.tags

        # Add tag back
        add_params = AddTagParams(
            user_id=test_user,
            task_id=test_task.id,
            tags=["urgent"]
        )
        add_result = add_tag(session, add_params)
        assert "urgent" in add_result.tags
        assert add_result.tags_added == ["urgent"]

    def test_modify_tags_on_multiple_tasks(self, session: Session, test_user: str):
        """Modify tags on multiple tasks independently."""
        # Create two tasks
        task1 = Task(
            title="Task 1",
            user_id=test_user,
            priority="high",
            completed=False,
            tags=["work"]
        )
        task2 = Task(
            title="Task 2",
            user_id=test_user,
            priority="low",
            completed=False,
            tags=["personal"]
        )
        session.add(task1)
        session.add(task2)
        session.commit()
        session.refresh(task1)
        session.refresh(task2)

        # Add tag to task1
        add_tag(session, AddTagParams(
            user_id=test_user,
            task_id=task1.id,
            tags=["urgent"]
        ))

        # Remove tag from task2
        remove_tag(session, RemoveTagParams(
            user_id=test_user,
            task_id=task2.id,
            tags=["personal"]
        ))

        # Verify changes
        session.refresh(task1)
        session.refresh(task2)
        assert set(task1.tags) == {"work", "urgent"}
        assert task2.tags == []
