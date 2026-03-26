"""In-App Notification Handler

Stores in-app notifications in database for display in frontend.

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
Tasks: T146-T149
"""

import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ..schemas import ReminderEvent, NotificationLogEntry

logger = logging.getLogger(__name__)


class InAppNotificationError(Exception):
    """Raised when in-app notification fails."""
    pass


async def send_in_app_reminder(
    event: ReminderEvent,
    db=None
) -> NotificationLogEntry:
    """Send in-app notification by storing in database.

    Implements:
    - T147: Main send_in_app_reminder function
    - T148: Database storage with InAppNotification table
    - T149: NotificationLog creation

    Args:
        event: ReminderEvent with task details
        db: Database session (SQLModel Session)

    Returns:
        NotificationLogEntry with delivery status

    Raises:
        InAppNotificationError: If database operation fails
    """
    logger.info(
        f"Sending in-app notification: task_id={event.task_id}, "
        f"user_id={event.user_id}, reminder_type={event.reminder_type}"
    )

    # T148: Check for existing notification with same event_id (idempotency)
    if db is not None:
        try:
            # Import InAppNotification model
            from ..models import InAppNotification

            # Check if notification with this event_id already exists
            existing = db.query(InAppNotification).filter(
                InAppNotification.event_id == event.event_id
            ).first()

            if existing:
                logger.info(
                    f"In-app notification already exists for event_id={event.event_id}. "
                    f"Skipping duplicate creation (idempotency)."
                )
                # T149: Return successful NotificationLog (already sent)
                return NotificationLogEntry(
                    task_id=event.task_id,
                    user_id=event.user_id,
                    reminder_type=event.reminder_type,
                    channel="in_app",
                    status="success",
                    sent_at=existing.created_at,
                    error_message=None,
                    event_id=event.event_id
                )
        except Exception as e:
            logger.warning(
                f"Failed to check for existing in-app notification: {e}. "
                f"Proceeding with creation."
            )

    # T148: Build in-app notification title and message
    notification_title, notification_message = _build_in_app_content(event)

    # T148: Store notification in database
    try:
        if db is None:
            # No database provided - cannot store in-app notification
            logger.error("No database session provided for in-app notification")
            return NotificationLogEntry(
                task_id=event.task_id,
                user_id=event.user_id,
                reminder_type=event.reminder_type,
                channel="in_app",
                status="failed",
                sent_at=datetime.now(ZoneInfo("UTC")),
                error_message="No database session provided",
                event_id=event.event_id
            )

        # Import InAppNotification model
        from ..models import InAppNotification

        # Create in-app notification record
        in_app_notification = InAppNotification(
            user_id=event.user_id,
            task_id=event.task_id,
            title=notification_title,
            message=notification_message,
            reminder_type=event.reminder_type,
            is_read=False,
            created_at=datetime.now(ZoneInfo("UTC")),
            event_id=event.event_id
        )

        # Save to database
        db.add(in_app_notification)
        db.commit()
        db.refresh(in_app_notification)

        logger.info(
            f"In-app notification stored successfully: "
            f"task_id={event.task_id}, notification_id={in_app_notification.id}"
        )

        # T149: Return successful NotificationLog
        return NotificationLogEntry(
            task_id=event.task_id,
            user_id=event.user_id,
            reminder_type=event.reminder_type,
            channel="in_app",
            status="success",
            sent_at=in_app_notification.created_at,
            error_message=None,
            event_id=event.event_id
        )

    except Exception as e:
        logger.error(
            f"In-app notification database storage failed: "
            f"task_id={event.task_id}, error={str(e)}",
            exc_info=True
        )

        # T149: Return failed NotificationLog
        return NotificationLogEntry(
            task_id=event.task_id,
            user_id=event.user_id,
            reminder_type=event.reminder_type,
            channel="in_app",
            status="failed",
            sent_at=datetime.now(ZoneInfo("UTC")),
            error_message=f"Database storage failed: {str(e)}",
            event_id=event.event_id
        )


def _build_in_app_content(event: ReminderEvent) -> tuple[str, str]:
    """Build in-app notification title and message (T148).

    Title Format:
    - 1h reminder: "[URGENT] Reminder: {task_title}"
    - Other: "Reminder: {task_title}"

    Message Format:
    - 1h reminder: "⚠️ Your task '{task_title}' is due in 1 HOUR at {due_date_formatted}"
    - 24h reminder: "Your task '{task_title}' is due in 24 hours at {due_date_formatted}"
    - Custom (3d): "Your task '{task_title}' is due in 3 days at {due_date_formatted}"

    Args:
        event: ReminderEvent with task details

    Returns:
        Tuple of (title, message)
    """
    # Determine urgency (1h reminders are urgent)
    is_urgent = event.reminder_type == "1h"
    urgency_prefix = "[URGENT] " if is_urgent else ""

    # Build title
    title = f"{urgency_prefix}Reminder: {event.task_title}"

    # Build message with human-readable interval
    interval_text = _format_interval(event.reminder_type, is_urgent)

    # Add urgency emoji for 1h reminders
    urgency_emoji = "⚠️ " if is_urgent else ""

    # Format due date for human readability
    try:
        due_date_obj = datetime.fromisoformat(event.due_date.replace('Z', '+00:00'))
        due_date_formatted = due_date_obj.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        due_date_formatted = event.due_date  # Fallback to raw ISO format

    # Build message
    message = (
        f"{urgency_emoji}Your task '{event.task_title}' is due in {interval_text} "
        f"at {due_date_formatted}"
    )

    # Add description if available (optional context)
    if event.task_description:
        message += f" - {event.task_description}"

    return title, message


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
