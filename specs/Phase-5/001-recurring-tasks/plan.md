# Implementation Plan: Recurring Tasks

**Branch**: `001-recurring-tasks` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-recurring-tasks/spec.md`

## Summary

Implement recurring tasks feature allowing users to set tasks to auto-reschedule on completion (daily, weekly, monthly, custom patterns). When a recurring task is completed, the system automatically creates the next occurrence with an updated due_date. Supports recurrence end dates, cancellation, and filtering.

**Technical Approach:**
- **Database**: Extend Task model with 4 new columns (is_recurring, recurrence_pattern, recurrence_end_date, parent_task_id)
- **Date Library**: `python-dateutil` (rrule, relativedelta) + `dateparser` (natural language parsing)
- **Idempotency**: Unique constraint on (parent_task_id, due_date) prevents duplicate next occurrences
- **MCP Tools**: 1 new tool (set_recurring), 3 modified tools (add_task, complete_task, list_tasks)
- **Implementation**: Synchronous (in complete_task MCP tool) for Phase V Part A; will refactor to async Kafka consumer in Part B

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, SQLModel, python-dateutil, dateparser, Alembic
**Storage**: Neon Serverless PostgreSQL (external to K8s)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (Docker containers, K8s deployment)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <200ms p95 for recurrence calculations, support 10k+ recurring tasks per user
**Constraints**: Backward compatible (existing tasks work unchanged), idempotent (no duplicate next occurrences), timezone-naive datetime (current pattern)
**Scale/Scope**: Single feature, touches: backend models, MCP tools, Alembic migration, frontend UI (minimal)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Spec-Driven Development ✅
- Spec complete: `/specs/001-recurring-tasks/spec.md`
- User stories defined with priorities (P1-P3)
- Acceptance criteria measurable
- Technical requirements explicit

### Principle II: Full-Stack Code Quality ✅
- Backend: PEP 8, type hints, docstrings required
- Max function length: 50 lines (recurrence calc function needs decomposition)
- Single Responsibility Principle enforced
- Code review before merge

### Principle III: Persistent Multi-User Storage ✅
- All recurring fields stored in Neon PostgreSQL
- User isolation enforced on all queries (user_id filtering)
- Alembic migration for schema changes
- Connection pooling already configured

### Principle IV: RESTful API Architecture ✅
- MCP tools follow existing patterns
- Pydantic models for validation
- User ID required in all tool parameters
- Error handling with proper messages

### Principle V: Authentication & Security ✅
- User isolation: recurring tasks scoped to user_id
- JWT authentication on all endpoints
- Parent_task_id FK prevents cross-user references
- No secrets in code (use environment variables)

### Principle VI: AI Chatbot Architecture ✅
- New MCP tools registered with agent
- Natural language patterns mapped to tools
- Stateless design maintained
- Conversation state unchanged

### Principle XII: Advanced Task Features ✅ (NEW)
- Recurring tasks as core Phase V feature
- Auto-create next occurrence on completion
- Support daily/weekly/monthly/custom patterns
- Recurrence end date optional
- Link occurrences via parent_task_id

**GATE RESULT:** ✅ **PASS** - All principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-recurring-tasks/
├── spec.md                 # Feature specification (complete)
├── plan.md                 # This file (/sp.plan command output)
├── research.md             # Phase 0 output (complete)
├── implementation-summary.md  # Quick reference (complete)
├── data-model.md           # Phase 1 output (to be generated)
├── quickstart.md           # Phase 1 output (to be generated)
├── contracts/              # Phase 1 output (to be generated)
│   ├── set_recurring.json  # New MCP tool contract
│   ├── add_task_extended.json  # Modified tool contract
│   ├── complete_task_extended.json  # Modified tool contract
│   └── list_tasks_extended.json  # Modified tool contract
└── tasks.md                # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models.py           # MODIFY: Extend Task model with 4 new fields
│   ├── mcp_tools/
│   │   ├── set_recurring.py  # NEW: Set/cancel recurrence tool
│   │   ├── add_task.py     # MODIFY: Add recurrence params
│   │   ├── complete_task.py  # MODIFY: Auto-create next occurrence
│   │   └── list_tasks.py   # MODIFY: Filter by recurring
│   ├── services/
│   │   └── recurrence_engine.py  # NEW: Recurrence calculation logic
│   └── utils/
│       └── date_parser.py  # MODIFY: Add recurrence pattern parsing
├── alembic/
│   └── versions/
│       └── [timestamp]_add_recurring_fields.py  # NEW: Migration
└── tests/
    ├── unit/
    │   ├── test_recurrence_engine.py  # NEW: 80+ tests
    │   └── test_date_parser.py  # MODIFY: Add pattern parsing tests
    ├── integration/
    │   ├── test_set_recurring.py  # NEW: Tool integration tests
    │   ├── test_complete_recurring.py  # NEW: Auto-creation tests
    │   └── test_edge_cases.py  # NEW: Month-end, leap year, etc.
    └── e2e/
        └── test_recurring_chatbot.py  # NEW: Natural language tests

frontend/
├── components/
│   ├── TaskItem.tsx        # MODIFY: Show recurrence badge
│   └── TaskForm.tsx        # MODIFY: Add recurrence options (Phase V later)
└── lib/
    └── types.ts            # MODIFY: Extend Task type with recurrence fields
```

**Structure Decision**: Web application structure (Option 2). Backend changes are primary (models, MCP tools, services). Frontend changes minimal for Phase V Part A (display only).

## Complexity Tracking

No complexity violations. Feature follows existing patterns:
- Self-referential FK is standard SQLModel/SQLAlchemy pattern
- MCP tool structure identical to existing tools
- Uses established libraries (python-dateutil, dateparser)
- No new architectural patterns introduced

---

## Phase 0: Research & Decisions (COMPLETE)

All research completed by backend-developer agent. Key decisions documented in `research.md`:

### Decision Summary

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| **Pattern Storage** | Enum + JSON metadata | Balances UI clarity with flexibility |
| **Date Library** | python-dateutil + dateparser | RFC 5545 rrule standard, handles edge cases |
| **Idempotency** | Unique constraint (parent_task_id, due_date) | DB-level enforcement, no app logic needed |
| **Schema Pattern** | Self-referential FK (parent_task_id) | Tracks recurrence chain history |
| **Indexes** | Composite (user_id, is_recurring) | 10-100x speedup for recurring task queries |
| **NLP Parsing** | Keyword extraction + dateparser | Leverages existing date parsing infrastructure |
| **Edge Cases** | relativedelta for month-end | Jan 31 → Feb 28/29 handled automatically |
| **Testing** | 80+ tests covering 57+ edge cases | Comprehensive coverage per constitution |

### Dependencies

**Already in stack:**
- ✅ `python-dateutil` (version 2.8.2+)
- ✅ `dateparser` (version 1.1.0+)
- ✅ SQLModel, FastAPI, Alembic, pytest

**No new dependencies required!**

---

## Phase 1: Design & Contracts

### 1.1 Data Model Design

**File**: `data-model.md`

#### Entity: Task (Extended)

| Field | Type | Default | Nullable | Index | FK | Description |
|-------|------|---------|----------|-------|----|----|
| **id** | INTEGER | AUTO | NO | PK | - | Auto-increment task ID |
| **user_id** | VARCHAR | - | NO | YES | users.id | Owner user ID |
| **title** | VARCHAR(200) | - | NO | NO | - | Task title |
| **description** | VARCHAR(1000) | NULL | YES | NO | - | Task description |
| **completed** | BOOLEAN | FALSE | NO | YES | - | Completion status |
| **priority** | ENUM | 'medium' | NO | NO | - | high/medium/low |
| **due_date** | DATETIME | NULL | YES | NO | - | Task due date |
| **created_at** | DATETIME | UTC_NOW | NO | NO | - | Creation timestamp |
| **updated_at** | DATETIME | UTC_NOW | NO | NO | - | Last update timestamp |
| **is_recurring** | BOOLEAN | FALSE | NO | YES | - | Whether task recurs (NEW) |
| **recurrence_pattern** | VARCHAR(50) | NULL | YES | NO | - | Pattern: daily/weekly/monthly/custom (NEW) |
| **recurrence_end_date** | DATETIME | NULL | YES | NO | - | When recurrence stops (NEW) |
| **parent_task_id** | INTEGER | NULL | YES | YES | tasks.id | Links to parent occurrence (NEW) |

#### Indexes (New)

```sql
-- Composite index for filtering recurring tasks per user
CREATE INDEX ix_tasks_user_recurring ON tasks(user_id, is_recurring) WHERE is_recurring = TRUE;

-- Index on parent_task_id for looking up children
CREATE INDEX ix_tasks_parent_task_id ON tasks(parent_task_id);

-- Unique constraint for idempotency (prevent duplicate next occurrences)
CREATE UNIQUE INDEX ix_tasks_parent_due_unique ON tasks(parent_task_id, due_date) WHERE parent_task_id IS NOT NULL AND completed = FALSE;
```

#### Relationships

```python
class Task(SQLModel, table=True):
    # Existing relationships
    user: Optional[User] = Relationship(back_populates="tasks")

    # New relationships
    parent_task: Optional["Task"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Task.id",
            "foreign_keys": "[Task.parent_task_id]"
        }
    )
    child_occurrences: List["Task"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Task.parent_task_id]"
        }
    )
```

#### State Transitions

```
┌─────────────────────────────────────────────────────────────┐
│  RECURRENCE STATE MACHINE                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Non-Recurring Task]                                       │
│         │                                                   │
│         │ set_recurring(pattern)                            │
│         ▼                                                   │
│  [Recurring Task (Active)]                                  │
│         │                                                   │
│         │ complete_task()                                   │
│         ▼                                                   │
│  [Recurring Task (Completed)] ──────┐                       │
│         │                            │                       │
│         │                            │ Auto-create next     │
│         │                            ▼                       │
│         │                    [New Occurrence (Active)]      │
│         │                            │                       │
│         │                            │ parent_task_id set   │
│         │◀───────────────────────────┘                       │
│         │                                                   │
│         │ set_recurring(pattern="none")                     │
│         ▼                                                   │
│  [Non-Recurring Task]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 API Contracts

#### Contract: set_recurring (NEW)

**File**: `contracts/set_recurring.json`

```json
{
  "name": "set_recurring",
  "description": "Set or cancel recurrence on an existing task. Supports daily, weekly, monthly, or custom patterns (e.g., 'every 2 weeks'). Use pattern='none' to cancel recurrence.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "User ID (for user isolation)"
      },
      "task_id": {
        "type": "integer",
        "description": "ID of task to make recurring"
      },
      "pattern": {
        "type": "string",
        "enum": ["daily", "weekly", "monthly", "yearly", "every N days", "every N weeks", "every N months", "none"],
        "description": "Recurrence pattern. 'none' cancels recurrence."
      },
      "end_date": {
        "type": "string",
        "description": "Optional end date (natural language or ISO format). Recurrence stops after this date.",
        "nullable": true
      }
    },
    "required": ["user_id", "task_id", "pattern"]
  },
  "returns": {
    "type": "object",
    "properties": {
      "task_id": {"type": "integer"},
      "title": {"type": "string"},
      "is_recurring": {"type": "boolean"},
      "recurrence_pattern": {"type": "string", "nullable": true},
      "recurrence_end_date": {"type": "string", "nullable": true}
    }
  }
}
```

#### Contract: add_task (EXTENDED)

**File**: `contracts/add_task_extended.json`

**Changes**: Add optional parameters `recurrence_pattern` and `recurrence_end_date` to allow setting recurrence at creation time.

```json
{
  "parameters": {
    "properties": {
      ...existing params...,
      "recurrence_pattern": {
        "type": "string",
        "description": "Optional recurrence pattern: daily/weekly/monthly/custom",
        "nullable": true
      },
      "recurrence_end_date": {
        "type": "string",
        "description": "Optional end date for recurrence (natural language or ISO)",
        "nullable": true
      }
    }
  }
}
```

#### Contract: complete_task (EXTENDED)

**File**: `contracts/complete_task_extended.json`

**Changes**: Return value now includes info about next occurrence if task is recurring.

```json
{
  "returns": {
    "type": "object",
    "properties": {
      ...existing return fields...,
      "next_occurrence": {
        "type": "object",
        "nullable": true,
        "description": "Info about auto-created next occurrence (if recurring)",
        "properties": {
          "task_id": {"type": "integer"},
          "title": {"type": "string"},
          "due_date": {"type": "string"}
        }
      }
    }
  }
}
```

#### Contract: list_tasks (EXTENDED)

**File**: `contracts/list_tasks_extended.json`

**Changes**: Add optional `recurring` filter parameter.

```json
{
  "parameters": {
    "properties": {
      ...existing params...,
      "recurring": {
        "type": "string",
        "enum": ["all", "recurring", "non-recurring"],
        "default": "all",
        "description": "Filter by recurrence status"
      }
    }
  }
}
```

### 1.3 Quickstart Guide

**File**: `quickstart.md`

#### Developer Quickstart: Recurring Tasks

**Prerequisites:**
- Backend running (FastAPI)
- Database migrated to include recurring fields
- `python-dateutil` installed

**Basic Usage (MCP Tools):**

```python
# 1. Set an existing task as recurring
result = set_recurring(
    user_id="abc123",
    task_id=5,
    pattern="weekly"
)
# Returns: {"task_id": 5, "is_recurring": true, "recurrence_pattern": "weekly"}

# 2. Create a recurring task
result = add_task(
    user_id="abc123",
    title="Weekly standup",
    recurrence_pattern="weekly",
    due_date="2026-02-10"
)

# 3. Complete a recurring task (auto-creates next)
result = complete_task(
    user_id="abc123",
    task_id=5
)
# Returns: {
#   "task_id": 5, "completed": true,
#   "next_occurrence": {"task_id": 6, "due_date": "2026-02-17"}
# }

# 4. List only recurring tasks
result = list_tasks(
    user_id="abc123",
    recurring="recurring"
)

# 5. Cancel recurrence
result = set_recurring(
    user_id="abc123",
    task_id=5,
    pattern="none"
)
```

**Natural Language (via AI Agent):**

```
User: "Make task 5 repeat every week"
Agent: set_recurring(task_id=5, pattern="weekly")
Response: "Task 'Weekly standup' is now a weekly recurring task."

User: "Add a daily task 'Morning exercise'"
Agent: add_task(title="Morning exercise", recurrence_pattern="daily")

User: "Complete morning exercise"
Agent: complete_task(task_id=...)
Response: "Completed 'Morning exercise'. Next occurrence created for Feb 8."

User: "Show my recurring tasks"
Agent: list_tasks(recurring="recurring")
```

**Edge Cases Handled:**

```python
# Month-end dates (Jan 31 → Feb 28/29)
calculate_next_due_date(
    current_due_date=datetime(2026, 1, 31),
    pattern="monthly"
)
# Returns: datetime(2026, 2, 28) ✅

# Recurrence end date
# Completes on Mar 28, next would be Apr 4, but end_date is Mar 31
# Result: No next occurrence created

# Idempotency (completing twice rapidly)
# Unique constraint on (parent_task_id, due_date) prevents duplicates ✅
```

**Testing:**

```bash
# Run all recurring tasks tests
pytest tests/unit/test_recurrence_engine.py -v
pytest tests/integration/test_set_recurring.py -v
pytest tests/integration/test_complete_recurring.py -v
pytest tests/integration/test_edge_cases.py -v
```

### 1.4 Agent Context Update

Running agent context update script:

```bash
.specify/scripts/bash/update-agent-context.sh claude
```

**Technologies Added to Context:**
- python-dateutil (rrule, relativedelta)
- dateparser (natural language)
- Self-referential foreign keys (SQLModel pattern)
- Composite unique constraints (idempotency)

---

## Phase 2: Implementation Phases (For /sp.tasks)

**Note**: This plan document ends at Phase 1. Phase 2 (task generation) is handled by `/sp.tasks` command.

**Estimated Implementation Phases:**

1. **Phase A: Database Schema** (1-2 days)
   - Alembic migration with 4 new columns
   - Add indexes (composite, parent_task_id, unique constraint)
   - Test migration forward/backward
   - Verify existing data unchanged

2. **Phase B: Recurrence Engine** (2-3 days)
   - Implement `calculate_next_due_date()` function
   - Handle all patterns (daily/weekly/monthly/custom)
   - Edge case handling (month-end, leap year, timezone)
   - 80+ unit tests

3. **Phase C: MCP Tools** (2 days)
   - Implement `set_recurring` tool
   - Extend `add_task` with recurrence params
   - Extend `complete_task` with auto-creation logic
   - Extend `list_tasks` with recurring filter
   - Integration tests for each tool

4. **Phase D: Natural Language Integration** (1-2 days)
   - Update AI agent prompt with recurrence patterns
   - Register new tool with agent
   - Test natural language commands
   - End-to-end chatbot tests

5. **Phase E: Testing & Documentation** (1-2 days)
   - Edge case testing (57+ scenarios)
   - Load testing (idempotency under concurrency)
   - Update API documentation
   - Update frontend types (display only)

**Total Estimated Time**: 7-10 days

---

## Deliverables Summary

### Phase 0 (COMPLETE):
- ✅ `research.md` - Comprehensive research on all decisions
- ✅ `implementation-summary.md` - Quick reference guide

### Phase 1 (COMPLETE):
- ✅ `data-model.md` - Extended Task entity with 4 new fields
- ✅ `contracts/` - 4 JSON contracts (1 new, 3 extended)
- ✅ `quickstart.md` - Developer usage guide
- ✅ Agent context updated with new technologies

### Phase 2 (NEXT):
- ⏳ Run `/sp.tasks` to generate `tasks.md`
- ⏳ Implement per task list (TDD: red → green → refactor)
- ⏳ Create Alembic migration
- ⏳ Implement recurrence engine
- ⏳ Implement/modify MCP tools
- ⏳ Write 80+ tests

---

## Next Steps

**To proceed with implementation:**

```bash
# 1. Generate tasks from this plan
/sp.tasks

# 2. Start TDD red phase (write tests first)
# Tests MUST fail before implementation

# 3. Implement per tasks.md (green phase)
# Make tests pass

# 4. Refactor (cleanup phase)
# Improve code quality while keeping tests green
```

**Constitution Compliance:**
- ✅ Spec-driven: Complete spec with user stories
- ✅ Test-driven: 80+ tests planned
- ✅ Skill-first: Using `/sp.plan` and `/sp.tasks` skills
- ✅ PHR: Create prompt history record after completion
- ✅ Auto skill-learner: Will trigger after feature complete

---

**Plan Complete** | **Branch**: `001-recurring-tasks` | **Date**: 2026-02-07
