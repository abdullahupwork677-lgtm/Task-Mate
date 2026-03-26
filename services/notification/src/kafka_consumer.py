"""Kafka Consumer for Reminder Events

Consumes reminder events from Kafka and routes to notification handlers.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Tasks: T095-T102
"""

import asyncio
import gzip
import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from config import settings

logger = logging.getLogger(__name__)


class ReminderEvent(BaseModel):
    """Reminder event schema (matches backend ReminderEventSchema).

    Fields:
        task_id: Task database ID
        user_id: User database ID
        task_title: Task title
        task_description: Task description (optional)
        due_date: Task due date (ISO 8601)
        reminder_type: Reminder interval (e.g., "24h", "1h")
        channels: Notification channels (email, push, in_app)
        event_id: Unique event ID for idempotency
    """
    task_id: int
    user_id: str
    task_title: str
    task_description: str | None = None
    due_date: str
    reminder_type: str
    channels: List[str]
    event_id: str


class KafkaConsumerService:
    """Kafka consumer for reminder events.

    Implements:
    - T096: Async consume with aiokafka
    - T097: Connect with consumer group
    - T098: Subscribe to reminders topic
    - T099: Deserialize JSON messages
    - T100: Route to handlers
    - T101: Commit offsets after processing
    - T102: Error handling
    """

    def __init__(self):
        """Initialize Kafka consumer."""
        self.consumer: AIOKafkaConsumer | None = None
        self.bootstrap_servers = settings.kafka_bootstrap_servers
        self.topic = settings.kafka_topic_reminders
        self.consumer_group = settings.kafka_consumer_group

        logger.info(
            f"Initializing Kafka consumer: "
            f"bootstrap={self.bootstrap_servers}, "
            f"topic={self.topic}, "
            f"group={self.consumer_group}"
        )

    async def start(self):
        """Start Kafka consumer connection (T096, T097, T098).

        Raises:
            Exception: If connection to Kafka fails
        """
        try:
            # T097: Create consumer with group_id
            self.consumer = AIOKafkaConsumer(
                # T098: Subscribe to reminders topic
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                # Consumer settings
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Manual commit for at-least-once
                fetch_max_bytes=settings.consumer_fetch_max_bytes,
                max_poll_records=settings.consumer_max_poll_records,
            )

            await self.consumer.start()
            logger.info(f"Kafka consumer started: topic={self.topic}")

        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}", exc_info=True)
            raise Exception(f"Failed to connect to Kafka: {str(e)}") from e

    async def stop(self):
        """Stop Kafka consumer connection."""
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume_one_message(self, message):
        """Process a single Kafka message (T099, T100, T101, T102).

        Args:
            message: Kafka message

        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            # T099: Deserialize GZIP JSON message
            try:
                decompressed = gzip.decompress(message.value)
                event_dict = json.loads(decompressed)
            except Exception as e:
                # T102: Handle deserialization errors
                logger.error(
                    f"Failed to deserialize message: {e}",
                    exc_info=True
                )
                return False

            # Parse to ReminderEvent
            try:
                event = ReminderEvent(**event_dict)
            except Exception as e:
                # T102: Handle validation errors
                logger.error(
                    f"Failed to validate event: {e}",
                    exc_info=True
                )
                return False

            logger.info(
                f"Processing reminder event: "
                f"event_id={event.event_id}, "
                f"task_id={event.task_id}, "
                f"user_id={event.user_id}, "
                f"reminder_type={event.reminder_type}"
            )

            # T100: Route to appropriate handlers
            try:
                results = await route_to_handlers(event)

                # Check if all handlers succeeded
                all_success = all(r.get("status") == "success" for r in results)

                if all_success:
                    logger.info(
                        f"Event processed successfully: event_id={event.event_id}, "
                        f"handlers={len(results)}"
                    )
                    return True
                else:
                    # T102: Some handlers failed
                    failed_count = sum(1 for r in results if r.get("status") != "success")
                    logger.warning(
                        f"Event partially processed: event_id={event.event_id}, "
                        f"failed_handlers={failed_count}/{len(results)}"
                    )
                    return False

            except Exception as e:
                # T102: Handle handler errors
                logger.error(
                    f"Failed to process event: event_id={event.event_id}, error={e}",
                    exc_info=True
                )
                return False

        except Exception as e:
            # T102: Handle unexpected errors
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            return False

    async def consume_loop(self):
        """Main consumer loop (T096, T101).

        Continuously consumes messages and commits offsets after successful processing.
        """
        try:
            async for message in self.consumer:
                try:
                    # Process message
                    success = await self.consume_one_message(message)

                    # T101: Commit offset after successful processing (at-least-once)
                    if success:
                        await self.consumer.commit()
                        logger.debug(f"Offset committed: partition={message.partition}, offset={message.offset}")
                    else:
                        # Don't commit on failure - message will be reprocessed
                        logger.warning(
                            f"Skipping commit due to processing failure: "
                            f"partition={message.partition}, offset={message.offset}"
                        )

                except Exception as e:
                    # T102: Log and continue on error
                    logger.error(f"Error in consumer loop: {e}", exc_info=True)
                    # Continue processing next message

        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in consumer loop: {e}", exc_info=True)
            raise


async def route_to_handlers(event: ReminderEvent) -> List[Dict[str, Any]]:
    """Route reminder event to appropriate notification handlers.

    Implements:
    - T100: Route to handlers
    - T150: Multi-channel orchestration with asyncio.gather (parallel execution)
    - T154: Resilience - one channel failure doesn't stop others

    Args:
        event: Reminder event to process

    Returns:
        List of handler results with status

    Handlers:
    - email: send_email_reminder()
    - push: send_push_reminder()
    - in_app: send_in_app_reminder()
    """
    # T150: Build parallel tasks for each enabled channel
    tasks = []
    channel_names = []

    for channel in event.channels:
        if channel == "email":
            tasks.append(_send_email_wrapper(event))
            channel_names.append("email")
        elif channel == "push":
            tasks.append(_send_push_wrapper(event))
            channel_names.append("push")
        elif channel == "in_app":
            tasks.append(_send_in_app_wrapper(event))
            channel_names.append("in_app")
        else:
            logger.warning(f"Unknown channel: {channel}")
            # Add placeholder for unknown channel
            async def unknown_channel():
                return {
                    "channel": channel,
                    "status": "error",
                    "error": f"Unknown channel: {channel}"
                }
            tasks.append(unknown_channel())
            channel_names.append(channel)

    if not tasks:
        logger.warning(
            f"No channels enabled for event {event.event_id}. "
            f"Channels: {event.channels}"
        )
        return []

    # T150: Execute all channels in parallel with asyncio.gather
    # T154: return_exceptions=True ensures one failure doesn't stop others
    logger.info(
        f"Sending to {len(tasks)} channels in parallel: {channel_names} "
        f"(event_id={event.event_id})"
    )

    from datetime import datetime
    from zoneinfo import ZoneInfo
    start_time = datetime.now(ZoneInfo("UTC"))

    handler_results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = datetime.now(ZoneInfo("UTC"))
    duration_ms = (end_time - start_time).total_seconds() * 1000

    # Process results
    results = []
    success_count = 0
    failed_count = 0

    for channel_name, result in zip(channel_names, handler_results):
        if isinstance(result, Exception):
            # T154: One channel fails, others still deliver
            logger.error(
                f"Channel '{channel_name}' failed: {result}",
                extra={
                    "event_id": event.event_id,
                    "channel": channel_name
                },
                exc_info=True
            )
            failed_count += 1
            results.append({
                "channel": channel_name,
                "status": "error",
                "error": str(result)
            })
        elif isinstance(result, dict):
            # Handler returned dict result
            if result.get("status") == "success":
                success_count += 1
            else:
                failed_count += 1
            results.append({"channel": channel_name, **result})
        else:
            # Unknown result type
            logger.warning(
                f"Unexpected result type from channel '{channel_name}': {type(result)}"
            )
            failed_count += 1
            results.append({
                "channel": channel_name,
                "status": "error",
                "error": f"Unexpected result type: {type(result)}"
            })

    # T153: Log multi-channel delivery summary
    logger.info(
        f"Multi-channel delivery complete: "
        f"event_id={event.event_id}, "
        f"channels={len(channel_names)}, "
        f"success={success_count}, "
        f"failed={failed_count}, "
        f"duration={duration_ms:.2f}ms"
    )

    return results


async def _send_email_wrapper(event: ReminderEvent) -> Dict[str, Any]:
    """Wrapper for email notification handler.

    Placeholder - email handler will be implemented in future task.
    """
    try:
        # Import here to avoid circular dependency
        from notification_handlers.email_handler import send_email_reminder
        result = await send_email_reminder(event)
        return {"status": "success", **result}
    except ImportError:
        logger.info(
            f"Email notification handler not yet implemented (event_id={event.event_id})"
        )
        return {
            "status": "skipped",
            "error": "Email handler not yet implemented"
        }
    except Exception as e:
        logger.error(
            f"Email notification error: {e}",
            extra={"event_id": event.event_id},
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(e)
        }


async def _send_push_wrapper(event: ReminderEvent) -> Dict[str, Any]:
    """Wrapper for push notification handler."""
    try:
        # Import here to avoid circular dependency
        from notification_handlers.push_handler import send_push_reminder

        # TODO: Fetch user's FCM token from database
        # For now, use None (handler will skip if no token)
        fcm_token = None

        result = await send_push_reminder(
            event=event,
            firebase_app=None,  # Uses default Firebase app
            fcm_token=fcm_token
        )

        # Convert NotificationLogEntry to dict
        return {
            "status": result.status,
            "sent_at": result.sent_at.isoformat() if result.sent_at else None,
            "error": result.error_message
        }

    except Exception as e:
        logger.error(
            f"Push notification error: {e}",
            extra={"event_id": event.event_id},
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(e)
        }


async def _send_in_app_wrapper(event: ReminderEvent) -> Dict[str, Any]:
    """Wrapper for in-app notification handler."""
    try:
        # Import here to avoid circular dependency
        from notification_handlers.in_app_handler import send_in_app_reminder

        # TODO: Get database session from dependency injection
        # For now, return skipped (handler needs database)
        logger.warning(
            f"In-app notification requires database session "
            f"(event_id={event.event_id}). Skipping."
        )

        return {
            "status": "skipped",
            "error": "Database session not available in consumer"
        }

    except Exception as e:
        logger.error(
            f"In-app notification error: {e}",
            extra={"event_id": event.event_id},
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(e)
        }


async def consume_reminder_events():
    """Main function to consume reminder events (T096).

    This is the entry point called from main.py lifespan.
    """
    logger.info("Starting reminder events consumer...")

    consumer_service = KafkaConsumerService()

    try:
        await consumer_service.start()
        await consumer_service.consume_loop()

    except asyncio.CancelledError:
        logger.info("Consumer cancelled, shutting down...")
    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
    finally:
        await consumer_service.stop()
        logger.info("Consumer stopped")


# Utility function for processing (used in tests)
async def process_reminder_event(event_data: Dict[str, Any]) -> bool:
    """Process a single reminder event (utility function).

    Args:
        event_data: Event data dictionary

    Returns:
        bool: True if processed successfully
    """
    try:
        event = ReminderEvent(**event_data)
        results = await route_to_handlers(event)
        return all(r.get("status") == "success" for r in results)
    except Exception as e:
        logger.error(f"Failed to process event: {e}", exc_info=True)
        return False
