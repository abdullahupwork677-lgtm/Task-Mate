"""Task service layer for business logic and database operations."""

from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func, text
from sqlalchemy import or_, case

from src.models import Task
from src.services.tag_service import TagService


class TaskService:
    """
    Service layer for task management operations.

    Handles business logic for tasks including tag operations, filtering, and ownership checks.
    All methods enforce user isolation - users can only access their own tasks.
    """

    def __init__(self, session: Session):
        """
        Initialize TaskService with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session
        self.tag_service = TagService()

    def add_tags_to_task(self, task_id: int, user_id: str, tags: List[str]) -> Task:
        """
        Add tags to an existing task.

        Tags are normalized (lowercase, deduplicated) and merged with existing tags.
        Enforces user ownership - can only add tags to own tasks.

        Args:
            task_id: ID of task to add tags to
            user_id: Owner user ID (for isolation)
            tags: List of tags to add

        Returns:
            Updated Task object

        Raises:
            ValueError: If task not found or user doesn't own task
            ValueError: If invalid tags provided

        Examples:
            >>> task = task_service.add_tags_to_task(5, "user-123", ["urgent", "Work"])
            >>> task.tags
            ['urgent', 'work']
        """
        # Validate and normalize tags
        validated_tags = self.tag_service.validate_and_normalize_tags(tags)
        if not validated_tags:
            raise ValueError("No valid tags provided")

        # Fetch task with ownership check
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        task = self.session.exec(statement).first()

        if not task:
            raise ValueError(f"Task {task_id} not found or access denied")

        # Merge with existing tags (deduplicate)
        existing_tags = task.tags or []
        combined_tags = list(set(existing_tags + validated_tags))
        task.tags = combined_tags

        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return task

    def remove_tags_from_task(self, task_id: int, user_id: str, tags: List[str]) -> Task:
        """
        Remove tags from an existing task.

        Case-insensitive tag removal (normalized before comparison).
        Enforces user ownership - can only remove tags from own tasks.

        Args:
            task_id: ID of task to remove tags from
            user_id: Owner user ID (for isolation)
            tags: List of tags to remove

        Returns:
            Updated Task object

        Raises:
            ValueError: If task not found or user doesn't own task

        Examples:
            >>> task = task_service.remove_tags_from_task(5, "user-123", ["urgent"])
            >>> "urgent" in task.tags
            False
        """
        # Normalize tags to remove (for case-insensitive matching)
        tags_to_remove = self.tag_service.normalize_tags(tags)

        # Fetch task with ownership check
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        task = self.session.exec(statement).first()

        if not task:
            raise ValueError(f"Task {task_id} not found or access denied")

        # Filter out tags to remove (case-insensitive)
        existing_tags = task.tags or []
        remaining_tags = [tag for tag in existing_tags if tag not in tags_to_remove]
        task.tags = remaining_tags

        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return task

    def list_user_tags(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all unique tags used by a user with counts and colors.

        Uses PostgreSQL jsonb_array_elements_text for efficient tag extraction.
        For SQLite, uses JSON extraction with text() wrapper.

        Args:
            user_id: User ID to list tags for

        Returns:
            List of dictionaries with keys: name, color, count
            Sorted by count (descending) then name (alphabetical)

        Examples:
            >>> tags = task_service.list_user_tags("user-123")
            >>> tags[0]
            {'name': 'work', 'color': '#3b82f6', 'count': 15}
        """
        # Detect database dialect
        dialect_name = self.session.bind.dialect.name

        if dialect_name == "postgresql":
            # PostgreSQL: Use jsonb_array_elements_text for efficient extraction
            query = text("""
                SELECT
                    tag_value AS name,
                    COUNT(*) AS count
                FROM tasks,
                    jsonb_array_elements_text(tags) AS tag_value
                WHERE user_id = :user_id
                GROUP BY tag_value
                ORDER BY count DESC, tag_value ASC
            """)
        else:
            # SQLite: Use json_each for extraction
            query = text("""
                SELECT
                    json_each.value AS name,
                    COUNT(*) AS count
                FROM tasks,
                    json_each(tasks.tags)
                WHERE user_id = :user_id
                GROUP BY json_each.value
                ORDER BY count DESC, json_each.value ASC
            """)

        result = self.session.execute(query, {"user_id": user_id})
        rows = result.fetchall()

        # Build response with colors
        tags_with_metadata = []
        for row in rows:
            tag_name = row[0]  # name
            tag_count = row[1]  # count
            tag_color = self.tag_service.generate_tag_color(tag_name)

            tags_with_metadata.append({
                "name": tag_name,
                "color": tag_color,
                "count": tag_count
            })

        return tags_with_metadata

    def get_user_tasks(
        self,
        user_id: str,
        completed: Optional[bool] = None,
        tag_filter: Optional[List[str]] = None
    ) -> List[Task]:
        """
        Get tasks for a user with optional filtering.

        Supports filtering by completion status and tags (OR logic for multiple tags).

        Args:
            user_id: User ID to get tasks for
            completed: Optional filter for completion status
            tag_filter: Optional list of tags (task must have ANY of these tags)

        Returns:
            List of Task objects matching filters

        Examples:
            >>> # Get all work or urgent tasks
            >>> tasks = task_service.get_user_tasks("user-123", tag_filter=["work", "urgent"])
        """
        # Start with user isolation
        statement = select(Task).where(Task.user_id == user_id)

        # Apply completion filter if provided
        if completed is not None:
            statement = statement.where(Task.completed == completed)

        # Apply tag filter if provided (OR logic)
        if tag_filter:
            # Normalize tags for case-insensitive matching
            normalized_tags = self.tag_service.normalize_tags(tag_filter)

            # PostgreSQL vs SQLite syntax
            dialect_name = self.session.bind.dialect.name
            if dialect_name == "postgresql":
                # PostgreSQL: Use ?| operator for OR matching
                statement = statement.where(Task.tags.op("?|")(normalized_tags))
            else:
                # SQLite: Check if any tag exists in JSON array
                # Build OR conditions for each tag
                tag_conditions = []
                for tag in normalized_tags:
                    # SQLite JSON contains check
                    tag_conditions.append(
                        func.json_extract(Task.tags, "$").contains(f'"{tag}"')
                    )
                statement = statement.where(or_(*tag_conditions))

        # Execute query
        tasks = self.session.exec(statement).all()
        return tasks

    def search_and_filter_tasks(
        self,
        user_id: str,
        keyword: Optional[str] = None,
        status_filter: str = "all",
        priority_filter: str = "all",
        tags_filter: Optional[List[str]] = None,
        due_date_filter: str = "all",
        sort_by: str = "created_at",
        sort_direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search, filter, and sort tasks with multiple criteria and pagination.

        Combines keyword search with multiple filters (status, priority, tags, due date)
        using AND logic between filter types and OR logic within tags.
        Supports sorting by due_date, priority, created_at, or title.

        Args:
            user_id: User ID for task ownership (enforces user isolation)
            keyword: Optional keyword for searching in title and description
            status_filter: Filter by completion status ('all', 'completed', 'incomplete')
            priority_filter: Filter by priority ('all', 'high', 'medium', 'low')
            tags_filter: Filter by tags (OR logic - tasks with ANY of these tags)
            due_date_filter: Filter by due date category ('all', 'overdue', 'today', 'this_week', 'this_month', 'no_due_date')
            sort_by: Field to sort by ('due_date', 'priority', 'created_at', 'title') - Phase V: 005-task-sort
            sort_direction: Sort direction ('asc', 'desc') - defaults vary by field - Phase V: 005-task-sort
            page: Page number for pagination (1-indexed)
            page_size: Number of results per page

        Returns:
            Dictionary with:
                - tasks: List of task dictionaries
                - total_count: Total number of tasks matching filters
                - filtered_count: Number of tasks in this page
                - pagination: Pagination metadata
                - applied_filters: Summary of filters applied

        Raises:
            ValueError: If invalid filter values provided

        Examples:
            >>> # Search for grocery tasks that are incomplete and high priority, sorted by due date
            >>> result = task_service.search_and_filter_tasks(
            ...     user_id="user-123",
            ...     keyword="grocery",
            ...     status_filter="incomplete",
            ...     priority_filter="high",
            ...     sort_by="due_date",
            ...     sort_direction="asc",
            ...     page=1,
            ...     page_size=20
            ... )
            >>> print(result["total_count"])
            5
            >>> print(len(result["tasks"]))
            5

        Phase: 004-search-filter (search/filter), 005-task-sort (sorting)
        Task: T007 (search/filter), T005-T006 (sorting)
        """
        from src.utils.query_builder import QueryBuilder
        from src.schemas.search import PaginationInfo, AppliedFilters

        # Build base query
        base_query = select(Task)
        builder = QueryBuilder(base_query)

        # Apply filters
        builder.filter_by_user(user_id, Task)

        # Keyword search (title and description)
        if keyword:
            builder.filter_by_keyword(keyword, Task, ["title", "description"])

        # Status filter
        if status_filter == "completed":
            builder.filter_by_status(True, Task)
        elif status_filter == "incomplete":
            builder.filter_by_status(False, Task)

        # Priority filter
        builder.filter_by_priority(
            priority_filter if priority_filter != "all" else None,
            Task
        )

        # Tags filter (OR logic)
        if tags_filter:
            builder.filter_by_tags(tags_filter, Task)

        # Due date filter
        builder.filter_by_due_date(due_date_filter, Task)

        # Build query with filters (before applying sort and pagination)
        filtered_query = builder.build()

        # Apply sorting (Phase V: 005-task-sort, T005-T006)
        # Default sort direction depends on field if not provided
        if sort_direction is None:
            direction_defaults = {
                "created_at": "desc",  # Newest first
                "due_date": "asc",  # Earliest first
                "priority": "asc",  # High → medium → low
                "title": "asc"  # A → Z
            }
            sort_direction = direction_defaults.get(sort_by, "desc")

        # Apply field-specific sorting logic
        if sort_by == "due_date":
            # Sort by due_date with NULLS LAST (tasks without due dates at end)
            # Tiebreaker: created_at descending
            if sort_direction == "asc":
                # SQLite compatible: NULL values naturally sort last
                filtered_query = filtered_query.order_by(
                    Task.due_date.asc().nullslast(),
                    Task.created_at.desc()
                )
            else:
                filtered_query = filtered_query.order_by(
                    Task.due_date.desc().nullslast(),
                    Task.created_at.desc()
                )

        elif sort_by == "priority":
            # Sort by priority using CASE statement mapping
            # high=1, medium=2, low=3 for ascending
            # low=1, medium=2, high=3 for descending
            if sort_direction == "asc":
                priority_order = case(
                    (Task.priority == "high", 1),
                    (Task.priority == "medium", 2),
                    (Task.priority == "low", 3),
                    else_=4  # For any unexpected values
                )
            else:
                # Reverse priority order for descending
                priority_order = case(
                    (Task.priority == "low", 1),
                    (Task.priority == "medium", 2),
                    (Task.priority == "high", 3),
                    else_=4
                )

            filtered_query = filtered_query.order_by(
                priority_order.asc(),
                Task.created_at.desc()
            )

        elif sort_by == "title":
            # Sort by title case-insensitive using LOWER()
            # Tiebreaker: created_at descending
            if sort_direction == "asc":
                filtered_query = filtered_query.order_by(
                    func.lower(Task.title).asc(),
                    Task.created_at.desc()
                )
            else:
                filtered_query = filtered_query.order_by(
                    func.lower(Task.title).desc(),
                    Task.created_at.desc()
                )

        else:  # created_at (default)
            # Sort by created_at (no tiebreaker needed - created_at is unique enough)
            if sort_direction == "desc":
                filtered_query = filtered_query.order_by(Task.created_at.desc())
            else:
                filtered_query = filtered_query.order_by(Task.created_at.asc())

        # Get total count before pagination
        total_count = len(self.session.exec(filtered_query).all())

        # Apply pagination directly to filtered_query
        offset = (page - 1) * page_size
        paginated_query = filtered_query.limit(page_size).offset(offset)

        # Execute query
        tasks = self.session.exec(paginated_query).all()

        # Convert tasks to dictionaries
        task_dicts = []
        for task in tasks:
            task_dict = {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority,
                "tags": task.tags if task.tags else [],
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }
            task_dicts.append(task_dict)

        # Calculate pagination metadata
        filtered_count = len(task_dicts)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1

        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )

        # Applied filters summary with human-readable description
        applied_filters = AppliedFilters.from_filters(
            keyword=keyword,
            status=status_filter,
            priority=priority_filter,
            tags=tags_filter,
            due_date=due_date_filter,
            result_count=total_count
        )

        return {
            "tasks": task_dicts,
            "total_count": total_count,
            "filtered_count": filtered_count,
            "pagination": pagination.model_dump(),
            "applied_filters": applied_filters.model_dump()
        }
