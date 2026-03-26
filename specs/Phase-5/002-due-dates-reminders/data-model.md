# Data Model: Due Dates & Reminders

**Feature**: 002-due-dates-reminders
**Date**: 2026-02-09
**Status**: Design Phase

## Overview

This document defines the data entities and relationships for the Due Dates & Reminders feature. The design extends the existing Task and User models with new fields, adds a NotificationLog entity for audit trails, and defines the Reminder Event schema for Kafka messages.

---

## Entity Definitions

### 1. Task (Extended)

**Purpose**: Core entity representing a todo item with due date and reminder configuration.

**Database Table**: `tasks` (existing, extended)

**New Fields**:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `due_date` | TIMESTAMP WITH TIME ZONE | YES | NULL | When the task must be completed (UTC) |
| `remind_before` | JSONB | YES | `'["24h", "1h"]'` | Array of reminder intervals (e.g., ["24h", "1h", "3d"]) |
| `reminder_sent` | JSONB | YES | `'{}'` | Object tracking sent reminders: `{"24h": "2026-02-09T10:00:00Z", "1h": "2026-02-10T09:00:00Z"}` |

**Existing Fields** (unchanged):
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (VARCHAR(100), FOREIGN KEY → users.id)
- `title` (VARCHAR(500), NOT NULL)
- `description` (TEXT)
- `completed` (BOOLEAN, DEFAULT FALSE)
- `priority` (VARCHAR(20), DEFAULT 'medium')
- `tags` (JSONB)
- `is_recurring` (BOOLEAN, DEFAULT FALSE)
- `recurrence_pattern` (VARCHAR(50))
- `recurrence_end_date` (TIMESTAMP WITH TIME ZONE)
- `parent_task_id` (INTEGER, FOREIGN KEY → tasks.id)
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())
- `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())

**Validation Rules**:

1. `due_date`:
   - Must be a valid timestamp with timezone
   - Can be in the past (for overdue tasks)
   - NULL is valid (no due date)
   - If `is_recurring=TRUE`, due_date determines next occurrence schedule

2. `remind_before`:
   - Must be JSON array of strings
   - Valid interval formats: "24h", "1h", "3d", "30m", "1w"
   - Pattern: `\d+(m|h|d|w)` (number + unit)
   - Default: `["24h", "1h"]` if NULL or not specified
   - Maximum 5 intervals per task
   - Intervals must be less than time until due_date

3. `reminder_sent`:
   - Must be JSON object with interval keys
   - Keys match remind_before intervals
   - Values are ISO 8601 timestamps (UTC)
   - Empty object `{}` means no reminders sent yet
   - Cleared when task is completed or due_date is updated

**Indexes**:

```sql
-- Partial index for efficient reminder queries (WHERE clause filters out completed/NULL)
CREATE INDEX idx_tasks_reminders
ON tasks(user_id, due_date)
WHERE due_date IS NOT NULL AND completed = FALSE;

-- Index for due date sorting and filtering
CREATE INDEX idx_tasks_due_date
ON tasks(due_date)
WHERE due_date IS NOT NULL;
```

**Relationships**:
- Belongs to User (user_id → users.id)
- May belong to parent Task (parent_task_id → tasks.id) for recurring tasks
- Has many NotificationLogs (task_id → notification_logs.task_id)

**State Transitions**:
- `reminder_sent` populated as reminders are sent
- `completed=TRUE` → skip future reminder checks (no state clearing needed, query filters)
- `due_date` updated → reset `reminder_sent` to `{}`

---

### 2. NotificationLog (New)

**Purpose**: Audit trail for sent notifications, used for debugging, analytics, and preventing duplicates.

**Database Table**: `notification_logs` (new)

**Fields**:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | SERIAL (INTEGER) | NO | AUTO | Primary key |
| `task_id` | INTEGER | NO | - | Task that triggered notification |
| `user_id` | VARCHAR(100) | NO | - | Recipient user |
| `reminder_type` | VARCHAR(50) | NO | - | Interval (e.g., "24h", "1h", "3d") |
| `channel` | VARCHAR(50) | NO | - | Delivery method (email, push, in_app) |
| `status` | VARCHAR(20) | NO | - | success, failed, pending |
| `sent_at` | TIMESTAMP WITH TIME ZONE | NO | NOW() | When notification was sent |
| `error_message` | TEXT | YES | NULL | If status=failed, error details |
| `event_id` | UUID | NO | - | Kafka event ID for idempotency |

**Validation Rules**:

1. `reminder_type`: Must match pattern `\d+(m|h|d|w)`
2. `channel`: Must be one of: email, push, in_app
3. `status`: Must be one of: success, failed, pending
4. `event_id`: Must be unique (enforced by index)

**Indexes**:

```sql
-- Query notifications by task
CREATE INDEX idx_notification_logs_task ON notification_logs(task_id);

-- Query notifications by user
CREATE INDEX idx_notification_logs_user ON notification_logs(user_id);

-- Query notifications by timestamp (for analytics/cleanup)
CREATE INDEX idx_notification_logs_sent_at ON notification_logs(sent_at);

-- Unique constraint for idempotency
CREATE UNIQUE INDEX idx_notification_logs_event_id ON notification_logs(event_id);
```

**Relationships**:
- Belongs to Task (task_id → tasks.id, CASCADE DELETE)
- Belongs to User (user_id → users.id, CASCADE DELETE)

**Retention Policy**:
- Keep logs for 90 days (configurable)
- Cleanup via scheduled job: `DELETE FROM notification_logs WHERE sent_at < NOW() - INTERVAL '90 days'`

---

### 3. User (Extended)

**Purpose**: User account with timezone and notification preferences for reminders.

**Database Table**: `users` (existing, extended)

**New Fields**:

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `timezone` | VARCHAR(50) | NO | `'UTC'` | IANA timezone (e.g., "America/New_York", "Europe/London") |
| `notification_preferences` | JSONB | NO | `'{"email": true, "push": false, "in_app": true}'` | Enabled channels per type |

**Existing Fields** (unchanged):
- `id` (VARCHAR(100), PRIMARY KEY)
- `username` (VARCHAR(100), UNIQUE, NOT NULL)
- `email` (VARCHAR(200), UNIQUE, NOT NULL)
- `hashed_password` (VARCHAR(200), NOT NULL)
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT NOW())

**Validation Rules**:

1. `timezone`:
   - Must be valid IANA timezone (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")
   - Validated against pytz.all_timezones list
   - Default: 'UTC' if not specified

2. `notification_preferences`:
   - Must be JSON object
   - Valid keys: email, push, in_app
   - Valid values: boolean (true/false)
   - At least one channel must be enabled (enforced in application logic)

**Relationships**:
- Has many Tasks (user_id → tasks.user_id)
- Has many NotificationLogs (user_id → notification_logs.user_id)

---

### 4. ReminderEvent (Kafka Message)

**Purpose**: Event published when a reminder needs to be sent. Consumed by notification microservice.

**Kafka Topic**: `reminders`

**Schema** (JSON with Pydantic validation):

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from uuid import UUID

class ReminderEvent(BaseModel):
    event_id: UUID = Field(..., description="Unique identifier for idempotency")
    task_id: int = Field(..., description="Task being reminded about")
    user_id: str = Field(..., description="Task owner")
    task_title: str = Field(..., max_length=500, description="Human-readable task description")
    due_date: datetime = Field(..., description="When task is due (UTC)")
    reminder_type: str = Field(..., pattern=r"^\d+(m|h|d|w)$", description="Interval (e.g., '24h', '1h', '3d')")
    priority: str = Field(default="medium", description="Task priority (high/medium/low)")
    channels: List[str] = Field(..., description="Channels to notify (email, push, in_app)")
    user_timezone: str = Field(..., description="User's IANA timezone")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When event was created (UTC)")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": 123,
                "user_id": "user-abc-123",
                "task_title": "Submit quarterly report",
                "due_date": "2026-02-15T17:00:00Z",
                "reminder_type": "24h",
                "priority": "high",
                "channels": ["email", "push", "in_app"],
                "user_timezone": "America/New_York",
                "timestamp": "2026-02-14T17:00:00Z"
            }
        }
```

**Partitioning Strategy**:
- Partition by `user_id` (ensures ordered processing per user)
- Number of partitions: 3 (based on expected load)

**Serialization**:
- Format: JSON (UTF-8 encoded)
- Compression: GZIP (70% size reduction)

**Idempotency**:
- `event_id` must be unique UUID
- Notification service tracks processed `event_id` in `notification_logs.event_id` (unique index)
- Duplicate events are safely ignored (INSERT will fail due to unique constraint)

---

## Entity Relationships

```
User (1) ──── (∞) Task
  │                │
  │                │ (1)
  │                │
  │                ▼
  │              NotificationLog (∞)
  │                ▲
  └──────────────(∞)

Task (parent) ──── (∞) Task (child) [recurring tasks]

ReminderEvent (Kafka) ─[consumed by]→ Notification Microservice
                                            │
                                            ▼
                                        NotificationLog (persisted)
```

**Cascade Rules**:
- User deleted → CASCADE delete all Tasks and NotificationLogs
- Task deleted → CASCADE delete all NotificationLogs
- Parent Task deleted → SET NULL on child Tasks (parent_task_id)

---

## Database Migration

**Alembic Migration File**: `backend/src/migrations/versions/00X_add_due_date_reminder_fields.py`

```python
"""Add due_date and reminder fields to tasks table

Revision ID: 00X
Revises: 00Y
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '00X'
down_revision = '00Y'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to tasks table
    op.add_column('tasks', sa.Column('due_date', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column(
        'remind_before',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
        server_default=sa.text("'[\"24h\", \"1h\"]'::jsonb")
    ))
    op.add_column('tasks', sa.Column(
        'reminder_sent',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
        server_default=sa.text("'{}'::jsonb")
    ))

    # Create indexes for tasks table
    op.create_index(
        'idx_tasks_reminders',
        'tasks',
        ['user_id', 'due_date'],
        postgresql_where=sa.text('due_date IS NOT NULL AND completed = FALSE')
    )
    op.create_index(
        'idx_tasks_due_date',
        'tasks',
        ['due_date'],
        postgresql_where=sa.text('due_date IS NOT NULL')
    )

    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('reminder_type', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create indexes for notification_logs table
    op.create_index('idx_notification_logs_task', 'notification_logs', ['task_id'])
    op.create_index('idx_notification_logs_user', 'notification_logs', ['user_id'])
    op.create_index('idx_notification_logs_sent_at', 'notification_logs', ['sent_at'])
    op.create_unique_index('idx_notification_logs_event_id', 'notification_logs', ['event_id'])

    # Add new columns to users table
    op.add_column('users', sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'))
    op.add_column('users', sa.Column(
        'notification_preferences',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'{\"email\": true, \"push\": false, \"in_app\": true}'::jsonb")
    ))

def downgrade():
    # Remove columns from users table
    op.drop_column('users', 'notification_preferences')
    op.drop_column('users', 'timezone')

    # Drop notification_logs table and indexes
    op.drop_index('idx_notification_logs_event_id', table_name='notification_logs')
    op.drop_index('idx_notification_logs_sent_at', table_name='notification_logs')
    op.drop_index('idx_notification_logs_user', table_name='notification_logs')
    op.drop_index('idx_notification_logs_task', table_name='notification_logs')
    op.drop_table('notification_logs')

    # Drop indexes from tasks table
    op.drop_index('idx_tasks_due_date', table_name='tasks')
    op.drop_index('idx_tasks_reminders', table_name='tasks')

    # Remove columns from tasks table
    op.drop_column('tasks', 'reminder_sent')
    op.drop_column('tasks', 'remind_before')
    op.drop_column('tasks', 'due_date')
```

**Migration Testing**:
1. Test upgrade on empty database
2. Test upgrade on database with 10,000+ existing tasks
3. Test downgrade (no data loss for non-reminder fields)
4. Verify indexes are created and used by queries

---

## Query Examples

### 1. Find tasks with reminders due in next 24 hours

```sql
SELECT id, user_id, title, due_date, remind_before, reminder_sent
FROM tasks
WHERE user_id = :user_id
  AND due_date IS NOT NULL
  AND completed = FALSE
  AND due_date BETWEEN NOW() AND NOW() + INTERVAL '24 hours'
  AND (
    -- Check if 24h reminder needs to be sent
    (remind_before @> '["24h"]'::jsonb AND NOT (reminder_sent ? '24h'))
    OR
    -- Check if 1h reminder needs to be sent
    (remind_before @> '["1h"]'::jsonb AND NOT (reminder_sent ? '1h'))
  );
```

**Expected Performance**: < 50ms with `idx_tasks_reminders` index

### 2. Mark reminder as sent

```sql
UPDATE tasks
SET reminder_sent = jsonb_set(
  COALESCE(reminder_sent, '{}'::jsonb),
  '{24h}',
  to_jsonb(NOW()::text)
)
WHERE id = :task_id;
```

### 3. Query notification logs for a user

```sql
SELECT nl.*, t.title as task_title
FROM notification_logs nl
JOIN tasks t ON nl.task_id = t.id
WHERE nl.user_id = :user_id
  AND nl.sent_at >= NOW() - INTERVAL '30 days'
ORDER BY nl.sent_at DESC
LIMIT 100;
```

**Expected Performance**: < 100ms with `idx_notification_logs_user` index

---

**Data Model Status**: ✅ COMPLETE

**Next Steps**:
1. Generate API contracts in `contracts/openapi.yaml`
2. Generate MCP tool specifications in `contracts/mcp-tools.md`
3. Generate Kafka event schemas in `contracts/kafka-events.md`
4. Create integration guide in `quickstart.md`
