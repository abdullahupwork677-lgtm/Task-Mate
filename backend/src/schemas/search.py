"""Search and filter schemas for task searching functionality.

This module defines Pydantic schemas for search requests and responses,
supporting keyword search, status filter, priority filter, tags filter,
due date filter, and pagination.

Phase: 004-search-filter
Tasks: T003, T004
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    """Request schema for searching and filtering tasks.

    Attributes:
        keyword: Optional keyword for searching in title and description
        status_filter: Filter by completion status ('all', 'completed', 'incomplete')
        priority_filter: Filter by priority ('all', 'high', 'medium', 'low')
        tags_filter: Filter by tags (OR logic - tasks with ANY of these tags)
        due_date_filter: Filter by due date category ('all', 'overdue', 'today', 'this_week', 'this_month', 'no_due_date')
        page: Page number for pagination (1-indexed)
        page_size: Number of results per page
        user_id: User ID for task ownership (enforces user isolation)
    """

    keyword: Optional[str] = Field(
        None,
        description="Keyword for case-insensitive partial matching in title and description"
    )

    status_filter: str = Field(
        "all",
        description="Filter by completion status: 'all', 'completed', or 'incomplete'"
    )

    priority_filter: str = Field(
        "all",
        description="Filter by priority: 'all', 'high', 'medium', or 'low'"
    )

    tags_filter: Optional[List[str]] = Field(
        None,
        description="Filter by tags (OR logic): returns tasks with ANY of these tags"
    )

    due_date_filter: str = Field(
        "all",
        description="Filter by due date: 'all', 'overdue', 'today', 'this_week', 'this_month', or 'no_due_date'"
    )

    page: int = Field(
        1,
        ge=1,
        description="Page number for pagination (1-indexed)"
    )

    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Number of results per page (max 100)"
    )

    user_id: str = Field(
        ...,
        description="User ID for task ownership (enforces user isolation)"
    )

    @validator('status_filter')
    def validate_status(cls, v):
        """Validate status filter is one of allowed values."""
        allowed = ["all", "completed", "incomplete"]
        if v not in allowed:
            raise ValueError(f"Status filter must be one of {allowed}, got '{v}'")
        return v

    @validator('priority_filter')
    def validate_priority(cls, v):
        """Validate priority filter is one of allowed values."""
        allowed = ["all", "high", "medium", "low"]
        if v not in allowed:
            raise ValueError(f"Priority filter must be one of {allowed}, got '{v}'")
        return v

    @validator('due_date_filter')
    def validate_due_date(cls, v):
        """Validate due date filter is one of allowed values."""
        allowed = ["all", "overdue", "today", "this_week", "this_month", "no_due_date"]
        if v not in allowed:
            raise ValueError(f"Due date filter must be one of {allowed}, got '{v}'")
        return v

    @validator('keyword')
    def validate_keyword(cls, v):
        """Validate keyword length if provided."""
        if v is not None and len(v.strip()) == 0:
            return None  # Treat empty string as None
        if v is not None and len(v) > 200:
            raise ValueError("Keyword must be 200 characters or less")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "keyword": "grocery",
                "status_filter": "incomplete",
                "priority_filter": "high",
                "tags_filter": ["shopping", "urgent"],
                "due_date_filter": "today",
                "page": 1,
                "page_size": 20,
                "user_id": "user-123"
            }
        }


class PaginationInfo(BaseModel):
    """Pagination metadata for search results.

    Attributes:
        page: Current page number (1-indexed)
        page_size: Number of results per page
        total_pages: Total number of pages
        has_next: Whether there is a next page
        has_prev: Whether there is a previous page
    """

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Results per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class AppliedFilters(BaseModel):
    """Summary of applied filters for search request.

    Attributes:
        keyword: Keyword used for search (if any)
        status: Status filter applied
        priority: Priority filter applied
        tags: Tags filter applied (if any)
        due_date: Due date filter applied
        summary: Human-readable summary of applied filters
    """

    keyword: Optional[str] = Field(None, description="Keyword search term")
    status: str = Field(..., description="Status filter")
    priority: str = Field(..., description="Priority filter")
    tags: Optional[List[str]] = Field(None, description="Tags filter")
    due_date: str = Field(..., description="Due date filter")
    summary: str = Field(..., description="Human-readable summary of active filters")

    @classmethod
    def from_filters(
        cls,
        keyword: Optional[str],
        status: str,
        priority: str,
        tags: Optional[List[str]],
        due_date: str,
        result_count: int
    ) -> "AppliedFilters":
        """Create AppliedFilters with generated summary.

        Args:
            keyword: Keyword filter
            status: Status filter
            priority: Priority filter
            tags: Tags filter
            due_date: Due date filter
            result_count: Number of results found

        Returns:
            AppliedFilters instance with human-readable summary
        """
        # Build summary parts
        summary_parts = []

        if keyword:
            summary_parts.append(f'matching "{keyword}"')

        if status != "all":
            summary_parts.append(status)

        if priority != "all":
            summary_parts.append(f"{priority} priority")

        if tags:
            tags_str = ", ".join(tags)
            summary_parts.append(f"tagged with {tags_str}")

        if due_date == "overdue":
            summary_parts.append("overdue")
        elif due_date == "today":
            summary_parts.append("due today")
        elif due_date == "this_week":
            summary_parts.append("due this week")
        elif due_date == "this_month":
            summary_parts.append("due this month")
        elif due_date == "no_due_date":
            summary_parts.append("with no due date")

        # Generate summary
        if summary_parts:
            summary = f"Showing {result_count} {' '.join(summary_parts)} task{'s' if result_count != 1 else ''}"
        else:
            summary = f"Showing all {result_count} task{'s' if result_count != 1 else ''}"

        return cls(
            keyword=keyword,
            status=status,
            priority=priority,
            tags=tags,
            due_date=due_date,
            summary=summary
        )


class SearchResponse(BaseModel):
    """Response schema for search and filter results.

    Attributes:
        tasks: List of tasks matching the search and filter criteria
        total_count: Total number of tasks matching filters (across all pages)
        filtered_count: Number of tasks returned in this page
        pagination: Pagination metadata
        applied_filters: Summary of filters applied to this search
    """

    tasks: List[Dict[str, Any]] = Field(
        ...,
        description="List of tasks matching search and filter criteria"
    )

    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of tasks matching filters (across all pages)"
    )

    filtered_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks in this page"
    )

    pagination: PaginationInfo = Field(
        ...,
        description="Pagination metadata"
    )

    applied_filters: AppliedFilters = Field(
        ...,
        description="Summary of filters applied"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "task_id": 1,
                        "title": "Buy groceries",
                        "description": "Get milk and eggs",
                        "completed": False,
                        "priority": "high",
                        "tags": ["shopping", "urgent"],
                        "due_date": "2026-02-15T10:00:00Z",
                        "created_at": "2026-02-14T08:00:00Z"
                    }
                ],
                "total_count": 5,
                "filtered_count": 1,
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False
                },
                "applied_filters": {
                    "keyword": "grocery",
                    "status": "incomplete",
                    "priority": "high",
                    "tags": ["shopping", "urgent"],
                    "due_date": "today"
                }
            }
        }
