"""MCP Tool: list_tags

Lists all unique tags used by the authenticated user with counts and colors.

This tool enables AI agents to show users their tag vocabulary and
help them discover which tags they've been using.

Phase V - Task Tags & Categories (003-task-tags) - User Story 5
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..services.task_service import TaskService


class ListTagsParams(BaseModel):
    """Input parameters for list_tags tool.

    Attributes:
        user_id: ID of the authenticated user (for isolation)
    """

    user_id: str = Field(..., description="User ID for tag ownership")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "user_id": "user-123"
            }
        }


class TagInfo(BaseModel):
    """Information about a single tag.

    Attributes:
        name: Tag name (lowercase)
        color: Hex color code generated deterministically from tag name
        count: Number of tasks using this tag
    """

    name: str = Field(..., description="Tag name (lowercase)")
    color: str = Field(..., description="Hex color code (e.g., '#3b82f6')")
    count: int = Field(..., ge=1, description="Number of tasks using this tag")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "work",
                "color": "#3b82f6",
                "count": 15
            }
        }


class ListTagsResult(BaseModel):
    """Result from list_tags tool execution.

    Attributes:
        tags: List of tags with metadata (name, color, count)
        total_tags: Total number of unique tags
        total_tasks: Total number of tasks with tags
    """

    tags: List[TagInfo] = Field(
        ...,
        description="List of tags sorted by count (descending) then name (alphabetical)"
    )
    total_tags: int = Field(..., ge=0, description="Total number of unique tags")
    total_tasks: int = Field(..., ge=0, description="Total number of tasks with tags")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "tags": [
                    {"name": "work", "color": "#3b82f6", "count": 15},
                    {"name": "urgent", "color": "#ef4444", "count": 10},
                    {"name": "shopping", "color": "#10b981", "count": 7}
                ],
                "total_tags": 3,
                "total_tasks": 32
            }
        }


def list_tags(db: Session, params: ListTagsParams) -> ListTagsResult:
    """List all unique tags for the user with counts and colors.

    This is the core MCP tool function that AI agents call to retrieve
    tag vocabulary and usage statistics.

    Args:
        db: Database session
        params: List parameters with user_id

    Returns:
        ListTagsResult with tags array, total_tags, and total_tasks

    Performance:
        - Uses efficient SQL with jsonb_array_elements_text (PostgreSQL)
        - Uses json_each for SQLite compatibility
        - Returns tags sorted by popularity (count DESC, name ASC)

    Example:
        >>> params = ListTagsParams(user_id="user-123")
        >>> result = list_tags(db, params)
        >>> assert result.total_tags >= 0
        >>> assert all(tag.count >= 1 for tag in result.tags)

    User Story:
        User: "Show me all my tags"
        Agent: Calls list_tags(user_id="...")
        Returns: List of tags with colors and counts
    """
    # Initialize TaskService
    task_service = TaskService(db)

    # Get tags from service (enforces user isolation)
    tags_data = task_service.list_user_tags(params.user_id)

    # Convert to TagInfo models
    tags = [TagInfo(**tag_dict) for tag_dict in tags_data]

    # Calculate totals
    total_tags = len(tags)
    total_tasks = sum(tag.count for tag in tags)

    # Return result
    return ListTagsResult(
        tags=tags,
        total_tags=total_tags,
        total_tasks=total_tasks
    )
