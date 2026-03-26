"""Notification Preferences Routes

API endpoints for managing user notification channel preferences.

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
Tasks: T155-T158
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel, Field, field_validator

from src.db import get_session
from src.models import User
from src.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["notification-preferences"]
)


class NotificationPreferencesUpdate(BaseModel):
    """Request body for updating notification preferences (T155).

    Fields:
        email: Enable/disable email notifications
        push: Enable/disable push notifications
        in_app: Enable/disable in-app notifications

    Validation (T157):
        At least one channel must be enabled
    """

    email: bool = Field(description="Enable email notifications")
    push: bool = Field(description="Enable push notifications")
    in_app: bool = Field(description="Enable in-app notifications")

    @field_validator('email', 'push', 'in_app')
    @classmethod
    def validate_at_least_one_enabled(cls, v, info):
        """Validate that at least one channel is enabled (T157).

        This validator runs after all fields are set, so we can check
        if at least one is True.
        """
        # This validator runs for each field individually, so we can't check here.
        # Instead, we'll validate in the endpoint logic.
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": True,
                "push": False,
                "in_app": True
            }
        }


class NotificationPreferencesResponse(BaseModel):
    """Response body for notification preferences (T155)."""

    user_id: str
    email: bool
    push: bool
    in_app: bool

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "email": True,
                "push": False,
                "in_app": True
            }
        }


@router.get("/{user_id}/notification-preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> NotificationPreferencesResponse:
    """Get user's notification channel preferences.

    Args:
        user_id: User ID to fetch preferences for
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        NotificationPreferencesResponse with current preferences

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If user not found
    """
    # User isolation: Only allow users to access their own preferences
    if current_user.id != user_id:
        logger.warning(
            f"User {current_user.id} attempted to access preferences for user {user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only access your own notification preferences"
        )

    # Fetch user from database
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get preferences (defaults if not set)
    preferences = user.notification_preferences or {
        "email": True,
        "push": False,
        "in_app": True
    }

    return NotificationPreferencesResponse(
        user_id=user_id,
        email=preferences.get("email", True),
        push=preferences.get("push", False),
        in_app=preferences.get("in_app", True)
    )


@router.patch("/{user_id}/notification-preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    user_id: str,
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> NotificationPreferencesResponse:
    """Update user's notification channel preferences (T155, T156, T157).

    Implements:
    - T155: PATCH endpoint for updating preferences
    - T156: Update user.notification_preferences JSONB field
    - T157: Validate at least one channel must be enabled

    Args:
        user_id: User ID to update preferences for
        preferences: New notification preferences
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        NotificationPreferencesResponse with updated preferences

    Raises:
        HTTPException 400: If all channels are disabled (T157)
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If user not found
    """
    # User isolation: Only allow users to update their own preferences
    if current_user.id != user_id:
        logger.warning(
            f"User {current_user.id} attempted to update preferences for user {user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only update your own notification preferences"
        )

    # T157: Validate at least one channel is enabled
    if not preferences.email and not preferences.push and not preferences.in_app:
        logger.warning(
            f"User {user_id} attempted to disable all notification channels"
        )
        raise HTTPException(
            status_code=400,
            detail="At least one notification channel must be enabled. "
                   "You cannot disable all channels."
        )

    # Fetch user from database
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # T156: Update user.notification_preferences JSONB field
    user.notification_preferences = {
        "email": preferences.email,
        "push": preferences.push,
        "in_app": preferences.in_app
    }

    # Save to database
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(
        f"Updated notification preferences for user {user_id}: "
        f"email={preferences.email}, push={preferences.push}, in_app={preferences.in_app}"
    )

    return NotificationPreferencesResponse(
        user_id=user_id,
        email=preferences.email,
        push=preferences.push,
        in_app=preferences.in_app
    )
