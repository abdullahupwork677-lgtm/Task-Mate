"""
Remove Tag MCP Tool

Allows removing tags from existing tasks via natural language commands.

Examples:
- "remove tag urgent from task 5"
- "remove tags work and important from task 3"
- "untag task 7 from shopping"

Phase V - Task Tags & Categories (003-task-tags)
"""

from typing import List
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..services.task_service import TaskService
from ..services.tag_service import TagService


class RemoveTagParams(BaseModel):
    """Parameters for removing tags from an existing task."""

    user_id: str = Field(
        description="User ID (from JWT authentication)"
    )

    task_id: int = Field(
        gt=0,
        description="ID of the task to remove tags from"
    )

    tags: List[str] = Field(
        min_length=1,
        max_length=100,
        description="Array of tags to remove (e.g., ['urgent', 'work']). Tags will be normalized to lowercase for matching."
    )


class RemoveTagResult(BaseModel):
    """Result of removing tags from a task."""

    task_id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    tags: List[str] = Field(description="Remaining tags on the task after removal (normalized lowercase)")
    tags_removed: List[str] = Field(description="Tags that were successfully removed")
    tags_not_found: List[str] = Field(description="Tags that were not on the task")
    message: str = Field(description="Human-readable success message")


def remove_tag(db: Session, params: RemoveTagParams) -> RemoveTagResult:
    """
    Remove tags from an existing task.

    This tool:
    1. Normalizes the provided tags for matching
    2. Removes matching tags from the task (case-insensitive)
    3. Enforces user isolation (can only modify own tasks)
    4. Returns remaining tags on the task after removal

    Args:
        db: Database session
        params: Parameters including user_id, task_id, and tags to remove

    Returns:
        RemoveTagResult with task details and which tags were removed

    Raises:
        ValueError: If task not found or user doesn't have access

    Examples:
        >>> remove_tag(db, RemoveTagParams(
        ...     user_id="user-123",
        ...     task_id=5,
        ...     tags=["urgent", "work"]
        ... ))
        RemoveTagResult(
            task_id=5,
            title="Complete report",
            tags=["important"],
            tags_removed=["urgent", "work"],
            tags_not_found=[],
            message="Removed 2 tags from task #5"
        )
    """
    # Initialize services
    tag_service = TagService()
    task_service = TaskService(db, tag_service)

    # Normalize tags for case-insensitive matching
    normalized_tags = tag_service.normalize_tags(params.tags)

    # Get current task tags before removal
    from ..models import Task
    from sqlmodel import select

    statement = select(Task).where(
        Task.id == params.task_id,
        Task.user_id == params.user_id
    )
    task = db.exec(statement).first()

    if not task:
        raise ValueError(
            f"Task {params.task_id} not found or you don't have access to it"
        )

    existing_tags = set(task.tags or [])

    # Remove tags from task
    updated_task = task_service.remove_tags_from_task(
        task_id=params.task_id,
        user_id=params.user_id,
        tags=normalized_tags
    )

    # Determine which tags were removed vs not found
    new_tags_set = set(updated_task.tags)
    tags_removed = [tag for tag in normalized_tags if tag in existing_tags]
    tags_not_found = [tag for tag in normalized_tags if tag not in existing_tags]

    # Generate message
    if tags_removed and tags_not_found:
        message = (
            f"Removed {len(tags_removed)} tag(s) from task #{params.task_id}. "
            f"{len(tags_not_found)} tag(s) were not found on the task."
        )
    elif tags_removed:
        message = f"Removed {len(tags_removed)} tag(s) from task #{params.task_id}"
    else:
        message = f"None of the specified tags were found on task #{params.task_id}"

    return RemoveTagResult(
        task_id=updated_task.id,
        title=updated_task.title,
        tags=updated_task.tags,
        tags_removed=tags_removed,
        tags_not_found=tags_not_found,
        message=message
    )
