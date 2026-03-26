"""Query Builder utility for dynamic WHERE clause construction.

This module provides a flexible query builder for constructing SQLAlchemy
queries with multiple optional filters, supporting the search and filter
functionality.

Phase: 004-search-filter
Task: T006
"""

from typing import List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import Select, or_, and_, func
from sqlmodel import col


class QueryBuilder:
    """Utility class for building dynamic SQLAlchemy queries with multiple filters.

    This class helps construct complex queries with optional filters,
    avoiding the need for multiple if-else blocks in service layer.

    Example:
        >>> from sqlmodel import select
        >>> from src.models import Task
        >>>
        >>> query = select(Task)
        >>> builder = QueryBuilder(query)
        >>> builder.filter_by_user("user-123")
        >>> builder.filter_by_keyword("grocery", ["title", "description"])
        >>> builder.filter_by_status(False)
        >>> final_query = builder.build()
    """

    def __init__(self, base_query: Select):
        """Initialize QueryBuilder with a base SQLAlchemy Select query.

        Args:
            base_query: Base SQLAlchemy Select statement to build upon
        """
        self.query = base_query
        self._conditions = []

    def filter_by_user(self, user_id: str, model_class: Any) -> "QueryBuilder":
        """Add user isolation filter (required for all queries).

        Args:
            user_id: User ID for data isolation
            model_class: SQLModel class (e.g., Task)

        Returns:
            Self for method chaining
        """
        self._conditions.append(model_class.user_id == user_id)
        return self

    def filter_by_keyword(
        self,
        keyword: Optional[str],
        model_class: Any,
        fields: List[str]
    ) -> "QueryBuilder":
        """Add keyword search filter with case-insensitive partial matching.

        Uses PostgreSQL ILIKE for case-insensitive search across multiple fields
        with OR logic (matches if keyword found in ANY field).

        Args:
            keyword: Search keyword (optional)
            model_class: SQLModel class (e.g., Task)
            fields: List of field names to search (e.g., ["title", "description"])

        Returns:
            Self for method chaining
        """
        if keyword and keyword.strip():
            # Create OR condition: keyword in field1 OR keyword in field2...
            keyword_conditions = []
            search_pattern = f"%{keyword}%"

            for field_name in fields:
                field = getattr(model_class, field_name)
                # Use ilike for case-insensitive partial matching
                keyword_conditions.append(field.ilike(search_pattern))

            if keyword_conditions:
                self._conditions.append(or_(*keyword_conditions))

        return self

    def filter_by_status(
        self,
        completed: Optional[bool],
        model_class: Any
    ) -> "QueryBuilder":
        """Add completion status filter.

        Args:
            completed: True for completed tasks, False for incomplete, None for all
            model_class: SQLModel class (e.g., Task)

        Returns:
            Self for method chaining
        """
        if completed is not None:
            self._conditions.append(model_class.completed == completed)
        return self

    def filter_by_priority(
        self,
        priority: Optional[str],
        model_class: Any
    ) -> "QueryBuilder":
        """Add priority filter.

        Args:
            priority: Priority level ('high', 'medium', 'low') or None for all
            model_class: SQLModel class (e.g., Task)

        Returns:
            Self for method chaining
        """
        if priority and priority != "all":
            self._conditions.append(model_class.priority == priority)
        return self

    def filter_by_tags(
        self,
        tags: Optional[List[str]],
        model_class: Any
    ) -> "QueryBuilder":
        """Add tags filter with OR logic.

        Returns tasks that have ANY of the specified tags (OR logic).

        Args:
            tags: List of tags to filter by (optional)
            model_class: SQLModel class (e.g., Task)

        Returns:
            Self for method chaining
        """
        if tags and len(tags) > 0:
            # Normalize tags (lowercase)
            normalized_tags = [tag.lower() for tag in tags]

            # Build OR condition: task has tag1 OR tag2 OR tag3...
            tag_conditions = []
            for tag in normalized_tags:
                # For SQLite: json_extract checks if tag exists in JSON array
                # For PostgreSQL: use jsonb operator ?
                tag_conditions.append(
                    func.json_extract(model_class.tags, '$').contains(tag)
                )

            if tag_conditions:
                self._conditions.append(or_(*tag_conditions))

        return self

    def filter_by_due_date(
        self,
        due_date_filter: Optional[str],
        model_class: Any,
        timezone_offset: int = 0
    ) -> "QueryBuilder":
        """Add due date filter with predefined categories.

        Supports filtering by:
        - 'overdue': Tasks past their due date
        - 'today': Tasks due today
        - 'this_week': Tasks due this week
        - 'this_month': Tasks due this month
        - 'no_due_date': Tasks without a due date
        - 'all' or None: No filtering

        Args:
            due_date_filter: Due date category or None
            model_class: SQLModel class (e.g., Task)
            timezone_offset: UTC offset in hours for "today" calculation (default: 0)

        Returns:
            Self for method chaining
        """
        if not due_date_filter or due_date_filter == "all":
            return self

        now = datetime.utcnow()

        if due_date_filter == "overdue":
            # Due date < now AND not completed
            self._conditions.append(
                and_(
                    model_class.due_date < now,
                    model_class.completed == False
                )
            )

        elif due_date_filter == "today":
            # Due date is today (considering timezone)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            self._conditions.append(
                and_(
                    model_class.due_date >= today_start,
                    model_class.due_date < today_end
                )
            )

        elif due_date_filter == "this_week":
            # Due date is within this week
            week_start = now - timedelta(days=now.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = week_start + timedelta(days=7)
            self._conditions.append(
                and_(
                    model_class.due_date >= week_start,
                    model_class.due_date < week_end
                )
            )

        elif due_date_filter == "this_month":
            # Due date is within this month
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                month_end = month_start.replace(year=now.year + 1, month=1)
            else:
                month_end = month_start.replace(month=now.month + 1)
            self._conditions.append(
                and_(
                    model_class.due_date >= month_start,
                    model_class.due_date < month_end
                )
            )

        elif due_date_filter == "no_due_date":
            # Tasks without a due date
            self._conditions.append(model_class.due_date == None)

        return self

    def order_by(self, model_class: Any, field_name: str, descending: bool = False) -> "QueryBuilder":
        """Add ORDER BY clause to query.

        Args:
            model_class: SQLModel class (e.g., Task)
            field_name: Name of field to order by
            descending: True for DESC, False for ASC (default)

        Returns:
            Self for method chaining
        """
        field = getattr(model_class, field_name)
        if descending:
            self.query = self.query.order_by(col(field).desc())
        else:
            self.query = self.query.order_by(col(field).asc())
        return self

    def paginate(self, page: int, page_size: int) -> "QueryBuilder":
        """Add pagination (LIMIT and OFFSET) to query.

        Args:
            page: Page number (1-indexed)
            page_size: Number of results per page

        Returns:
            Self for method chaining
        """
        offset = (page - 1) * page_size
        self.query = self.query.limit(page_size).offset(offset)
        return self

    def build(self) -> Select:
        """Build final query with all applied filters.

        Combines all filter conditions with AND logic and returns
        the complete SQLAlchemy Select statement.

        Returns:
            Complete SQLAlchemy Select statement ready for execution
        """
        if self._conditions:
            # Combine all conditions with AND
            self.query = self.query.where(and_(*self._conditions))

        return self

    def count_query(self) -> Select:
        """Build a count query (for total_count without pagination).

        Returns:
            SQLAlchemy Select statement for counting results
        """
        # Apply all conditions but remove limit/offset
        count_query = self.query
        if self._conditions:
            count_query = count_query.where(and_(*self._conditions))

        return count_query
