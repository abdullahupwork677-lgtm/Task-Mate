"""Tag-specific schemas for API request/response validation."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class AddTagRequest(BaseModel):
    """Request schema for adding tags to an existing task."""

    task_id: int = Field(gt=0, description="ID of task to add tags to")
    tags: List[str] = Field(min_length=1, max_length=100, description="Tags to add")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags are not empty."""
        if not v or len(v) == 0:
            raise ValueError("At least one tag is required")
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tags cannot be empty or whitespace only")
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds maximum length of 50 characters")
        return v


class RemoveTagRequest(BaseModel):
    """Request schema for removing tags from an existing task."""

    task_id: int = Field(gt=0, description="ID of task to remove tags from")
    tags: List[str] = Field(min_length=1, max_length=100, description="Tags to remove")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags are not empty."""
        if not v or len(v) == 0:
            raise ValueError("At least one tag is required")
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tags cannot be empty or whitespace only")
        return v


class TagInfo(BaseModel):
    """Information about a single tag."""

    name: str = Field(description="Tag name (normalized, lowercase)")
    color: str = Field(description="Hex color for visual display (e.g., '#3b82f6')")
    count: int = Field(ge=0, description="Number of tasks with this tag")


class ListTagsResponse(BaseModel):
    """Response schema for listing all user's tags."""

    tags: List[TagInfo] = Field(description="List of tags with metadata")
    total_count: int = Field(ge=0, description="Total number of unique tags")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tags": [
                    {"name": "work", "color": "#3b82f6", "count": 15},
                    {"name": "urgent", "color": "#ef4444", "count": 8},
                    {"name": "shopping", "color": "#10b981", "count": 5}
                ],
                "total_count": 3
            }
        }
    }
