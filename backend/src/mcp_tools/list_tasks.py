"""MCP Tool: list_tasks

Lists tasks for the authenticated user with optional status and priority filtering.

This tool enables AI agents to retrieve and display user tasks based on
natural language queries.

Phase V Extension (US1):
- Display due_date_formatted in user's timezone
- Calculate is_overdue for tasks past due date
- Calculate overdue_by as human-readable duration
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, validator
from sqlmodel import Session, select, col

from ..models import Task
from ..services.date_parser_service import format_due_date


def calculate_overdue_by(due_date: datetime) -> str:
    """Calculate human-readable overdue duration.

    Args:
        due_date: Task due date (timezone-aware)

    Returns:
        Human-readable duration like "2 days", "3 hours", "45 minutes"
    """
    now = datetime.now(ZoneInfo("UTC"))
    delta = now - due_date

    # Calculate total seconds
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return "less than a minute"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif total_seconds < 86400:  # Less than 1 day
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:  # Days
        days = total_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"


class ListTasksParams(BaseModel):
    """Input parameters for list_tasks tool.

    Attributes:
        user_id: ID of the authenticated user (for isolation)
        status: Filter by completion status ('all', 'pending', 'completed')
        priority: Filter by priority level ('all', 'high', 'medium', 'low')
        recurring: Filter by recurring status ('all', 'recurring', 'non-recurring') [Phase V]
        user_timezone: User's IANA timezone for displaying due dates (Phase V - US1)
        sort_by: Field to sort tasks by ('due_date', 'priority', 'created_at', 'title') [Phase V - 005-task-sort]
        sort_direction: Sort direction ('asc', 'desc') - defaults vary by field [Phase V - 005-task-sort]
    """

    user_id: str = Field(..., description="User ID for task ownership")
    status: str = Field(
        "all",
        description="Filter by status: 'all', 'pending', or 'completed'"
    )
    priority: str = Field(
        "all",
        description="Filter by priority: 'all', 'high', 'medium', or 'low'"
    )
    recurring: str = Field(
        "all",
        description="Filter by recurring: 'all', 'recurring', or 'non-recurring' (Phase V)"
    )
    user_timezone: str = Field(
        default="UTC",
        description="User's IANA timezone for displaying due dates (e.g., 'America/New_York') (Phase V - US1)"
    )
    tag_filter: Optional[List[str]] = Field(
        None,
        description="Filter by tags (OR logic) - returns tasks with ANY of the specified tags (Phase V - US3 003-task-tags). Example: ['work', 'urgent'] returns tasks tagged with 'work' OR 'urgent'"
    )
    sort_by: str = Field(
        default="created_at",
        description="Field to sort tasks by: 'due_date' (earliest first), 'priority' (high→medium→low), 'created_at' (newest first, default), or 'title' (A-Z) [Phase V - 005-task-sort US1]"
    )
    sort_direction: Optional[str] = Field(
        default=None,
        description="Sort direction: 'asc' or 'desc'. If not provided, uses field-specific default (created_at=desc, due_date=asc, priority=asc, title=asc) [Phase V - 005-task-sort US1]"
    )

    @validator('status')
    def validate_status(cls, v):
        """Validate status is one of allowed values."""
        allowed = ["all", "pending", "completed"]
        if v not in allowed:
            raise ValueError(
                f"Status must be one of {allowed}, got '{v}'"
            )
        return v

    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority is one of allowed values."""
        allowed = ["all", "high", "medium", "low"]
        if v not in allowed:
            raise ValueError(
                f"Priority must be one of {allowed}, got '{v}'"
            )
        return v

    @validator('recurring')
    def validate_recurring(cls, v):
        """Validate recurring is one of allowed values."""
        allowed = ["all", "recurring", "non-recurring"]
        if v not in allowed:
            raise ValueError(
                f"Recurring filter must be one of {allowed}, got '{v}'"
            )
        return v

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by is one of allowed values."""
        allowed = ["due_date", "priority", "created_at", "title"]
        if v not in allowed:
            raise ValueError(
                f"sort_by must be one of {allowed}, got '{v}'"
            )
        return v

    @validator('sort_direction')
    def validate_sort_direction(cls, v):
        """Validate sort_direction is one of allowed values if provided."""
        if v is not None:
            allowed = ["asc", "desc"]
            if v not in allowed:
                raise ValueError(
                    f"sort_direction must be one of {allowed}, got '{v}'"
                )
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "status": "pending",
                "priority": "high",
                "sort_by": "due_date",
                "sort_direction": "asc"
            }
        }


class ListTasksResult(BaseModel):
    """Result from list_tasks tool execution.

    Attributes:
        tasks: List of task dictionaries with all fields
        count: Total number of tasks returned
    """

    tasks: List[Dict[str, Any]] = Field(
        ...,
        description="List of tasks matching the filter"
    )
    count: int = Field(..., description="Total number of tasks")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "task_id": 1,
                        "title": "Buy milk",
                        "description": None,
                        "completed": False,
                        "priority": "high",
                        "created_at": "2025-12-30T10:30:00Z"
                    },
                    {
                        "task_id": 2,
                        "title": "Call mom",
                        "description": "Wish her happy birthday",
                        "completed": False,
                        "priority": "medium",
                        "created_at": "2025-12-30T11:00:00Z"
                    }
                ],
                "count": 2
            }
        }


def list_tasks(db: Session, params: ListTasksParams) -> ListTasksResult:
    """List tasks for the user with optional status and priority filtering.

    This is the core MCP tool function that AI agents call to retrieve tasks.

    Args:
        db: Database session
        params: List parameters with user_id, status filter, and priority filter

    Returns:
        ListTasksResult with tasks array and count

    Raises:
        ValueError: If status or priority validation fails

    Performance:
        Uses composite index (user_id, priority) for efficient filtering (T026)

    Example:
        >>> params = ListTasksParams(
        ...     user_id="user-123",
        ...     status="pending",
        ...     priority="high"
        ... )
        >>> result = list_tasks(db, params)
        >>> assert result.count >= 0
        >>> assert all(not t["completed"] and t["priority"] == "high" for t in result.tasks)
    """
    # Build base query with user isolation (T082)
    query = select(Task).where(Task.user_id == params.user_id)

    # Apply status filter if not "all" (T083)
    if params.status == "pending":
        query = query.where(Task.completed == False)
    elif params.status == "completed":
        query = query.where(Task.completed == True)
    # For "all", no additional filter needed

    # Apply priority filter if not "all" (T026)
    # Uses composite index (user_id, priority) for optimal performance
    if params.priority != "all":
        query = query.where(Task.priority == params.priority)

    # Phase V: Apply recurring filter if not "all" (T111, T112)
    # Uses composite index (user_id, is_recurring) for optimal performance
    if params.recurring == "recurring":
        query = query.where(Task.is_recurring == True)
    elif params.recurring == "non-recurring":
        query = query.where(Task.is_recurring == False)
    # For "all", no additional filter needed

    # Phase V - US3 (003-task-tags): Apply tag filter with OR logic (T030, T031)
    # Returns tasks with ANY of the specified tags (OR logic)
    # Uses GIN index on tags column for optimal performance
    if params.tag_filter:
        # Normalize tags for case-insensitive matching
        from ..services.tag_service import TagService
        tag_service = TagService()
        normalized_tags = tag_service.normalize_tags(params.tag_filter)

        if normalized_tags:
            # Build OR condition: task has ANY of the specified tags
            # For JSON column, we need to check if any tag in the filter exists in the array
            from sqlalchemy import or_, func

            # For each tag, check if it's in the task's tags array
            tag_conditions = []
            for tag in normalized_tags:
                # Check if the JSON array contains the tag
                # SQLite: json_extract returns the array, we check if tag is in it
                # PostgreSQL: jsonb array operator ?
                tag_conditions.append(func.json_extract(Task.tags, '$').contains(tag))

            if tag_conditions:
                query = query.where(or_(*tag_conditions))

    # Phase V - 005-task-sort (T007): Apply sorting
    # Default sort direction depends on field if not provided
    sort_direction = params.sort_direction
    if sort_direction is None:
        direction_defaults = {
            "created_at": "desc",  # Newest first
            "due_date": "asc",     # Earliest first
            "priority": "asc",     # High → medium → low
            "title": "asc"         # A → Z
        }
        sort_direction = direction_defaults.get(params.sort_by, "desc")

    # Apply field-specific sorting logic
    if params.sort_by == "due_date":
        # Sort by due_date with NULLS LAST (tasks without due dates at end)
        # Tiebreaker: created_at descending
        if sort_direction == "asc":
            query = query.order_by(
                Task.due_date.asc().nullslast(),
                Task.created_at.desc()
            )
        else:
            query = query.order_by(
                Task.due_date.desc().nullslast(),
                Task.created_at.desc()
            )

    elif params.sort_by == "priority":
        # Sort by priority using CASE statement mapping
        from sqlalchemy import case as sql_case

        if sort_direction == "asc":
            # high=1, medium=2, low=3
            priority_order = sql_case(
                (Task.priority == "high", 1),
                (Task.priority == "medium", 2),
                (Task.priority == "low", 3),
                else_=4
            )
        else:
            # low=1, medium=2, high=3 (reverse)
            priority_order = sql_case(
                (Task.priority == "low", 1),
                (Task.priority == "medium", 2),
                (Task.priority == "high", 3),
                else_=4
            )

        query = query.order_by(
            priority_order.asc(),
            Task.created_at.desc()
        )

    elif params.sort_by == "title":
        # Sort by title case-insensitive using LOWER()
        # Tiebreaker: created_at descending
        from sqlalchemy import func as sql_func

        if sort_direction == "asc":
            query = query.order_by(
                sql_func.lower(Task.title).asc(),
                Task.created_at.desc()
            )
        else:
            query = query.order_by(
                sql_func.lower(Task.title).desc(),
                Task.created_at.desc()
            )

    else:  # created_at (default)
        # Sort by created_at
        if sort_direction == "desc":
            query = query.order_by(col(Task.created_at).desc())
        else:
            query = query.order_by(col(Task.created_at).asc())

    # Execute query
    try:
        results = db.exec(query).all()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch tasks: {str(e)}") from e

    # Convert tasks to dict format (T084, T113, T048-T050)
    now = datetime.now(ZoneInfo("UTC"))

    tasks = []
    for task in results:
        # Phase V - US1: Calculate is_overdue and overdue_by (T049, T050)
        is_overdue = False
        overdue_by = None
        due_date_formatted = None

        if task.due_date:
            # Format due date in user's timezone (T048)
            due_date_formatted = format_due_date(task.due_date, params.user_timezone)

            # Calculate is_overdue: due_date < now AND not completed (T049)
            if task.due_date < now and not task.completed:
                is_overdue = True
                # Calculate overdue_by human-readable duration (T050)
                overdue_by = calculate_overdue_by(task.due_date)

        task_dict = {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "due_date_formatted": due_date_formatted,  # Phase V - US1 (T048)
            "is_overdue": is_overdue,  # Phase V - US1 (T049)
            "overdue_by": overdue_by,  # Phase V - US1 (T050)
            "created_at": task.created_at.isoformat() if task.created_at else None,
            # Phase V: Include recurrence info (T113)
            "is_recurring": task.is_recurring,
            "recurrence_pattern": task.recurrence_pattern if task.is_recurring else None,
            "recurrence_end_date": task.recurrence_end_date.isoformat() if task.recurrence_end_date else None,
            # Phase V - US4 (003-task-tags): Include tags (T021)
            "tags": task.tags if task.tags else []
        }

        tasks.append(task_dict)

    # Return result with count (T084)
    return ListTasksResult(
        tasks=tasks,
        count=len(tasks)
    )
