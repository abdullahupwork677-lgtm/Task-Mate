# Quick Start Guide: Task Tags & Categories

**Feature**: 003-task-tags
**Date**: 2026-02-14
**Phase**: 1 (Design & Contracts)

---

## Implementation Overview

**Time Estimate**: 6-8 hours
**Complexity**: Medium (Database extension + MCP tools + Frontend components)
**Dependencies**: Existing auth system, task management API

---

## Step-by-Step Implementation

### Step 1: Database Migration (30 minutes)

**Create Alembic Migration:**

```bash
cd backend
alembic revision -m "add_tags_to_tasks"
```

**Edit Migration File:**

```python
"""Add tags field to tasks table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade() -> None:
    # Add tags column
    op.add_column(
        'tasks',
        sa.Column('tags', JSONB, nullable=False, server_default="'[]'::jsonb")
    )

    # Add GIN index
    op.create_index('idx_tasks_tags', 'tasks', ['tags'], postgresql_using='gin')

def downgrade() -> None:
    op.drop_index('idx_tasks_tags', table_name='tasks')
    op.drop_column('tasks', 'tags')
```

**Apply Migration:**

```bash
alembic upgrade head
```

**Verify:**

```bash
# PostgreSQL console
\d tasks
# Should show: tags | jsonb | not null | default '[]'::jsonb
```

---

### Step 2: Update SQLModel (30 minutes)

**File**: `backend/src/models/task.py`

```python
from typing import List
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON, Index

class Task(SQLModel, table=True):
    # ... existing fields ...

    # NEW: Tags field
    tags: List[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False, server_default='[]')
    )

    __table_args__ = (
        Index('idx_tasks_tags', 'tags', postgresql_using='gin'),
    )
```

**Update Schemas** (`backend/src/schemas/task.py`):

```python
from pydantic import field_validator

class TaskBase(BaseModel):
    # ... existing fields ...
    tags: List[str] = Field(default=[], max_length=20)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        # Normalize and validate (see data-model.md for full code)
        return normalize_tags(tags)
```

---

### Step 3: Create Tag Service (1 hour)

**File**: `backend/src/services/tag_service.py`

```python
import hashlib
from typing import List

class TagService:
    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        """Normalize tags to lowercase and remove duplicates."""
        normalized = []
        seen = set()
        for tag in tags:
            tag = tag.strip().lower()
            if tag and tag not in seen:
                normalized.append(tag)
                seen.add(tag)
        return normalized

    @staticmethod
    def generate_tag_color(tag_name: str) -> str:
        """Generate consistent color for tag using hash."""
        # Full implementation in data-model.md
        hash_obj = hashlib.md5(tag_name.encode())
        return f"#{hash_obj.hexdigest()[:6]}"

    @staticmethod
    def validate_tag(tag: str) -> bool:
        """Validate single tag format."""
        if not tag or len(tag) > 50:
            return False
        cleaned = tag.replace('-', '').replace('_', '').replace(' ', '')
        return cleaned.isalnum()
```

---

### Step 4: Extend Task Service (1-2 hours)

**File**: `backend/src/services/task_service.py`

**Add Methods:**

1. `get_user_tasks()` - Add tag_filter parameter
2. `add_tags_to_task()` - NEW method
3. `remove_tags_from_task()` - NEW method
4. `list_user_tags()` - NEW method

**See data-model.md for complete code examples.**

---

### Step 5: Create MCP Tools (2-3 hours)

**Create 3 NEW tools:**

1. **`backend/src/mcp_tools/add_tag.py`**
   - Input: task_id, tags[]
   - Calls task_service.add_tags_to_task()
   - See contracts/add_tag_mcp.json

2. **`backend/src/mcp_tools/remove_tag.py`**
   - Input: task_id, tags[]
   - Calls task_service.remove_tags_from_task()
   - See contracts/remove_tag_mcp.json

3. **`backend/src/mcp_tools/list_tags.py`**
   - Input: none
   - Calls task_service.list_user_tags()
   - See contracts/list_tags_mcp.json

**Extend 3 EXISTING tools:**

1. **`backend/src/mcp_tools/add_task.py`** (v2.0.0)
   - Add optional tags parameter

2. **`backend/src/mcp_tools/update_task.py`** (v2.0.0)
   - Add optional tags parameter

3. **`backend/src/mcp_tools/list_tasks.py`** (v2.0.0)
   - Add optional tag_filter parameter

**Register Tools:**

```python
# backend/src/ai/agent.py
tools = [
    add_task_tool,
    update_task_tool,
    list_tasks_tool,
    add_tag_tool,      # NEW
    remove_tag_tool,   # NEW
    list_tags_tool,    # NEW
]
```

---

### Step 6: Update Agent Prompt (30 minutes)

**File**: `backend/src/ai/agent.py`

**Add to System Prompt:**

```text
You have access to tag management tools:

1. add_tag(task_id, tags) - Add tags to a task
2. remove_tag(task_id, tags) - Remove tags from a task
3. list_tags() - List all user's tags with counts

Examples:
- "add task buy milk, tags: shopping, urgent" → add_task(title="buy milk", tags=["shopping", "urgent"])
- "add tag work to task 5" → add_tag(task_id=5, tags=["work"])
- "show work tasks" → list_tasks(tag_filter=["work"])
- "what tags do I use most?" → list_tags()

Tags are case-insensitive and normalized to lowercase.
Multiple tags with "and" use OR logic for filtering.
```

---

### Step 7: Frontend Components (2-3 hours)

**Create Components:**

1. **`frontend/src/components/TagBadge.tsx`**
   ```tsx
   interface TagBadgeProps {
     tagName: string;
     onRemove?: () => void;
   }

   export function TagBadge({ tagName, onRemove }: TagBadgeProps) {
     const bgColor = generateTagColor(tagName);
     const textColor = getContrastColor(bgColor);

     return (
       <span
         className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
         style={{ backgroundColor: bgColor, color: textColor }}
       >
         {tagName}
         {onRemove && (
           <button onClick={onRemove} aria-label={`Remove ${tagName}`}>×</button>
         )}
       </span>
     );
   }
   ```

2. **`frontend/src/components/TagInput.tsx`**
   - Multi-select tag input
   - Autocomplete from existing tags
   - Create new tags on Enter

3. **`frontend/src/utils/tagColors.ts`**
   - Client-side hash color generation
   - Must match backend algorithm (see data-model.md)

**Update Components:**

- **TaskCard.tsx** - Display tags as badges
- **TaskForm.tsx** - Add tag input field
- **TaskList.tsx** - Add tag filter dropdown

---

### Step 8: Testing (2 hours)

**Backend Tests:**

```bash
# Unit tests
pytest tests/unit/test_tag_service.py
pytest tests/unit/test_tag_normalization.py
pytest tests/unit/test_color_generator.py

# Integration tests
pytest tests/integration/test_tag_api.py
pytest tests/integration/test_tag_filtering.py

# E2E tests
pytest tests/e2e/test_tag_workflow.py
```

**Frontend Tests:**

```bash
# Component tests
npm test TagBadge.test.tsx
npm test TagInput.test.tsx

# Color generation tests
npm test tagColors.test.ts
```

---

## Testing Checklist

### Backend (pytest)

- [ ] Tag normalization (lowercase, no duplicates)
- [ ] Color generation (deterministic, readable)
- [ ] Add tags (single, multiple, duplicate handling)
- [ ] Remove tags (single, multiple, non-existent)
- [ ] List tags (sorted by count, with colors)
- [ ] Filter by tag (single, multiple OR logic)
- [ ] User isolation (can't tag others' tasks)
- [ ] Validation (max 20 tags, 50 chars each)
- [ ] Edge cases (empty tags, special chars, case sensitivity)

### Frontend (Jest + React Testing Library)

- [ ] TagBadge renders with correct color
- [ ] TagBadge remove button works
- [ ] TagInput accepts new tags
- [ ] TagInput shows autocomplete
- [ ] TaskCard displays multiple tags
- [ ] Tag filter dropdown works
- [ ] Color generation matches backend

### E2E (Playwright)

- [ ] Add task with tags via chatbot
- [ ] Add tag to existing task
- [ ] Remove tag from task
- [ ] Filter tasks by tag
- [ ] List all tags
- [ ] Tags persist after page refresh
- [ ] Tags display correctly across devices

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (backend + frontend)
- [ ] Migration tested on staging database
- [ ] GIN index created successfully
- [ ] MCP tools registered with agent
- [ ] Frontend builds without errors
- [ ] Color generation matches backend/frontend
- [ ] User isolation verified
- [ ] Performance tested (< 100ms tag filtering)

### Deployment Steps

1. **Backend:**
   ```bash
   # Run migration
   alembic upgrade head

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
   # Test tag operations via API
   curl -X POST /api/tasks -d '{"title":"test","tags":["work"]}'

   # Test MCP tools via chatbot
   # "add task buy milk, tags: shopping"
   # "show work tasks"
   ```

---

## Performance Optimization

### Database

- ✅ GIN index on tags field (created in migration)
- ✅ Always include user_id in WHERE clause
- ✅ Use JSONB contains (@>) for filtering

### Backend

- Cache tag colors (optional - computation is < 1ms)
- Paginate list_tags for 100+ unique tags

### Frontend

- Memoize color generation (useMemo)
- Virtualize tag list if 50+ tags

---

## Troubleshooting

### Issue: Migration fails with "column already exists"

**Fix:** Check if previous migration attempt partially succeeded
```bash
# Rollback and retry
alembic downgrade -1
alembic upgrade head
```

### Issue: Tags not filtering correctly

**Fix:** Verify GIN index exists
```sql
SELECT * FROM pg_indexes WHERE tablename = 'tasks' AND indexname = 'idx_tasks_tags';
```

### Issue: Colors don't match backend/frontend

**Fix:** Ensure hash algorithms identical
- Backend: MD5 hash → hex[:6]
- Frontend: Same algorithm in tagColors.ts

### Issue: "Too many tags" error

**Fix:** Enforce limit (20 tags) in service layer before database
```python
if len(merged_tags) > 20:
    raise ValueError("Maximum 20 tags per task")
```

---

## Related Documentation

- **Data Model**: See `data-model.md` for schema details and service code
- **API Contracts**: See `contracts/` for MCP tool specifications
- **Research**: See `research.md` for technical decisions
- **Plan**: See `plan.md` for constitution check and architecture

---

**Quick Start Complete**: 2026-02-14
**Total Implementation Time**: 6-8 hours
**Next Phase**: Task Breakdown (`/sp.tasks`)
