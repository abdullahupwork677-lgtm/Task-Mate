"""End-to-End Tests for Recurring Tasks via Chatbot

Tests natural language interaction with AI chatbot to set recurring tasks.
Following TDD approach - tests written FIRST before implementation.
"""

import pytest
from datetime import datetime
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
        id="test-user-e2e-recurring",
        email="e2e.recurring@example.com",
        name="E2E Test User",
        password_hash="$2b$12$dummy.hash.for.testing"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create JWT token (mock for testing)
    # In real test, use the actual JWT creation function
    token = "mock-jwt-token-for-e2e-testing"

    return {"user": user, "token": token, "user_id": user.id}


@pytest.fixture
def test_conversation(db_session: Session, test_user_with_auth: dict):
    """Create a test conversation."""
    conv = Conversation(
        user_id=test_user_with_auth["user_id"],
        title="Recurring Tasks E2E Test",
        created_at=datetime.utcnow()
    )
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)
    return conv


@pytest.mark.asyncio
class TestRecurringChatbotE2E:
    """End-to-end tests for recurring tasks via chatbot."""

    async def test_natural_language_make_task_weekly(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Make task 5 repeat weekly'"""
        # Create a task first
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Team standup",
            description="Weekly team meeting",
            due_date=datetime(2026, 2, 10, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Send chat message to make it recurring
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": f"Make task {task.id} repeat weekly"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify chatbot response mentions recurrence
        assert "weekly" in data["message"].lower()
        assert "recurring" in data["message"].lower()

        # Verify task is now recurring in database
        db_session.refresh(task)
        assert task.is_recurring is True
        assert task.recurrence_pattern == "weekly"

    async def test_natural_language_add_recurring_task(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Add a recurring task Pay rent every month'"""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a recurring task 'Pay rent' every month"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify chatbot created the task
        assert "pay rent" in data["message"].lower()
        assert "monthly" in data["message"].lower() or "month" in data["message"].lower()

        # Verify task was created in database
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%pay rent%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "monthly"

    async def test_natural_language_change_to_daily(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Change task 5 to repeat daily'"""
        # Create a recurring task
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Morning exercise",
            is_recurring=True,
            recurrence_pattern="weekly",
            due_date=datetime(2026, 2, 10, 6, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Change recurrence pattern
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": f"Change task {task.id} to repeat daily"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response mentions daily
        assert "daily" in data["message"].lower()

        # Verify database update
        db_session.refresh(task)
        assert task.recurrence_pattern == "daily"

    async def test_natural_language_invalid_pattern(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Make task 5 repeat every century' (invalid pattern)"""
        # Create a task
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Test task",
            due_date=datetime(2026, 2, 10, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Try invalid pattern
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": f"Make task {task.id} repeat every century"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify chatbot explains supported patterns
        assert "supported patterns" in data["message"].lower() or "invalid" in data["message"].lower()
        assert "daily" in data["message"].lower()
        assert "weekly" in data["message"].lower()
        assert "monthly" in data["message"].lower()

        # Verify task was NOT made recurring
        db_session.refresh(task)
        assert task.is_recurring is False

    async def test_natural_language_cancel_recurrence(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test: 'Stop repeating task 5' or 'Make task 5 not recurring'"""
        # Create a recurring task
        task = Task(
            user_id=test_user_with_auth["user_id"],
            title="Canceled recurring task",
            is_recurring=True,
            recurrence_pattern="weekly",
            due_date=datetime(2026, 2, 10, 10, 0, 0)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Cancel recurrence
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": f"Stop repeating task {task.id}"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response mentions cancellation
        assert "stopped" in data["message"].lower() or "cancelled" in data["message"].lower() or "not recurring" in data["message"].lower()

        # Verify database update
        db_session.refresh(task)
        assert task.is_recurring is False
        assert task.recurrence_pattern is None


@pytest.mark.asyncio
class TestAddRecurringTaskNaturalLanguage:
    """Test creating recurring tasks via natural language (Phase 8)."""

    async def test_add_daily_task_natural_language(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test 'Add a daily task Exercise' natural language command."""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a daily task 'Morning exercise'"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify task was created
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%morning exercise%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "daily"
        assert "daily" in data["message"].lower()

    async def test_add_weekly_task_natural_language(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test 'Add a weekly task Team meeting' natural language command."""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a weekly task 'Team meeting'"
            }
        )

        assert response.status_code == 200

        # Verify task
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%team meeting%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "weekly"

    async def test_add_recurring_task_every_month(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test 'Add recurring task every month' natural language command."""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a recurring task 'Pay rent' every month"
            }
        )

        assert response.status_code == 200

        # Verify task
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%pay rent%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "monthly"

    async def test_add_task_every_3_days(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test 'Add task every 3 days' natural language command."""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a task 'Water plants' every 3 days"
            }
        )

        assert response.status_code == 200

        # Verify task
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%water plants%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "every 3 days"

    async def test_add_daily_task_with_due_date(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test adding daily task with specific due date."""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a daily task 'Check emails' starting tomorrow at 9am"
            }
        )

        assert response.status_code == 200

        # Verify task
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%check emails%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "daily"
        assert task.due_date is not None

    async def test_add_recurring_task_with_end_date(
        self,
        client: TestClient,
        db_session: Session,
        test_user_with_auth: dict,
        test_conversation: Conversation
    ):
        """Test adding recurring task with end date."""
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {test_user_with_auth['token']}"},
            json={
                "conversation_id": test_conversation.id,
                "message": "Add a daily task 'Workout' until March 31"
            }
        )

        assert response.status_code == 200

        # Verify task
        statement = select(Task).where(
            Task.user_id == test_user_with_auth["user_id"],
            Task.title.ilike("%workout%")
        )
        task = db_session.exec(statement).first()

        assert task is not None
        assert task.is_recurring is True
        assert task.recurrence_pattern == "daily"
        assert task.recurrence_end_date is not None
