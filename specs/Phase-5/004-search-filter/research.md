# Technical Research: Task Search & Advanced Filtering

**Feature**: 004-search-filter
**Date**: 2026-02-14
**Phase**: 0 (Outline & Research)

## Research Overview

Task Search & Advanced Filtering requires implementing efficient keyword search across text fields, multiple filter types (status, priority, tags, due date), and combining filters with AND/OR logic. Performance must be maintained for large task lists (10,000+ tasks) with search results returning in < 500ms.

---

## Research Question 1: Keyword Search Implementation

### Decision: PostgreSQL ILIKE with Composite Indexes

**Rationale:**
- PostgreSQL ILIKE operator provides case-insensitive pattern matching
- Supports partial matching (substring search): `%keyword%`
- No additional extensions needed (unlike pg_trgm for fuzzy search)
- Fast enough for < 10,000 tasks with proper indexes
- Simple to implement and maintain

**SQL Pattern:**

```sql
-- Search in title OR description
SELECT * FROM tasks
WHERE user_id = ?
AND (
  title ILIKE '%grocery%'
  OR description ILIKE '%grocery%'
);
```

**SQLModel/SQLAlchemy Pattern:**

```python
from sqlmodel import select, or_, func

def search_tasks(session, user_id: int, keyword: str):
    """Search tasks by keyword in title or description."""
    # Add wildcards for partial matching
    pattern = f"%{keyword}%"

    statement = select(Task).where(
        Task.user_id == user_id,
        or_(
            func.lower(Task.title).like(func.lower(pattern)),
            func.lower(Task.description).like(func.lower(pattern))
        )
    )

    return session.exec(statement).all()
```

**Index Strategy:**

```sql
-- Composite index for efficient user + text search
CREATE INDEX idx_tasks_user_title ON tasks(user_id, LOWER(title));
CREATE INDEX idx_tasks_user_description ON tasks(user_id, LOWER(description));

-- Alternative: GIN index for full-text search (if needed later)
-- CREATE INDEX idx_tasks_title_gin ON tasks USING gin(to_tsvector('english', title));
```

**Performance:**
- Without index: O(n) full table scan - 500ms for 10,000 tasks
- With index: O(log n) index scan - 50-100ms for 10,000 tasks
- ILIKE with % prefix disables index, but user_id filter reduces scan

**Alternatives Considered:**
- ❌ PostgreSQL Full-Text Search (pg_trgm): Overkill for simple substring matching, requires extension
- ❌ Elasticsearch: External service, adds complexity, not needed for < 10,000 tasks
- ❌ Application-level filtering: Too slow, doesn't scale
- ✅ ILIKE with indexes: Simple, fast enough, no extensions needed

---

## Research Question 2: Multi-Field Filtering (Status, Priority, Tags, Due Date)

### Decision: Incremental WHERE Clause Building

**Rationale:**
- Dynamically build WHERE clauses based on active filters
- Each filter is optional (user may apply none, one, or all)
- AND logic between filter types (status + priority + tags all must match)
- OR logic within tag filters (show tasks with work OR home tags)
- SQLModel supports dynamic query building

**Implementation Pattern:**

```python
from typing import Optional, List
from datetime import datetime, date
from sqlmodel import Session, select, or_, and_
from sqlalchemy import func

def search_and_filter_tasks(
    session: Session,
    user_id: int,
    keyword: Optional[str] = None,
    status_filter: Optional[bool] = None,  # True=completed, False=incomplete, None=all
    priority_filter: Optional[str] = None,  # "high", "medium", "low", None=all
    tags_filter: Optional[List[str]] = None,  # ["work", "urgent"] with OR logic
    due_date_filter: Optional[str] = None,  # "overdue", "today", "this_week", "this_month", "no_due_date"
    due_date_range: Optional[tuple[date, date]] = None  # Custom range (start, end)
) -> List[Task]:
    """Search and filter tasks with multiple criteria."""

    # Start with base query
    statement = select(Task).where(Task.user_id == user_id)

    # Apply keyword search (OR: title OR description)
    if keyword:
        pattern = f"%{keyword}%"
        statement = statement.where(
            or_(
                func.lower(Task.title).like(func.lower(pattern)),
                func.lower(Task.description).like(func.lower(pattern))
            )
        )

    # Apply status filter
    if status_filter is not None:
        statement = statement.where(Task.completed == status_filter)

    # Apply priority filter
    if priority_filter:
        statement = statement.where(Task.priority == priority_filter)

    # Apply tags filter (OR logic: work OR urgent)
    if tags_filter:
        tag_conditions = [Task.tags.contains([tag]) for tag in tags_filter]
        statement = statement.where(or_(*tag_conditions))

    # Apply due date filter
    if due_date_filter:
        today = date.today()

        if due_date_filter == "overdue":
            statement = statement.where(Task.due_date < today)

        elif due_date_filter == "today":
            statement = statement.where(Task.due_date == today)

        elif due_date_filter == "this_week":
            week_end = today + timedelta(days=7)
            statement = statement.where(
                Task.due_date >= today,
                Task.due_date <= week_end
            )

        elif due_date_filter == "this_month":
            month_end = today.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            statement = statement.where(
                Task.due_date >= today,
                Task.due_date <= month_end
            )

        elif due_date_filter == "no_due_date":
            statement = statement.where(Task.due_date == None)

    # Apply custom date range
    if due_date_range:
        start_date, end_date = due_date_range
        statement = statement.where(
            Task.due_date >= start_date,
            Task.due_date <= end_date
        )

    # Execute query
    return session.exec(statement).all()
```

**SQL Generated Example:**

```sql
SELECT * FROM tasks
WHERE user_id = ?
AND (LOWER(title) LIKE LOWER('%grocery%') OR LOWER(description) LIKE LOWER('%grocery%'))
AND completed = false
AND priority = 'high'
AND (tags @> '["work"]'::jsonb OR tags @> '["urgent"]'::jsonb)
AND due_date < '2026-02-14';
```

**Alternatives Considered:**
- ❌ Separate queries for each filter: Inefficient, doesn't support combined filters
- ❌ Application-level filtering: Too slow for large datasets
- ✅ Dynamic WHERE clause building: Efficient, flexible, database-optimized

---

## Research Question 3: Performance Optimization for Large Task Lists

### Decision: Database Indexes + Pagination + Query Optimization

**Rationale:**
- Database-level filtering is 10-100x faster than application-level
- Indexes drastically reduce query time for filtered searches
- Pagination prevents loading 10,000+ tasks into memory
- Proper index usage ensures < 500ms response time

**Index Strategy:**

```sql
-- Existing indexes (from previous features)
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_tags ON tasks USING gin(tags);

-- NEW indexes for search/filter
CREATE INDEX idx_tasks_user_completed ON tasks(user_id, completed);
CREATE INDEX idx_tasks_user_priority ON tasks(user_id, priority);
CREATE INDEX idx_tasks_user_due_date ON tasks(user_id, due_date);
CREATE INDEX idx_tasks_user_title_lower ON tasks(user_id, LOWER(title));
CREATE INDEX idx_tasks_user_description_lower ON tasks(user_id, LOWER(description));
```

**Pagination Pattern:**

```python
def search_with_pagination(
    session: Session,
    user_id: int,
    keyword: Optional[str] = None,
    # ... other filters ...
    page: int = 1,
    page_size: int = 20
) -> dict:
    """Search with pagination for large result sets."""

    # Build query with filters (same as above)
    statement = build_search_query(user_id, keyword, ...)

    # Get total count
    count_statement = select(func.count()).select_from(
        statement.subquery()
    )
    total_count = session.exec(count_statement).one()

    # Apply pagination
    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)

    # Execute query
    tasks = session.exec(statement).all()

    return {
        "tasks": tasks,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }
```

**Query Optimization:**

```python
# Use EXPLAIN ANALYZE to verify index usage
def explain_search_query(keyword: str, filters: dict):
    """Analyze query performance."""
    query = build_search_query(keyword, filters)

    # PostgreSQL EXPLAIN ANALYZE
    result = session.execute(f"EXPLAIN ANALYZE {query}")

    # Check for:
    # ✅ Index Scan (good)
    # ❌ Seq Scan (bad - add index)
```

**Performance Targets:**
- 1,000 tasks: < 100ms (with indexes)
- 10,000 tasks: < 500ms (with indexes + pagination)
- 100,000 tasks: < 1s (with indexes + pagination + query optimization)

**Alternatives Considered:**
- ❌ Load all tasks into memory: Doesn't scale, high memory usage
- ❌ Client-side filtering: Too slow, wasted bandwidth
- ✅ Database indexes + pagination: Scalable, efficient, standard practice

---

## Research Question 4: Natural Language Search via AI Chatbot

### Decision: Regex Pattern Extraction + GPT-4 Intent Fallback

**Rationale:**
- Regex handles 80-90% of common search patterns
- GPT-4 fallback handles complex or ambiguous queries
- No external NLP library needed
- Leverages existing OpenAI Agents SDK integration

**Parsing Patterns:**

```python
import re
from typing import Optional, Dict, List

# Pattern 1: "search for X" or "find X"
KEYWORD_SEARCH_PATTERN = r'(?:search|find|show|list)(?:\s+for)?\s+(.+?)(?:\s+tasks?)?$'

# Pattern 2: "show incomplete tasks"
STATUS_PATTERN = r'(completed|incomplete|done|pending|active)'

# Pattern 3: "high priority tasks"
PRIORITY_PATTERN = r'(high|medium|low)\s+priority'

# Pattern 4: "show work tasks" or "find urgent and work tasks"
TAG_PATTERN = r'(?:tagged|with)?\s+([a-z0-9\-_]+)(?:\s+and\s+([a-z0-9\-_]+))*'

# Pattern 5: "overdue tasks" or "due today"
DUE_DATE_PATTERN = r'(overdue|today|this\s+week|this\s+month|no\s+due\s+date)'

# Pattern 6: Combined: "search grocery in incomplete high priority work tasks"
COMBINED_PATTERN = r'(?:search|find)\s+(.+?)\s+in\s+(.*)'

def parse_search_command(user_input: str) -> Dict:
    """Extract search parameters from natural language."""
    user_input_lower = user_input.lower()

    filters = {
        "keyword": None,
        "status_filter": None,
        "priority_filter": None,
        "tags_filter": [],
        "due_date_filter": None
    }

    # Extract keyword
    match = re.search(KEYWORD_SEARCH_PATTERN, user_input_lower)
    if match:
        filters["keyword"] = match.group(1).strip()

    # Extract status
    if "incomplete" in user_input_lower or "pending" in user_input_lower or "active" in user_input_lower:
        filters["status_filter"] = False
    elif "completed" in user_input_lower or "done" in user_input_lower:
        filters["status_filter"] = True

    # Extract priority
    match = re.search(PRIORITY_PATTERN, user_input_lower)
    if match:
        filters["priority_filter"] = match.group(1)

    # Extract tags (work, urgent, etc.)
    # Look for tag names (assuming user has tags: work, home, urgent, shopping, etc.)
    common_tags = ["work", "home", "urgent", "shopping", "personal", "family"]
    for tag in common_tags:
        if tag in user_input_lower:
            filters["tags_filter"].append(tag)

    # Extract due date filter
    match = re.search(DUE_DATE_PATTERN, user_input_lower)
    if match:
        filters["due_date_filter"] = match.group(1).replace(" ", "_")

    return filters
```

**GPT-4 Prompt Enhancement:**

```text
You have access to search_tasks MCP tool with these parameters:
- keyword: Text to search in title/description (case-insensitive, partial match)
- status_filter: null (all), true (completed), false (incomplete)
- priority_filter: null (all), "high", "medium", "low"
- tags_filter: Array of tags (OR logic: ["work", "urgent"] shows tasks with work OR urgent)
- due_date_filter: "overdue", "today", "this_week", "this_month", "no_due_date"

Examples:
- "search for grocery tasks" → search_tasks(keyword="grocery")
- "show incomplete work tasks" → search_tasks(status_filter=false, tags_filter=["work"])
- "find overdue high priority items" → search_tasks(due_date_filter="overdue", priority_filter="high")
- "search report in completed tasks due this week" → search_tasks(keyword="report", status_filter=true, due_date_filter="this_week")

Combined filters use AND logic (all must match). Tag filters use OR logic (any tag matches).
```

**Alternatives Considered:**
- ❌ Pure regex only: Brittle, misses complex patterns
- ❌ Pure GPT-4 only: Slower, costs more, less reliable for simple patterns
- ❌ Dedicated NLP library (spaCy, NLTK): Overkill, adds dependencies
- ✅ Hybrid regex + GPT-4: Fast for common cases, accurate for complex ones

---

## Research Question 5: Debounced Search Input (300ms Delay)

### Decision: Frontend Debouncing with useDebounce Hook

**Rationale:**
- Prevents excessive API calls during typing
- 300ms is optimal balance (responsive but not spammy)
- Frontend debouncing reduces backend load
- React hook pattern is reusable

**Frontend Implementation:**

```typescript
// hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage in SearchInput component
function SearchInput() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  useEffect(() => {
    if (debouncedSearchTerm) {
      // Call API with debounced value
      searchTasks(debouncedSearchTerm);
    }
  }, [debouncedSearchTerm]);

  return (
    <input
      type="text"
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      placeholder="Search tasks..."
    />
  );
}
```

**Backend Rate Limiting (Optional):**

```python
from fastapi_limiter import limiter

@app.get("/api/tasks/search")
@limiter.limit("10/second")  # Max 10 requests per second per user
async def search_tasks(...):
    pass
```

**Alternatives Considered:**
- ❌ No debouncing: Too many API calls, poor performance
- ❌ Backend-only throttling: Still processes every keystroke, wasteful
- ✅ Frontend debouncing: Prevents unnecessary requests, optimal UX

---

## Research Question 6: Keyword Highlighting in Search Results

### Decision: Client-Side Highlighting with React Component

**Rationale:**
- Highlighting done in frontend (backend returns plain text)
- No HTML injection risk (React escapes by default)
- Flexible styling (bold, background color, etc.)
- Case-insensitive highlighting matches case-insensitive search

**Frontend Implementation:**

```typescript
// components/HighlightedText.tsx
interface HighlightedTextProps {
  text: string;
  keyword: string;
}

export function HighlightedText({ text, keyword }: HighlightedTextProps) {
  if (!keyword) {
    return <>{text}</>;
  }

  // Case-insensitive replace with highlighting
  const regex = new RegExp(`(${keyword})`, 'gi');
  const parts = text.split(regex);

  return (
    <>
      {parts.map((part, index) =>
        regex.test(part) ? (
          <mark key={index} className="bg-yellow-200 font-semibold">
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        )
      )}
    </>
  );
}

// Usage in TaskCard
<TaskCard task={task}>
  <h3>
    <HighlightedText text={task.title} keyword={searchKeyword} />
  </h3>
  <p>
    <HighlightedText text={task.description} keyword={searchKeyword} />
  </p>
</TaskCard>
```

**Alternatives Considered:**
- ❌ Backend HTML injection: Security risk, complexity
- ❌ No highlighting: Poor UX, hard to see why task matched
- ✅ Client-side React highlighting: Safe, flexible, performant

---

## Research Question 7: MCP Tool Contract for search_tasks

### Decision: Single search_tasks Tool with Optional Parameters

**Rationale:**
- One tool handles all search/filter combinations
- All parameters optional (user can apply none, one, or all)
- Backward compatible (works with existing list_tasks)
- Natural language friendly

**MCP Tool Contract:**

```json
{
  "tool_name": "search_tasks",
  "description": "Search and filter tasks by keyword, status, priority, tags, and due date",
  "category": "task_management",
  "version": "1.0.0",
  "input_schema": {
    "type": "object",
    "properties": {
      "keyword": {
        "type": "string",
        "description": "Search keyword for title/description (case-insensitive, partial match)",
        "examples": ["grocery", "report", "call"]
      },
      "status_filter": {
        "type": "boolean",
        "nullable": true,
        "description": "Filter by completion status: true (completed), false (incomplete), null (all)",
        "examples": [true, false, null]
      },
      "priority_filter": {
        "type": "string",
        "enum": ["high", "medium", "low"],
        "nullable": true,
        "description": "Filter by priority level, null for all",
        "examples": ["high", "medium", null]
      },
      "tags_filter": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Filter by tags (OR logic: tasks with any of these tags)",
        "examples": [["work"], ["work", "urgent"], []]
      },
      "due_date_filter": {
        "type": "string",
        "enum": ["overdue", "today", "this_week", "this_month", "no_due_date"],
        "nullable": true,
        "description": "Filter by due date category",
        "examples": ["overdue", "today", null]
      },
      "page": {
        "type": "integer",
        "default": 1,
        "minimum": 1,
        "description": "Page number for pagination"
      },
      "page_size": {
        "type": "integer",
        "default": 20,
        "minimum": 1,
        "maximum": 100,
        "description": "Number of results per page"
      }
    },
    "required": []
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "tasks": {
        "type": "array",
        "items": {"$ref": "#/definitions/Task"}
      },
      "total_count": {
        "type": "integer",
        "description": "Total matching tasks (all pages)"
      },
      "filtered_count": {
        "type": "integer",
        "description": "Number of tasks after filtering"
      },
      "page": {"type": "integer"},
      "page_size": {"type": "integer"},
      "total_pages": {"type": "integer"}
    }
  }
}
```

**Alternatives Considered:**
- ❌ Separate tools for each filter type: Too many tools, complex to use
- ❌ Extend list_tasks: Would break backward compatibility
- ✅ New search_tasks tool: Clear intent, all filters in one call

---

## Research Summary

### Technical Approach

**Backend:**
1. Implement search_and_filter_tasks service method with dynamic WHERE clause building
2. Add 5 composite indexes for efficient filtering
3. Create search_tasks MCP tool with all filter parameters
4. Implement pagination for large result sets
5. Update agent prompt with search examples

**Frontend:**
1. Create SearchInput component with debounced input (300ms)
2. Create FilterBar component with status/priority/tags/due date filters
3. Create HighlightedText component for keyword highlighting
4. Implement useDebounce hook for search input
5. Add result count display ("Showing X of Y tasks")
6. Add "Clear filters" button

**Database:**
1. Add 5 new composite indexes (Alembic migration)
2. No schema changes needed (all fields exist)

**AI Agent:**
1. Add regex patterns for search command parsing
2. Update prompt with search examples
3. Register search_tasks MCP tool

### Performance Validation

- Keyword search: < 100ms with indexes (user_id + LOWER(title/description))
- Multi-filter queries: < 200ms with composite indexes
- Pagination: < 50ms for count query + result query
- 10,000 tasks: < 500ms with all optimizations

### No Clarifications Needed

All technical questions resolved. Ready for Phase 1 (Design & Contracts).

---

**Research Complete**: 2026-02-14
**Next Phase**: Phase 1 - Design & Contracts
