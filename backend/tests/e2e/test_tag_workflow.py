"""E2E tests for complete tag lifecycle via chatbot.

Tests the full tag workflow from user perspective:
1. Create tasks with tags via natural language
2. Add tags to existing tasks
3. Remove tags from tasks
4. Filter tasks by tags
5. List all available tags
6. Verify tag colors and counts

Phase V - Task Tags & Categories (003-task-tags) - Phase 8 E2E Testing
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.models import User, Task
from src.mcp_tools.add_task import add_task, AddTaskParams
from src.mcp_tools.add_tag import add_tag, AddTagParams
from src.mcp_tools.remove_tag import remove_tag, RemoveTagParams
from src.mcp_tools.list_tasks import list_tasks, ListTasksParams
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
        id="test-user-e2e",
        email="e2e@example.com",
        name="E2E Test User",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    return user.id


class TestCompleteTagWorkflow:
    """Test complete tag lifecycle via MCP tools (simulating chatbot)."""

    def test_end_to_end_tag_workflow(self, session: Session, test_user: str):
        """Complete workflow: Create with tags → Add → Remove → Filter → List.

        Simulates this conversation:
        User: "add task buy groceries, tags: shopping, groceries"
        Agent: [Creates task with tags]
        User: "add tag urgent to task 1"
        Agent: [Adds urgent tag]
        User: "show shopping tasks"
        Agent: [Filters by shopping tag]
        User: "remove tag groceries from task 1"
        Agent: [Removes groceries tag]
        User: "show all my tags"
        Agent: [Lists all tags with counts]
        """

        # === Step 1: Create task with tags ===
        # User: "add task buy groceries, tags: shopping, groceries"
        add_task_params = AddTaskParams(
            user_id=test_user,
            title="Buy groceries",
            description="Weekly shopping",
            priority="medium",
            tags=["shopping", "groceries"]
        )
        task_result = add_task(session, add_task_params)

        assert task_result.task_id is not None
        assert set(task_result.tags) == {"shopping", "groceries"}
        task_id = task_result.task_id

        # === Step 2: Add tag to existing task ===
        # User: "add tag urgent to task 1"
        add_tag_params = AddTagParams(
            user_id=test_user,
            task_id=task_id,
            tags=["urgent"]
        )
        add_tag_result = add_tag(session, add_tag_params)

        assert add_tag_result.tags_added == ["urgent"]
        assert set(add_tag_result.tags) == {"shopping", "groceries", "urgent"}

        # === Step 3: Filter tasks by tag ===
        # User: "show shopping tasks"
        list_params = ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["shopping"]
        )
        list_result = list_tasks(session, list_params)

        assert list_result.count == 1
        assert list_result.tasks[0]["title"] == "Buy groceries"
        assert "shopping" in list_result.tasks[0]["tags"]

        # === Step 4: Remove tag from task ===
        # User: "remove tag groceries from task 1"
        remove_tag_params = RemoveTagParams(
            user_id=test_user,
            task_id=task_id,
            tags=["groceries"]
        )
        remove_tag_result = remove_tag(session, remove_tag_params)

        assert remove_tag_result.tags_removed == ["groceries"]
        assert set(remove_tag_result.tags) == {"shopping", "urgent"}

        # === Step 5: List all tags ===
        # User: "show all my tags"
        list_tags_params = ListTagsParams(user_id=test_user)
        tags_result = list_tags(session, list_tags_params)

        assert tags_result.total_tags == 2  # shopping, urgent (groceries removed)
        tag_names = {tag.name for tag in tags_result.tags}
        assert tag_names == {"shopping", "urgent"}

        # Verify counts
        shopping_tag = next((t for t in tags_result.tags if t.name == "shopping"), None)
        urgent_tag = next((t for t in tags_result.tags if t.name == "urgent"), None)
        assert shopping_tag.count == 1
        assert urgent_tag.count == 1

        # Verify colors are consistent
        assert shopping_tag.color.startswith("#")
        assert urgent_tag.color.startswith("#")

    def test_workflow_with_multiple_tasks(self, session: Session, test_user: str):
        """Workflow with multiple tasks and tag operations."""

        # === Create 3 tasks with different tags ===
        # Task 1: work, urgent
        task1 = add_task(session, AddTaskParams(
            user_id=test_user,
            title="Finish report",
            priority="high",
            tags=["work", "urgent"]
        ))

        # Task 2: work, important
        task2 = add_task(session, AddTaskParams(
            user_id=test_user,
            title="Review pull request",
            priority="medium",
            tags=["work", "important"]
        ))

        # Task 3: personal, health
        task3 = add_task(session, AddTaskParams(
            user_id=test_user,
            title="Doctor appointment",
            priority="high",
            tags=["personal", "health"]
        ))

        # === Add tag to task 3 ===
        # User: "add tag urgent to task 3"
        add_tag(session, AddTagParams(
            user_id=test_user,
            task_id=task3.task_id,
            tags=["urgent"]
        ))

        # === Filter by work tag (should return 2 tasks) ===
        work_tasks = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work"]
        ))

        assert work_tasks.count == 2
        work_titles = {task["title"] for task in work_tasks.tasks}
        assert work_titles == {"Finish report", "Review pull request"}

        # === Filter by urgent tag (should return 2 tasks) ===
        urgent_tasks = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["urgent"]
        ))

        assert urgent_tasks.count == 2
        urgent_titles = {task["title"] for task in urgent_tasks.tasks}
        assert urgent_titles == {"Finish report", "Doctor appointment"}

        # === Filter by work OR personal (should return 3 tasks) ===
        work_or_personal = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work", "personal"]
        ))

        assert work_or_personal.count == 3

        # === List all tags ===
        all_tags = list_tags(session, ListTagsParams(user_id=test_user))

        # Should have 5 unique tags
        assert all_tags.total_tags == 5
        tag_names = {tag.name for tag in all_tags.tags}
        assert tag_names == {"work", "urgent", "important", "personal", "health"}

        # Verify counts
        tag_counts = {tag.name: tag.count for tag in all_tags.tags}
        assert tag_counts["work"] == 2  # Task 1, Task 2
        assert tag_counts["urgent"] == 2  # Task 1, Task 3
        assert tag_counts["important"] == 1  # Task 2
        assert tag_counts["personal"] == 1  # Task 3
        assert tag_counts["health"] == 1  # Task 3

        # Verify sorting (by count DESC, then name ASC)
        # work (2), urgent (2) should come first (alphabetically between them)
        # Then health (1), important (1), personal (1) alphabetically
        expected_order = ["urgent", "work", "health", "important", "personal"]
        actual_order = [tag.name for tag in all_tags.tags]
        assert actual_order == expected_order

    def test_workflow_tag_modification_and_filtering(self, session: Session, test_user: str):
        """Test modifying tags and verifying filter results."""

        # Create task with initial tags
        task = add_task(session, AddTaskParams(
            user_id=test_user,
            title="Project task",
            priority="high",
            tags=["project-a", "backend"]
        ))

        # Add more tags
        add_tag(session, AddTagParams(
            user_id=test_user,
            task_id=task.task_id,
            tags=["python", "api"]
        ))

        # Verify task has 4 tags
        tasks = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all"
        ))
        assert len(tasks.tasks[0]["tags"]) == 4

        # Filter by project-a (should find the task)
        project_tasks = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["project-a"]
        ))
        assert project_tasks.count == 1

        # Remove backend tag
        remove_tag(session, RemoveTagParams(
            user_id=test_user,
            task_id=task.task_id,
            tags=["backend"]
        ))

        # Filter by backend (should not find the task)
        backend_tasks = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["backend"]
        ))
        assert backend_tasks.count == 0

        # Filter by python OR api (should still find the task)
        python_api_tasks = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["python", "api"]
        ))
        assert python_api_tasks.count == 1

        # List tags (should have 3: project-a, python, api)
        all_tags = list_tags(session, ListTagsParams(user_id=test_user))
        assert all_tags.total_tags == 3
        tag_names = {tag.name for tag in all_tags.tags}
        assert tag_names == {"project-a", "python", "api"}


class TestWorkflowEdgeCases:
    """Test edge cases in tag workflow."""

    def test_workflow_with_no_tags(self, session: Session, test_user: str):
        """Workflow when user has no tags."""

        # Create task without tags
        add_task(session, AddTaskParams(
            user_id=test_user,
            title="Simple task",
            priority="low",
            tags=[]
        ))

        # List tags (should be empty)
        all_tags = list_tags(session, ListTagsParams(user_id=test_user))
        assert all_tags.total_tags == 0
        assert all_tags.tags == []

        # Filter by tag (should return no tasks)
        filtered = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["work"]
        ))
        assert filtered.count == 0

    def test_workflow_duplicate_tag_handling(self, session: Session, test_user: str):
        """Test adding duplicate tags."""

        # Create task with tag
        task = add_task(session, AddTaskParams(
            user_id=test_user,
            title="Task with tags",
            priority="medium",
            tags=["work"]
        ))

        # Try to add same tag again
        result = add_tag(session, AddTagParams(
            user_id=test_user,
            task_id=task.task_id,
            tags=["work", "Work", "WORK"]  # Different cases
        ))

        # Should detect duplicates
        assert result.tags_added == []
        assert "work" in result.tags_already_present
        assert result.tags == ["work"]  # Still only 1 work tag

    def test_workflow_case_insensitive_operations(self, session: Session, test_user: str):
        """Test case-insensitive tag operations."""

        # Create task with lowercase tag
        task = add_task(session, AddTaskParams(
            user_id=test_user,
            title="Task",
            priority="medium",
            tags=["work"]
        ))

        # Filter by uppercase (should still find the task)
        filtered = list_tasks(session, ListTasksParams(
            user_id=test_user,
            status="all",
            tag_filter=["WORK"]
        ))
        assert filtered.count == 1

        # Remove with mixed case (should work)
        result = remove_tag(session, RemoveTagParams(
            user_id=test_user,
            task_id=task.task_id,
            tags=["WoRk"]
        ))
        assert result.tags_removed == ["work"]
        assert result.tags == []
