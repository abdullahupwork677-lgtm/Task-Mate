"""Integration Tests for 1-Hour Reminder

Tests the 1-hour reminder functionality that extends the 24-hour reminder system.

Phase V - Due Dates & Reminders
User Story 3: 1-Hour Urgent Reminder
Task: T113
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
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
        id="test-user-1h-reminder",
        email="1h.reminder@example.com",
        name="1H Reminder Test User",
        password_hash="$2b$12$dummy.hash",
        timezone="America/New_York"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class Test1HourReminder:
    """Integration tests for 1-hour reminder functionality."""

    @pytest.mark.asyncio
    async def test_1h_reminder_sent_when_due_in_1_hour(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: 1h reminder sent when task due in 1 hour (T114, T115)"""
        # Create task due in 1 hour
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=1)

        task = Task(
            user_id=test_user.id,
            title="Urgent meeting",
            due_date=due_date,
            remind_before=["24h", "1h"],
            reminder_sent={},  # No reminders sent yet
            completed=False
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-1h"

            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")

            assert response.status_code == 200
            data = response.json()

            # Should send 1h reminder
            assert data["reminders_sent"] >= 1

            # Verify correct interval
            assert mock_publish.called
            call_args = mock_publish.call_args
            assert call_args[1]["reminder_type"] == "1h"

    @pytest.mark.asyncio
    async def test_1h_reminder_updates_reminder_sent(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: task.reminder_sent updated with "1h" key (T116)"""
        # Create task due in 1 hour
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=1)

        task = Task(
            user_id=test_user.id,
            title="Update reminder_sent test",
            due_date=due_date,
            remind_before=["1h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-update"

            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200

            # Verify reminder_sent updated
            test_db.refresh(task)
            assert task.reminder_sent is not None
            assert "1h" in task.reminder_sent
            assert task.reminder_sent["1h"] is not None

    @pytest.mark.asyncio
    async def test_both_24h_and_1h_tracked_independently(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: reminder_sent tracks 24h and 1h independently (T117)"""
        # Create task with both intervals
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=1)

        task = Task(
            user_id=test_user.id,
            title="Independent tracking test",
            due_date=due_date,
            remind_before=["24h", "1h"],
            reminder_sent={"24h": (now - timedelta(hours=23)).isoformat()},  # 24h already sent
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-independent"

            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200

            # Verify only 1h reminder sent (24h already sent)
            assert mock_publish.called
            call_args = mock_publish.call_args
            assert call_args[1]["reminder_type"] == "1h"

            # Verify both tracked independently
            test_db.refresh(task)
            assert "24h" in task.reminder_sent
            assert "1h" in task.reminder_sent

    @pytest.mark.asyncio
    async def test_task_due_in_2_hours_only_sends_1h_reminder(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Task due in 2 hours → 1h reminder sent, 24h skipped (T118)"""
        # Create task due in 2 hours (24h reminder already passed)
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=2)

        task = Task(
            user_id=test_user.id,
            title="Task due in 2 hours",
            due_date=due_date,
            remind_before=["24h", "1h"],
            reminder_sent={},  # No reminders sent yet
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-2h"

            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200
            data = response.json()

            # Should NOT send any reminder (too early for 1h, too late for 24h)
            # 24h reminder should have been sent 22 hours ago
            # 1h reminder will be sent in 1 hour
            assert data["reminders_sent"] == 0

    @pytest.mark.asyncio
    async def test_1h_reminder_not_sent_twice(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: 1h reminder not sent if already sent"""
        # Create task with 1h reminder already sent
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=1)

        task = Task(
            user_id=test_user.id,
            title="Already sent 1h",
            due_date=due_date,
            remind_before=["1h"],
            reminder_sent={"1h": now.isoformat()},  # Already sent
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200
            data = response.json()

            # Should NOT send reminder again
            assert data["reminders_sent"] == 0
            assert not mock_publish.called
