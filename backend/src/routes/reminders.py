"""Reminders Routes

Internal endpoints for reminder checking triggered by Dapr cron binding.

Phase V - Due Dates & Reminders
User Story 2: 24-Hour Advance Reminder
"""

import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.db import get_session
from src.services.reminder_service import get_tasks_needing_reminders, should_send_reminder
from src.services.kafka_producer_service import publish_reminder_event
from src.models import Task, User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/internal/dapr",
    tags=["internal", "dapr", "reminders"]
)


def _get_enabled_channels(user_id: str, db: Session) -> list[str]:
    """Get enabled notification channels from user preferences (T152).

    Args:
        user_id: User ID to fetch preferences for
        db: Database session

    Returns:
        List of enabled channel names (e.g., ["email", "in_app"])

    Default channels if user not found or no preferences:
        ["email", "in_app"]  (push disabled by default)
    """
    try:
        # Query user from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(
                f"User not found for user_id={user_id}. "
                f"Using default channels: email, in_app"
            )
            return ["email", "in_app"]

        # Get notification preferences (defaults to {"email": True, "push": False, "in_app": True})
        preferences = user.notification_preferences or {}

        # Build list of enabled channels
        enabled_channels = []

        if preferences.get("email", True):  # Default: enabled
            enabled_channels.append("email")

        if preferences.get("push", False):  # Default: disabled
            enabled_channels.append("push")

        if preferences.get("in_app", True):  # Default: enabled
            enabled_channels.append("in_app")

        # T157: Ensure at least one channel is enabled
        if not enabled_channels:
            logger.warning(
                f"User {user_id} has all channels disabled. "
                f"Enabling email and in_app by default."
            )
            enabled_channels = ["email", "in_app"]

        logger.debug(
            f"User {user_id} notification channels: {enabled_channels}"
        )

        return enabled_channels

    except Exception as e:
        logger.error(
            f"Failed to get user notification preferences for user_id={user_id}: {e}",
            exc_info=True
        )
        # Fallback to default channels
        return ["email", "in_app"]


@router.post("/reminder-check")
async def reminder_check_endpoint(
    db: Session = Depends(get_session)
):
    """Check tasks and send reminders via Kafka.

    This endpoint is triggered by Dapr cron binding every 5 minutes.

    Implements:
    - T079: POST /api/internal/dapr/reminder-check endpoint
    - T080: Call reminder_service.get_tasks_needing_reminders()
    - T081: Loop through tasks, publish reminder events for pending intervals
    - T082: Update task.reminder_sent field after publishing
    - T083: Add structured logging (tasks_checked, reminders_sent, duration_ms)
    - T084: Error handling (database errors, Kafka errors)

    Flow:
    1. Get current time (UTC)
    2. Query tasks with due dates (not completed)
    3. For each task, check each reminder interval
    4. If reminder should be sent:
       a. Publish event to Kafka
       b. Update task.reminder_sent field
       c. Commit to database
    5. Log metrics and return summary

    Returns:
        JSON response with metrics:
        - tasks_checked: Number of tasks checked
        - reminders_sent: Number of reminders sent
        - duration_ms: Execution time in milliseconds
    """
    start_time = time.time()
    current_time = datetime.now(ZoneInfo("UTC"))

    tasks_checked = 0
    reminders_sent = 0
    errors = []

    logger.info(f"Reminder check started at {current_time}")

    try:
        # T080: Get tasks needing reminders
        tasks = get_tasks_needing_reminders(db, current_time)
        tasks_checked = len(tasks)

        logger.info(f"Found {tasks_checked} tasks with due dates to check")

        # T081: Loop through tasks and check intervals
        for task in tasks:
            try:
                # Get reminder intervals for this task
                intervals = task.remind_before or []

                for interval in intervals:
                    try:
                        # Check if reminder should be sent for this interval
                        if should_send_reminder(task, interval, current_time):
                            logger.info(
                                f"Sending reminder: task_id={task.id}, "
                                f"interval={interval}, user_id={task.user_id}"
                            )

                            # T152: Determine notification channels from user preferences
                            channels = _get_enabled_channels(task.user_id, db)

                            # Publish event to Kafka
                            event_id = await publish_reminder_event(
                                task=task,
                                reminder_type=interval,
                                channels=channels
                            )

                            # T082: Update task.reminder_sent field
                            if not task.reminder_sent:
                                task.reminder_sent = {}

                            task.reminder_sent[interval] = current_time.isoformat()

                            # Commit update to database
                            db.add(task)
                            db.commit()
                            db.refresh(task)

                            reminders_sent += 1

                            logger.info(
                                f"Reminder sent successfully: event_id={event_id}, "
                                f"task_id={task.id}, interval={interval}"
                            )

                    except Exception as e:
                        # T084: Error handling for Kafka errors
                        error_msg = (
                            f"Failed to send reminder for task_id={task.id}, "
                            f"interval={interval}: {str(e)}"
                        )
                        logger.error(error_msg, exc_info=True)
                        errors.append(error_msg)
                        # Continue processing other intervals/tasks

            except Exception as e:
                # T084: Error handling for task processing errors
                error_msg = (
                    f"Failed to process task_id={task.id}: {str(e)}"
                )
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                # Continue processing other tasks

    except Exception as e:
        # T084: Error handling for database errors
        error_msg = f"Failed to query tasks: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append(error_msg)

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # T083: Structured logging with metrics
    logger.info(
        f"Reminder check completed: "
        f"tasks_checked={tasks_checked}, "
        f"reminders_sent={reminders_sent}, "
        f"duration_ms={duration_ms}, "
        f"errors={len(errors)}"
    )

    # Return metrics
    return {
        "status": "success" if len(errors) == 0 else "partial_success",
        "tasks_checked": tasks_checked,
        "reminders_sent": reminders_sent,
        "duration_ms": duration_ms,
        "errors": errors if len(errors) > 0 else None,
        "timestamp": current_time.isoformat()
    }
