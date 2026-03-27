"""In-App Notifications Routes

API endpoints for fetching and managing in-app notifications.

Phase V - Due Dates & Reminders
User Story 5: Multi-Channel Notifications
Tasks: T160, T162
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, and_
from sqlalchemy import text
from pydantic import BaseModel

from src.db import get_session
from src.auth import get_current_user
from src.models import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["in-app-notifications"]
)


# T160: Import InAppNotification model
# Note: This will be imported from notification service models
# For now, we'll create a placeholder Pydantic model
class InAppNotificationResponse(BaseModel):
    """Response model for in-app notifications (T160)."""

    id: int
    user_id: str
    task_id: int
    title: str
    message: str
    reminder_type: str
    is_read: bool
    created_at: str
    event_id: str

    class Config:
        from_attributes = True


@router.get("/{user_id}/notifications", response_model=List[InAppNotificationResponse])
def get_in_app_notifications(
    user_id: str,
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> List[InAppNotificationResponse]:
    """Get user's in-app notifications (T160).

    Args:
        user_id: User ID to fetch notifications for
        limit: Maximum number of notifications to return (default: 50)
        unread_only: If True, only return unread notifications
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        List of InAppNotificationResponse objects

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If user not found
    """
    # User isolation: Only allow users to access their own notifications
    if current_user.id != user_id:
        logger.warning(
            f"User {current_user.id} attempted to access notifications for user {user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only access your own notifications"
        )

    # Fetch user from database
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # T160: Query in-app notifications
    # Note: InAppNotification table is in notification service database
    # For Phase V implementation, we'll need to either:
    # 1. Query notification service API
    # 2. Use shared database connection
    # 3. Sync notifications to main database
    #
    # For now, we'll create a placeholder that returns empty list
    # This should be replaced with actual database query:
    #
    # try:
    #     from notification_service.models import InAppNotification
    #
    #     query = (
    #         select(InAppNotification)
    #         .where(InAppNotification.user_id == user_id)
    #         .order_by(InAppNotification.created_at.desc())
    #         .limit(limit)
    #     )
    #
    #     if unread_only:
    #         query = query.where(InAppNotification.is_read == False)
    #
    #     notifications = db.exec(query).all()
    #     return [InAppNotificationResponse.model_validate(n) for n in notifications]
    #
    # except Exception as e:
    #     logger.error(f"Failed to fetch notifications: {e}", exc_info=True)
    #     raise HTTPException(status_code=500, detail="Failed to fetch notifications")

    logger.info(
        f"Fetching in-app notifications for user {user_id}: "
        f"limit={limit}, unread_only={unread_only}"
    )

    try:
        query = """
            SELECT id, user_id, task_id, title, message, reminder_type,
                   is_read, created_at, event_id
            FROM notification_logs
            WHERE user_id = :user_id AND channel = 'in_app'
            {unread_filter}
            ORDER BY created_at DESC
            LIMIT :limit
        """.format(unread_filter="AND is_read = false" if unread_only else "")

        rows = db.execute(
            text(query),
            {"user_id": user_id, "limit": limit}
        ).fetchall()

        result = []
        for row in rows:
            result.append(InAppNotificationResponse(
                id=row[0],
                user_id=str(row[1]),
                task_id=row[2],
                title=row[3] or "Reminder",
                message=row[4] or "",
                reminder_type=row[5] or "",
                is_read=row[6] or False,
                created_at=str(row[7]),
                event_id=str(row[8]),
            ))
        return result

    except Exception as e:
        logger.error(f"Failed to fetch in-app notifications: {e}", exc_info=True)
        return []


@router.patch("/{user_id}/notifications/{notification_id}/read")
def mark_notification_as_read(
    user_id: str,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> dict:
    """Mark in-app notification as read (T162).

    Args:
        user_id: User ID
        notification_id: Notification ID to mark as read
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If notification not found or doesn't belong to user
    """
    # User isolation: Only allow users to update their own notifications
    if current_user.id != user_id:
        logger.warning(
            f"User {current_user.id} attempted to update notification for user {user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only update your own notifications"
        )

    # T162: Mark notification as read
    # Note: InAppNotification table is in notification service database
    # For Phase V implementation, we'll need to either:
    # 1. Query notification service API
    # 2. Use shared database connection
    # 3. Sync notifications to main database
    #
    # For now, we'll create a placeholder that returns success
    # This should be replaced with actual database update:
    #
    # try:
    #     from notification_service.models import InAppNotification
    #
    #     notification = db.query(InAppNotification).filter(
    #         and_(
    #             InAppNotification.id == notification_id,
    #             InAppNotification.user_id == user_id
    #         )
    #     ).first()
    #
    #     if not notification:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="Notification not found"
    #         )
    #
    #     notification.is_read = True
    #     db.add(notification)
    #     db.commit()
    #
    #     logger.info(
    #         f"Marked notification {notification_id} as read for user {user_id}"
    #     )
    #
    #     return {"success": True, "message": "Notification marked as read"}
    #
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     logger.error(
    #         f"Failed to mark notification as read: {e}",
    #         exc_info=True
    #     )
    #     raise HTTPException(
    #         status_code=500,
    #         detail="Failed to update notification"
    #     )

    logger.info(
        f"Marking notification {notification_id} as read for user {user_id}"
    )

    try:
        result = db.execute(
            text("""
                UPDATE notification_logs
                SET is_read = true
                WHERE id = :id AND user_id = :user_id AND channel = 'in_app'
            """),
            {"id": notification_id, "user_id": user_id}
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"success": True, "message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update notification")
