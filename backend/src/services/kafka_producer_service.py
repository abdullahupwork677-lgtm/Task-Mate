"""Kafka Producer Service

Publishes reminder events to Kafka with idempotency, partitioning, compression,
and error handling.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
"""

import asyncio
import gzip
import json
import logging
import os
import ssl
import uuid
from typing import List
from datetime import datetime
from pydantic import BaseModel

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from src.models import Task

logger = logging.getLogger(__name__)

# Kafka configuration from environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_REMINDERS = os.getenv("KAFKA_TOPIC_REMINDERS", "reminders")
KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
KAFKA_SASL_MECHANISM = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")
KAFKA_SASL_USERNAME = os.getenv("KAFKA_SASL_USERNAME", "")
KAFKA_SASL_PASSWORD = os.getenv("KAFKA_SASL_PASSWORD", "")

# Retry configuration (T076)
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1


class ReminderEventSchema(BaseModel):
    """Schema for reminder events published to Kafka.

    Fields:
        task_id: Task database ID
        user_id: User database ID
        task_title: Task title
        task_description: Task description (optional)
        due_date: Task due date (ISO 8601 format)
        reminder_type: Reminder interval (e.g., "24h", "1h")
        channels: Notification channels (email, push, in_app)
        event_id: Unique event ID for idempotency (T073)
    """
    task_id: int
    user_id: str
    task_title: str
    task_description: str | None = None
    due_date: str  # ISO 8601 datetime string
    reminder_type: str  # e.g., "24h", "1h"
    channels: List[str]  # e.g., ["email", "push", "in_app"]
    event_id: str  # UUID for idempotency


class KafkaProducerService:
    """Kafka producer for publishing reminder events.

    Features:
    - Idempotency via event_id UUID (T073)
    - GZIP compression for reduced bandwidth (T074)
    - Partitioning by user_id for ordered processing (T075)
    - Retry logic for send failures (T076)
    """

    def __init__(self):
        """Initialize Kafka producer."""
        self.producer: AIOKafkaProducer | None = None
        self.bootstrap_servers = KAFKA_BOOTSTRAP_SERVERS
        self.topic = KAFKA_TOPIC_REMINDERS

        logger.info(
            f"Initializing KafkaProducerService: "
            f"bootstrap_servers={self.bootstrap_servers}, topic={self.topic}"
        )

    async def start(self):
        """Start Kafka producer connection.

        Raises:
            Exception: If connection to Kafka fails (T076)
        """
        try:
            # Build kwargs based on security protocol
            producer_kwargs: dict = {
                "bootstrap_servers": self.bootstrap_servers,
                "compression_type": "gzip",
                "acks": "all",
            }

            if KAFKA_SECURITY_PROTOCOL in ("SASL_SSL", "SSL"):
                ssl_context = ssl.create_default_context()
                producer_kwargs["ssl_context"] = ssl_context

            if KAFKA_SECURITY_PROTOCOL in ("SASL_SSL", "SASL_PLAINTEXT"):
                producer_kwargs["security_protocol"] = KAFKA_SECURITY_PROTOCOL
                producer_kwargs["sasl_mechanism"] = KAFKA_SASL_MECHANISM
                producer_kwargs["sasl_plain_username"] = KAFKA_SASL_USERNAME
                producer_kwargs["sasl_plain_password"] = KAFKA_SASL_PASSWORD

            logger.info(
                f"Connecting to Kafka: servers={self.bootstrap_servers}, "
                f"protocol={KAFKA_SECURITY_PROTOCOL}, mechanism={KAFKA_SASL_MECHANISM}"
            )

            self.producer = AIOKafkaProducer(**producer_kwargs)
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}", exc_info=True)
            raise Exception(f"Failed to connect to Kafka: {str(e)}") from e

    async def stop(self):
        """Stop Kafka producer connection."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_reminder_event(
        self,
        task: Task,
        reminder_type: str,
        channels: List[str]
    ) -> str:
        """Publish reminder event to Kafka.

        Implements:
        - T072: Publish reminder event function
        - T073: Generate event_id UUID for idempotency
        - T074: Serialize to JSON with GZIP compression
        - T075: Partition by user_id for ordered processing
        - T076: Error handling with retry logic (3 attempts)

        Args:
            task: Task requiring reminder
            reminder_type: Reminder interval (e.g., "24h", "1h")
            channels: Notification channels (e.g., ["email", "push", "in_app"])

        Returns:
            event_id: Unique event ID (UUID string)

        Raises:
            Exception: If send fails after MAX_RETRIES attempts
        """
        # Generate unique event_id for idempotency (T073)
        event_id = str(uuid.uuid4())

        # Create event schema
        event = ReminderEventSchema(
            task_id=task.id,
            user_id=task.user_id,
            task_title=task.title,
            task_description=task.description,
            due_date=task.due_date.isoformat() if task.due_date else "",
            reminder_type=reminder_type,
            channels=channels,
            event_id=event_id
        )

        # Serialize to JSON (T074)
        event_json = event.model_dump_json()
        event_bytes = event_json.encode('utf-8')

        # GZIP compress (T074)
        event_compressed = gzip.compress(event_bytes)

        # Partition key: user_id for ordered processing (T075)
        partition_key = task.user_id.encode('utf-8')

        # Send with retry logic (T076)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Sending reminder event (attempt {attempt}/{MAX_RETRIES}): "
                    f"task_id={task.id}, user_id={task.user_id}, "
                    f"reminder_type={reminder_type}, event_id={event_id}"
                )

                # Send to Kafka
                await self.producer.send(
                    self.topic,
                    value=event_compressed,
                    key=partition_key
                )

                logger.info(
                    f"Reminder event sent successfully: event_id={event_id}, "
                    f"task_id={task.id}"
                )

                return event_id

            except KafkaError as e:
                logger.warning(
                    f"Kafka send failed (attempt {attempt}/{MAX_RETRIES}): {e}",
                    exc_info=True
                )

                if attempt == MAX_RETRIES:
                    # Max retries exceeded, raise exception
                    logger.error(
                        f"Max retries exceeded for event_id={event_id}. "
                        f"Giving up."
                    )
                    raise Exception(f"Send failed: {str(e)}") from e

                # Wait before retry
                await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

            except Exception as e:
                logger.error(
                    f"Unexpected error sending reminder event (attempt {attempt}): {e}",
                    exc_info=True
                )

                if attempt == MAX_RETRIES:
                    raise Exception(f"Send failed: {str(e)}") from e

                await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

        # Should never reach here (loop always returns or raises)
        raise Exception("Unexpected error in send_reminder_event")


# Singleton instance for application-wide use
_producer_instance: KafkaProducerService | None = None


async def get_kafka_producer() -> KafkaProducerService:
    """Get or create Kafka producer singleton.

    Returns:
        KafkaProducerService instance
    """
    global _producer_instance

    if _producer_instance is None:
        _producer_instance = KafkaProducerService()
        await _producer_instance.start()

    return _producer_instance


async def publish_reminder_event(
    task: Task,
    reminder_type: str,
    channels: List[str]
) -> str:
    """Publish reminder event to Kafka (convenience function).

    This is the main function used by the reminder check endpoint (T072).

    Args:
        task: Task requiring reminder
        reminder_type: Reminder interval (e.g., "24h", "1h")
        channels: Notification channels (e.g., ["email", "push", "in_app"])

    Returns:
        event_id: Unique event ID (UUID string)

    Raises:
        Exception: If send fails after retries

    Example:
        >>> event_id = await publish_reminder_event(
        ...     task=task,
        ...     reminder_type="24h",
        ...     channels=["email", "in_app"]
        ... )
        >>> print(f"Published event: {event_id}")
    """
    producer = await get_kafka_producer()
    return await producer.send_reminder_event(task, reminder_type, channels)
