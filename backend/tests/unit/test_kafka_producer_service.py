"""Unit Tests for Kafka Producer Service

Tests for publishing reminder events to Kafka with idempotency, partitioning,
compression, and error handling.

Following TDD approach - tests written FIRST before implementation.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
"""

import pytest
import json
import gzip
from datetime import datetime
from uuid import UUID
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from zoneinfo import ZoneInfo

# Import will fail initially (TDD RED phase) - this is expected
from src.services.kafka_producer_service import (
    KafkaProducerService,
    publish_reminder_event,
    ReminderEventSchema
)
from src.models import Task


# ========== TEST FIXTURES ==========

@pytest.fixture
def sample_task():
    """Sample task for testing."""
    task = Task(
        id=42,
        user_id="user-123",
        title="Submit quarterly report",
        description="Q4 2025 financial report",
        due_date=datetime(2026, 2, 11, 17, 0, 0, tzinfo=ZoneInfo("UTC")),
        remind_before=["24h", "1h"],
        reminder_sent={},
        completed=False
    )
    return task


@pytest.fixture
def reminder_event_data(sample_task):
    """Sample reminder event data."""
    return {
        "task_id": sample_task.id,
        "user_id": sample_task.user_id,
        "task_title": sample_task.title,
        "task_description": sample_task.description,
        "due_date": sample_task.due_date.isoformat(),
        "reminder_type": "24h",
        "channels": ["email", "in_app"],
        "event_id": "550e8400-e29b-41d4-a716-446655440000"
    }


# ========== TEST CASE 1: publish_reminder_event generates UUID ==========

@pytest.mark.asyncio
async def test_publish_reminder_event_generates_event_id(sample_task):
    """Test: Generate unique event_id UUID for idempotency (T073)"""
    with patch('src.services.kafka_producer_service.KafkaProducerService') as MockProducer:
        mock_producer = AsyncMock()
        MockProducer.return_value = mock_producer
        mock_producer.send_reminder_event.return_value = "test-uuid-1234"

        # Publish event
        event_id = await publish_reminder_event(
            task=sample_task,
            reminder_type="24h",
            channels=["email", "in_app"]
        )

        # Verify event_id is a valid UUID string
        assert event_id is not None
        try:
            uuid_obj = UUID(event_id)
            assert str(uuid_obj) == event_id
        except ValueError:
            pytest.fail(f"event_id '{event_id}' is not a valid UUID")


# ========== TEST CASE 2: Serialize to JSON with GZIP compression ==========

@pytest.mark.asyncio
async def test_serialize_event_with_gzip_compression(sample_task):
    """Test: Serialize ReminderEventSchema to JSON with GZIP compression (T074)"""
    with patch('aiokafka.AIOKafkaProducer') as MockKafka:
        mock_kafka = AsyncMock()
        MockKafka.return_value = mock_kafka

        producer = KafkaProducerService()
        await producer.start()

        # Send event
        event_id = await producer.send_reminder_event(
            task=sample_task,
            reminder_type="24h",
            channels=["email"]
        )

        # Verify send was called
        assert mock_kafka.send.called

        # Get the call arguments
        call_args = mock_kafka.send.call_args
        topic = call_args[0][0]
        value = call_args[1]['value']

        # Verify topic
        assert topic == "reminders"

        # Verify value is GZIP compressed
        # Should be able to decompress and parse JSON
        try:
            decompressed = gzip.decompress(value)
            event_data = json.loads(decompressed)

            assert event_data["task_id"] == sample_task.id
            assert event_data["user_id"] == sample_task.user_id
            assert event_data["reminder_type"] == "24h"
            assert "event_id" in event_data
        except Exception as e:
            pytest.fail(f"Failed to decompress/parse event data: {e}")


# ========== TEST CASE 3: Partition by user_id ==========

@pytest.mark.asyncio
async def test_partition_by_user_id(sample_task):
    """Test: Partition events by user_id for ordered processing (T075)"""
    with patch('aiokafka.AIOKafkaProducer') as MockKafka:
        mock_kafka = AsyncMock()
        MockKafka.return_value = mock_kafka

        producer = KafkaProducerService()
        await producer.start()

        # Send event
        await producer.send_reminder_event(
            task=sample_task,
            reminder_type="24h",
            channels=["email"]
        )

        # Verify partition key is user_id
        call_args = mock_kafka.send.call_args
        partition_key = call_args[1]['key']

        # Key should be user_id as bytes
        assert partition_key == sample_task.user_id.encode('utf-8')


# ========== TEST CASE 4: Error handling - Connection failures ==========

@pytest.mark.asyncio
async def test_error_handling_kafka_connection_failure():
    """Test: Handle Kafka connection failures gracefully (T076)"""
    with patch('aiokafka.AIOKafkaProducer') as MockKafka:
        # Simulate connection failure
        MockKafka.side_effect = Exception("Failed to connect to Kafka")

        producer = KafkaProducerService()

        with pytest.raises(Exception, match="Failed to connect to Kafka"):
            await producer.start()


# ========== TEST CASE 5: Error handling - Send failures with retry ==========

@pytest.mark.asyncio
async def test_error_handling_send_failure_with_retry(sample_task):
    """Test: Retry logic for send failures (3 attempts) (T076)"""
    with patch('aiokafka.AIOKafkaProducer') as MockKafka:
        mock_kafka = AsyncMock()
        MockKafka.return_value = mock_kafka

        # First 2 attempts fail, 3rd succeeds
        mock_kafka.send.side_effect = [
            Exception("Send failed - attempt 1"),
            Exception("Send failed - attempt 2"),
            AsyncMock()  # Success on 3rd attempt
        ]

        producer = KafkaProducerService()
        await producer.start()

        # Should retry and eventually succeed
        event_id = await producer.send_reminder_event(
            task=sample_task,
            reminder_type="24h",
            channels=["email"]
        )

        # Verify send was called 3 times
        assert mock_kafka.send.call_count == 3
        assert event_id is not None


# ========== TEST CASE 6: Error handling - Max retries exceeded ==========

@pytest.mark.asyncio
async def test_error_handling_max_retries_exceeded(sample_task):
    """Test: Raise error after max retries (3 attempts) (T076)"""
    with patch('aiokafka.AIOKafkaProducer') as MockKafka:
        mock_kafka = AsyncMock()
        MockKafka.return_value = mock_kafka

        # All attempts fail
        mock_kafka.send.side_effect = Exception("Send failed")

        producer = KafkaProducerService()
        await producer.start()

        # Should raise exception after 3 attempts
        with pytest.raises(Exception, match="Send failed"):
            await producer.send_reminder_event(
                task=sample_task,
                reminder_type="24h",
                channels=["email"]
            )

        # Verify send was called 3 times (max retries)
        assert mock_kafka.send.call_count == 3


# ========== TEST CASE 7: ReminderEventSchema validation ==========

def test_reminder_event_schema_validation(sample_task):
    """Test: ReminderEventSchema validates required fields"""
    # Valid event
    valid_event = ReminderEventSchema(
        task_id=sample_task.id,
        user_id=sample_task.user_id,
        task_title=sample_task.title,
        task_description=sample_task.description,
        due_date=sample_task.due_date.isoformat(),
        reminder_type="24h",
        channels=["email"],
        event_id="550e8400-e29b-41d4-a716-446655440000"
    )

    assert valid_event.task_id == sample_task.id
    assert valid_event.user_id == sample_task.user_id
    assert valid_event.reminder_type == "24h"
    assert valid_event.channels == ["email"]


# ========== TEST CASE 8: Multiple channels support ==========

@pytest.mark.asyncio
async def test_multiple_channels_support(sample_task):
    """Test: Support multiple notification channels (email, push, in_app)"""
    with patch('aiokafka.AIOKafkaProducer') as MockKafka:
        mock_kafka = AsyncMock()
        MockKafka.return_value = mock_kafka

        producer = KafkaProducerService()
        await producer.start()

        # Send event with multiple channels
        event_id = await producer.send_reminder_event(
            task=sample_task,
            reminder_type="24h",
            channels=["email", "push", "in_app"]
        )

        # Verify event was sent
        assert mock_kafka.send.called

        # Verify channels in event data
        call_args = mock_kafka.send.call_args
        value = call_args[1]['value']
        decompressed = gzip.decompress(value)
        event_data = json.loads(decompressed)

        assert set(event_data["channels"]) == {"email", "push", "in_app"}
