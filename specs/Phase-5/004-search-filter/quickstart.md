# Quick Start Guide: Task Search & Advanced Filtering

**Feature**: 004-search-filter
**Date**: 2026-02-14
**Phase**: 1 (Design & Contracts)

---

## Implementation Overview

**Time Estimate**: 8-12 hours
**Complexity**: Medium-High (No schema changes, but complex query logic + frontend components)
**Dependencies**: Existing priority, tags, and due dates features MUST be implemented first

---

## Prerequisites Check

**CRITICAL:** This feature depends on three other features being implemented first:

1. ✅ **Priority** (002-due-dates-reminders OR separate priority feature)
   - Requires: `tasks.priority` column (enum: high/medium/low)

2. ✅ **Tags** (003-task-tags)
   - Requires: `tasks.tags` JSONB column + GIN index

3. ✅ **Due Dates** (002-due-dates-reminders)
   - Requires: `tasks.due_date` column (date or datetime)

**Verify prerequisites before starting:**

```bash
# Check if columns exist
psql -d your_database -c "\d tasks"

# Should show:
# - priority (text or enum)
# - tags (jsonb)
# - due_date (date or timestamp)
```

---

## Step-by-Step Implementation

### Step 1: Database Indexes (30 minutes)

**Create Alembic Migration:**

```bash
cd backend
alembic revision -m "add_search_filter_indexes"
```

**Edit Migration File:**

```python
"""Add composite indexes for search/filter performance"""

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Composite indexes for efficient filtering
    op.create_index('idx_tasks_user_completed', 'tasks', ['user_id', 'completed'])
    op.create_index('idx_tasks_user_priority', 'tasks', ['user_id', 'priority'])
    op.create_index('idx_tasks_user_due_date', 'tasks', ['user_id', 'due_date'])

    # Functional indexes for case-insensitive search
    op.execute("""
        CREATE INDEX idx_tasks_user_title_lower
        ON tasks(user_id, LOWER(title));
    """)

    op.execute("""
        CREATE INDEX idx_tasks_user_description_lower
        ON tasks(user_id, LOWER(description));
    """)

def downgrade() -> None:
    op.drop_index('idx_tasks_user_description_lower')
    op.drop_index('idx_tasks_user_title_lower')
    op.drop_index('idx_tasks_user_due_date')
    op.drop_index('idx_tasks_user_priority')
    op.drop_index('idx_tasks_user_completed')
```

**Apply Migration:**

```bash
alembic upgrade head
```

---

### Step 2: Backend Service Layer (2-3 hours)

**File**: `backend/src/services/task_service.py`

**Add search_and_filter_tasks Method:**

See `research.md` Research Question 2 for complete implementation (~100 lines).

Key features:
- Dynamic WHERE clause building
- Optional parameters (all filters optional)
- AND logic between filter types
- OR logic within tag filters
- Pagination support
- User isolation enforced

---

### Step 3: Backend Schemas (30 minutes)

**File**: `backend/src/schemas/search.py` (NEW)

```python
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date

class SearchRequest(BaseModel):
    """Request for searching and filtering tasks."""
    keyword: Optional[str] = Field(None, max_length=200)
    status_filter: Optional[bool] = None  # True=completed, False=incomplete, None=all
    priority_filter: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    tags_filter: Optional[List[str]] = None
    due_date_filter: Optional[str] = Field(None, pattern="^(overdue|today|this_week|this_month|no_due_date)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class SearchResponse(BaseModel):
    """Response with search results."""
    tasks: List[TaskResponse]
    total_count: int
    filtered_count: int
    page: int
    page_size: int
    total_pages: int
    applied_filters: dict
```

---

### Step 4: REST API Endpoint (1 hour)

**File**: `backend/src/api/tasks.py`

```python
@router.get("/search", response_model=SearchResponse)
async def search_tasks(
    keyword: Optional[str] = None,
    status_filter: Optional[bool] = None,
    priority_filter: Optional[str] = None,
    tags_filter: Optional[List[str]] = Query(None),
    due_date_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Search and filter tasks."""

    # Call service method
    result = task_service.search_and_filter_tasks(
        session=session,
        user_id=current_user.id,
        keyword=keyword,
        status_filter=status_filter,
        priority_filter=priority_filter,
        tags_filter=tags_filter,
        due_date_filter=due_date_filter,
        page=page,
        page_size=page_size
    )

    return SearchResponse(
        tasks=result["tasks"],
        total_count=result["total_count"],
        filtered_count=result["filtered_count"],
        page=page,
        page_size=page_size,
        total_pages=result["total_pages"],
        applied_filters={
            "keyword": keyword,
            "status": status_filter,
            "priority": priority_filter,
            "tags": tags_filter,
            "due_date": due_date_filter
        }
    )
```

---

### Step 5: MCP Tool (1-2 hours)

**File**: `backend/src/mcp_tools/search_tasks.py` (NEW)

See `research.md` Research Question 7 for MCP contract specification.

**Register Tool:**

```python
# backend/src/ai/agent.py
from mcp_tools.search_tasks import search_tasks_tool

tools = [
    # ... existing tools ...
    search_tasks_tool,  # NEW
]
```

---

### Step 6: Agent Prompt Update (30 minutes)

**File**: `backend/src/ai/agent.py`

**Add to System Prompt:**

```text
You have access to search_tasks tool for advanced task searching and filtering:

search_tasks(keyword, status_filter, priority_filter, tags_filter, due_date_filter)

Examples:
- "search for grocery tasks" → search_tasks(keyword="grocery")
- "show incomplete work tasks" → search_tasks(status_filter=false, tags_filter=["work"])
- "find overdue high priority items" → search_tasks(due_date_filter="overdue", priority_filter="high")
- "search report in completed tasks due this week" → search_tasks(keyword="report", status_filter=true, due_date_filter="this_week")

Filters use AND logic between types (status + priority + tags all must match).
Tag filters use OR logic (any tag matches).
All parameters are optional.
```

**Add Regex Patterns:**

See `research.md` Research Question 4 for regex parsing patterns (~100 lines).

---

### Step 7: Frontend Components (3-4 hours)

**Create 4 New Components:**

1. **SearchInput.tsx** - Debounced search input (300ms)
2. **FilterBar.tsx** - Multi-criteria filter controls
3. **HighlightedText.tsx** - Keyword highlighting in results
4. **TaskList.tsx** - Display results with count

**See `research.md` Research Questions 5-6 for complete implementations.**

---

### Step 8: Frontend Hooks (1 hour)

**useDebounce.ts:**

See `research.md` Research Question 5 for implementation.

**useSearch.ts:**

```typescript
export function useSearch() {
  const [filters, setFilters] = useState<SearchFilters>({
    keyword: '',
    status: null,
    priority: null,
    tags: [],
    dueDate: null
  });

  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);

  const debouncedKeyword = useDebounce(filters.keyword, 300);

  useEffect(() => {
    async function search() {
      setLoading(true);
      const response = await fetch('/api/tasks/search?' + buildQueryString(filters));
      const data = await response.json();
      setResults(data);
      setLoading(false);
    }

    search();
  }, [debouncedKeyword, filters.status, filters.priority, filters.tags, filters.dueDate]);

  return { filters, setFilters, results, loading };
}
```

---

### Step 9: Testing (2-3 hours)

**Backend Tests:**

```bash
# Unit tests
pytest tests/unit/test_search_parsing.py
pytest tests/unit/test_query_builder.py

# Integration tests
pytest tests/integration/test_search_api.py
pytest tests/integration/test_combined_filters.py

# E2E tests
pytest tests/e2e/test_search_workflow.py
```

**Frontend Tests:**

```bash
npm test SearchInput.test.tsx
npm test FilterBar.test.tsx
npm test HighlightedText.test.tsx
```

---

## Testing Checklist

### Backend (pytest)

- [ ] Keyword search (case-insensitive, partial match)
- [ ] Status filter (completed/incomplete/all)
- [ ] Priority filter (high/medium/low/all)
- [ ] Tags filter (single tag, multiple tags OR logic)
- [ ] Due date filter (overdue, today, this_week, this_month, no_due_date)
- [ ] Combined filters (keyword + status + priority + tags + due_date)
- [ ] Pagination (page 1, page 2, page size variations)
- [ ] User isolation (can't search other users' tasks)
- [ ] Empty results (friendly message)
- [ ] Performance (< 500ms for 1,000 tasks)

### Frontend (Jest + RTL)

- [ ] SearchInput debounces correctly (300ms delay)
- [ ] FilterBar updates filters on change
- [ ] HighlightedText highlights keywords
- [ ] TaskList displays result count
- [ ] Clear filters button resets all filters
- [ ] Loading state displays while searching

### E2E (Playwright)

- [ ] Search via chatbot: "search grocery tasks"
- [ ] Filter via chatbot: "show incomplete work tasks"
- [ ] Combined search: "search report in high priority tasks due today"
- [ ] Keyword highlighting works in UI
- [ ] Pagination works (next/prev buttons)
- [ ] Filters persist in UI state (not lost on component re-render)

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (backend + frontend)
- [ ] Migration tested on staging (5 indexes created)
- [ ] Search performance tested (< 500ms for 1,000 tasks)
- [ ] MCP tool registered with agent
- [ ] Frontend builds without errors
- [ ] Debouncing works (300ms delay verified)
- [ ] User isolation verified
- [ ] Keyword highlighting works

### Deployment Steps

1. **Backend:**
   ```bash
   # Run migration
   alembic upgrade head

   # Verify indexes
   psql -c "SELECT * FROM pg_indexes WHERE tablename = 'tasks';"

   # Restart backend
   systemctl restart backend
   ```

2. **Frontend:**
   ```bash
   npm run build
   vercel deploy
   ```

3. **Verification:**
   ```bash
   # Test search API
   curl -X GET '/api/tasks/search?keyword=grocery&status_filter=false'

   # Test MCP tool via chatbot
   # "search grocery in incomplete tasks"
   ```

---

## Performance Optimization

### Database

- ✅ 5 composite indexes created (migration)
- ✅ Always include user_id in WHERE clause
- ✅ Use ILIKE for case-insensitive search
- ✅ Pagination for large result sets

### Backend

- Use connection pooling (already configured)
- Cache common queries (optional)
- Monitor slow queries with EXPLAIN ANALYZE

### Frontend

- Debounce search input (300ms) ✅
- Memoize filter components (useMemo)
- Virtualize large result lists (react-window)

---

## Troubleshooting

### Issue: Migration fails "index already exists"

**Fix:** Check if previous migration partially succeeded
```bash
alembic downgrade -1
alembic upgrade head
```

### Issue: Search is slow (> 500ms)

**Fix:** Verify indexes exist and are used
```sql
EXPLAIN ANALYZE
SELECT * FROM tasks
WHERE user_id = 1 AND LOWER(title) LIKE LOWER('%grocery%');

-- Should show "Index Scan" not "Seq Scan"
```

### Issue: Debouncing not working

**Fix:** Check useDebounce hook implementation
```typescript
// Ensure setTimeout cleanup is working
useEffect(() => {
  const handler = setTimeout(() => {
    setDebouncedValue(value);
  }, delay);

  return () => clearTimeout(handler);  // CRITICAL
}, [value, delay]);
```

### Issue: Tags filter not working

**Fix:** Ensure tags feature is implemented first
```sql
-- Check tags column exists
SELECT tags FROM tasks LIMIT 1;

-- Check GIN index exists
SELECT * FROM pg_indexes WHERE indexname = 'idx_tasks_tags';
```

---

## Related Documentation

- **Research**: See `research.md` for detailed technical decisions (7 research questions)
- **Plan**: See `plan.md` for constitution check and architecture
- **Spec**: See `spec.md` for user stories and requirements

---

**Quick Start Complete**: 2026-02-14
**Total Implementation Time**: 8-12 hours
**Next Phase**: Task Breakdown (`/sp.tasks`)
**Dependencies**: Priority, Tags, and Due Dates features MUST be implemented first
