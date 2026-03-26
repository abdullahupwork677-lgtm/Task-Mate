"""Integration Tests for Reminder Check Endpoint

Tests the full reminder check flow:
1. Query tasks needing reminders
2. Publish events to Kafka
3. Update database with reminder_sent
4. Return metrics

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models import Task, User
from src.db import get_db


# In-memory SQLite for testing
@pytest.fixture(name="test_db")
def test_db_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(test_db: Session):
    """Create a test client with overridden database."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    user = User(
        id="test-user-reminder-endpoint",
        email="reminder.endpoint@example.com",
        name="Reminder Endpoint Test User",
        password_hash="$2b$12$dummy.hash",
        timezone="America/New_York"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestReminderCheckEndpoint:
    """Integration tests for POST /api/internal/dapr/reminder-check"""

    @pytest.mark.asyncio
    async def test_endpoint_queries_tasks_needing_reminders(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Endpoint calls get_tasks_needing_reminders (T080)"""
        # Create task needing reminder
        due_date = datetime.now(ZoneInfo("UTC")) + timedelta(hours=23)
        task = Task(
            user_id=test_user.id,
            title="Task needing reminder",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        # Mock Kafka publisher
        with patch('src.routes.reminders.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "test-event-id"

            # Call endpoint
            response = client.post("/api/internal/dapr/reminder-check")

            assert response.status_code == 200
            data = response.json()

            # Verify endpoint checked tasks
            assert data["tasks_checked"] >= 1
            assert "duration_ms" in data

    @pytest.mark.asyncio
    async def test_endpoint_publishes_reminder_event(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Endpoint publishes events to Kafka for pending reminders (T081)"""
        # Create task needing 24h reminder
        due_date = datetime.now(ZoneInfo("UTC")) + timedelta(hours=23)
        task = Task(
            user_id=test_user.id,
            title="Publish event test",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        # Mock Kafka publisher
        with patch('src.routes.reminders.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-123"

            # Call endpoint
            response = client.post("/api/internal/dapr/reminder-check")

            assert response.status_code == 200
            data = response.json()

            # Verify event was published
            assert mock_publish.called
            assert data["reminders_sent"] >= 1

    @pytest.mark.asyncio
    async def test_endpoint_updates_reminder_sent_field(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Endpoint updates task.reminder_sent after sending (T082)"""
        # Create task needing reminder
        due_date = datetime.now(ZoneInfo("UTC")) + timedelta(hours=23)
        task = Task(
            user_id=test_user.id,
            title="Update reminder_sent test",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        # Mock Kafka publisher
        with patch('src.routes.reminders.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-456"

            # Call endpoint
            response = client.post("/api/internal/dapr/reminder-check")

            assert response.status_code == 200

            # Refresh task from database
            test_db.refresh(task)

            # Verify reminder_sent was updated
            assert task.reminder_sent is not None
            assert "24h" in task.reminder_sent
            assert task.reminder_sent["24h"] is not None

    @pytest.mark.asyncio
    async def test_endpoint_returns_metrics(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Endpoint returns structured metrics (T083)"""
        # Call endpoint
        response = client.post("/api/internal/dapr/reminder-check")

        assert response.status_code == 200
        data = response.json()

        # Verify metrics structure
        assert "status" in data
        assert "tasks_checked" in data
        assert "reminders_sent" in data
        assert "duration_ms" in data
        assert "timestamp" in data

        # Verify types
        assert isinstance(data["tasks_checked"], int)
        assert isinstance(data["reminders_sent"], int)
        assert isinstance(data["duration_ms"], int)

    @pytest.mark.asyncio
    async def test_endpoint_handles_kafka_errors_gracefully(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Endpoint handles Kafka errors and continues (T084)"""
        # Create task
        due_date = datetime.now(ZoneInfo("UTC")) + timedelta(hours=23)
        task = Task(
            user_id=test_user.id,
            title="Kafka error test",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        # Mock Kafka publisher to raise error
        with patch('src.routes.reminders.publish_reminder_event') as mock_publish:
            mock_publish.side_effect = Exception("Kafka connection failed")

            # Call endpoint
            response = client.post("/api/internal/dapr/reminder-check")

            # Endpoint should still return 200 (partial success)
            assert response.status_code == 200
            data = response.json()

            # Verify status indicates partial success
            assert data["status"] == "partial_success"
            assert data["errors"] is not None
            assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_endpoint_skips_completed_tasks(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Endpoint skips completed tasks"""
        # Create completed task
        due_date = datetime.now(ZoneInfo("UTC")) + timedelta(hours=23)
        task = Task(
            user_id=test_user.id,
            title="Completed task",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=True  # Completed
        )
        test_db.add(task)
        test_db.commit()

        # Mock Kafka publisher
        with patch('src.routes.reminders.publish_reminder_event') as mock_publish:
            # Call endpoint
            response = client.post("/api/internal/dapr/reminder-check")

            assert response.status_code == 200
            data = response.json()

            # Verify no reminders sent for completed task
            assert not mock_publish.called
            assert data["reminders_sent"] == 0
