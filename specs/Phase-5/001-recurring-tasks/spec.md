# Feature Specification: Recurring Tasks

**Feature Branch**: `001-recurring-tasks`
**Created**: 2026-02-07
**Status**: Draft
**Input**: Phase V Constitution Principle XII - Advanced Task Features
**Constitution Ref**: Principles I (SDD), II (Code Quality), XII (Recurring Tasks)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set a Task as Recurring via Chat (Priority: P1)

A user creates a task (or has an existing task) and tells the chatbot to make it
recurring. The system stores the recurrence pattern and marks the task as
recurring. When the task is listed, the recurrence info is visible.

**Why this priority**: This is the core capability - without setting recurrence,
no other recurring behaviour can exist.

**Independent Test**: Create a task via chat, say "Make this a weekly task",
verify the task's `is_recurring=True` and `recurrence_pattern="weekly"` in DB.

**Acceptance Scenarios**:

1. **Given** a user has an existing task "Weekly standup",
   **When** the user says "Make task 5 repeat every week",
   **Then** the system sets `is_recurring=True`, `recurrence_pattern="weekly"`
   on task 5 and confirms "Task 'Weekly standup' is now a weekly recurring task."

2. **Given** a user is creating a new task,
   **When** the user says "Add a recurring task 'Pay rent' every month",
   **Then** the system creates a task with `is_recurring=True`,
   `recurrence_pattern="monthly"` and confirms creation with recurrence info.

3. **Given** a user has an existing recurring task,
   **When** the user says "Change task 5 to repeat daily",
   **Then** the system updates `recurrence_pattern` to "daily" and confirms.

4. **Given** a user provides an invalid recurrence pattern,
   **When** the user says "Make task 5 repeat every century",
   **Then** the system responds with supported patterns:
   daily, weekly, monthly, custom (e.g., "every 3 days").

---

### User Story 2 - Auto-Create Next Occurrence on Completion (Priority: P1)

When a user completes a recurring task, the system automatically creates the
next occurrence with an updated due date. The original task stays completed.

**Why this priority**: This is the fundamental value of recurring tasks - the
auto-reschedule behaviour. Without this, "recurring" is just a label.

**Independent Test**: Complete a daily recurring task with due_date=today, verify
a new task is created with due_date=tomorrow and same recurrence pattern.

**Acceptance Scenarios**:

1. **Given** a daily recurring task "Morning exercise" with due_date=2026-02-07,
   **When** the user says "Complete task 5" or "Mark morning exercise as done",
   **Then** the original task is marked `completed=True` AND a new task is
   created with title="Morning exercise", `due_date=2026-02-08`,
   `is_recurring=True`, `recurrence_pattern="daily"`,
   `parent_task_id=5` (links to original).
   The chatbot responds: "Completed 'Morning exercise'. Next occurrence
   created for Feb 8, 2026."

2. **Given** a weekly recurring task "Team meeting" with due_date=2026-02-07 (Friday),
   **When** the user completes it,
   **Then** a new task is created with `due_date=2026-02-14` (next Friday).

3. **Given** a monthly recurring task "Pay rent" with due_date=2026-02-01,
   **When** the user completes it,
   **Then** a new task is created with `due_date=2026-03-01`.

4. **Given** a custom recurring task "Water plants" with pattern "every 3 days"
   and due_date=2026-02-07,
   **When** the user completes it,
   **Then** a new task is created with `due_date=2026-02-10`.

5. **Given** a recurring task WITHOUT a due_date,
   **When** the user completes it,
   **Then** a new task is created with `due_date` calculated from today's date
   plus the recurrence interval.

---

### User Story 3 - Cancel/Stop Recurrence (Priority: P2)

A user can stop a task from recurring. The task remains but no longer
auto-creates the next occurrence on completion.

**Why this priority**: Users need an escape hatch to stop recurring tasks.
Lower than P1 because initial value delivery works without cancellation.

**Independent Test**: Set a task as recurring, then say "Stop repeating task 5",
verify `is_recurring=False` and completing the task does NOT create a new one.

**Acceptance Scenarios**:

1. **Given** a recurring task "Weekly standup",
   **When** the user says "Stop repeating task 5" or "Cancel recurrence for task 5",
   **Then** `is_recurring` is set to `False`, `recurrence_pattern` is set to `None`,
   and the chatbot confirms: "Task 'Weekly standup' will no longer repeat."

2. **Given** a task that is NOT recurring,
   **When** the user says "Stop repeating task 5",
   **Then** the chatbot responds: "Task 'Weekly standup' is not a recurring task."

---

### User Story 4 - Set Recurrence End Date (Priority: P3)

A user can set an end date for recurrence. After that date, no more occurrences
are auto-created.

**Why this priority**: Nice-to-have refinement. Most users want indefinite
recurrence initially; end dates are for advanced use.

**Independent Test**: Set a recurring task with end_date=2026-03-01, complete it
on 2026-02-28, verify new task IS created. Complete the new task on 2026-03-01,
verify NO new task is created.

**Acceptance Scenarios**:

1. **Given** a weekly recurring task "Sprint review" ending on 2026-03-31,
   **When** the user completes it on 2026-03-28,
   **Then** a new task IS created (next occurrence 2026-04-04 > end date,
   so NO new task is created). The chatbot notes: "Completed 'Sprint review'.
   This was the last occurrence (recurrence ends 2026-03-31)."

2. **Given** a user sets recurrence with "repeat weekly until March 31",
   **When** the system processes this,
   **Then** `recurrence_end_date=2026-03-31` is stored.

---

### User Story 5 - List Recurring Tasks (Priority: P2)

A user can ask the chatbot to show only recurring tasks. The list shows
recurrence pattern and next due date.

**Why this priority**: Important for management but not blocking core
recurring functionality.

**Independent Test**: Create 3 tasks (2 recurring, 1 not), say "Show my
recurring tasks", verify only 2 are returned with pattern info.

**Acceptance Scenarios**:

1. **Given** a user has 5 tasks (3 recurring, 2 non-recurring),
   **When** the user says "Show my recurring tasks",
   **Then** only the 3 recurring tasks are listed with their recurrence pattern
   and next due date. E.g.:
   ```
   1. #5 Weekly standup (weekly, next: Feb 14)
   2. #8 Pay rent (monthly, next: Mar 1)
   3. #12 Water plants (every 3 days, next: Feb 10)
   ```

2. **Given** a user has no recurring tasks,
   **When** the user says "Show recurring tasks",
   **Then** the chatbot responds: "You don't have any recurring tasks."

---

### Edge Cases

- **Month-end dates**: Recurring monthly task due on Jan 31 → next occurrence
  should be Feb 28 (or Feb 29 in leap year), NOT error out.
- **Custom intervals**: "every 2 weeks" = 14 days, "every 3 months" = 3 months.
- **Rapid completions**: Completing a recurring task twice quickly MUST NOT
  create duplicate next occurrences (idempotency).
- **Deleted recurring tasks**: Deleting a recurring task MUST NOT create a next
  occurrence. Only completion triggers auto-creation.
- **Completing a non-current occurrence**: If a user completes an older
  parent task, the system MUST create the next occurrence from the latest
  occurrence's due date, not the old parent's.
- **Timezone handling**: Due dates are stored as naive datetime (current
  pattern). Recurrence calculations use the same approach.
- **No due_date on recurring task**: If a user sets a task as recurring but
  hasn't set a due date, the next occurrence's due_date is calculated from
  the completion timestamp.
- **Concurrent completions**: Two simultaneous requests to complete the same
  recurring task MUST NOT create two next occurrences. Use DB-level locking
  or unique constraint on `parent_task_id + completed=False`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow setting any task as recurring via the `set_recurring`
  MCP tool with patterns: daily, weekly, monthly, or custom (every N days/weeks/months).
- **FR-002**: System MUST allow setting recurrence during task creation via `add_task`
  MCP tool by accepting optional `recurrence_pattern` parameter.
- **FR-003**: When a recurring task is completed, the system MUST automatically create
  the next occurrence with an updated `due_date` and the same recurrence pattern.
- **FR-004**: The new occurrence MUST link to the completed task via `parent_task_id`
  for tracking the recurrence chain.
- **FR-005**: System MUST support cancelling recurrence via `set_recurring` tool
  with `pattern=null/none`.
- **FR-006**: System MUST support optional `recurrence_end_date` to auto-stop
  recurrence after a specified date.
- **FR-007**: System MUST allow filtering tasks by `is_recurring=true` in the
  `list_tasks` MCP tool.
- **FR-008**: The AI chatbot MUST understand natural language recurrence commands:
  "repeat daily", "make this weekly", "every Monday", "stop repeating".
- **FR-009**: The new occurrence MUST copy: title, description, priority, tags
  (Phase V), recurrence_pattern, recurrence_end_date, remind_before from parent.
- **FR-010**: System MUST handle month-end edge cases correctly (Jan 31 → Feb 28).
- **FR-011**: System MUST prevent duplicate next occurrences via idempotency check
  (only one pending child per parent).
- **FR-012**: User isolation MUST be enforced - a user can only manage recurrence
  on their own tasks.

### Key Entities

- **Task (Extended)**: Existing task entity extended with 4 new fields:
  `is_recurring` (bool), `recurrence_pattern` (string), `recurrence_end_date`
  (datetime), `parent_task_id` (int FK → tasks.id).
- **Recurrence Chain**: Linked list of tasks where each completed occurrence
  points to the next via `parent_task_id`. The chain tracks the full history.

### Database Schema Changes

**New columns on `tasks` table:**

| Column | Type | Default | Nullable | Index | Description |
|--------|------|---------|----------|-------|-------------|
| `is_recurring` | BOOLEAN | False | NOT NULL | Yes (composite with user_id) | Whether task recurs |
| `recurrence_pattern` | VARCHAR(50) | NULL | YES | No | "daily", "weekly", "monthly", "every N days/weeks/months" |
| `recurrence_end_date` | DATETIME | NULL | YES | No | Optional end date for recurrence |
| `parent_task_id` | INTEGER | NULL | YES | Yes | FK to tasks.id - links to completed parent |

**Indexes:**
- `ix_tasks_user_recurring` → composite index on `(user_id, is_recurring)` for
  efficient filtering of recurring tasks per user.
- `ix_tasks_parent_task_id` → index on `parent_task_id` for looking up children.

**Foreign Key:**
- `parent_task_id` → `tasks.id` (self-referential, ON DELETE SET NULL)

### MCP Tool Changes

**New Tool: `set_recurring`**

| Field | Value |
|-------|-------|
| **Purpose** | Set or cancel recurrence on a task |
| **Parameters** | `user_id` (str, required), `task_id` (int, required), `pattern` (str, required: "daily"/"weekly"/"monthly"/"every N days"/"every N weeks"/"every N months"/"none"), `end_date` (str, optional: natural language or ISO date) |
| **Returns** | `task_id`, `title`, `is_recurring`, `recurrence_pattern`, `recurrence_end_date` |
| **Example Input** | `{"user_id": "abc", "task_id": 5, "pattern": "weekly"}` |
| **Example Output** | `{"task_id": 5, "title": "Standup", "is_recurring": true, "recurrence_pattern": "weekly", "recurrence_end_date": null}` |

**Modified Tool: `add_task`**

Add optional parameters:
- `recurrence_pattern` (str, optional) - sets recurrence at creation time
- `recurrence_end_date` (str, optional) - sets end date at creation time

**Modified Tool: `complete_task`**

After marking a recurring task as complete:
1. Check `is_recurring == True`
2. Calculate next due_date based on `recurrence_pattern`
3. Check `recurrence_end_date` - if next due_date exceeds it, do NOT create next
4. Create new task copying fields from completed task
5. Set `parent_task_id` on new task to completed task's ID
6. Return both completed task info AND new occurrence info

**Modified Tool: `list_tasks`**

Add optional parameter:
- `recurring` (str, optional: "all"/"recurring"/"non-recurring", default "all")

### Natural Language Patterns

The AI agent MUST map these patterns to MCP tool calls:

| User Says | MCP Tool Call |
|-----------|---------------|
| "Make task 5 weekly" | `set_recurring(task_id=5, pattern="weekly")` |
| "Add a daily task 'Exercise'" | `add_task(title="Exercise", recurrence_pattern="daily")` |
| "Repeat this every 2 weeks" | `set_recurring(task_id=..., pattern="every 2 weeks")` |
| "Stop repeating task 5" | `set_recurring(task_id=5, pattern="none")` |
| "Show recurring tasks" | `list_tasks(recurring="recurring")` |
| "Repeat weekly until March" | `set_recurring(..., pattern="weekly", end_date="March 31 2026")` |
| "Complete morning exercise" | `complete_task(task_id=...)` → auto-creates next |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can set any task as recurring (daily/weekly/monthly/custom) via
  natural language in under 5 seconds response time.
- **SC-002**: Completing a recurring task auto-creates next occurrence with correct
  due_date 100% of the time (including month-end edge cases).
- **SC-003**: Recurrence chain is traceable via `parent_task_id` linkage - any
  occurrence can be traced back to the original task.
- **SC-004**: All existing Phase I-IV functionality works unchanged after
  recurring tasks implementation (backward compatibility).
- **SC-005**: Zero duplicate next occurrences created under concurrent load
  (idempotency guarantee).
- **SC-006**: All recurring task operations respect user isolation - no
  cross-user recurrence manipulation possible.

## Technical Notes

### Recurrence Calculation Logic

```python
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re

def calculate_next_due_date(
    current_due_date: datetime | None,
    pattern: str,
    completion_date: datetime | None = None
) -> datetime:
    """Calculate next occurrence due date."""
    base_date = current_due_date or completion_date or datetime.utcnow()

    if pattern == "daily":
        return base_date + timedelta(days=1)
    elif pattern == "weekly":
        return base_date + timedelta(weeks=1)
    elif pattern == "monthly":
        return base_date + relativedelta(months=1)
    else:
        # Custom: "every N days/weeks/months"
        match = re.match(r"every (\d+) (days?|weeks?|months?)", pattern)
        if match:
            n = int(match.group(1))
            unit = match.group(2).rstrip("s")
            if unit == "day":
                return base_date + timedelta(days=n)
            elif unit == "week":
                return base_date + timedelta(weeks=n)
            elif unit == "month":
                return base_date + relativedelta(months=n)
    raise ValueError(f"Invalid recurrence pattern: {pattern}")
```

### Dependency: `python-dateutil`
Required for `relativedelta` (month-aware date arithmetic).
Add to `backend/requirements.txt`.

### Alembic Migration
Single migration adding 4 columns + 2 indexes. MUST be backward compatible -
all new columns are nullable or have defaults.

### Phase V Kafka Integration (Future)
In the Kafka/Dapr phase, the auto-creation of next occurrence will move from
synchronous (inside `complete_task`) to asynchronous (Kafka consumer). For now,
implement synchronously in `complete_task` tool. The refactor to Kafka will be:
1. `complete_task` publishes `task-completed` event to Kafka
2. Recurring Task Service (consumer) listens and creates next occurrence
3. Same logic, just async and decoupled

This spec covers the synchronous implementation first (Part A of Phase V).
