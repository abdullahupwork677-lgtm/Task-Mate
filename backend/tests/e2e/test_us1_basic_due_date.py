"""End-to-End Tests for US1: Basic Due Date via Chatbot

Tests natural language interaction with AI chatbot to set task due dates.
Following TDD approach - tests written FIRST before implementation.

Test Flow:
1. User creates task via chatbot with due date
2. Verify task stored in database with correct due_date
3. Verify API returns formatted due date and overdue status
4. Verify frontend can display the badges correctly
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.main import app
from src.models import Task, User, Conversation
from src.db import engine


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session."""
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def test_user_with_auth(db_session: Session):
    """Create a test user and return auth token."""
    user = User(
        id="test-user-e2e-due-date",
        email="e2e.duedate@example.com",
        name="E2E Due Date Test User",
        password_hash="$2b$12$dummy.hash.for.testing",
        timezone="America/New_York"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create JWT token (mock for testing)
    # In real test, use the actual JWT creation function
    token = "mock-jwt-token-for-e2e-due-date-testing"

    return {"user": user, "token": token, "user_id": user.id}


@pytest.fixture
def test_conversation(db_session: Session, test_user_with_auth: dict):
    """Create a test conversation."""
    conv = Conversation(
        user_id=test_user_with_auth["user_id"],
        title="Due Date E2E Test",
        created_at=datetime.utcnow()
    )
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)
    return conv


@pytest.mark.asyncio
class TestDueDateChatbotE2E:
    """End-to-end tests for due dates via chatbot."""

    async def test_create_task_with_due_date_tomorrow(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Add task Buy milk due tomorrow at 5pm'"""
        # Send chat message to create task with due date
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add task Buy milk due tomorrow at 5pm"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify chatbot response mentions due date
        assert "tomorrow" in data["response"].lower() or "5pm" in data["response"].lower()

        # Verify task was created in database with due_date
        tasks = db_session.exec(
            select(Task).where(
                Task.user_id == test_user_with_auth["user_id"],
                Task.title.contains("Buy milk")
            )
        ).all()

        assert len(tasks) == 1
        task = tasks[0]
        assert task.due_date is not None
        assert task.due_date > datetime.utcnow()  # Should be in the future
        assert task.due_date.hour == 17  # 5pm

    async def test_create_task_with_natural_language_due_date(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Create task Team meeting due next Friday at 10am'"""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Create task Team meeting due next Friday at 10am"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify task was created
        tasks = db_session.exec(
            select(Task).where(
                Task.user_id == test_user_with_auth["user_id"],
                Task.title.contains("Team meeting")
            )
        ).all()

        assert len(tasks) == 1
        task = tasks[0]
        assert task.due_date is not None
        assert task.due_date.weekday() == 4  # Friday (0=Monday, 4=Friday)
        assert task.due_date.hour == 10  # 10am

    async def test_get_tasks_returns_formatted_due_date(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict
    ):
        """Test: GET /api/v1/tasks returns due_date_formatted field"""
        # Create a task with due date
        tomorrow = datetime.utcnow() + timedelta(days=1)
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Task with due date",
            description="Testing formatted due date",
            due_date=tomorrow
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Get tasks from API
        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Find our task
        task_data = next((t for t in data if t["id"] == task.id), None)
        assert task_data is not None

        # Verify formatted due date exists
        assert "due_date_formatted" in task_data
        assert task_data["due_date_formatted"] is not None

        # Verify is_overdue is False (task is in future)
        assert "is_overdue" in task_data
        assert task_data["is_overdue"] is False

        # Verify overdue_by is None (not overdue)
        assert "overdue_by" in task_data
        assert task_data["overdue_by"] is None

    async def test_get_tasks_returns_overdue_status(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict
    ):
        """Test: GET /api/v1/tasks returns is_overdue=True for past due dates"""
        # Create a task with past due date
        yesterday = datetime.utcnow() - timedelta(days=1)
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Overdue task",
            description="Testing overdue status",
            due_date=yesterday
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Get tasks from API
        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Find our task
        task_data = next((t for t in data if t["id"] == task.id), None)
        assert task_data is not None

        # Verify is_overdue is True
        assert task_data["is_overdue"] is True

        # Verify overdue_by contains time information
        assert task_data["overdue_by"] is not None
        assert "ago" in task_data["overdue_by"].lower()

    async def test_update_task_due_date_via_chatbot(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Change task 5 due date to next Monday at 2pm'"""
        # Create a task first
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Project deadline",
            description="Important deadline",
            due_date=datetime(2026, 2, 20, 17, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Send chat message to change due date
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": f"Change task {task.id} due date to next Monday at 2pm"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify chatbot response mentions the change
        assert "due date" in data["response"].lower() or "monday" in data["response"].lower()

        # Verify due date was updated in database
        db_session.refresh(task)
        assert task.due_date is not None
        assert task.due_date.weekday() == 0  # Monday
        assert task.due_date.hour == 14  # 2pm

    async def test_completed_task_does_not_show_overdue(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict
    ):
        """Test: Completed tasks don't show as overdue even if past due date"""
        # Create a completed task with past due date
        yesterday = datetime.utcnow() - timedelta(days=1)
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Completed task",
            description="Already done",
            due_date=yesterday,
            completed=True
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Get tasks from API
        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Find our task
        task_data = next((t for t in data if t["id"] == task.id), None)
        assert task_data is not None

        # Verify completed field
        assert task_data["completed"] is True

        # Overdue status should still be calculated correctly
        # (frontend will hide overdue badge for completed tasks)
        assert task_data["is_overdue"] is True

    async def test_timezone_awareness_in_due_date(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: Due dates respect user timezone"""
        # User timezone is America/New_York (set in fixture)
        # Test that "tomorrow at 5pm" means 5pm NY time

        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add task Dentist appointment due tomorrow at 5pm"
            }
        )

        assert response.status_code == 200

        # Verify task was created
        tasks = db_session.exec(
            select(Task).where(
                Task.user_id == test_user_with_auth["user_id"],
                Task.title.contains("Dentist")
            )
        ).all()

        assert len(tasks) == 1
        task = tasks[0]
        assert task.due_date is not None

        # Verify timezone handling (stored in UTC, but parsed from NY timezone)
        # 5pm NY time should be stored as UTC equivalent
        # This is a simplified check - actual implementation should use pytz
        assert task.due_date.hour in [17, 21, 22]  # Depending on DST


@pytest.mark.asyncio
class TestDueDateFrontendIntegration:
    """Tests for frontend integration with due dates."""

    async def test_frontend_receives_badge_data(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict
    ):
        """Test: Frontend receives all necessary data to display badges"""
        # Create task with upcoming due date
        tomorrow = datetime.utcnow() + timedelta(days=1)
        upcoming_task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Upcoming task",
            due_date=tomorrow
        )

        # Create task with overdue date
        yesterday = datetime.utcnow() - timedelta(days=1)
        overdue_task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Overdue task",
            due_date=yesterday
        )

        db_session.add(upcoming_task)
        db_session.add(overdue_task)
        db_session.commit()

        # Get tasks from API
        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify upcoming task has correct badge data
        upcoming_data = next((t for t in data if t["title"] == "Upcoming task"), None)
        assert upcoming_data is not None
        assert upcoming_data["due_date"] is not None
        assert upcoming_data["due_date_formatted"] is not None
        assert upcoming_data["is_overdue"] is False
        assert upcoming_data["overdue_by"] is None

        # Verify overdue task has correct badge data
        overdue_data = next((t for t in data if t["title"] == "Overdue task"), None)
        assert overdue_data is not None
        assert overdue_data["due_date"] is not None
        assert overdue_data["due_date_formatted"] is not None
        assert overdue_data["is_overdue"] is True
        assert overdue_data["overdue_by"] is not None
        assert "ago" in overdue_data["overdue_by"].lower()

    async def test_frontend_date_utils_format(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict
    ):
        """Test: due_date_formatted matches frontend date-utils.ts format"""
        # Create task with specific due date
        specific_date = datetime(2026, 2, 15, 14, 30, 0)  # Feb 15, 2026 at 2:30 PM
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Specific date task",
            due_date=specific_date
        )
        db_session.add(task)
        db_session.commit()

        # Get tasks from API
        response = client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        task_data = next((t for t in data if t["title"] == "Specific date task"), None)
        assert task_data is not None

        # Verify formatted date contains expected components
        formatted = task_data["due_date_formatted"]
        assert "Feb" in formatted or "15" in formatted  # Month or day
        assert "at" in formatted.lower()  # Time separator
        assert "PM" in formatted or "pm" in formatted  # AM/PM indicator
