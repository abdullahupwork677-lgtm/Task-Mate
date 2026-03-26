"""End-to-End Tests for US3: 1-Hour Urgent Reminder

Tests the dual reminder flow where a task receives both:
1. 24-hour advance reminder
2. 1-hour urgent reminder

Following TDD approach - tests written FIRST before full integration.

Phase V - Due Dates & Reminders
User Story 3: 1-Hour Urgent Reminder
Task: T121
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
from src.db import get_session


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
    def override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session):
    """Create a test user."""
    user = User(
        id="test-user-e2e-1h-reminder",
        email="e2e.1h@example.com",
        name="E2E 1H Reminder Test User",
        password_hash="$2b$12$dummy.hash",
        timezone="America/New_York"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestUS3_DualReminders_E2E:
    """End-to-end tests for dual reminder flow (24h + 1h)."""

    def test_task_receives_both_24h_and_1h_reminders(
        self,
        client: TestClient,
        test_db: Session,
        test_user: User
    ):
        """Test: Task receives both 24h and 1h reminders at correct times (T121)

        Scenario:
        1. Create task due in 25 hours
        2. Advance time to 24h before due → 24h reminder sent
        3. Advance time to 1h before due → 1h reminder sent
        4. Verify both reminders were sent independently
        """
        # Step 1: Create task due in 25 hours
        now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        due_date = datetime(2026, 2, 11, 13, 0, 0, tzinfo=ZoneInfo("UTC"))  # Tomorrow 1pm

        task = Task(
            user_id=test_user.id,
            title="Important presentation",
            description="Board meeting presentation",
            due_date=due_date,
            remind_before=["24h", "1h"],
            reminder_sent={},
            completed=False
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        with patch('src.routes.reminders.publish_reminder_event', new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = "event-dual-reminder"

            # Step 2: Advance time to 24h before due (tomorrow 12pm → 1pm is 25h away)
            time_24h_before = datetime(2026, 2, 10, 13, 0, 0, tzinfo=ZoneInfo("UTC"))

            with freeze_time(time_24h_before):
                response = client.post("/api/internal/dapr/reminder-check")
                assert response.status_code == 200
                data = response.json()

                # Verify 24h reminder was sent
                assert data["reminders_sent"] >= 1

                # Verify correct reminder type
                call_args = mock_publish.call_args
                assert call_args[1]["reminder_type"] == "24h"

                # Verify task.reminder_sent updated with 24h
                test_db.refresh(task)
                assert task.reminder_sent is not None
                assert "24h" in task.reminder_sent
                assert "1h" not in task.reminder_sent  # Not sent yet

            # Step 3: Advance time to 1h before due (tomorrow 12pm)
            time_1h_before = datetime(2026, 2, 11, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

            # Reset mock call count
            mock_publish.reset_mock()

            with freeze_time(time_1h_before):
                response = client.post("/api/internal/dapr/reminder-check")
                assert response.status_code == 200
                data = response.json()

                # Verify 1h reminder was sent
                assert data["reminders_sent"] >= 1

                # Verify correct reminder type (1h, not 24h again)
                call_args = mock_publish.call_args
                assert call_args[1]["reminder_type"] == "1h"

                # Step 4: Verify both reminders tracked independently
                # Query task fresh from database to see committed changes
                updated_task = test_db.get(Task, task.id)
                assert updated_task is not None
                assert "24h" in updated_task.reminder_sent  # Still has 24h
                assert "1h" in updated_task.reminder_sent  # Now has 1h

                # Verify both timestamps are different
                timestamp_24h = datetime.fromisoformat(updated_task.reminder_sent["24h"])
                timestamp_1h = datetime.fromisoformat(updated_task.reminder_sent["1h"])
                assert timestamp_24h != timestamp_1h
                assert timestamp_1h > timestamp_24h  # 1h sent after 24h
