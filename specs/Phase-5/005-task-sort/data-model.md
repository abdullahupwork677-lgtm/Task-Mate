# Data Model: Task Sorting

**Feature**: 005-task-sort
**Date**: 2026-02-14
**Phase**: 1 (Design & Contracts)

## Overview

Task Sorting does NOT require any database schema changes. All sortable fields already exist in the `tasks` table from previous phases. This document describes the existing data structures and how they support sorting functionality.

---

## Existing Database Schema

### Task Table (No Changes Required)

**Table**: `tasks`

**Sortable Fields** (already exist):

| Column | Type | Nullable | Index | Description | Phase Added |
|--------|------|----------|-------|-------------|-------------|
| `id` | integer | NO | PRIMARY KEY | Auto-incrementing task ID | Phase I |
| `user_id` | string | NO | INDEX | Owner user ID (foreign key to users.id) | Phase I |
| `title` | string(200) | NO | NO | Task title | Phase I |
| `description` | string(1000) | YES | NO | Task description | Phase I |
| `completed` | boolean | NO | INDEX | Completion status | Phase I |
| `priority` | enum | NO | NO | Priority level: high, medium, low | Phase III |
| `due_date` | datetime | YES | NO | Task due date and time | Phase V |
| `created_at` | datetime | NO | NO | Task creation timestamp | Phase I |
| `updated_at` | datetime | NO | NO | Last update timestamp | Phase I |

**Additional Fields** (not sortable, but exist):

| Column | Type | Description | Phase Added |
|--------|------|-------------|-------------|
| `is_recurring` | boolean | Whether task repeats on completion | Phase V |
| `recurrence_pattern` | string | Recurrence pattern: daily/weekly/monthly | Phase V |
| `recurrence_end_date` | datetime | Optional end date for recurrence | Phase V |
| `parent_task_id` | integer | Links to parent recurring task | Phase V |
| `remind_before` | JSON array | Reminder intervals before due date | Phase V |
| `reminder_sent` | JSON object | Tracking for sent reminders | Phase V |

---

## Sort Configuration (Session State)

**NOT stored in database** - Stored in frontend session state

### Sort Parameters

**Type**: Ephemeral (session-only)

| Field | Type | Valid Values | Default | Description |
|-------|------|--------------|---------|-------------|
| `sort_by` | enum | `due_date`, `priority`, `created_at`, `title` | `created_at` | Field to sort by |
| `sort_direction` | enum | `asc`, `desc` | Depends on `sort_by` | Sort direction |

**Default Sort Direction by Field:**
- `created_at`: `desc` (newest first)
- `due_date`: `asc` (earliest first)
- `priority`: `asc` (high → medium → low)
- `title`: `asc` (A → Z)

**Storage Location**: `sessionStorage` (frontend) - persists during session, cleared on tab close

---

## Database Index Requirements

### NEW Indexes for Optimal Sort Performance

**Migration Required**: YES - Add 4 composite indexes

```sql
-- Index 1: Sort by due_date (with NULL handling)
CREATE INDEX idx_tasks_user_due_date
ON tasks(user_id, due_date NULLS LAST, created_at DESC);

-- Index 2: Sort by priority (with tiebreaker)
CREATE INDEX idx_tasks_user_priority
ON tasks(user_id, priority, created_at DESC);

-- Index 3: Sort by created_at (default sort)
CREATE INDEX idx_tasks_user_created
ON tasks(user_id, created_at DESC);

-- Index 4: Sort by title case-insensitive (with tiebreaker)
CREATE INDEX idx_tasks_user_title
ON tasks(user_id, LOWER(title), created_at DESC);
```

**Rationale:**
- All queries filter by `user_id` first (user isolation)
- Composite indexes enable index-only scans (no table access)
- Tiebreaker column (`created_at DESC`) ensures deterministic ordering
- NULL handling for due_date (nulls appear last)
- Case-insensitive title sorting with `LOWER()` function

**Performance Impact:**
- **Before**: 500-1000ms for 1,000 tasks (table scan + sort)
- **After**: 50-200ms for 1,000 tasks (index-only scan)
- **Write Overhead**: Minimal (~5-10% slower inserts/updates for index maintenance)

---

## Sort Field Mapping

### Sort Field → Database Column

| Sort Field Value | Database Column | SQL ORDER BY Clause | Secondary Sort |
|------------------|-----------------|---------------------|----------------|
| `due_date` | `tasks.due_date` | `due_date ASC NULLS LAST` | `created_at DESC` |
| `priority` | `tasks.priority` | `CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END ASC` | `created_at DESC` |
| `created_at` | `tasks.created_at` | `created_at DESC` | None (primary sort is unique enough) |
| `title` | `tasks.title` | `LOWER(title) ASC` | `created_at DESC` |

**Tiebreaker Logic:**
- When multiple tasks have the same value for the primary sort field, use `created_at DESC` to break ties
- Ensures deterministic ordering (same input always produces same output)
- Example: If 3 tasks have priority="high", they'll be sub-sorted by newest first

---

## Priority Enum Ordering

**Database Type**: `priority_enum` (Enum: "high", "medium", "low")

**Natural Database Order**: Alphabetical → `high, low, medium` ❌ INCORRECT

**Desired Sort Order**: Importance → `high, medium, low` ✅ CORRECT

**Solution**: Use SQL CASE statement to map priorities to numeric values:

```sql
ORDER BY
  CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
  END ASC
```

**Reverse Order** (low to high):
```sql
ORDER BY
  CASE priority
    WHEN 'low' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'high' THEN 3
  END ASC
```

---

## NULL Handling for due_date

**Problem**: Tasks without due dates should appear at the end when sorting by due_date

**Solution**: PostgreSQL `NULLS LAST` clause

**SQL Pattern:**
```sql
-- Ascending (earliest first, nulls last)
ORDER BY due_date ASC NULLS LAST, created_at DESC

-- Descending (latest first, nulls last)
ORDER BY due_date DESC NULLS LAST, created_at DESC
```

**Behavior:**
- Tasks with due dates sort first (by date)
- Tasks without due dates (`NULL`) appear at the end
- Within tasks without due dates, sort by created_at descending

---

## Case-Insensitive Title Sorting

**Problem**: "attend meeting" should come before "Buy groceries" (case-insensitive)

**Solution**: PostgreSQL `LOWER()` function

**SQL Pattern:**
```sql
-- Case-insensitive ascending
ORDER BY LOWER(title) ASC, created_at DESC

-- Case-insensitive descending
ORDER BY LOWER(title) DESC, created_at DESC
```

**Example Results:**
```
Input: ["Buy groceries", "attend meeting", "Call doctor"]
A-Z Sort: ["attend meeting", "Buy groceries", "Call doctor"]
Z-A Sort: ["Call doctor", "Buy groceries", "attend meeting"]
```

---

## SQLModel Implementation Patterns

### Service Layer (task_service.py)

```python
from sqlmodel import Session, select, asc, desc, func
from sqlalchemy import case

def get_user_tasks_sorted(
    session: Session,
    user_id: str,
    sort_by: str = "created_at",
    sort_direction: str = "desc"
) -> List[Task]:
    """Get user's tasks with sorting."""

    # Build base query
    statement = select(Task).where(Task.user_id == user_id)

    # Apply sorting based on field
    if sort_by == "due_date":
        if sort_direction == "asc":
            statement = statement.order_by(
                Task.due_date.asc().nullslast(),
                Task.created_at.desc()
            )
        else:
            statement = statement.order_by(
                Task.due_date.desc().nullslast(),
                Task.created_at.desc()
            )

    elif sort_by == "priority":
        priority_order = case(
            (Task.priority == "high", 1),
            (Task.priority == "medium", 2),
            (Task.priority == "low", 3),
            else_=4
        )
        if sort_direction == "asc":
            statement = statement.order_by(priority_order.asc(), Task.created_at.desc())
        else:
            # Reverse priority order for descending
            priority_order_desc = case(
                (Task.priority == "low", 1),
                (Task.priority == "medium", 2),
                (Task.priority == "high", 3),
                else_=4
            )
            statement = statement.order_by(priority_order_desc.asc(), Task.created_at.desc())

    elif sort_by == "title":
        if sort_direction == "asc":
            statement = statement.order_by(func.lower(Task.title).asc(), Task.created_at.desc())
        else:
            statement = statement.order_by(func.lower(Task.title).desc(), Task.created_at.desc())

    else:  # created_at (default)
        if sort_direction == "desc":
            statement = statement.order_by(Task.created_at.desc())
        else:
            statement = statement.order_by(Task.created_at.asc())

    return session.exec(statement).all()
```

---

## Pydantic DTOs

### Request DTO (Query Parameters)

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class SortField(str, Enum):
    """Sortable task fields."""
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    CREATED_AT = "created_at"
    TITLE = "title"

class SortDirection(str, Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"

class TaskListParams(BaseModel):
    """Query parameters for listing tasks."""
    completed: Optional[bool] = Field(None, description="Filter by completion status")
    sort_by: SortField = Field(SortField.CREATED_AT, description="Field to sort by")
    sort_direction: Optional[SortDirection] = Field(None, description="Sort direction (defaults based on field)")
```

### Response DTO

```python
class TaskResponse(BaseModel):
    """Single task response."""
    id: int
    user_id: str
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # ... other fields

class TaskListResponse(BaseModel):
    """List of tasks with sort metadata."""
    tasks: List[TaskResponse]
    total: int
    sort_by: str
    sort_direction: str
```

---

## Entity Relationships

**No Changes** - Task Sorting does not affect entity relationships

**Existing Relationships:**
- `Task.user` → `User` (many-to-one)
- `Task.parent_task` → `Task` (self-referential for recurring tasks)
- `Task.child_occurrences` → `List[Task]` (self-referential)
- `Task.notification_logs` → `List[NotificationLog]` (one-to-many)

Sorting applies only to the result set of tasks, not to relationships.

---

## Validation Rules

### Sort Parameters

| Rule | Validation |
|------|------------|
| `sort_by` must be valid enum | Pydantic enum validation |
| `sort_direction` must be valid enum | Pydantic enum validation |
| Default `sort_by` is `created_at` | Applied in API route |
| Default `sort_direction` depends on field | Applied in service layer |

### Business Rules

| Rule | Implementation |
|------|----------------|
| Only user's own tasks are sortable | WHERE clause filters by user_id |
| Completed and incomplete tasks can be sorted together | No filtering by completed unless specified |
| Sorting works with existing filters | Combine WHERE clauses with ORDER BY |
| Sort order is deterministic | Always include tiebreaker (created_at) |

---

## Data Flow

```
User → Frontend → API → Service → Database
  ↓        ↓        ↓       ↓         ↓
  1. Click   2. GET    3. Parse   4. Build   5. Execute
     sort       /tasks    params     SELECT     ORDER BY
     button     ?sort_by          statement   query

Database → Service → API → Frontend → User
    ↓         ↓      ↓        ↓        ↓
  6. Return  7. Map  8. JSON  9. Render  10. Display
     sorted     to      response   sorted     sorted
     rows    DTOs              list      list
```

---

## State Transitions

**No State Transitions** - Sorting does not change task state

- Tasks remain `completed=true` or `completed=false`
- Tasks remain `is_recurring=true/false`
- No status changes occur during sorting
- Sorting is a read-only operation

---

## Summary

### Schema Changes: NONE ✅
- All sortable fields exist in tasks table
- No new columns needed
- No data migrations needed

### Index Changes: YES ✅
- 4 new composite indexes required
- Alembic migration needed
- Performance optimization only

### Storage: Session-Based ✅
- Sort preferences stored in sessionStorage (frontend)
- NOT persisted in database (per spec requirements)
- Cleared on tab close

### Entity Relationships: NO CHANGES ✅
- Sorting does not affect relationships
- Read-only operation

---

**Data Model Complete**: 2026-02-14
**Next Step**: Create API contracts (contracts/ directory)
