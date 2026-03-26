"""End-to-End Tests for US2: 24-Hour Advance Reminder

Tests the complete reminder flow:
1. Create task with due date
2. Time advances to 24h before due date
3. Dapr cron triggers reminder check
4. Backend publishes Kafka event
5. Notification service consumes event
6. Email reminder sent
7. Database updated

Following TDD approach - tests written FIRST before full integration.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Tasks: T111, T112
"""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, AsyncMock, Mock
from freezegun import freeze_time
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models import Task, User, NotificationLog
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
        id="test-user-e2e-24h-reminder",
        email="e2e.24h@example.com",
        name="E2E 24h Reminder Test User",
        password_hash="$2b$12$dummy.hash",
        timezone="America/New_York"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestUS2_24HourReminder_E2E:
    """End-to-end tests for 24-hour reminder flow."""

    @pytest.mark.asyncio
    async def test_full_reminder_flow_24h_before_due(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Full flow from task creation to reminder sent (T111)

        Flow:
        1. Create task with due_date = now + 25 hours
        2. Freeze time at now + 1 hour (24h before due)
        3. Trigger reminder check endpoint
        4. Verify reminder event published to Kafka
        5. Verify task.reminder_sent updated
        """
        # Step 1: Create task due in 25 hours
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=25)

        task = Task(
            user_id=test_user.id,
            title="Submit quarterly report",
            description="Q4 2025 financial report",
            due_date=due_date,
            remind_before=["24h", "1h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        # Step 2: Advance time to 24h before due date
        time_24h_before = now + timedelta(hours=1)  # Now it's 24h before due

        with freeze_time(time_24h_before):
            # Step 3: Mock Kafka producer
            with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
                mock_publish.return_value = "test-event-id-123"

                # Step 4: Trigger reminder check endpoint (simulating Dapr cron)
                response = client.post("/api/internal/dapr/reminder-check")

                assert response.status_code == 200
                data = response.json()

                # Verify metrics
                assert data["status"] in ["success", "partial_success"]
                assert data["tasks_checked"] >= 1
                assert data["reminders_sent"] >= 1

                # Verify Kafka event was published
                assert mock_publish.called
                call_args = mock_publish.call_args
                published_task = call_args[1]["task"]
                assert published_task.id == task.id

                # Step 5: Verify task.reminder_sent updated
                test_db.refresh(task)
                assert task.reminder_sent is not None
                assert "24h" in task.reminder_sent
                assert task.reminder_sent["24h"] is not None

    @pytest.mark.asyncio
    async def test_time_advancement_triggers_reminder(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Time advancement from 25h to 24h before due triggers reminder (T112)"""
        # Create task
        now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))  # Tomorrow 5pm

        task = Task(
            user_id=test_user.id,
            title="Important meeting",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-456"

            # Time 1: 25 hours before due (too early)
            with freeze_time(datetime(2026, 2, 10, 16, 0, 0, tzinfo=ZoneInfo("UTC"))):
                response = client.post("/api/internal/dapr/reminder-check")
                assert response.status_code == 200
                data = response.json()

                # Should NOT send reminder (too early)
                assert data["reminders_sent"] == 0

            # Time 2: Exactly 24 hours before due (trigger time)
            with freeze_time(datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))):
                response = client.post("/api/internal/dapr/reminder-check")
                assert response.status_code == 200
                data = response.json()

                # Should send reminder
                assert data["reminders_sent"] >= 1
                assert mock_publish.called

    @pytest.mark.asyncio
    async def test_no_duplicate_reminders_sent(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Reminder sent only once (no duplicates)"""
        # Create task
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=24)

        task = Task(
            user_id=test_user.id,
            title="No duplicate test",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-789"

            # First call - should send reminder
            response1 = client.post("/api/internal/dapr/reminder-check")
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["reminders_sent"] >= 1

            # Verify task.reminder_sent updated
            test_db.refresh(task)
            assert "24h" in task.reminder_sent

            # Second call (same time) - should NOT send reminder again
            response2 = client.post("/api/internal/dapr/reminder-check")
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["reminders_sent"] == 0  # No new reminders

    @pytest.mark.asyncio
    async def test_completed_task_skipped(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Completed tasks don't trigger reminders"""
        # Create completed task
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=24)

        task = Task(
            user_id=test_user.id,
            title="Already completed",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=True  # Completed
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200
            data = response.json()

            # Should NOT send reminder for completed task
            assert data["reminders_sent"] == 0
            assert not mock_publish.called

    @pytest.mark.asyncio
    async def test_multiple_tasks_multiple_reminders(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Multiple tasks trigger multiple reminders"""
        # Create 3 tasks all due in 24 hours
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=24)

        for i in range(3):
            task = Task(
                user_id=test_user.id,
                title=f"Task {i+1}",
                due_date=due_date,
                remind_before=["24h"],
                reminder_sent={},
                completed=False
            )
            test_db.add(task)

        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-multi"

            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200
            data = response.json()

            # Should send 3 reminders
            assert data["reminders_sent"] == 3
            assert mock_publish.call_count == 3

    @pytest.mark.asyncio
    async def test_grace_period_within_1_hour(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Grace period allows sending reminder within 1 hour window"""
        # Create task
        now = datetime(2026, 2, 10, 17, 0, 0, tzinfo=ZoneInfo("UTC"))
        due_date = datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC"))  # 24h later

        task = Task(
            user_id=test_user.id,
            title="Grace period test",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-grace"

            # 30 minutes after ideal reminder time (within grace period)
            with freeze_time(datetime(2026, 2, 10, 17, 30, 0, tzinfo=ZoneInfo("UTC"))):
                response = client.post("/api/internal/dapr/reminder-check")
                assert response.status_code == 200
                data = response.json()

                # Should still send reminder (within grace period)
                assert data["reminders_sent"] >= 1
                assert mock_publish.called

    @pytest.mark.asyncio
    async def test_user_with_multiple_intervals(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Task with multiple intervals (24h and 1h) sends correct reminder"""
        # Create task with both 24h and 1h reminders
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=24)

        task = Task(
            user_id=test_user.id,
            title="Multiple intervals",
            due_date=due_date,
            remind_before=["24h", "1h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            mock_publish.return_value = "event-multi-interval"

            # Trigger reminder check at 24h before due
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200
            data = response.json()

            # Should send only 24h reminder (not 1h yet)
            assert data["reminders_sent"] == 1

            # Verify correct interval
            call_args = mock_publish.call_args
            assert call_args[1]["reminder_type"] == "24h"

            # Verify reminder_sent updated for 24h only
            test_db.refresh(task)
            assert "24h" in task.reminder_sent
            assert "1h" not in task.reminder_sent

    @pytest.mark.asyncio
    async def test_kafka_failure_logged_but_continues(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Kafka failure logged but endpoint continues processing other tasks"""
        # Create 2 tasks
        now = datetime.now(ZoneInfo("UTC"))
        due_date = now + timedelta(hours=24)

        task1 = Task(
            user_id=test_user.id,
            title="Task 1",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        task2 = Task(
            user_id=test_user.id,
            title="Task 2",
            due_date=due_date,
            remind_before=["24h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task1)
        test_db.add(task2)
        test_db.commit()

        with patch('src.services.kafka_producer_service.publish_reminder_event') as mock_publish:
            # First task fails, second succeeds
            mock_publish.side_effect = [
                Exception("Kafka connection lost"),
                "event-success"
            ]

            # Trigger reminder check
            response = client.post("/api/internal/dapr/reminder-check")
            assert response.status_code == 200
            data = response.json()

            # Should have partial success
            assert data["status"] == "partial_success"
            assert data["errors"] is not None
            assert len(data["errors"]) == 1

            # Second task should still process
            assert mock_publish.call_count == 2


class TestUS2_NotificationService_E2E:
    """E2E tests for notification service (would require running Kafka)."""

    @pytest.mark.skip(reason="Requires Kafka running - manual testing only")
    @pytest.mark.asyncio
    async def test_end_to_end_with_kafka_and_email(self):
        """Test: Full E2E flow with real Kafka and SendGrid

        This test requires:
        1. Redpanda/Kafka running
        2. Notification service running
        3. SendGrid API key configured

        Manual testing steps:
        1. Start Redpanda: docker run -d -p 9092:9092 redpanda...
        2. Start notification service: cd services/notification && uvicorn src.main:app --port 8001
        3. Run this test: pytest tests/e2e/test_us2_24h_reminder.py::test_end_to_end_with_kafka_and_email
        """
        pass
