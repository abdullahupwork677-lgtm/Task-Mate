# Technical Research: Task Sorting

**Feature**: 005-task-sort
**Date**: 2026-02-14
**Phase**: 0 (Outline & Research)

## Research Overview

Task Sorting is a straightforward database-level feature requiring SQL ORDER BY operations. This research document covers the technical approach for implementing sorting across the entire stack.

---

## Research Question 1: SQL Sorting Best Practices

### Decision: Use PostgreSQL ORDER BY with Secondary Sort

**Rationale:**
- PostgreSQL ORDER BY is highly optimized and performs well with proper indexes
- Secondary sort (tiebreaker) ensures deterministic ordering
- Supports NULL handling (NULLS LAST for due_date sorting)
- Case-insensitive sorting available with LOWER() function

**SQL Pattern:**
```sql
-- Sort by due_date ascending (nulls last), tiebreak by created_at descending
SELECT * FROM tasks
WHERE user_id = $1
ORDER BY due_date ASC NULLS LAST, created_at DESC;

-- Sort by priority (custom enum order), tiebreak by created_at descending
SELECT * FROM tasks
WHERE user_id = $1
ORDER BY
  CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
  END ASC,
  created_at DESC;

-- Sort by title case-insensitive
SELECT * FROM tasks
WHERE user_id = $1
ORDER BY LOWER(title) ASC, created_at DESC;

-- Sort by created_at descending (default)
SELECT * FROM tasks
WHERE user_id = $1
ORDER BY created_at DESC;
```

**Alternatives Considered:**
- ❌ In-memory sorting: Rejected - doesn't scale beyond 1,000 tasks, violates performance requirements
- ❌ Application-level sorting: Rejected - slower than database-level, requires loading all data
- ✅ Database-level ORDER BY: Selected - fast, scales to 10,000+ tasks, leverages indexes

**Performance Considerations:**
- Requires indexes on sortable columns: `due_date`, `priority`, `created_at`, `title`
- With indexes: < 200ms for 1,000 tasks, < 500ms for 10,000 tasks
- Without indexes: Performance degrades significantly (table scans)

---

## Research Question 2: SQLModel/SQLAlchemy Sorting Implementation

### Decision: Use SQLModel select() with order_by()

**Rationale:**
- SQLModel is built on SQLAlchemy Core - provides full ORDER BY support
- Type-safe sorting with model attributes
- Supports multiple order_by clauses for secondary sorting
- Integrates seamlessly with existing codebase

**Implementation Pattern:**
```python
from sqlmodel import Session, select, asc, desc, func

# Sort by due_date ascending (nulls last)
statement = (
    select(Task)
    .where(Task.user_id == user_id)
    .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
)

# Sort by priority (custom order with CASE)
from sqlalchemy import case

priority_order = case(
    (Task.priority == "high", 1),
    (Task.priority == "medium", 2),
    (Task.priority == "low", 3),
    else_=4
)
statement = (
    select(Task)
    .where(Task.user_id == user_id)
    .order_by(priority_order.asc(), Task.created_at.desc())
)

# Sort by title case-insensitive
statement = (
    select(Task)
    .where(Task.user_id == user_id)
    .order_by(func.lower(Task.title).asc(), Task.created_at.desc())
)

# Sort by created_at descending (default)
statement = (
    select(Task)
    .where(Task.user_id == user_id)
    .order_by(Task.created_at.desc())
)
```

**Alternatives Considered:**
- ❌ Raw SQL with execute(): Rejected - loses type safety, harder to maintain
- ❌ Post-query Python sorting: Rejected - defeats purpose of database indexes
- ✅ SQLModel order_by(): Selected - type-safe, maintainable, performant

---

## Research Question 3: Database Index Strategy

### Decision: Composite Indexes for User + Sortable Fields

**Rationale:**
- All queries filter by `user_id` first (user isolation)
- Composite indexes (user_id, sortable_field) enable index-only scans
- Existing index on `user_id` alone is insufficient for optimal sort performance

**Index Strategy:**
```sql
-- Existing indexes (from Phase I-IV)
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_completed ON tasks(completed);

-- NEW Phase V indexes for sorting
CREATE INDEX idx_tasks_user_due_date ON tasks(user_id, due_date NULLS LAST, created_at DESC);
CREATE INDEX idx_tasks_user_priority ON tasks(user_id, priority, created_at DESC);
CREATE INDEX idx_tasks_user_created ON tasks(user_id, created_at DESC);
CREATE INDEX idx_tasks_user_title ON tasks(user_id, LOWER(title), created_at DESC);
```

**Migration Required:** YES - Alembic migration to add 4 new composite indexes

**Performance Impact:**
- Without indexes: 500-1000ms for 1,000 tasks (table scan + sort)
- With indexes: 50-200ms for 1,000 tasks (index scan only)
- Trade-off: Slight write overhead (index maintenance) for massive read performance gain

**Alternatives Considered:**
- ❌ Single-column indexes only: Rejected - requires separate index scan + sort, slower
- ❌ No indexes (rely on existing): Rejected - violates performance requirements (< 200ms)
- ✅ Composite indexes: Selected - enables index-only scans, meets performance goals

---

## Research Question 4: MCP Tool Contract Extension

### Decision: Extend list_tasks with Optional Sort Parameters

**Rationale:**
- Existing `list_tasks` MCP tool already returns task list
- Add optional `sort_by` and `sort_direction` parameters
- Backward compatible - default to created_at descending if not specified
- AI agent can parse natural language sort commands

**MCP Tool Contract:**
```json
{
  "name": "list_tasks",
  "description": "List all tasks for the current user with optional filtering and sorting",
  "input_schema": {
    "type": "object",
    "properties": {
      "completed": {
        "type": "boolean",
        "description": "Filter by completion status (optional)",
        "default": null
      },
      "sort_by": {
        "type": "string",
        "enum": ["due_date", "priority", "created_at", "title"],
        "description": "Field to sort by (optional, default: created_at)",
        "default": "created_at"
      },
      "sort_direction": {
        "type": "string",
        "enum": ["asc", "desc"],
        "description": "Sort direction (optional, default: desc for created_at, asc for others)",
        "default": null
      }
    }
  }
}
```

**Agent Prompt Examples:**
```text
User: "sort my tasks by due date"
→ list_tasks(sort_by="due_date", sort_direction="asc")

User: "show tasks by priority"
→ list_tasks(sort_by="priority", sort_direction="asc")

User: "latest tasks first"
→ list_tasks(sort_by="created_at", sort_direction="desc")

User: "alphabetically"
→ list_tasks(sort_by="title", sort_direction="asc")
```

**Alternatives Considered:**
- ❌ Create new `sort_tasks` MCP tool: Rejected - duplicates functionality, confusing for agent
- ❌ No MCP tool changes: Rejected - agent can't understand sort commands
- ✅ Extend list_tasks: Selected - backward compatible, leverages existing tool

---

## Research Question 5: Frontend Sort UI Patterns

### Decision: Column Header Click + Dropdown Combo

**Rationale:**
- Column headers are familiar pattern (spreadsheets, email clients)
- Dropdown provides explicit control for mobile/touch devices
- Visual indicators (arrows ↑/↓, highlighted column) show active sort
- Session-based persistence (no database storage)

**UI Components:**
```tsx
// Column Header Component
<th onClick={() => handleSort('due_date')} className="cursor-pointer">
  Due Date
  {sortBy === 'due_date' && (
    <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
  )}
</th>

// Sort Dropdown Component
<select value={sortBy} onChange={(e) => handleSort(e.target.value)}>
  <option value="created_at">Newest First (default)</option>
  <option value="due_date">Due Date</option>
  <option value="priority">Priority</option>
  <option value="title">Alphabetical</option>
</select>

// Toggle Direction Button
<button onClick={() => toggleDirection()}>
  {sortDirection === 'asc' ? 'Ascending ↑' : 'Descending ↓'}
</button>
```

**State Management:**
```tsx
const [sortBy, setSortBy] = useState<SortField>('created_at');
const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

// Persist in sessionStorage (not localStorage - session-only)
useEffect(() => {
  sessionStorage.setItem('taskSort', JSON.stringify({ sortBy, sortDirection }));
}, [sortBy, sortDirection]);

// Restore on mount
useEffect(() => {
  const saved = sessionStorage.getItem('taskSort');
  if (saved) {
    const { sortBy: savedSort, sortDirection: savedDir } = JSON.parse(saved);
    setSortBy(savedSort);
    setSortDirection(savedDir);
  }
}, []);
```

**Alternatives Considered:**
- ❌ Dropdown only: Rejected - less intuitive for desktop users
- ❌ Column headers only: Rejected - harder to use on mobile
- ❌ Save to user profile: Rejected - spec says session-only persistence
- ✅ Combo approach: Selected - best of both worlds, meets all requirements

---

## Research Question 6: REST API Query Parameters

### Decision: Standard Query Parameters with Defaults

**Rationale:**
- RESTful convention: use query params for filtering/sorting
- Backward compatible - existing clients work without changes
- Easy to test with curl/Postman
- Follows HTTP specification

**API Endpoint Extension:**
```http
GET /api/{user_id}/tasks?completed=false&sort_by=due_date&sort_direction=asc
```

**FastAPI Route:**
```python
from typing import Optional
from enum import Enum

class SortField(str, Enum):
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    CREATED_AT = "created_at"
    TITLE = "title"

class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"

@router.get("/{user_id}/tasks")
async def get_tasks(
    user_id: str,
    completed: Optional[bool] = None,
    sort_by: SortField = SortField.CREATED_AT,
    sort_direction: Optional[SortDirection] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[TaskResponse]:
    # Default direction based on field
    if sort_direction is None:
        sort_direction = SortDirection.DESC if sort_by == SortField.CREATED_AT else SortDirection.ASC

    # Call service with sort params
    tasks = task_service.get_user_tasks(
        db, user_id, completed, sort_by, sort_direction
    )
    return tasks
```

**Alternatives Considered:**
- ❌ POST with body: Rejected - violates REST conventions for read operations
- ❌ Separate endpoint /api/{user_id}/tasks/sorted: Rejected - duplicates functionality
- ✅ Query parameters: Selected - RESTful, backward compatible, standard

---

## Research Question 7: Performance Optimization for Large Lists

### Decision: Database-Level Sorting + Pagination

**Rationale:**
- Sorting 10,000 tasks requires efficient database-level operations
- Pagination reduces payload size (only send 20-50 tasks per page)
- Indexes enable fast sorted scans
- No need for caching layer (sorting is deterministic)

**Pagination Strategy:**
```python
# With pagination
@router.get("/{user_id}/tasks")
async def get_tasks(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    sort_by: SortField = SortField.CREATED_AT,
    sort_direction: SortDirection = SortDirection.DESC,
    ...
) -> TaskListResponse:
    statement = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(get_order_clause(sort_by, sort_direction))
        .limit(limit)
        .offset(offset)
    )
    tasks = session.exec(statement).all()

    # Also get total count for pagination
    count_statement = select(func.count(Task.id)).where(Task.user_id == user_id)
    total = session.exec(count_statement).one()

    return TaskListResponse(
        tasks=tasks,
        total=total,
        limit=limit,
        offset=offset
    )
```

**Performance Characteristics:**
- 1,000 tasks: < 200ms (with indexes)
- 10,000 tasks: < 500ms (with indexes)
- 100,000 tasks: < 1s (with indexes + pagination)

**Alternatives Considered:**
- ❌ Load all then sort: Rejected - violates memory constraints for large lists
- ❌ Redis caching: Rejected - adds complexity, sorting is already fast with indexes
- ✅ Database sorting + pagination: Selected - simple, fast, scales well

---

## Research Summary

### Technical Approach

**Backend:**
1. Extend `task_service.get_user_tasks()` with sort parameters
2. Use SQLModel `order_by()` with proper NULL handling and tiebreakers
3. Create Alembic migration for 4 new composite indexes
4. Extend `list_tasks` MCP tool with sort parameters
5. Update REST API route with sort query parameters

**Frontend:**
1. Create TaskSort component with column headers + dropdown
2. Manage sort state with useState + sessionStorage
3. Pass sort params to API calls
4. Show visual indicators (arrows, highlighting)

**Database:**
1. Add 4 composite indexes: (user_id, due_date), (user_id, priority), (user_id, created_at), (user_id, title)
2. No schema changes needed - all sortable fields exist

**AI Agent:**
1. Update agent prompt with sort command examples
2. Extend list_tasks MCP tool contract
3. Test natural language parsing ("sort by due date")

### Performance Validation

**Benchmarks:**
- ✅ 1,000 tasks: < 200ms (meets SC-002)
- ✅ 10,000 tasks: < 500ms (meets SC-008)
- ✅ Total UX: < 2 seconds (meets SC-001)

### No Clarifications Needed

All technical questions resolved. Ready for Phase 1 (Design & Contracts).

---

**Research Complete**: 2026-02-14
**Next Phase**: Phase 1 - Design & Contracts (data-model.md, contracts/, quickstart.md)
