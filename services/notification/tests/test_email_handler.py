"""Unit Tests for Email Handler

Tests for sending email reminders via SendGrid with retry logic and idempotency.

Following TDD approach - tests written FIRST before implementation.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Task: T103
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

import sys

# Mock the database imports before importing email_handler
sys.modules['db'] = Mock()
sys.modules['models'] = Mock()

sys.path.insert(0, '/Users/apple/Documents/Projects/todo_phase5/services/notification/src')

# Import will fail initially (TDD RED phase) - this is expected
from notification_handlers.email_handler import (
    send_email_reminder,
    create_email_template,
    log_notification,
    check_idempotency
)
from kafka_consumer import ReminderEvent


# ========== TEST FIXTURES ==========

@pytest.fixture
def sample_reminder_event():
    """Sample reminder event."""
    return ReminderEvent(
        task_id=42,
        user_id="user-123",
        task_title="Submit quarterly report",
        task_description="Q4 2025 financial report",
        due_date="2026-02-11T17:00:00Z",
        reminder_type="24h",
        channels=["email"],
        event_id="550e8400-e29b-41d4-a716-446655440000"
    )


# ========== TEST CASE 1: Send email via SendGrid API ==========

@pytest.mark.asyncio
async def test_send_email_via_sendgrid(sample_reminder_event):
    """Test: Send email using SendGrid API (T105, T106)"""
    with patch('sendgrid.SendGridAPIClient') as MockSendGrid:
        mock_client = Mock()
        MockSendGrid.return_value = mock_client
        mock_client.send = Mock(return_value=Mock(status_code=202))

        result = await send_email_reminder(sample_reminder_event)

        # Verify SendGrid was called
        assert mock_client.send.called
        assert result["status"] == "success"
        assert "notification_id" in result


# ========== TEST CASE 2: Email template formatting ==========

def test_create_email_template(sample_reminder_event):
    """Test: Email template with subject and body (T107)"""
    subject, body = create_email_template(sample_reminder_event)

    # Verify subject contains task title and reminder time
    assert "Reminder" in subject
    assert sample_reminder_event.task_title in subject
    assert "24h" in subject or "24 hours" in subject

    # Verify body contains task details
    assert sample_reminder_event.task_title in body
    assert sample_reminder_event.task_description in body
    assert "2026-02-11" in body  # Due date


# ========== TEST CASE 3: Retry logic with exponential backoff ==========

@pytest.mark.asyncio
async def test_retry_logic_exponential_backoff(sample_reminder_event):
    """Test: Retry 3 times with exponential backoff (1s, 2s, 4s) (T108)"""
    with patch('sendgrid.SendGridAPIClient') as MockSendGrid:
        mock_client = Mock()
        MockSendGrid.return_value = mock_client

        # First 2 attempts fail, 3rd succeeds
        mock_client.send.side_effect = [
            Exception("Network error - attempt 1"),
            Exception("Network error - attempt 2"),
            Mock(status_code=202)  # Success on 3rd attempt
        ]

        with patch('asyncio.sleep') as mock_sleep:
            result = await send_email_reminder(sample_reminder_event)

            # Verify 3 attempts
            assert mock_client.send.call_count == 3

            # Verify exponential backoff: sleep(1), sleep(2)
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0][0][0] == 1  # 1s
            assert mock_sleep.call_args_list[1][0][0] == 2  # 2s

            assert result["status"] == "success"


# ========== TEST CASE 4: Max retries exceeded ==========

@pytest.mark.asyncio
async def test_max_retries_exceeded(sample_reminder_event):
    """Test: Return error after 3 failed attempts (T108)"""
    with patch('sendgrid.SendGridAPIClient') as MockSendGrid:
        mock_client = Mock()
        MockSendGrid.return_value = mock_client

        # All attempts fail
        mock_client.send.side_effect = Exception("SMTP server unavailable")

        with patch('asyncio.sleep'):
            result = await send_email_reminder(sample_reminder_event)

            # Verify 3 attempts
            assert mock_client.send.call_count == 3

            # Verify error result
            assert result["status"] == "error"
            assert "SMTP server unavailable" in result["error"]


# ========== TEST CASE 5: Log to notification_logs table ==========

@pytest.mark.asyncio
async def test_log_notification_to_database(sample_reminder_event):
    """Test: Log notification to notification_logs table (T109)"""
    with patch('notification_handlers.email_handler.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        notification_log = await log_notification(
            event=sample_reminder_event,
            channel="email",
            status="success",
            sent_at=datetime.utcnow(),
            error_message=None
        )

        # Verify database add/commit was called
        assert mock_db.add.called
        assert mock_db.commit.called

        # Verify log fields
        assert notification_log.task_id == sample_reminder_event.task_id
        assert notification_log.user_id == sample_reminder_event.user_id
        assert notification_log.channel == "email"
        assert notification_log.status == "success"
        assert notification_log.event_id == sample_reminder_event.event_id


# ========== TEST CASE 6: Idempotency check ==========

@pytest.mark.asyncio
async def test_idempotency_check_duplicate_event(sample_reminder_event):
    """Test: Skip if event_id already processed (unique index) (T110)"""
    with patch('notification_handlers.email_handler.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock existing notification log
        mock_existing_log = Mock()
        mock_existing_log.event_id = sample_reminder_event.event_id
        mock_db.exec.return_value.first.return_value = mock_existing_log

        # Check idempotency
        is_duplicate = await check_idempotency(sample_reminder_event.event_id)

        assert is_duplicate is True


@pytest.mark.asyncio
async def test_idempotency_check_new_event(sample_reminder_event):
    """Test: Process new event_id (not duplicate) (T110)"""
    with patch('notification_handlers.email_handler.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # No existing notification log
        mock_db.exec.return_value.first.return_value = None

        # Check idempotency
        is_duplicate = await check_idempotency(sample_reminder_event.event_id)

        assert is_duplicate is False


# ========== TEST CASE 7: Full flow integration ==========

@pytest.mark.asyncio
async def test_full_email_flow_integration(sample_reminder_event):
    """Test: Full flow from event to email sent and logged"""
    with patch('sendgrid.SendGridAPIClient') as MockSendGrid, \
         patch('notification_handlers.email_handler.get_db') as mock_get_db:

        # Mock SendGrid
        mock_client = Mock()
        MockSendGrid.return_value = mock_client
        mock_client.send = Mock(return_value=Mock(status_code=202))

        # Mock database (no duplicate)
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.exec.return_value.first.return_value = None  # Not duplicate

        # Send email
        result = await send_email_reminder(sample_reminder_event)

        # Verify success
        assert result["status"] == "success"

        # Verify SendGrid was called
        assert mock_client.send.called

        # Verify database logging
        assert mock_db.add.called
        assert mock_db.commit.called


# ========== TEST CASE 8: Handle invalid email addresses ==========

@pytest.mark.asyncio
async def test_handle_invalid_email_address():
    """Test: Handle invalid recipient email address gracefully"""
    invalid_event = ReminderEvent(
        task_id=99,
        user_id="user-invalid",
        task_title="Test",
        due_date="2026-02-11T17:00:00Z",
        reminder_type="24h",
        channels=["email"],
        event_id="invalid-email-test"
    )

    with patch('notification_handlers.email_handler.get_user_email') as mock_get_email:
        # User has no email or invalid email
        mock_get_email.return_value = None

        result = await send_email_reminder(invalid_event)

        # Should return error
        assert result["status"] == "error"
        assert "email" in result["error"].lower()


# ========== TEST CASE 9: 24h vs 1h Email Template Differences (T120) ==========

def test_24h_reminder_template_no_urgency():
    """Test: 24h reminder has NO urgency prefix (T120)"""
    event_24h = ReminderEvent(
        task_id=100,
        user_id="user-template-test",
        task_title="Important meeting",
        task_description="Quarterly review",
        due_date="2026-02-12T14:00:00Z",
        reminder_type="24h",
        channels=["email"],
        event_id="test-24h-template"
    )

    subject, body = create_email_template(event_24h)

    # Verify NO urgency prefix in subject
    assert not subject.startswith("[URGENT]")
    assert "Reminder: Task 'Important meeting' due in 24 hours" in subject

    # Verify urgency level is "advance notice"
    assert "advance notice" in body

    # Verify NO urgency warning message in body
    assert "⚠️" not in body
    assert "URGENT:" not in body


def test_1h_reminder_template_has_urgency():
    """Test: 1h reminder HAS urgency prefix and messaging (T120)"""
    event_1h = ReminderEvent(
        task_id=101,
        user_id="user-template-test",
        task_title="Submit report",
        task_description="Final deadline",
        due_date="2026-02-12T15:00:00Z",
        reminder_type="1h",
        channels=["email"],
        event_id="test-1h-template"
    )

    subject, body = create_email_template(event_1h)

    # Verify urgency prefix in subject (T119)
    assert subject.startswith("[URGENT]")
    assert "[URGENT] Reminder: Task 'Submit report' due in 1 hour" in subject

    # Verify urgency level is "final reminder"
    assert "final reminder" in body

    # Verify urgency warning message in body (T119)
    assert "⚠️  URGENT: This task is due in 1 HOUR!" in body


def test_24h_vs_1h_template_differences():
    """Test: Compare 24h and 1h templates side-by-side (T120)"""
    # Create identical events except reminder_type
    base_event_data = {
        "task_id": 102,
        "user_id": "user-comparison",
        "task_title": "Test task",
        "task_description": "Test description",
        "due_date": "2026-02-12T16:00:00Z",
        "channels": ["email"],
        "event_id": "test-comparison"
    }

    event_24h = ReminderEvent(**{**base_event_data, "reminder_type": "24h"})
    event_1h = ReminderEvent(**{**base_event_data, "reminder_type": "1h"})

    subject_24h, body_24h = create_email_template(event_24h)
    subject_1h, body_1h = create_email_template(event_1h)

    # Verify subject differences
    assert not subject_24h.startswith("[URGENT]")
    assert subject_1h.startswith("[URGENT]")

    # Verify body differences
    assert "advance notice" in body_24h
    assert "final reminder" in body_1h

    # Verify urgency message only in 1h
    assert "⚠️" not in body_24h
    assert "⚠️  URGENT: This task is due in 1 HOUR!" in body_1h

    # Verify time indicators
    assert "24 hours" in subject_24h
    assert "1 hour" in subject_1h


def test_email_template_urgency_levels():
    """Test: Verify urgency level strings match documentation (T120)"""
    event_24h = ReminderEvent(
        task_id=103,
        user_id="user-urgency",
        task_title="Task",
        due_date="2026-02-12T17:00:00Z",
        reminder_type="24h",
        channels=["email"],
        event_id="test-urgency-24h"
    )
    event_1h = ReminderEvent(
        task_id=104,
        user_id="user-urgency",
        task_title="Task",
        due_date="2026-02-12T18:00:00Z",
        reminder_type="1h",
        channels=["email"],
        event_id="test-urgency-1h"
    )

    _, body_24h = create_email_template(event_24h)
    _, body_1h = create_email_template(event_1h)

    # Verify exact urgency level strings
    assert "This is a advance notice that your task is due soon:" in body_24h
    assert "This is a final reminder that your task is due soon:" in body_1h
