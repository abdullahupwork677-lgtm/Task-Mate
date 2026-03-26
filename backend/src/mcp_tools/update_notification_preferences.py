"""MCP Tool: Update Notification Preferences

Allows AI agent to update user's notification channel preferences.

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
Task: T158
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import Session

from src.models import User

logger = logging.getLogger(__name__)


class UpdateNotificationPreferencesParams(BaseModel):
    """Parameters for update_notification_preferences MCP tool (T158).

    Fields:
        user_id: User ID (automatically provided by agent)
        email: Enable/disable email notifications (optional)
        push: Enable/disable push notifications (optional)
        in_app: Enable/disable in-app notifications (optional)

    At least one field must be provided.
    """

    user_id: str = Field(description="User ID (automatically provided)")
    email: Optional[bool] = Field(
        default=None,
        description="Enable/disable email notifications. Leave None to keep current setting."
    )
    push: Optional[bool] = Field(
        default=None,
        description="Enable/disable push notifications. Leave None to keep current setting."
    )
    in_app: Optional[bool] = Field(
        default=None,
        description="Enable/disable in-app notifications. Leave None to keep current setting."
    )


class UpdateNotificationPreferencesResult(BaseModel):
    """Result from update_notification_preferences MCP tool (T158)."""

    success: bool
    message: str
    email: bool
    push: bool
    in_app: bool


class NotificationPreferencesError(Exception):
    """Raised when notification preferences update fails."""
    pass


def update_notification_preferences(
    params: UpdateNotificationPreferencesParams,
    db: Session
) -> UpdateNotificationPreferencesResult:
    """Update user's notification channel preferences (T158).

    Implements:
    - T158: Chatbot command to update notification preferences
    - T157: Validate at least one channel must be enabled

    Args:
        params: UpdateNotificationPreferencesParams with user_id and preferences
        db: Database session

    Returns:
        UpdateNotificationPreferencesResult with updated preferences

    Raises:
        NotificationPreferencesError: If user not found or all channels disabled

    Examples:
        >>> # Turn off email reminders
        >>> result = update_notification_preferences(
        ...     UpdateNotificationPreferencesParams(
        ...         user_id="user-123",
        ...         email=False
        ...     ),
        ...     db
        ... )
        >>> result.message
        "Notification preferences updated. Email notifications disabled."

        >>> # Enable push notifications
        >>> result = update_notification_preferences(
        ...     UpdateNotificationPreferencesParams(
        ...         user_id="user-123",
        ...         push=True
        ...     ),
        ...     db
        ... )
        >>> result.message
        "Notification preferences updated. Push notifications enabled."
    """
    logger.info(
        f"Updating notification preferences for user {params.user_id}: "
        f"email={params.email}, push={params.push}, in_app={params.in_app}"
    )

    # Fetch user from database
    user = db.get(User, params.user_id)
    if not user:
        logger.error(f"User not found: {params.user_id}")
        raise NotificationPreferencesError(f"User not found: {params.user_id}")

    # Get current preferences
    current_preferences = user.notification_preferences or {
        "email": True,
        "push": False,
        "in_app": True
    }

    # Update only provided fields
    new_preferences = {
        "email": params.email if params.email is not None else current_preferences.get("email", True),
        "push": params.push if params.push is not None else current_preferences.get("push", False),
        "in_app": params.in_app if params.in_app is not None else current_preferences.get("in_app", True)
    }

    # T157: Validate at least one channel is enabled
    if not new_preferences["email"] and not new_preferences["push"] and not new_preferences["in_app"]:
        logger.warning(
            f"User {params.user_id} attempted to disable all notification channels"
        )
        raise NotificationPreferencesError(
            "At least one notification channel must be enabled. "
            "You cannot disable all channels."
        )

    # Update user preferences
    user.notification_preferences = new_preferences

    # Save to database
    db.add(user)
    db.commit()
    db.refresh(user)

    # Build human-readable message
    changes = []
    if params.email is not None:
        status = "enabled" if params.email else "disabled"
        changes.append(f"Email notifications {status}")
    if params.push is not None:
        status = "enabled" if params.push else "disabled"
        changes.append(f"Push notifications {status}")
    if params.in_app is not None:
        status = "enabled" if params.in_app else "disabled"
        changes.append(f"In-app notifications {status}")

    if changes:
        message = f"Notification preferences updated. {'. '.join(changes)}."
    else:
        message = "No changes made to notification preferences."

    logger.info(
        f"Successfully updated notification preferences for user {params.user_id}: "
        f"{new_preferences}"
    )

    return UpdateNotificationPreferencesResult(
        success=True,
        message=message,
        email=new_preferences["email"],
        push=new_preferences["push"],
        in_app=new_preferences["in_app"]
    )
