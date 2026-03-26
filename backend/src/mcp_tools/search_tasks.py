"""MCP Tool: search_tasks

Search and filter tasks with multiple criteria including keyword search,
status, priority, tags, and due date filters.

This tool enables AI agents to provide powerful search functionality through
natural language queries.

Phase: 004-search-filter
Task: T011 (US1)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlmodel import Session

from ..services.task_service import TaskService
from ..schemas.search import SearchRequest, SearchResponse


class SearchTasksParams(BaseModel):
    """Input parameters for search_tasks tool.

    Attributes:
        user_id: ID of the authenticated user (for isolation)
        keyword: Optional keyword for searching in title and description
        status_filter: Filter by completion status
        priority_filter: Filter by priority level
        tags_filter: Filter by tags (OR logic)
        due_date_filter: Filter by due date category
        page: Page number for pagination (1-indexed)
        page_size: Number of results per page
    """

    user_id: str = Field(..., description="User ID for task ownership")

    keyword: Optional[str] = Field(
        None,
        description="Keyword for case-insensitive partial matching in title and description"
    )

    status_filter: str = Field(
        "all",
        description="Filter by status: 'all', 'pending', or 'completed'"
    )

    priority_filter: str = Field(
        "all",
        description="Filter by priority: 'all', 'high', 'medium', or 'low'"
    )

    tags_filter: Optional[List[str]] = Field(
        None,
        description="Filter by tags (OR logic) - returns tasks with ANY of the specified tags"
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

    @validator('status_filter')
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        # Map 'pending' to 'incomplete' for user-friendly language
        if v == "pending":
            return "incomplete"

        allowed = ["all", "incomplete", "completed"]
        if v not in allowed:
            raise ValueError(
                f"Status must be 'all', 'pending', or 'completed', got '{v}'"
            )
        return v

    @validator('priority_filter')
    def validate_priority(cls, v):
        """Validate priority is one of allowed values."""
        allowed = ["all", "high", "medium", "low"]
        if v not in allowed:
            raise ValueError(
                f"Priority must be one of {allowed}, got '{v}'"
            )
        return v

    @validator('due_date_filter')
    def validate_due_date(cls, v):
        """Validate due date filter is one of allowed values."""
        allowed = ["all", "overdue", "today", "this_week", "this_month", "no_due_date"]
        if v not in allowed:
            raise ValueError(
                f"Due date filter must be one of {allowed}, got '{v}'"
            )
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "keyword": "grocery",
                "status_filter": "pending",
                "priority_filter": "high",
                "tags_filter": ["shopping", "urgent"],
                "due_date_filter": "today",
                "page": 1,
                "page_size": 20
            }
        }


class SearchTasksResult(BaseModel):
    """Result from search_tasks tool execution.

    Attributes:
        tasks: List of tasks matching search criteria
        total_count: Total number of tasks matching filters (across all pages)
        filtered_count: Number of tasks in this page
        pagination: Pagination metadata
        applied_filters: Summary of filters applied
        summary: Human-readable summary of results
    """

    tasks: List[Dict[str, Any]] = Field(
        ...,
        description="List of tasks matching search and filter criteria"
    )

    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of tasks matching filters"
    )

    filtered_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks in this page"
    )

    pagination: Dict[str, Any] = Field(
        ...,
        description="Pagination metadata"
    )

    applied_filters: Dict[str, Any] = Field(
        ...,
        description="Summary of filters applied"
    )

    summary: str = Field(
        ...,
        description="Human-readable summary of search results"
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
                },
                "summary": "Found 5 tasks matching 'grocery' (showing 1 result)"
            }
        }


def search_tasks(db: Session, params: SearchTasksParams) -> SearchTasksResult:
    """Search and filter tasks with multiple criteria.

    This is the core MCP tool function that AI agents call to search tasks.
    Supports keyword search, status filtering, priority filtering, tag filtering,
    and due date filtering with pagination.

    Args:
        db: Database session
        params: Search parameters with filters and pagination

    Returns:
        SearchTasksResult with matching tasks and metadata

    Raises:
        ValueError: If invalid filter values provided

    Performance:
        Uses composite indexes (user_id, completed), (user_id, priority),
        (user_id, tags), (user_id, due_date), (user_id, title) for efficient filtering.

    Examples:
        >>> # Search for grocery tasks
        >>> params = SearchTasksParams(
        ...     user_id="user-123",
        ...     keyword="grocery",
        ...     status_filter="pending"
        ... )
        >>> result = search_tasks(db, params)
        >>> print(result.summary)
        "Found 3 tasks matching 'grocery'"

        >>> # Find overdue high priority tasks
        >>> params = SearchTasksParams(
        ...     user_id="user-123",
        ...     priority_filter="high",
        ...     due_date_filter="overdue"
        ... )
        >>> result = search_tasks(db, params)
        >>> print(result.summary)
        "Found 2 high priority overdue tasks"

    Phase: 004-search-filter
    Task: T011 (US1)
    """
    # Use TaskService to execute search
    task_service = TaskService(db)

    # Execute search with all filters
    search_result = task_service.search_and_filter_tasks(
        user_id=params.user_id,
        keyword=params.keyword,
        status_filter=params.status_filter,
        priority_filter=params.priority_filter,
        tags_filter=params.tags_filter,
        due_date_filter=params.due_date_filter,
        page=params.page,
        page_size=params.page_size
    )

    # Generate human-readable summary
    summary_parts = []

    # Total count
    if search_result["total_count"] == 0:
        summary_parts.append("No tasks found")
    elif search_result["total_count"] == 1:
        summary_parts.append("Found 1 task")
    else:
        summary_parts.append(f"Found {search_result['total_count']} tasks")

    # Keyword
    if params.keyword:
        summary_parts.append(f"matching '{params.keyword}'")

    # Filters
    filter_descriptions = []
    if params.status_filter != "all":
        filter_descriptions.append(params.status_filter)
    if params.priority_filter != "all":
        filter_descriptions.append(f"{params.priority_filter} priority")
    if params.tags_filter:
        tag_list = ", ".join(params.tags_filter)
        filter_descriptions.append(f"tagged with {tag_list}")
    if params.due_date_filter != "all":
        filter_descriptions.append(params.due_date_filter)

    if filter_descriptions:
        summary_parts.append(f"({', '.join(filter_descriptions)})")

    # Pagination
    if search_result["total_count"] > params.page_size:
        summary_parts.append(
            f"(showing page {params.page} of {search_result['pagination']['total_pages']})"
        )

    summary = " ".join(summary_parts)

    return SearchTasksResult(
        tasks=search_result["tasks"],
        total_count=search_result["total_count"],
        filtered_count=search_result["filtered_count"],
        pagination=search_result["pagination"],
        applied_filters=search_result["applied_filters"],
        summary=summary
    )
