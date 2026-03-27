"""
Add Tag MCP Tool

Allows adding tags to existing tasks via natural language commands.

Examples:
- "add tag urgent to task 5"
- "add tags work and important to task 3"
- "tag task 7 with shopping"

Phase V - Task Tags & Categories (003-task-tags)
"""

from typing import List
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..services.task_service import TaskService
from ..services.tag_service import TagService


class AddTagParams(BaseModel):
    """Parameters for adding tags to an existing task."""

    user_id: str = Field(
        description="User ID (from JWT authentication)"
    )

    task_id: int = Field(
        gt=0,
        description="ID of the task to add tags to"
    )

    tags: List[str] = Field(
        min_length=1,
        max_length=100,
        description="Array of tags to add (e.g., ['urgent', 'work']). Tags will be normalized to lowercase and deduplicated."
    )


class AddTagResult(BaseModel):
    """Result of adding tags to a task."""

    task_id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    tags: List[str] = Field(description="All tags on the task after addition (normalized lowercase)")
    tags_added: List[str] = Field(description="Tags that were newly added")
    tags_already_present: List[str] = Field(description="Tags that were already on the task")
    message: str = Field(description="Human-readable success message")


def add_tag(db: Session, params: AddTagParams) -> AddTagResult:
    """
    Add tags to an existing task.

    This tool:
    1. Validates and normalizes the provided tags
    2. Adds tags to the task (deduplicates if already present)
    3. Enforces user isolation (can only modify own tasks)
    4. Returns all tags on the task after addition

    Args:
        db: Database session
        params: Parameters including user_id, task_id, and tags to add

    Returns:
        AddTagResult with task details and which tags were added

    Raises:
        ValueError: If task not found or user doesn't have access
        ValueError: If all provided tags are invalid

    Examples:
        >>> add_tag(db, AddTagParams(
        ...     user_id="user-123",
        ...     task_id=5,
        ...     tags=["urgent", "work"]
        ... ))
        AddTagResult(
            task_id=5,
            title="Complete report",
            tags=["work", "urgent", "important"],
            tags_added=["urgent", "work"],
            tags_already_present=[],
            message="Added 2 tags to task #5"
        )
    """
    # Initialize services
    tag_service = TagService()
    task_service = TaskService(db)

    # Validate and normalize tags
    normalized_tags = tag_service.validate_and_normalize_tags(params.tags)

    if not normalized_tags:
        raise ValueError(
            f"All provided tags are invalid. Tags must be 1-50 characters, "
            f"alphanumeric with hyphens/underscores only. Invalid tags: {params.tags}"
        )

    # Get current task tags before addition
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

    # Add tags to task (service handles deduplication)
    updated_task = task_service.add_tags_to_task(
        task_id=params.task_id,
        user_id=params.user_id,
        tags=normalized_tags
    )

    # Determine which tags were added vs already present
    tags_added = [tag for tag in normalized_tags if tag not in existing_tags]
    tags_already_present = [tag for tag in normalized_tags if tag in existing_tags]

    # Generate message
    if tags_added and tags_already_present:
        message = (
            f"Added {len(tags_added)} tag(s) to task #{params.task_id}. "
            f"{len(tags_already_present)} tag(s) were already present."
        )
    elif tags_added:
        message = f"Added {len(tags_added)} tag(s) to task #{params.task_id}"
    else:
        message = f"All tags were already present on task #{params.task_id}"

    return AddTagResult(
        task_id=updated_task.id,
        title=updated_task.title,
        tags=updated_task.tags,
        tags_added=tags_added,
        tags_already_present=tags_already_present,
        message=message
    )
