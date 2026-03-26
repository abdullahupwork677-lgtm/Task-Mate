"""Push Notification Handler

Sends push notifications via Firebase Cloud Messaging (FCM).

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
Tasks: T139-T144
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

try:
    import firebase_admin
    from firebase_admin import messaging, credentials
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not installed. Push notifications disabled.")

from ..schemas import ReminderEvent, NotificationLogEntry

logger = logging.getLogger(__name__)


class PushNotificationError(Exception):
    """Raised when push notification fails after all retries."""
    pass


# Retry configuration (T143)
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [1, 2, 4]  # Exponential backoff


async def send_push_reminder(
    event: ReminderEvent,
    firebase_app=None,
    fcm_token: Optional[str] = None
) -> NotificationLogEntry:
    """Send push notification reminder via Firebase Cloud Messaging.

    Implements:
    - T140: Main send_push_reminder function
    - T141: Firebase Cloud Messaging integration
    - T142: Push payload structure (title, body, data)
    - T143: Retry logic with exponential backoff (3 attempts)
    - T144: NotificationLog creation

    Args:
        event: ReminderEvent with task details
        firebase_app: Firebase Admin SDK app (optional, uses default if None)
        fcm_token: User's FCM device token (if None, will be fetched from DB)

    Returns:
        NotificationLogEntry with delivery status

    Raises:
        PushNotificationError: If all retry attempts fail
    """
    logger.info(
        f"Sending push notification: task_id={event.task_id}, "
        f"user_id={event.user_id}, reminder_type={event.reminder_type}"
    )

    # T141: Check Firebase availability
    if not FIREBASE_AVAILABLE:
        logger.error("Firebase Admin SDK not available")
        return NotificationLogEntry(
            task_id=event.task_id,
            user_id=event.user_id,
            reminder_type=event.reminder_type,
            channel="push",
            status="failed",
            sent_at=datetime.now(ZoneInfo("UTC")),
            error_message="Firebase Admin SDK not installed",
            event_id=event.event_id
        )

    # T141: Get user's FCM token (from database or parameter)
    if not fcm_token:
        # TODO: Query user's FCM token from database
        # For now, log error and skip
        logger.warning(
            f"No FCM token provided for user {event.user_id}. "
            f"Push notification skipped."
        )
        return NotificationLogEntry(
            task_id=event.task_id,
            user_id=event.user_id,
            reminder_type=event.reminder_type,
            channel="push",
            status="skipped",
            sent_at=datetime.now(ZoneInfo("UTC")),
            error_message="No FCM token available for user",
            event_id=event.event_id
        )

    # T142: Build push notification payload
    notification_title, notification_body = _build_push_payload(event)
    notification_data = {
        "task_id": str(event.task_id),
        "due_date": event.due_date,
        "priority": event.priority,
        "reminder_type": event.reminder_type,
        "event_id": event.event_id
    }

    # T143: Retry logic with exponential backoff
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                f"Push notification attempt {attempt + 1}/{MAX_RETRIES}: "
                f"task_id={event.task_id}, user_id={event.user_id}"
            )

            # T141: Send via Firebase Cloud Messaging
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification_title,
                    body=notification_body
                ),
                data=notification_data,
                token=fcm_token
            )

            # Send message
            response = messaging.send(message, app=firebase_app)

            logger.info(
                f"Push notification sent successfully: "
                f"task_id={event.task_id}, response={response}"
            )

            # T144: Return successful NotificationLog
            return NotificationLogEntry(
                task_id=event.task_id,
                user_id=event.user_id,
                reminder_type=event.reminder_type,
                channel="push",
                status="success",
                sent_at=datetime.now(ZoneInfo("UTC")),
                error_message=None,
                event_id=event.event_id
            )

        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"Push notification attempt {attempt + 1} failed: "
                f"task_id={event.task_id}, error={last_error}"
            )

            # T143: Exponential backoff (if not last attempt)
            if attempt < MAX_RETRIES - 1:
                backoff_seconds = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Retrying in {backoff_seconds}s...")
                await asyncio.sleep(backoff_seconds)

    # T144: All retries failed - return failed NotificationLog
    logger.error(
        f"Push notification failed after {MAX_RETRIES} attempts: "
        f"task_id={event.task_id}, error={last_error}"
    )

    return NotificationLogEntry(
        task_id=event.task_id,
        user_id=event.user_id,
        reminder_type=event.reminder_type,
        channel="push",
        status="failed",
        sent_at=datetime.now(ZoneInfo("UTC")),
        error_message=f"Failed after {MAX_RETRIES} retries: {last_error}",
        event_id=event.event_id
    )


def _build_push_payload(event: ReminderEvent) -> tuple[str, str]:
    """Build push notification title and body (T142).

    Title Format:
    - 1h reminder: "[URGENT] Reminder: {task_title}"
    - Other: "Reminder: {task_title}"

    Body Format:
    - 1h reminder: "⚠️ Due in 1 HOUR - {task_description}"
    - 24h reminder: "Due in 24 hours - {task_description}"
    - Custom (3d): "Due in 3 days - {task_description}"

    Args:
        event: ReminderEvent with task details

    Returns:
        Tuple of (title, body)
    """
    # Determine urgency (1h reminders are urgent)
    is_urgent = event.reminder_type == "1h"
    urgency_prefix = "[URGENT] " if is_urgent else ""

    # Build title
    title = f"{urgency_prefix}Reminder: {event.task_title}"

    # Build body with human-readable interval
    interval_text = _format_interval(event.reminder_type, is_urgent)

    # Add urgency emoji for 1h reminders
    urgency_emoji = "⚠️  " if is_urgent else ""

    # Include description if available
    description_text = event.task_description if event.task_description else event.task_title

    body = f"{urgency_emoji}Due in {interval_text} - {description_text}"

    return title, body


def _format_interval(interval: str, is_urgent: bool = False) -> str:
    """Format interval for human-readable notification text.

    Args:
        interval: Interval string (e.g., "24h", "3d", "1h")
        is_urgent: If True, use UPPERCASE for urgency

    Returns:
        Human-readable interval (e.g., "24 hours", "3 days", "1 HOUR")

    Examples:
        >>> _format_interval("24h")
        "24 hours"
        >>> _format_interval("1h", is_urgent=True)
        "1 HOUR"
        >>> _format_interval("3d")
        "3 days"
        >>> _format_interval("30m")
        "30 minutes"
    """
    # Parse interval
    import re
    pattern = r'^(\d+)([mhdw])$'
    match = re.match(pattern, interval)

    if not match:
        return interval  # Return as-is if can't parse

    amount = int(match.group(1))
    unit = match.group(2)

    # Map to human-readable units
    unit_map = {
        'm': 'minute' if amount == 1 else 'minutes',
        'h': 'hour' if amount == 1 else 'hours',
        'd': 'day' if amount == 1 else 'days',
        'w': 'week' if amount == 1 else 'weeks'
    }

    unit_text = unit_map.get(unit, interval)
    result = f"{amount} {unit_text}"

    # Uppercase for urgency (1h reminders)
    if is_urgent:
        result = result.upper()

    return result
