"""Unit Tests for Kafka Consumer

Tests for consuming reminder events from Kafka and routing to handlers.

Following TDD approach - tests written FIRST before implementation.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Task: T094
"""

import pytest
import json
import gzip
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# Import will fail initially (TDD RED phase) - this is expected
import sys
sys.path.insert(0, '/Users/apple/Documents/Projects/todo_phase5/services/notification/src')

from kafka_consumer import (
    consume_reminder_events,
    process_reminder_event,
    route_to_handlers,
    ReminderEvent
)


# ========== TEST FIXTURES ==========

@pytest.fixture
def sample_reminder_event():
    """Sample reminder event from Kafka."""
    return {
        "task_id": 42,
        "user_id": "user-123",
        "task_title": "Submit quarterly report",
        "task_description": "Q4 2025 financial report",
        "due_date": "2026-02-11T17:00:00Z",
        "reminder_type": "24h",
        "channels": ["email", "in_app"],
        "event_id": "550e8400-e29b-41d4-a716-446655440000"
    }


@pytest.fixture
def gzip_compressed_event(sample_reminder_event):
    """GZIP compressed reminder event (as received from Kafka)."""
    event_json = json.dumps(sample_reminder_event)
    event_bytes = event_json.encode('utf-8')
    return gzip.compress(event_bytes)


# ========== TEST CASE 1: Connect to Kafka with consumer group ==========

@pytest.mark.asyncio
async def test_consumer_connects_to_kafka():
    """Test: Consumer connects to Kafka with correct consumer group (T097)"""
    with patch('aiokafka.AIOKafkaConsumer') as MockConsumer:
        mock_consumer = AsyncMock()
        MockConsumer.return_value = mock_consumer

        # Mock consumer methods
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()
        mock_consumer.__aiter__ = AsyncMock(return_value=iter([]))

        # Start consumer
        from kafka_consumer import KafkaConsumerService
        consumer_service = KafkaConsumerService()
        await consumer_service.start()

        # Verify consumer was created with correct config
        MockConsumer.assert_called_once()
        call_kwargs = MockConsumer.call_args[1]

        assert call_kwargs['group_id'] == "notification-service-group"
        assert call_kwargs['bootstrap_servers'] == "localhost:9092"


# ========== TEST CASE 2: Subscribe to reminders topic ==========

@pytest.mark.asyncio
async def test_consumer_subscribes_to_reminders_topic():
    """Test: Consumer subscribes to 'reminders' topic (T098)"""
    with patch('aiokafka.AIOKafkaConsumer') as MockConsumer:
        mock_consumer = AsyncMock()
        MockConsumer.return_value = mock_consumer
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()
        mock_consumer.__aiter__ = AsyncMock(return_value=iter([]))

        from kafka_consumer import KafkaConsumerService
        consumer_service = KafkaConsumerService()
        await consumer_service.start()

        # Verify subscribe was called with reminders topic
        MockConsumer.assert_called_once()
        call_kwargs = MockConsumer.call_args[1]
        assert call_kwargs['topics'] == ["reminders"]


# ========== TEST CASE 3: Deserialize JSON messages ==========

@pytest.mark.asyncio
async def test_deserialize_gzip_json_messages(gzip_compressed_event):
    """Test: Deserialize GZIP JSON messages to ReminderEventSchema (T099)"""
    # Decompress and parse
    decompressed = gzip.decompress(gzip_compressed_event)
    event_dict = json.loads(decompressed)

    # Validate with ReminderEvent model
    event = ReminderEvent(**event_dict)

    assert event.task_id == 42
    assert event.user_id == "user-123"
    assert event.reminder_type == "24h"
    assert event.event_id == "550e8400-e29b-41d4-a716-446655440000"


# ========== TEST CASE 4: Route to appropriate handlers ==========

@pytest.mark.asyncio
async def test_route_to_email_handler(sample_reminder_event):
    """Test: Route to email handler when 'email' in channels (T100)"""
    event = ReminderEvent(**sample_reminder_event)

    with patch('kafka_consumer.send_email_reminder') as mock_email:
        mock_email.return_value = {"status": "success", "notification_id": 123}

        results = await route_to_handlers(event)

        # Verify email handler was called
        assert mock_email.called
        assert "email" in [r["channel"] for r in results]


@pytest.mark.asyncio
async def test_route_to_multiple_handlers(sample_reminder_event):
    """Test: Route to multiple handlers (email, push, in_app) (T100)"""
    sample_reminder_event["channels"] = ["email", "push", "in_app"]
    event = ReminderEvent(**sample_reminder_event)

    with patch('kafka_consumer.send_email_reminder') as mock_email, \
         patch('kafka_consumer.send_push_notification') as mock_push, \
         patch('kafka_consumer.send_in_app_notification') as mock_in_app:

        mock_email.return_value = {"status": "success"}
        mock_push.return_value = {"status": "success"}
        mock_in_app.return_value = {"status": "success"}

        results = await route_to_handlers(event)

        # Verify all handlers were called
        assert mock_email.called
        assert mock_push.called
        assert mock_in_app.called
        assert len(results) == 3


# ========== TEST CASE 5: Commit offsets after successful processing ==========

@pytest.mark.asyncio
async def test_commit_offsets_after_processing():
    """Test: Commit Kafka offsets after successful processing (T101)"""
    with patch('aiokafka.AIOKafkaConsumer') as MockConsumer:
        mock_consumer = AsyncMock()
        MockConsumer.return_value = mock_consumer

        # Mock message
        mock_message = Mock()
        mock_message.value = gzip.compress(json.dumps({
            "task_id": 1,
            "user_id": "user-1",
            "task_title": "Test",
            "due_date": "2026-02-11T17:00:00Z",
            "reminder_type": "24h",
            "channels": ["email"],
            "event_id": "test-id"
        }).encode('utf-8'))

        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()
        mock_consumer.__aiter__ = AsyncMock(return_value=iter([mock_message]))
        mock_consumer.commit = AsyncMock()

        with patch('kafka_consumer.route_to_handlers') as mock_route:
            mock_route.return_value = [{"status": "success"}]

            from kafka_consumer import KafkaConsumerService
            consumer_service = KafkaConsumerService()
            await consumer_service.start()

            # Process one message
            await consumer_service.consume_one_message(mock_message)

            # Verify commit was called
            assert mock_consumer.commit.called


# ========== TEST CASE 6: Handle deserialization errors ==========

@pytest.mark.asyncio
async def test_handle_deserialization_errors():
    """Test: Handle deserialization errors gracefully (T102)"""
    # Invalid JSON
    invalid_message = b"not valid json"

    mock_message = Mock()
    mock_message.value = invalid_message

    from kafka_consumer import KafkaConsumerService
    consumer_service = KafkaConsumerService()

    # Should not raise exception
    try:
        await consumer_service.consume_one_message(mock_message)
    except Exception as e:
        pytest.fail(f"Should handle deserialization error gracefully: {e}")


# ========== TEST CASE 7: Handle handler errors ==========

@pytest.mark.asyncio
async def test_handle_handler_errors(sample_reminder_event):
    """Test: Handle handler errors and continue (T102)"""
    event = ReminderEvent(**sample_reminder_event)

    with patch('kafka_consumer.send_email_reminder') as mock_email:
        # Email handler raises exception
        mock_email.side_effect = Exception("SMTP server unavailable")

        # Should not raise exception, should log and continue
        try:
            results = await route_to_handlers(event)
            # Error should be in results
            assert any(r.get("status") == "error" for r in results)
        except Exception as e:
            pytest.fail(f"Should handle handler error gracefully: {e}")


# ========== TEST CASE 8: At-least-once delivery guarantee ==========

@pytest.mark.asyncio
async def test_at_least_once_delivery():
    """Test: Commit only after successful processing (at-least-once) (T101)"""
    with patch('aiokafka.AIOKafkaConsumer') as MockConsumer:
        mock_consumer = AsyncMock()
        MockConsumer.return_value = mock_consumer

        mock_message = Mock()
        mock_message.value = gzip.compress(json.dumps({
            "task_id": 1,
            "user_id": "user-1",
            "task_title": "Test",
            "due_date": "2026-02-11T17:00:00Z",
            "reminder_type": "24h",
            "channels": ["email"],
            "event_id": "test-id"
        }).encode('utf-8'))

        mock_consumer.commit = AsyncMock()

        with patch('kafka_consumer.route_to_handlers') as mock_route:
            # First attempt fails
            mock_route.side_effect = Exception("Handler failed")

            from kafka_consumer import KafkaConsumerService
            consumer_service = KafkaConsumerService()

            # Should not commit on failure
            try:
                await consumer_service.consume_one_message(mock_message)
            except:
                pass

            # Verify commit was NOT called on failure
            assert not mock_consumer.commit.called


# ========== TEST CASE 9: ReminderEvent validation ==========

def test_reminder_event_validation():
    """Test: ReminderEvent validates required fields"""
    # Valid event
    valid_data = {
        "task_id": 42,
        "user_id": "user-123",
        "task_title": "Test",
        "due_date": "2026-02-11T17:00:00Z",
        "reminder_type": "24h",
        "channels": ["email"],
        "event_id": "test-id"
    }

    event = ReminderEvent(**valid_data)
    assert event.task_id == 42
    assert event.channels == ["email"]


# ========== TEST CASE 10: Consumer graceful shutdown ==========

@pytest.mark.asyncio
async def test_consumer_graceful_shutdown():
    """Test: Consumer stops gracefully on shutdown"""
    with patch('aiokafka.AIOKafkaConsumer') as MockConsumer:
        mock_consumer = AsyncMock()
        MockConsumer.return_value = mock_consumer
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()
        mock_consumer.__aiter__ = AsyncMock(return_value=iter([]))

        from kafka_consumer import KafkaConsumerService
        consumer_service = KafkaConsumerService()
        await consumer_service.start()
        await consumer_service.stop()

        # Verify stop was called
        assert mock_consumer.stop.called
