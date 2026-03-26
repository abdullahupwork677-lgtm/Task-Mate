"""Integration tests for adding tasks with tags via API and MCP tools.

Tests the complete flow:
1. REST API endpoint (POST /tasks) with tags
2. MCP tool (add_task) with tags parameter
3. Database persistence of normalized tags
4. Tag retrieval via TaskResponse schema
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.main import app
from src.db import get_session
from src.models import User, Task
from src.auth.jwt import create_access_token
from src.mcp_tools.add_task import add_task, AddTaskParams


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


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with database session override."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user and return user ID."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password"
    )
    session.add(user)
    session.commit()
    return user.id


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: str):
    """Create authentication headers with JWT token."""
    token = create_access_token(test_user)
    return {"Authorization": f"Bearer {token}"}


class TestAddTaskWithTagsAPI:
    """Test adding tasks with tags via REST API."""

    def test_create_task_with_tags(self, client: TestClient, session: Session, auth_headers: dict):
        """Create task with tags via API."""
        response = client.post(
            "/tasks",
            json={
                "title": "Buy groceries",
                "description": "Get milk and bread",
                "priority": "high",
                "tags": ["shopping", "urgent"]
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert "tags" in data
        assert set(data["tags"]) == {"shopping", "urgent"}

        # Verify in database
        task = session.get(Task, data["id"])
        assert task is not None
        assert set(task.tags) == {"shopping", "urgent"}

    def test_create_task_with_uppercase_tags(self, client: TestClient, auth_headers: dict):
        """Tags should be normalized to lowercase."""
        response = client.post(
            "/tasks",
            json={
                "title": "Complete project",
                "tags": ["Work", "URGENT", "Important"]
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        # Tags should be lowercase
        assert set(data["tags"]) == {"work", "urgent", "important"}

    def test_create_task_with_duplicate_tags(self, client: TestClient, auth_headers: dict):
        """Duplicate tags should be removed."""
        response = client.post(
            "/tasks",
            json={
                "title": "Team meeting",
                "tags": ["work", "Work", "WORK", "meeting"]
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        # Should only have unique lowercase tags
        assert set(data["tags"]) == {"work", "meeting"}
        assert len(data["tags"]) == 2

    def test_create_task_without_tags(self, client: TestClient, auth_headers: dict):
        """Creating task without tags should work (tags optional)."""
        response = client.post(
            "/tasks",
            json={"title": "Read book"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        # Tags should be empty list
        assert data["tags"] == []

    def test_create_task_with_empty_tags(self, client: TestClient, auth_headers: dict):
        """Empty tags array should work."""
        response = client.post(
            "/tasks",
            json={"title": "Walk dog", "tags": []},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tags"] == []


class TestAddTaskMCPToolWithTags:
    """Test add_task MCP tool with tags parameter."""

    def test_mcp_add_task_with_tags(self, session: Session, test_user: str):
        """MCP tool should accept and normalize tags."""
        params = AddTaskParams(
            user_id=test_user,
            title="Buy milk",
            description="2% milk",
            priority="high",
            tags=["shopping", "groceries"]
        )

        result = add_task(session, params)

        assert result.task_id > 0
        assert result.title == "Buy milk"
        assert set(result.tags) == {"shopping", "groceries"}

        # Verify in database
        task = session.get(Task, result.task_id)
        assert task is not None
        assert set(task.tags) == {"shopping", "groceries"}

    def test_mcp_add_task_normalizes_tags(self, session: Session, test_user: str):
        """MCP tool should normalize tags (lowercase, deduplicate)."""
        params = AddTaskParams(
            user_id=test_user,
            title="Project meeting",
            tags=["Work", "URGENT", "work", "Meeting"]
        )

        result = add_task(session, params)

        # Should be normalized: lowercase and deduplicated
        assert set(result.tags) == {"work", "urgent", "meeting"}

    def test_mcp_add_task_filters_invalid_tags(self, session: Session, test_user: str):
        """MCP tool should filter out invalid tags."""
        params = AddTaskParams(
            user_id=test_user,
            title="Call client",
            tags=["work", "urgent!", "", "   ", "a" * 51, "valid"]
        )

        result = add_task(session, params)

        # Should only include valid tags
        assert "work" in result.tags
        assert "valid" in result.tags
        # Invalid tags should be filtered out
        assert "urgent!" not in result.tags
        assert "" not in result.tags

    def test_mcp_add_task_without_tags(self, session: Session, test_user: str):
        """MCP tool should work without tags parameter."""
        params = AddTaskParams(
            user_id=test_user,
            title="Write report"
        )

        result = add_task(session, params)

        assert result.task_id > 0
        assert result.tags == []

    def test_mcp_add_task_with_due_date_and_tags(self, session: Session, test_user: str):
        """MCP tool should handle both due_date and tags together."""
        params = AddTaskParams(
            user_id=test_user,
            title="Submit proposal",
            due_date="tomorrow at 5pm",
            tags=["work", "deadline", "important"]
        )

        result = add_task(session, params)

        assert result.task_id > 0
        assert result.due_date is not None  # Should be parsed
        assert set(result.tags) == {"work", "deadline", "important"}


class TestTagPersistence:
    """Test that tags are correctly persisted and retrieved."""

    def test_tags_persist_after_creation(self, session: Session, test_user: str):
        """Tags should persist in database after task creation."""
        params = AddTaskParams(
            user_id=test_user,
            title="Grocery shopping",
            tags=["shopping", "food", "weekend"]
        )

        result = add_task(session, params)
        task_id = result.task_id

        # Refresh session to ensure data is from database
        session.expire_all()

        # Retrieve task from database
        task = session.get(Task, task_id)
        assert task is not None
        assert set(task.tags) == {"shopping", "food", "weekend"}

    def test_multiple_tasks_different_tags(self, session: Session, test_user: str):
        """Multiple tasks can have different tags."""
        # Create first task
        params1 = AddTaskParams(
            user_id=test_user,
            title="Task 1",
            tags=["work", "urgent"]
        )
        result1 = add_task(session, params1)

        # Create second task
        params2 = AddTaskParams(
            user_id=test_user,
            title="Task 2",
            tags=["personal", "home"]
        )
        result2 = add_task(session, params2)

        # Verify both tasks have their own tags
        task1 = session.get(Task, result1.task_id)
        task2 = session.get(Task, result2.task_id)

        assert set(task1.tags) == {"work", "urgent"}
        assert set(task2.tags) == {"personal", "home"}

    def test_empty_tags_list_persists(self, session: Session, test_user: str):
        """Empty tags list should persist as empty list."""
        params = AddTaskParams(
            user_id=test_user,
            title="Task without tags",
            tags=[]
        )

        result = add_task(session, params)

        task = session.get(Task, result.task_id)
        assert task.tags == []


class TestTagEdgeCases:
    """Test edge cases for tag handling."""

    def test_very_long_tag_list(self, session: Session, test_user: str):
        """Should handle many tags (up to 100 per validation)."""
        many_tags = [f"tag{i}" for i in range(50)]
        params = AddTaskParams(
            user_id=test_user,
            title="Task with many tags",
            tags=many_tags
        )

        result = add_task(session, params)

        assert len(result.tags) == 50
        assert all(f"tag{i}" in result.tags for i in range(50))

    def test_special_characters_in_tags(self, session: Session, test_user: str):
        """Tags with valid special characters (- and _) should work."""
        params = AddTaskParams(
            user_id=test_user,
            title="Project task",
            tags=["high-priority", "work_related", "q1-2026"]
        )

        result = add_task(session, params)

        assert set(result.tags) == {"high-priority", "work_related", "q1-2026"}

    def test_whitespace_in_tags(self, session: Session, test_user: str):
        """Whitespace should be stripped from tags."""
        params = AddTaskParams(
            user_id=test_user,
            title="Meeting",
            tags=["  work  ", " urgent ", "meeting"]
        )

        result = add_task(session, params)

        # Whitespace should be stripped
        assert set(result.tags) == {"work", "urgent", "meeting"}
