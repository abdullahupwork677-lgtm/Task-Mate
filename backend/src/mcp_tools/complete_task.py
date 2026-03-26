"""MCP Tool: complete_task

Marks a task as completed for the authenticated user.

Phase V Extensions:
- Auto-creates next occurrence for recurring tasks
- US1: Clears reminder_sent field when completing (stops future reminders)

This tool enables AI agents to mark tasks as complete based on
natural language input.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from ..models import Task
from ..services.recurrence_engine import calculate_next_due_date

logger = logging.getLogger(__name__)


class CompleteTaskParams(BaseModel):
    """Input parameters for complete_task tool.

    Attributes:
        user_id: ID of the authenticated user (for isolation)
        task_id: ID of the task to mark as complete
    """

    user_id: str = Field(..., description="User ID for task ownership")
    task_id: int = Field(..., description="ID of the task to mark as complete")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {"example": {"user_id": "user-123", "task_id": 5}}


class NextOccurrenceInfo(BaseModel):
    """Information about the auto-created next occurrence."""

    task_id: int = Field(..., description="ID of the next occurrence task")
    title: str = Field(..., description="Task title")
    due_date: datetime = Field(..., description="Next occurrence due date")


class CompleteTaskResult(BaseModel):
    """Result from complete_task tool execution.

    Attributes:
        task_id: ID of the completed task
        title: Task title
        description: Task description (if any)
        completed: Task completion status (always True)
        updated_at: Timestamp when task was marked complete
        next_occurrence: Info about auto-created next occurrence (Phase V, if recurring)
    """

    task_id: int = Field(..., description="ID of the task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    completed: bool = Field(True, description="Task completion status")
    updated_at: datetime = Field(..., description="Timestamp of completion")
    next_occurrence: Optional[NextOccurrenceInfo] = Field(
        None, description="Auto-created next occurrence (Phase V - recurring tasks)"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "task_id": 5,
                "title": "Buy milk",
                "description": None,
                "completed": True,
                "updated_at": "2025-12-30T15:45:00Z",
                "next_occurrence": {
                    "task_id": 6,
                    "title": "Buy milk",
                    "due_date": "2025-12-31T15:45:00Z",
                },
            }
        }


def complete_task(db: Session, params: CompleteTaskParams) -> CompleteTaskResult:
    """Mark a task as completed. Auto-creates next occurrence for recurring tasks.

    This is the core MCP tool function that AI agents call to complete tasks.

    Phase V Enhancement:
        - If task is recurring, automatically creates next occurrence
        - Calculates next due_date based on recurrence_pattern
        - Stops recurrence if recurrence_end_date is reached
        - Handles idempotency via unique constraint

    Args:
        db: Database session
        params: Task completion parameters

    Returns:
        CompleteTaskResult with updated task details and optional next_occurrence

    Raises:
        ValueError: If task not found or doesn't belong to user

    Security:
        - Enforces user isolation: query filters by both user_id AND task_id
        - Returns generic "not found" error (doesn't reveal if task exists for other user)

    Idempotency:
        - Completing an already-completed task succeeds without error
        - Updates timestamp even if already complete
        - Unique constraint prevents duplicate next occurrences

    Example:
        >>> params = CompleteTaskParams(
        ...     user_id="user-123",
        ...     task_id=5
        ... )
        >>> result = complete_task(db, params)
        >>> assert result.completed is True
        >>> if result.next_occurrence:
        ...     print(f"Next occurrence: {result.next_occurrence.due_date}")
    """
    # Query task with user_id AND task_id
    # This enforces user isolation - users can only complete their own tasks
    query = select(Task).where(
        Task.id == params.task_id, Task.user_id == params.user_id
    )

    try:
        result = db.exec(query).first()
    except Exception as e:
        raise RuntimeError(f"Failed to query task: {str(e)}") from e

    # Handle task not found
    # Returns generic error - doesn't reveal if task exists for other user
    if not result:
        raise ValueError("Task not found")

    task = result

    # Phase 9 Edge Case: Check if task is already completed (T134)
    # Prevents re-completing older parent tasks when newer occurrence exists
    if task.completed:
        raise ValueError(
            f"Task {task.id} is already completed. "
            f"Cannot complete the same task twice."
        )

    # Update completed status and timestamp
    task.completed = True
    task.updated_at = datetime.utcnow()

    # Phase V - US1: Clear reminder_sent field (T052)
    # This prevents future reminders from being sent for completed tasks
    task.reminder_sent = {}
    logger.debug(f"Cleared reminder_sent for completed task {task.id}")

    # Persist changes to completed task
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to update task: {str(e)}") from e

    # Phase V: Auto-create next occurrence for recurring tasks
    next_occurrence_info = None
    if task.is_recurring and task.recurrence_pattern:
        try:
            next_occurrence_info = _create_next_occurrence(db, task)
            if next_occurrence_info:
                logger.info(
                    f"Created next occurrence for recurring task {task.id}: "
                    f"next_id={next_occurrence_info['task_id']}, "
                    f"due_date={next_occurrence_info['due_date']}"
                )
        except IntegrityError as e:
            # Unique constraint violation - next occurrence already exists (idempotency)
            logger.warning(
                f"Next occurrence already exists for task {task.id}: {str(e)}"
            )
            db.rollback()
            # Query existing next occurrence
            existing_query = (
                select(Task)
                .where(Task.parent_task_id == task.id, Task.completed.is_(False))  # type: ignore[attr-defined]
                .order_by(Task.due_date)  # type: ignore[arg-type]
            )
            existing = db.exec(existing_query).first()
            if existing:
                next_occurrence_info = {
                    "task_id": existing.id,
                    "title": existing.title,
                    "due_date": existing.due_date,
                }
        except Exception as e:
            # Log error but don't fail the completion
            logger.error(
                f"Failed to create next occurrence for task {task.id}: {str(e)}",
                exc_info=True,
            )
            db.rollback()

    # Return result
    return CompleteTaskResult(
        task_id=task.id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        updated_at=task.updated_at,
        next_occurrence=(
            NextOccurrenceInfo(**next_occurrence_info) if next_occurrence_info else None
        ),
    )


def _create_next_occurrence(db: Session, parent_task: Task) -> Optional[Dict[str, Any]]:
    """Create the next occurrence of a recurring task.

    Args:
        db: Database session
        parent_task: The completed recurring task

    Returns:
        Dict with next occurrence info (task_id, title, due_date) or None if recurrence ended

    Raises:
        ValueError: If recurrence pattern is invalid
        IntegrityError: If next occurrence already exists (idempotency)
    """
    # Calculate next due date
    base_date = parent_task.due_date if parent_task.due_date else datetime.utcnow()

    try:
        next_due_date = calculate_next_due_date(
            current_due_date=base_date,
            recurrence_pattern=parent_task.recurrence_pattern,
            recurrence_end_date=parent_task.recurrence_end_date,
        )
    except ValueError as e:
        logger.error(f"Invalid recurrence pattern: {str(e)}")
        raise

    # Check if recurrence has ended
    if next_due_date is None:
        logger.info(
            f"Recurrence ended for task {parent_task.id} "
            f"(end_date: {parent_task.recurrence_end_date})"
        )
        return None

    # Create next occurrence with inherited fields
    next_task = Task(
        user_id=parent_task.user_id,
        title=parent_task.title,
        description=parent_task.description,
        priority=parent_task.priority,
        due_date=next_due_date,
        is_recurring=True,
        recurrence_pattern=parent_task.recurrence_pattern,
        recurrence_end_date=parent_task.recurrence_end_date,
        parent_task_id=parent_task.id,
        completed=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Save next occurrence
    db.add(next_task)
    db.commit()
    db.refresh(next_task)

    return {
        "task_id": next_task.id,
        "title": next_task.title,
        "due_date": next_task.due_date,
    }
