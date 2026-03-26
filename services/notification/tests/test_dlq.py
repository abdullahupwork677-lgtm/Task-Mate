"""Tests for Dead Letter Queue (DLQ) Handling

Phase V - Production Readiness
Task: T196
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from zoneinfo import ZoneInfo

from src.schemas import ReminderEvent
from src.dlq_handler import DLQHandler, RetryHandler
from src.handlers.email_handler import EmailHandler


@pytest.fixture
def reminder_event():
    """Create a test reminder event."""
    return ReminderEvent(
        event_id="test-event-dlq-123",
        task_id=999,
        user_id="user-dlq-test",
        user_email="dlq@example.com",
        task_title="DLQ Test Task",
        task_description="Testing DLQ flow",
        due_date=datetime(2026, 2, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC")),
        reminder_type="24h",
        channels=["email"],
        user_timezone="America/New_York",
        timestamp=datetime.utcnow().isoformat()
    )


@pytest.fixture
async def dlq_handler():
    """Create a DLQ handler instance."""
    handler = DLQHandler(
        kafka_bootstrap_servers="localhost:9092",
        dlq_topic="reminders.dlq"
    )
    # Mock the producer to avoid actual Kafka connection
    handler.producer = AsyncMock()
    handler.producer.send_and_wait = AsyncMock()
    return handler


class TestDLQHandler:
    """Test Dead Letter Queue handler (T196)."""
    
    def test_should_send_to_dlq_after_max_retries(self, dlq_handler):
        """Test T196: Messages sent to DLQ after 3 retries."""
        # Should NOT send to DLQ for retries 0, 1, 2
        assert not dlq_handler.should_send_to_dlq(retry_count=0)
        assert not dlq_handler.should_send_to_dlq(retry_count=1)
        assert not dlq_handler.should_send_to_dlq(retry_count=2)
        
        # SHOULD send to DLQ for retry 3+
        assert dlq_handler.should_send_to_dlq(retry_count=3)
        assert dlq_handler.should_send_to_dlq(retry_count=4)
    
    @pytest.mark.asyncio
    async def test_send_to_dlq(self, dlq_handler, reminder_event):
        """Test T196: Message is sent to DLQ topic."""
        # Send to DLQ
        await dlq_handler.send_to_dlq(
            event=reminder_event,
            error="SendGrid timeout after 3 retries",
            retry_count=3,
            failure_reason="max_retries"
        )
        
        # Verify producer was called
        assert dlq_handler.producer.send_and_wait.called
        
        # Verify DLQ topic
        call_args = dlq_handler.producer.send_and_wait.call_args
        assert call_args[0][0] == "reminders.dlq"
        
        # Verify message content
        dlq_message = call_args[1]["value"]
        assert "original_event" in dlq_message
        assert "error" in dlq_message
        assert dlq_message["retry_count"] == 3
        assert dlq_message["failure_reason"] == "max_retries"
        assert "SendGrid timeout" in dlq_message["error"]


class TestRetryLogic:
    """Test retry logic with exponential backoff (T196)."""
    
    def test_exponential_backoff_delay(self):
        """Test T196: Exponential backoff calculates correct delays."""
        # Retry 0: 1s
        assert RetryHandler.calculate_backoff(0, base_delay=1.0) == 1.0
        
        # Retry 1: 2s
        assert RetryHandler.calculate_backoff(1, base_delay=1.0) == 2.0
        
        # Retry 2: 4s
        assert RetryHandler.calculate_backoff(2, base_delay=1.0) == 4.0
        
        # Retry 3: 8s (then DLQ)
        assert RetryHandler.calculate_backoff(3, base_delay=1.0) == 8.0
    
    def test_backoff_respects_max_delay(self):
        """Test T196: Backoff doesn't exceed max_delay."""
        # With max_delay=10, should cap at 10s
        assert RetryHandler.calculate_backoff(10, base_delay=1.0, max_delay=10.0) == 10.0
        assert RetryHandler.calculate_backoff(20, base_delay=1.0, max_delay=10.0) == 10.0


class TestSendGridFailureScenario:
    """Test T196: Simulate SendGrid failure → DLQ flow."""
    
    @pytest.mark.asyncio
    @patch('src.handlers.email_handler.SendGridAPIClient')
    async def test_sendgrid_timeout_triggers_dlq(
        self,
        mock_sendgrid_client,
        reminder_event
    ):
        """Test T196: SendGrid timeout after retries sends message to DLQ.
        
        Scenario:
        1. Attempt to send email via SendGrid
        2. SendGrid times out (simulated)
        3. Retry 3 times with exponential backoff
        4. After 3 failures, send to DLQ
        5. Verify DLQ message includes error details
        """
        # Mock SendGrid client to raise timeout error
        mock_client_instance = MagicMock()
        mock_client_instance.send.side_effect = Exception("SendGrid API timeout")
        mock_sendgrid_client.return_value = mock_client_instance
        
        # Create email handler and DLQ handler
        email_handler = EmailHandler(
            sendgrid_api_key="test-api-key",
            from_email="test@example.com",
            from_name="Test"
        )
        
        dlq_handler = DLQHandler(
            kafka_bootstrap_servers="localhost:9092",
            dlq_topic="reminders.dlq"
        )
        dlq_handler.producer = AsyncMock()
        dlq_handler.producer.send_and_wait = AsyncMock()
        
        # Simulate retry loop
        retry_count = 0
        last_error = None
        
        while retry_count < 3:
            try:
                # Attempt to send email (will fail)
                await email_handler.send_reminder_email(reminder_event)
                break  # If successful, exit loop
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                if dlq_handler.should_send_to_dlq(retry_count):
                    # Send to DLQ after 3 failures
                    await dlq_handler.send_to_dlq(
                        event=reminder_event,
                        error=last_error,
                        retry_count=retry_count,
                        failure_reason="max_retries"
                    )
                    break
        
        # Verify all 3 retries were attempted
        assert retry_count == 3
        assert "SendGrid API timeout" in last_error
        
        # Verify message was sent to DLQ
        assert dlq_handler.producer.send_and_wait.called
        dlq_call = dlq_handler.producer.send_and_wait.call_args
        
        # Verify DLQ message structure
        dlq_message = dlq_call[1]["value"]
        assert dlq_message["original_event"]["task_id"] == 999
        assert dlq_message["retry_count"] == 3
        assert dlq_message["failure_reason"] == "max_retries"
        assert "SendGrid API timeout" in dlq_message["error"]
    
    @pytest.mark.asyncio
    @patch('src.handlers.email_handler.SendGridAPIClient')
    async def test_sendgrid_auth_error_immediate_dlq(
        self,
        mock_sendgrid_client,
        reminder_event
    ):
        """Test T196: SendGrid auth error sends to DLQ without retries.
        
        Scenario:
        1. Attempt to send email
        2. SendGrid returns 401 Unauthorized (invalid API key)
        3. No retries (auth errors are permanent)
        4. Send directly to DLQ with failure_reason="auth_error"
        """
        # Mock SendGrid client to raise auth error
        mock_client_instance = MagicMock()
        mock_client_instance.send.side_effect = Exception("401 Unauthorized: Invalid API key")
        mock_sendgrid_client.return_value = mock_client_instance
        
        email_handler = EmailHandler(
            sendgrid_api_key="invalid-key",
            from_email="test@example.com",
            from_name="Test"
        )
        
        dlq_handler = DLQHandler(
            kafka_bootstrap_servers="localhost:9092",
            dlq_topic="reminders.dlq"
        )
        dlq_handler.producer = AsyncMock()
        dlq_handler.producer.send_and_wait = AsyncMock()
        
        # Attempt to send (will fail)
        try:
            await email_handler.send_reminder_email(reminder_event)
        except Exception as e:
            # Auth errors should not be retried
            if "401 Unauthorized" in str(e) or "Invalid API key" in str(e):
                await dlq_handler.send_to_dlq(
                    event=reminder_event,
                    error=str(e),
                    retry_count=0,
                    failure_reason="auth_error"
                )
        
        # Verify sent to DLQ without retries
        assert dlq_handler.producer.send_and_wait.called
        dlq_call = dlq_handler.producer.send_and_wait.call_args
        dlq_message = dlq_call[1]["value"]
        
        assert dlq_message["failure_reason"] == "auth_error"
        assert dlq_message["retry_count"] == 0
        assert "Invalid API key" in dlq_message["error"]


class TestDLQMetrics:
    """Test T196: DLQ metrics are recorded correctly."""
    
    @pytest.mark.asyncio
    @patch('src.utils.metrics.dlq_messages_total')
    async def test_dlq_metrics_increment(self, mock_dlq_counter, dlq_handler, reminder_event):
        """Test T196: DLQ metrics increment when message sent to DLQ."""
        # Send to DLQ
        await dlq_handler.send_to_dlq(
            event=reminder_event,
            error="Test error",
            retry_count=3,
            failure_reason="max_retries"
        )
        
        # Verify metric was incremented
        mock_dlq_counter.labels.assert_called_with(reason="max_retries")
        mock_dlq_counter.labels().inc.assert_called_once()
