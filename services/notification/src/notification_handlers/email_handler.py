"""Email Notification Handler

Sends email reminders via SendGrid with retry logic, idempotency, and database logging.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
Tasks: T104-T110
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from zoneinfo import ZoneInfo

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

import sys
sys.path.insert(0, '/Users/apple/Documents/Projects/todo_phase5/backend/src')
from models import NotificationLog, User
from db import engine

sys.path.insert(0, '/Users/apple/Documents/Projects/todo_phase5/services/notification/src')
from config import settings
from kafka_consumer import ReminderEvent

logger = logging.getLogger(__name__)

# Retry configuration (T108)
MAX_RETRIES = settings.retry_attempts
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s


def get_db():
    """Get database session."""
    return Session(engine)


async def check_idempotency(event_id: str) -> bool:
    """Check if event has already been processed (T110).

    Args:
        event_id: Unique event ID

    Returns:
        bool: True if already processed (duplicate), False if new
    """
    try:
        with get_db() as db:
            # Query notification_logs for event_id
            existing = db.exec(
                select(NotificationLog).where(
                    NotificationLog.event_id == event_id
                )
            ).first()

            if existing:
                logger.info(
                    f"Duplicate event detected (already processed): event_id={event_id}"
                )
                return True

            return False

    except Exception as e:
        logger.error(f"Failed to check idempotency: {e}", exc_info=True)
        # On error, assume not duplicate (safer to send duplicate than miss notification)
        return False


async def get_user_email(user_id: str) -> str | None:
    """Get user email address from database.

    Args:
        user_id: User database ID

    Returns:
        Email address or None if not found
    """
    try:
        with get_db() as db:
            user = db.exec(
                select(User).where(User.id == user_id)
            ).first()

            if user and user.email:
                return user.email

            logger.warning(f"User email not found: user_id={user_id}")
            return None

    except Exception as e:
        logger.error(f"Failed to get user email: {e}", exc_info=True)
        return None


def create_email_template(event: ReminderEvent) -> Tuple[str, str]:
    """Create email subject and body (T107).

    Args:
        event: Reminder event

    Returns:
        Tuple of (subject, body)
    """
    # Parse due date
    try:
        due_date = datetime.fromisoformat(event.due_date.replace('Z', '+00:00'))
        formatted_due = due_date.strftime("%B %d, %Y at %I:%M %p UTC")
    except:
        formatted_due = event.due_date

    # Create subject with urgency indicator (T107, T119)
    if event.reminder_type == "24h":
        time_before = "24 hours"
        urgency_prefix = ""
        urgency_level = "advance notice"
    elif event.reminder_type == "1h":
        time_before = "1 hour"
        urgency_prefix = "[URGENT] "  # T119: Urgency indicator for 1h reminders
        urgency_level = "final reminder"
    else:
        time_before = event.reminder_type
        urgency_prefix = ""
        urgency_level = "reminder"

    subject = f"{urgency_prefix}Reminder: Task '{event.task_title}' due in {time_before}"

    # Create body with urgency messaging (T107, T119)
    urgency_message = ""
    if event.reminder_type == "1h":
        urgency_message = "\n⚠️  URGENT: This task is due in 1 HOUR!\n"

    body = f"""
Hello,
{urgency_message}
This is a {urgency_level} that your task is due soon:

Task: {event.task_title}
{f'Description: {event.task_description}' if event.task_description else ''}
Due Date: {formatted_due}
Time Remaining: {time_before}

Please make sure to complete this task before the due date.

Best regards,
Todo App Reminders

---
This is an automated reminder. You can manage your notification preferences in the app settings.
    """.strip()

    return subject, body


async def log_notification(
    event: ReminderEvent,
    channel: str,
    status: str,
    sent_at: datetime,
    error_message: str | None = None
) -> NotificationLog:
    """Log notification to notification_logs table (T109).

    Args:
        event: Reminder event
        channel: Notification channel (email, push, in_app)
        status: Status (success, failed)
        sent_at: Timestamp when notification was sent
        error_message: Error message if failed

    Returns:
        NotificationLog: Created log entry
    """
    try:
        with get_db() as db:
            # Create notification log (T109)
            notification_log = NotificationLog(
                task_id=event.task_id,
                user_id=event.user_id,
                reminder_type=event.reminder_type,
                channel=channel,
                status=status,
                sent_at=sent_at,
                error_message=error_message,
                event_id=event.event_id  # For idempotency (T110)
            )

            db.add(notification_log)
            db.commit()
            db.refresh(notification_log)

            logger.info(
                f"Notification logged: id={notification_log.id}, "
                f"event_id={event.event_id}, status={status}"
            )

            return notification_log

    except IntegrityError as e:
        # T110: Unique constraint on event_id violated (duplicate)
        logger.warning(
            f"Duplicate event_id detected (unique constraint): event_id={event.event_id}"
        )
        raise
    except Exception as e:
        logger.error(f"Failed to log notification: {e}", exc_info=True)
        raise


async def send_email_reminder(event: ReminderEvent) -> Dict[str, Any]:
    """Send email reminder via SendGrid (T105, T106, T108, T109, T110).

    Implements:
    - T105: send_email_reminder function
    - T106: SendGrid API integration
    - T107: Email template
    - T108: Retry logic (3 attempts, exponential backoff)
    - T109: Log to notification_logs table
    - T110: Check event_id uniqueness (idempotency)

    Args:
        event: Reminder event

    Returns:
        Dict with status, notification_id, error
    """
    # T110: Check idempotency first
    if await check_idempotency(event.event_id):
        logger.info(f"Skipping duplicate event: event_id={event.event_id}")
        return {
            "status": "skipped",
            "reason": "duplicate_event_id",
            "event_id": event.event_id
        }

    # Get user email address
    recipient_email = await get_user_email(event.user_id)
    if not recipient_email:
        error_msg = f"User email not found for user_id={event.user_id}"
        logger.error(error_msg)

        # Log failure
        await log_notification(
            event=event,
            channel="email",
            status="failed",
            sent_at=datetime.utcnow(),
            error_message=error_msg
        )

        return {
            "status": "error",
            "error": error_msg
        }

    # T107: Create email template
    subject, body = create_email_template(event)

    # T106: Send via SendGrid with T108: Retry logic
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Sending email (attempt {attempt}/{MAX_RETRIES}): "
                f"event_id={event.event_id}, to={recipient_email}"
            )

            # Create SendGrid message (T106)
            message = Mail(
                from_email=Email(settings.sendgrid_from_email, settings.sendgrid_from_name),
                to_emails=To(recipient_email),
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )

            # Send via SendGrid API (T106)
            sg = SendGridAPIClient(settings.sendgrid_api_key)
            response = sg.send(message)

            # Check response status
            if response.status_code in [200, 202]:
                logger.info(
                    f"Email sent successfully: event_id={event.event_id}, "
                    f"status_code={response.status_code}"
                )

                # T109: Log success to database
                notification_log = await log_notification(
                    event=event,
                    channel="email",
                    status="success",
                    sent_at=datetime.utcnow(),
                    error_message=None
                )

                return {
                    "status": "success",
                    "notification_id": notification_log.id,
                    "channel": "email",
                    "recipient": recipient_email
                }

            else:
                raise Exception(f"SendGrid returned status {response.status_code}")

        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"Email send failed (attempt {attempt}/{MAX_RETRIES}): {e}",
                exc_info=True
            )

            if attempt < MAX_RETRIES:
                # T108: Exponential backoff
                delay = RETRY_DELAYS[attempt - 1]
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                # Max retries exceeded
                logger.error(
                    f"Email send failed after {MAX_RETRIES} attempts: "
                    f"event_id={event.event_id}, error={last_error}"
                )

                # T109: Log failure to database
                await log_notification(
                    event=event,
                    channel="email",
                    status="failed",
                    sent_at=datetime.utcnow(),
                    error_message=last_error
                )

                return {
                    "status": "error",
                    "error": last_error,
                    "attempts": MAX_RETRIES
                }

    # Should never reach here
    return {
        "status": "error",
        "error": "Unexpected error in send_email_reminder"
    }
