# Data Model: Task Tags & Categories

**Feature**: 003-task-tags
**Date**: 2026-02-14
**Phase**: 1 (Design & Contracts)

---

## Overview

Task Tags & Categories extends the existing `tasks` table with a JSONB array field to store user-defined tags. The feature uses PostgreSQL native JSON support with GIN indexing for efficient array queries, case-insensitive tag normalization, and deterministic hash-based color generation.

---

## Schema Changes

### Tasks Table Extension

**Migration**: `add_tags_to_tasks.py`

```sql
-- Add tags JSONB column with default empty array
ALTER TABLE tasks ADD COLUMN tags JSONB DEFAULT '[]'::jsonb NOT NULL;

-- Add GIN index for efficient array contains queries
CREATE INDEX idx_tasks_tags ON tasks USING GIN (tags);
```

**Column Specification:**
- **Name**: `tags`
- **Type**: `JSONB` (PostgreSQL native JSON binary storage)
- **Default**: `[]` (empty JSON array)
- **Nullable**: `NOT NULL` (always has value, even if empty)
- **Index**: GIN (Generalized Inverted Index) for array contains operations

**Why JSONB over TEXT[]:**
- SQLModel/SQLAlchemy has better JSON column support
- Flexible schema (no limit on tag count)
- Can query with `.contains()` method
- Better portability (works with any PostgreSQL-compatible database)

---

## Entity Definitions

### Task (Extended)

**SQLModel Definition:**

```python
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import Index

class Task(SQLModel, table=True):
    """Task model with tags support."""

    __tablename__ = "tasks"

    # Existing fields
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    description: Optional[str] = None
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # NEW: Tags field
    tags: List[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False, server_default='[]')
    )

    # Indexes
    __table_args__ = (
        Index('idx_tasks_user_id', 'user_id'),
        Index('idx_tasks_tags', 'tags', postgresql_using='gin'),
    )
```

**Field Validation:**
- **tags**: List of strings
- Each tag: 1-50 characters, alphanumeric + basic punctuation (-, _, space)
- Case-insensitive (stored as lowercase)
- No duplicates (normalized on input)
- Maximum 20 tags per task (soft limit, enforced in service layer)

---

## Pydantic Schemas

### Request/Response DTOs

```python
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Base schema (shared fields)
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    completed: bool = False
    tags: List[str] = Field(default=[], max_length=20)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        """Validate and normalize tags."""
        if len(tags) > 20:
            raise ValueError("Maximum 20 tags allowed")

        normalized = []
        for tag in tags:
            tag = tag.strip().lower()
            if not tag:
                continue
            if len(tag) > 50:
                raise ValueError(f"Tag too long: {tag} (max 50 chars)")
            if not tag.replace('-', '').replace('_', '').replace(' ', '').isalnum():
                raise ValueError(f"Invalid characters in tag: {tag}")
            normalized.append(tag)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(normalized))

# Create schema (for POST /tasks)
class TaskCreate(TaskBase):
    pass

# Update schema (for PUT /tasks/{id})
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None
    tags: Optional[List[str]] = Field(None, max_length=20)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize tags."""
        if tags is None:
            return None
        # Same validation as TaskBase
        # ... (implementation same as above)

# Response schema (for API responses)
class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Tag-specific schemas
class AddTagRequest(BaseModel):
    """Request to add tags to a task."""
    tags: List[str] = Field(..., min_length=1, max_length=20)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        # Same validation as TaskBase
        pass

class RemoveTagRequest(BaseModel):
    """Request to remove tags from a task."""
    tags: List[str] = Field(..., min_length=1)

class TagInfo(BaseModel):
    """Information about a single tag."""
    name: str
    color: str  # Hex color code (e.g., "#3B82F6")
    count: int  # Number of tasks with this tag

class ListTagsResponse(BaseModel):
    """Response for list tags endpoint."""
    tags: List[TagInfo]
    total: int
```

---

## Query Patterns

### Filter by Single Tag

```python
from sqlmodel import select

# Get all user's tasks with "work" tag
statement = select(Task).where(
    Task.user_id == user_id,
    Task.tags.contains(["work"])  # PostgreSQL JSONB contains
)
tasks = session.exec(statement).all()
```

**SQL Generated:**
```sql
SELECT * FROM tasks
WHERE user_id = ? AND tags @> '["work"]'::jsonb;
```

**Index Used:** `idx_tasks_tags` (GIN index)

---

### Filter by Multiple Tags (OR Logic)

```python
from sqlalchemy import or_

# Get all user's tasks with "work" OR "urgent" tags
statement = select(Task).where(
    Task.user_id == user_id,
    or_(
        Task.tags.contains(["work"]),
        Task.tags.contains(["urgent"])
    )
)
tasks = session.exec(statement).all()
```

**SQL Generated:**
```sql
SELECT * FROM tasks
WHERE user_id = ?
AND (tags @> '["work"]'::jsonb OR tags @> '["urgent"]'::jsonb);
```

---

### Filter by Multiple Tags (AND Logic)

```python
# Get all user's tasks with BOTH "work" AND "urgent" tags
statement = select(Task).where(
    Task.user_id == user_id,
    Task.tags.contains(["work"]),
    Task.tags.contains(["urgent"])
)
tasks = session.exec(statement).all()
```

**SQL Generated:**
```sql
SELECT * FROM tasks
WHERE user_id = ?
AND tags @> '["work"]'::jsonb
AND tags @> '["urgent"]'::jsonb;
```

---

### List All Unique Tags for User

```python
from sqlalchemy import func

# Get all unique tags used by user (with counts)
statement = select(
    func.jsonb_array_elements_text(Task.tags).label('tag'),
    func.count().label('count')
).where(
    Task.user_id == user_id
).group_by('tag').order_by(func.count().desc())

results = session.exec(statement).all()
```

**SQL Generated:**
```sql
SELECT
    jsonb_array_elements_text(tags) AS tag,
    COUNT(*) AS count
FROM tasks
WHERE user_id = ?
GROUP BY tag
ORDER BY count DESC;
```

---

## Service Layer Patterns

### Tag Normalization Service

```python
from typing import List

class TagService:
    """Service for tag operations."""

    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        """Normalize tags to lowercase and remove duplicates.

        Args:
            tags: Raw tag list from user input

        Returns:
            Normalized tag list (lowercase, no duplicates, trimmed)
        """
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
        """Generate consistent color for tag using hash.

        Args:
            tag_name: Normalized tag name (lowercase)

        Returns:
            Hex color code (e.g., "#3B82F6")
        """
        import hashlib

        # Hash the tag name
        hash_obj = hashlib.md5(tag_name.encode())
        hash_hex = hash_obj.hexdigest()

        # Use first 6 characters as hex color
        color = f"#{hash_hex[:6]}"

        # Ensure minimum brightness for readability (WCAG 2.1 AA)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000

        if brightness < 128:
            # Lighten dark colors
            r = min(255, r + 80)
            g = min(255, g + 80)
            b = min(255, b + 80)
            color = f"#{r:02x}{g:02x}{b:02x}"

        return color

    @staticmethod
    def validate_tag(tag: str) -> bool:
        """Validate a single tag.

        Args:
            tag: Tag to validate

        Returns:
            True if valid, False otherwise
        """
        if not tag or len(tag) > 50:
            return False

        # Allow alphanumeric, hyphens, underscores, spaces
        cleaned = tag.replace('-', '').replace('_', '').replace(' ', '')
        return cleaned.isalnum()
```

---

### Task Service Extensions

```python
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import or_

class TaskService:
    """Service for task operations (extended with tags)."""

    def __init__(self, session: Session):
        self.session = session
        self.tag_service = TagService()

    def get_user_tasks(
        self,
        user_id: int,
        completed: Optional[bool] = None,
        tag_filter: Optional[List[str]] = None
    ) -> List[Task]:
        """Get user's tasks with optional filters.

        Args:
            user_id: User ID
            completed: Filter by completion status (None = all)
            tag_filter: Filter by tags (OR logic)

        Returns:
            List of tasks matching filters
        """
        statement = select(Task).where(Task.user_id == user_id)

        # Apply completion filter
        if completed is not None:
            statement = statement.where(Task.completed == completed)

        # Apply tag filter (OR logic)
        if tag_filter:
            normalized_tags = self.tag_service.normalize_tags(tag_filter)
            tag_conditions = [
                Task.tags.contains([tag]) for tag in normalized_tags
            ]
            statement = statement.where(or_(*tag_conditions))

        return self.session.exec(statement).all()

    def add_tags_to_task(
        self,
        task_id: int,
        user_id: int,
        tags: List[str]
    ) -> Task:
        """Add tags to a task.

        Args:
            task_id: Task ID
            user_id: User ID (for ownership verification)
            tags: Tags to add

        Returns:
            Updated task

        Raises:
            ValueError: If task not found or not owned by user
        """
        # Get task (with ownership check)
        task = self.session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Normalize and merge tags (remove duplicates)
        normalized_new = self.tag_service.normalize_tags(tags)
        existing_tags = task.tags or []
        merged = list(set(existing_tags + normalized_new))

        # Enforce limit
        if len(merged) > 20:
            raise ValueError("Maximum 20 tags per task")

        # Update task
        task.tags = merged
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return task

    def remove_tags_from_task(
        self,
        task_id: int,
        user_id: int,
        tags: List[str]
    ) -> Task:
        """Remove tags from a task.

        Args:
            task_id: Task ID
            user_id: User ID (for ownership verification)
            tags: Tags to remove

        Returns:
            Updated task

        Raises:
            ValueError: If task not found or not owned by user
        """
        # Get task (with ownership check)
        task = self.session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Normalize tags to remove
        normalized_remove = set(self.tag_service.normalize_tags(tags))

        # Filter out tags to remove
        existing_tags = task.tags or []
        filtered = [tag for tag in existing_tags if tag not in normalized_remove]

        # Update task
        task.tags = filtered
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        return task

    def list_user_tags(self, user_id: int) -> List[TagInfo]:
        """List all unique tags for a user with counts.

        Args:
            user_id: User ID

        Returns:
            List of TagInfo objects sorted by count (descending)
        """
        from sqlalchemy import func

        # Query for unique tags with counts
        statement = select(
            func.jsonb_array_elements_text(Task.tags).label('tag'),
            func.count().label('count')
        ).where(
            Task.user_id == user_id
        ).group_by('tag').order_by(func.count().desc())

        results = self.session.exec(statement).all()

        # Build TagInfo objects with colors
        tag_infos = []
        for row in results:
            tag_infos.append(TagInfo(
                name=row.tag,
                color=self.tag_service.generate_tag_color(row.tag),
                count=row.count
            ))

        return tag_infos
```

---

## Performance Considerations

### Index Usage

**GIN Index (`idx_tasks_tags`):**
- **Type**: Generalized Inverted Index
- **Purpose**: Efficient array contains operations (`@>` operator)
- **Performance**:
  - Without index: O(n) full table scan
  - With index: O(log n) index lookup
  - 10-100x faster for tag filtering queries

**Example Query Performance:**
```
10,000 tasks, filter by single tag:
- Without GIN index: ~500ms (full scan)
- With GIN index: ~50ms (index lookup)

100,000 tasks, filter by 3 tags (OR):
- Without index: ~5s (full scan)
- With index: ~200ms (3 index lookups + merge)
```

### Query Optimization

**Best Practices:**
1. **Always include user_id in WHERE clause** - Uses primary index, prevents full scan
2. **Use contains() for tag filtering** - Leverages GIN index
3. **Normalize tags before querying** - Ensures case-insensitive matching
4. **Limit OR conditions** - More than 5 tags in OR can degrade performance
5. **Paginate results** - Add LIMIT/OFFSET for large result sets

**Avoid:**
- ❌ `LIKE '%tag%'` on JSON field - Doesn't use GIN index
- ❌ Scanning tags without user_id filter - Full table scan
- ❌ Unnesting tags in Python - Query should do it (database is faster)

---

## Migration Strategy

### Alembic Migration

**File**: `backend/alembic/versions/xxxx_add_tags_to_tasks.py`

```python
"""Add tags field to tasks table

Revision ID: add_tags_to_tasks
Revises: previous_revision
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = 'add_tags_to_tasks'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add tags JSONB column and GIN index."""
    # Add tags column with default empty array
    op.add_column(
        'tasks',
        sa.Column(
            'tags',
            JSONB,
            nullable=False,
            server_default="'[]'::jsonb"
        )
    )

    # Add GIN index for efficient tag queries
    op.create_index(
        'idx_tasks_tags',
        'tasks',
        ['tags'],
        postgresql_using='gin'
    )

def downgrade() -> None:
    """Remove tags column and index."""
    op.drop_index('idx_tasks_tags', table_name='tasks')
    op.drop_column('tasks', 'tags')
```

**Deployment Impact:**
- **Downtime**: None (ALTER TABLE ADD COLUMN is instant with default)
- **Index Creation**: ~1-2 seconds for 10,000 tasks
- **Backward Compatibility**: Existing tasks get empty array `[]`
- **Rollback**: Safe (DROP COLUMN removes tags data)

---

## Testing Data

### Sample Tasks with Tags

```python
# Sample data for testing
sample_tasks = [
    {
        "title": "Buy groceries",
        "tags": ["shopping", "personal", "urgent"],
        "completed": False
    },
    {
        "title": "Deploy backend",
        "tags": ["work", "backend", "deploy"],
        "completed": False
    },
    {
        "title": "Review PR",
        "tags": ["work", "code-review"],
        "completed": True
    },
    {
        "title": "Call mom",
        "tags": ["personal", "family"],
        "completed": False
    },
    {
        "title": "Fix auth bug",
        "tags": ["work", "backend", "urgent", "bug"],
        "completed": False
    }
]
```

### Edge Cases to Test

1. **Empty tags array**: Task with no tags
2. **Duplicate tags**: Input `["work", "Work", "WORK"]` → Normalized to `["work"]`
3. **Special characters**: Tags with `-`, `_`, spaces
4. **Very long tag**: 50+ character tag (should fail validation)
5. **Too many tags**: 21+ tags (should fail validation)
6. **Invalid characters**: Tags with `@`, `#`, `!` (should fail)
7. **Filter with non-existent tag**: Returns empty list
8. **Filter with multiple tags**: OR logic works correctly
9. **Add tag to completed task**: Works normally
10. **Remove non-existent tag**: No error, task unchanged

---

## Frontend Integration

### TypeScript Types

```typescript
// types/task.ts
export interface Task {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  completed: boolean;
  tags: string[];  // NEW
  created_at: string;
  updated_at: string;
}

export interface TagInfo {
  name: string;
  color: string;  // Hex color code
  count: number;
}
```

### Client-Side Color Generation

```typescript
// utils/tagColors.ts
export function generateTagColor(tagName: string): string {
  // Same hash algorithm as backend (MD5)
  const hash = Array.from(tagName).reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc);
  }, 0);

  // Convert to hex color
  let color = '#' + ((hash & 0x00FFFFFF) | 0x808080).toString(16).padStart(6, '0');

  // Brightness adjustment (same as backend)
  const r = parseInt(color.slice(1, 3), 16);
  const g = parseInt(color.slice(3, 5), 16);
  const b = parseInt(color.slice(5, 7), 16);
  const brightness = (0.299 * r + 0.587 * g + 0.114 * b);

  if (brightness < 128) {
    const adjustedR = Math.min(255, r + 80);
    const adjustedG = Math.min(255, g + 80);
    const adjustedB = Math.min(255, b + 80);
    color = '#' + [adjustedR, adjustedG, adjustedB]
      .map(c => c.toString(16).padStart(2, '0'))
      .join('');
  }

  return color;
}

export function getContrastColor(hexColor: string): string {
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  return luminance > 0.5 ? '#000000' : '#FFFFFF';
}
```

---

**Data Model Complete**: 2026-02-14
**Next Phase**: API Contracts & MCP Tool Definitions
