# Quick Start: Task Sorting Integration

**Feature**: 005-task-sort
**Date**: 2026-02-14
**Phase**: 1 (Design & Contracts)

## Overview

This guide shows developers how to integrate task sorting into existing code. Task Sorting extends the existing `list_tasks` functionality with optional sort parameters.

---

## For Backend Developers

### 1. Extend Task Service

**File**: `backend/src/services/task_service.py`

```python
from sqlmodel import Session, select, asc, desc, func
from sqlalchemy import case
from typing import List, Optional

def get_user_tasks(
    session: Session,
    user_id: str,
    completed: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_direction: Optional[str] = None
) -> List[Task]:
    """
    Get user's tasks with optional filtering and sorting.

    Args:
        session: Database session
        user_id: User ID (for user isolation)
        completed: Filter by completion status (None = all)
        sort_by: Field to sort by (due_date, priority, created_at, title)
        sort_direction: Sort direction (asc, desc, None = default based on field)

    Returns:
        List of tasks sorted according to parameters
    """
    # Build base query
    statement = select(Task).where(Task.user_id == user_id)

    # Apply completed filter if specified
    if completed is not None:
        statement = statement.where(Task.completed == completed)

    # Determine default sort direction if not specified
    if sort_direction is None:
        if sort_by == "created_at":
            sort_direction = "desc"  # Newest first (default)
        else:
            sort_direction = "asc"   # Ascending for all other fields

    # Apply sorting
    statement = _apply_sorting(statement, sort_by, sort_direction)

    return session.exec(statement).all()


def _apply_sorting(statement, sort_by: str, sort_direction: str):
    """Apply ORDER BY clause based on sort parameters."""

    if sort_by == "due_date":
        # Sort by due_date with NULL handling
        if sort_direction == "asc":
            statement = statement.order_by(
                Task.due_date.asc().nullslast(),  # Nulls appear last
                Task.created_at.desc()             # Tiebreaker
            )
        else:
            statement = statement.order_by(
                Task.due_date.desc().nullslast(),  # Nulls still last
                Task.created_at.desc()
            )

    elif sort_by == "priority":
        # Custom priority ordering (high→medium→low)
        if sort_direction == "asc":
            priority_order = case(
                (Task.priority == "high", 1),
                (Task.priority == "medium", 2),
                (Task.priority == "low", 3),
                else_=4
            )
            statement = statement.order_by(priority_order.asc(), Task.created_at.desc())
        else:
            # Reverse priority order for descending
            priority_order = case(
                (Task.priority == "low", 1),
                (Task.priority == "medium", 2),
                (Task.priority == "high", 3),
                else_=4
            )
            statement = statement.order_by(priority_order.asc(), Task.created_at.desc())

    elif sort_by == "title":
        # Case-insensitive alphabetical sorting
        if sort_direction == "asc":
            statement = statement.order_by(func.lower(Task.title).asc(), Task.created_at.desc())
        else:
            statement = statement.order_by(func.lower(Task.title).desc(), Task.created_at.desc())

    else:  # created_at (default)
        if sort_direction == "desc":
            statement = statement.order_by(Task.created_at.desc())
        else:
            statement = statement.order_by(Task.created_at.asc())

    return statement
```

---

### 2. Extend REST API Route

**File**: `backend/src/routes/tasks.py`

```python
from fastapi import APIRouter, Depends, Query
from enum import Enum
from typing import Optional

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
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    sort_by: SortField = Query(SortField.CREATED_AT, description="Field to sort by"),
    sort_direction: Optional[SortDirection] = Query(None, description="Sort direction"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TaskListResponse:
    """
    Get user's tasks with optional sorting.

    Default sort: created_at descending (newest first)
    """
    # Verify user authorization
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="User ID mismatch")

    # Get sorted tasks
    tasks = task_service.get_user_tasks(
        db,
        user_id,
        completed=completed,
        sort_by=sort_by.value,
        sort_direction=sort_direction.value if sort_direction else None
    )

    return TaskListResponse(
        tasks=[TaskResponse.from_orm(task) for task in tasks],
        total=len(tasks),
        sort_by=sort_by.value,
        sort_direction=sort_direction.value if sort_direction else "default"
    )
```

---

### 3. Extend MCP Tool

**File**: `backend/src/mcp_tools/list_tasks.py`

```python
async def list_tasks(
    completed: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_direction: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all tasks for the current user with optional sorting.

    Args:
        completed: Filter by completion status (optional)
        sort_by: Field to sort by (due_date, priority, created_at, title)
        sort_direction: Sort direction (asc, desc, or None for default)

    Returns:
        Dict with tasks list, total count, and applied sort parameters
    """
    # Validate sort parameters
    valid_sort_fields = ["due_date", "priority", "created_at", "title"]
    if sort_by not in valid_sort_fields:
        raise ValueError(f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}")

    if sort_direction and sort_direction not in ["asc", "desc"]:
        raise ValueError("Invalid sort_direction. Must be 'asc' or 'desc'")

    # Get current user from context
    user_id = get_current_user_id()  # From agent context

    # Get database session
    with get_db_session() as session:
        tasks = task_service.get_user_tasks(
            session,
            user_id,
            completed=completed,
            sort_by=sort_by,
            sort_direction=sort_direction
        )

    # Format response
    return {
        "tasks": [task.dict() for task in tasks],
        "total": len(tasks),
        "sort_by": sort_by,
        "sort_direction": sort_direction or "default"
    }


# Update tool schema registration
TOOL_SCHEMA = {
    "name": "list_tasks",
    "description": "List all tasks for the current user with optional filtering and sorting",
    "input_schema": {
        "type": "object",
        "properties": {
            "completed": {
                "type": "boolean",
                "description": "Filter by completion status (optional)"
            },
            "sort_by": {
                "type": "string",
                "enum": ["due_date", "priority", "created_at", "title"],
                "description": "Field to sort by (default: created_at)",
                "default": "created_at"
            },
            "sort_direction": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Sort direction (default based on sort_by field)"
            }
        }
    }
}
```

---

### 4. Create Database Migration

**File**: `backend/alembic/versions/XXXXXX_add_sort_indexes.py`

```python
"""Add composite indexes for task sorting

Revision ID: XXXXXX
Revises: YYYYYY
Create Date: 2026-02-14

"""
from alembic import op

revision = 'XXXXXX'
down_revision = 'YYYYYY'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Index for sorting by due_date
    op.create_index(
        'idx_tasks_user_due_date',
        'tasks',
        ['user_id', 'due_date', 'created_at'],
        postgresql_ops={'due_date': 'NULLS LAST'}
    )

    # Index for sorting by priority
    op.create_index(
        'idx_tasks_user_priority',
        'tasks',
        ['user_id', 'priority', 'created_at']
    )

    # Index for sorting by created_at
    op.create_index(
        'idx_tasks_user_created',
        'tasks',
        ['user_id', 'created_at']
    )

    # Index for sorting by title (case-insensitive)
    op.execute(
        "CREATE INDEX idx_tasks_user_title ON tasks (user_id, LOWER(title), created_at DESC)"
    )

def downgrade() -> None:
    op.drop_index('idx_tasks_user_due_date', table_name='tasks')
    op.drop_index('idx_tasks_user_priority', table_name='tasks')
    op.drop_index('idx_tasks_user_created', table_name='tasks')
    op.drop_index('idx_tasks_user_title', table_name='tasks')
```

---

## For Frontend Developers

### 1. Create Sort Hook

**File**: `frontend/src/hooks/useTaskSort.ts`

```typescript
import { useState, useEffect } from 'react';

export type SortField = 'due_date' | 'priority' | 'created_at' | 'title';
export type SortDirection = 'asc' | 'desc';

interface SortState {
  sortBy: SortField;
  sortDirection: SortDirection;
}

export function useTaskSort() {
  const [sortState, setSortState] = useState<SortState>({
    sortBy: 'created_at',
    sortDirection: 'desc'
  });

  // Restore sort state from session storage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem('taskSort');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSortState(parsed);
      } catch (e) {
        console.error('Failed to parse saved sort state:', e);
      }
    }
  }, []);

  // Persist sort state to session storage
  useEffect(() => {
    sessionStorage.setItem('taskSort', JSON.stringify(sortState));
  }, [sortState]);

  const handleSort = (field: SortField) => {
    setSortState(prev => {
      // If clicking same field, toggle direction
      if (prev.sortBy === field) {
        return {
          sortBy: field,
          sortDirection: prev.sortDirection === 'asc' ? 'desc' : 'asc'
        };
      }

      // New field - use default direction
      const defaultDirection = field === 'created_at' ? 'desc' : 'asc';
      return {
        sortBy: field,
        sortDirection: defaultDirection
      };
    });
  };

  const toggleDirection = () => {
    setSortState(prev => ({
      ...prev,
      sortDirection: prev.sortDirection === 'asc' ? 'desc' : 'asc'
    }));
  };

  return {
    sortBy: sortState.sortBy,
    sortDirection: sortState.sortDirection,
    handleSort,
    toggleDirection
  };
}
```

---

### 2. Create Sort Component

**File**: `frontend/src/components/TaskSort.tsx`

```typescript
import React from 'react';
import { SortField, SortDirection } from '@/hooks/useTaskSort';

interface TaskSortProps {
  sortBy: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
  onToggleDirection: () => void;
}

export function TaskSort({
  sortBy,
  sortDirection,
  onSort,
  onToggleDirection
}: TaskSortProps) {
  const sortOptions: { value: SortField; label: string }[] = [
    { value: 'created_at', label: 'Newest First (default)' },
    { value: 'due_date', label: 'Due Date' },
    { value: 'priority', label: 'Priority' },
    { value: 'title', label: 'Alphabetical' }
  ];

  return (
    <div className="flex items-center gap-4">
      {/* Sort Field Dropdown */}
      <select
        value={sortBy}
        onChange={(e) => onSort(e.target.value as SortField)}
        className="border rounded px-3 py-2"
      >
        {sortOptions.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* Direction Toggle Button */}
      <button
        onClick={onToggleDirection}
        className="border rounded px-3 py-2 flex items-center gap-2"
      >
        {sortDirection === 'asc' ? '↑' : '↓'}
        {sortDirection === 'asc' ? 'Ascending' : 'Descending'}
      </button>
    </div>
  );
}

// Column Header Component (for table view)
interface SortableHeaderProps {
  field: SortField;
  label: string;
  currentSort: SortField;
  currentDirection: SortDirection;
  onSort: (field: SortField) => void;
}

export function SortableHeader({
  field,
  label,
  currentSort,
  currentDirection,
  onSort
}: SortableHeaderProps) {
  const isActive = currentSort === field;

  return (
    <th
      onClick={() => onSort(field)}
      className={`cursor-pointer select-none ${isActive ? 'font-bold' : ''}`}
    >
      <div className="flex items-center gap-2">
        {label}
        {isActive && (
          <span>{currentDirection === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </th>
  );
}
```

---

### 3. Integrate in Tasks Page

**File**: `frontend/src/app/tasks/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useTaskSort } from '@/hooks/useTaskSort';
import { TaskSort } from '@/components/TaskSort';
import { getTasks } from '@/lib/api';

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const { sortBy, sortDirection, handleSort, toggleDirection } = useTaskSort();

  // Fetch tasks whenever sort changes
  useEffect(() => {
    async function fetchTasks() {
      const data = await getTasks({
        sort_by: sortBy,
        sort_direction: sortDirection
      });
      setTasks(data.tasks);
    }

    fetchTasks();
  }, [sortBy, sortDirection]);

  return (
    <div>
      <h1>My Tasks</h1>

      {/* Sort Controls */}
      <TaskSort
        sortBy={sortBy}
        sortDirection={sortDirection}
        onSort={handleSort}
        onToggleDirection={toggleDirection}
      />

      {/* Task List */}
      <div className="mt-4">
        {tasks.map(task => (
          <div key={task.id}>{task.title}</div>
        ))}
      </div>
    </div>
  );
}
```

---

### 4. Update API Client

**File**: `frontend/src/lib/api.ts`

```typescript
export interface GetTasksParams {
  completed?: boolean;
  sort_by?: string;
  sort_direction?: string;
}

export async function getTasks(params: GetTasksParams = {}) {
  const queryParams = new URLSearchParams();

  if (params.completed !== undefined) {
    queryParams.append('completed', params.completed.toString());
  }
  if (params.sort_by) {
    queryParams.append('sort_by', params.sort_by);
  }
  if (params.sort_direction) {
    queryParams.append('sort_direction', params.sort_direction);
  }

  const url = `/api/${userId}/tasks?${queryParams.toString()}`;
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });

  return response.json();
}
```

---

## For AI Agent Integration

### Update Agent Prompt

**File**: `backend/src/ai/agent.py`

Add these examples to the agent's system prompt:

```python
SORT_EXAMPLES = """
You can sort tasks using the list_tasks tool with sort parameters:

Examples:
- User: "sort my tasks by due date"
  → list_tasks(sort_by="due_date", sort_direction="asc")

- User: "show tasks by priority"
  → list_tasks(sort_by="priority", sort_direction="asc")

- User: "latest tasks first"
  → list_tasks(sort_by="created_at", sort_direction="desc")

- User: "alphabetically"
  → list_tasks(sort_by="title", sort_direction="asc")

Sort Fields:
- due_date: Sort by task due dates (earliest first by default)
- priority: Sort by importance (high→medium→low by default)
- created_at: Sort by creation date (newest first by default)
- title: Sort alphabetically (A-Z by default)

Sort Directions:
- asc: Ascending order (A-Z, earliest→latest, low→high)
- desc: Descending order (Z-A, latest→earliest, high→low)

Special Behaviors:
- Tasks without due dates appear at the end when sorting by due_date
- Priority "asc" means high→medium→low (importance order)
- Title sorting is case-insensitive
- If no sort specified, defaults to created_at desc (newest first)
"""

# Add to agent configuration
agent = Agent(
    name="Todo Assistant",
    instructions=BASE_INSTRUCTIONS + SORT_EXAMPLES,
    tools=[list_tasks, add_task, complete_task, ...]
)
```

---

## Testing Guide

### Backend Tests

```python
# tests/unit/test_task_sort.py
import pytest
from datetime import datetime, timedelta

def test_sort_by_due_date_asc(db_session, user):
    """Tasks sorted by due date ascending (earliest first)."""
    # Create tasks with different due dates
    task1 = create_task(user.id, "Task 1", due_date=datetime.now() + timedelta(days=3))
    task2 = create_task(user.id, "Task 2", due_date=datetime.now() + timedelta(days=1))
    task3 = create_task(user.id, "Task 3", due_date=None)  # No due date

    tasks = get_user_tasks(db_session, user.id, sort_by="due_date", sort_direction="asc")

    assert tasks[0].id == task2.id  # Earliest due date first
    assert tasks[1].id == task1.id
    assert tasks[2].id == task3.id  # No due date last

def test_sort_by_priority_asc(db_session, user):
    """Tasks sorted by priority (high→medium→low)."""
    task1 = create_task(user.id, "Low priority", priority="low")
    task2 = create_task(user.id, "High priority", priority="high")
    task3 = create_task(user.id, "Medium priority", priority="medium")

    tasks = get_user_tasks(db_session, user.id, sort_by="priority", sort_direction="asc")

    assert tasks[0].priority == "high"
    assert tasks[1].priority == "medium"
    assert tasks[2].priority == "low"

def test_sort_by_title_case_insensitive(db_session, user):
    """Title sorting is case-insensitive."""
    create_task(user.id, "Buy groceries")
    create_task(user.id, "attend meeting")
    create_task(user.id, "Call doctor")

    tasks = get_user_tasks(db_session, user.id, sort_by="title", sort_direction="asc")

    assert tasks[0].title == "attend meeting"  # Case-insensitive
    assert tasks[1].title == "Buy groceries"
    assert tasks[2].title == "Call doctor"
```

### Frontend Tests

```typescript
// __tests__/useTaskSort.test.ts
import { renderHook, act } from '@testing-library/react';
import { useTaskSort } from '@/hooks/useTaskSort';

describe('useTaskSort', () => {
  it('defaults to created_at desc', () => {
    const { result } = renderHook(() => useTaskSort());

    expect(result.current.sortBy).toBe('created_at');
    expect(result.current.sortDirection).toBe('desc');
  });

  it('toggles direction when clicking same field', () => {
    const { result } = renderHook(() => useTaskSort());

    act(() => {
      result.current.handleSort('created_at');
    });

    expect(result.current.sortDirection).toBe('asc');  // Toggled
  });

  it('persists to sessionStorage', () => {
    const { result } = renderHook(() => useTaskSort());

    act(() => {
      result.current.handleSort('due_date');
    });

    const saved = JSON.parse(sessionStorage.getItem('taskSort')!);
    expect(saved.sortBy).toBe('due_date');
  });
});
```

---

## Performance Checklist

- [ ] Composite indexes created (user_id + sort field)
- [ ] Database queries use ORDER BY (not in-memory sorting)
- [ ] NULL handling for due_date (NULLS LAST)
- [ ] Tiebreaker included (created_at DESC)
- [ ] Response time < 200ms for 1,000 tasks
- [ ] Response time < 500ms for 10,000 tasks

---

## Common Pitfalls

### ❌ Wrong: In-Memory Sorting
```python
# DON'T DO THIS
tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()
tasks.sort(key=lambda t: t.due_date or datetime.max)  # Slow!
```

### ✅ Right: Database-Level Sorting
```python
# DO THIS
statement = (
    select(Task)
    .where(Task.user_id == user_id)
    .order_by(Task.due_date.asc().nullslast())
)
tasks = session.exec(statement).all()  # Fast!
```

---

**Integration Complete!** 🚀

For questions, see:
- Full contracts: `contracts/` directory
- Data model: `data-model.md`
- Research: `research.md`
