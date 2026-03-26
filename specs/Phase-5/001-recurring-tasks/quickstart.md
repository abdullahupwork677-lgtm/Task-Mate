# Recurring Tasks - Quickstart Guide

**Get started with recurring tasks in 5 minutes!**

This guide provides quick, copy-paste examples to get you up and running with recurring tasks.

---

## Prerequisites

- Backend running on `http://localhost:8000`
- User account created (signup completed)
- JWT token obtained (login completed)

---

## Quick Test Setup

### 1. Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload
```

### 2. Get Authentication Token

```bash
# Signup (if needed)
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Login and get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Save the access_token from the response
export TOKEN="your_access_token_here"
```

---

## Example 1: Create Daily Recurring Task

**Goal**: Create a task that repeats every day.

### Step 1: Create the task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Morning exercise",
    "priority": "high",
    "is_recurring": true,
    "recurrence_pattern": "daily"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Morning exercise",
  "priority": "high",
  "is_recurring": true,
  "recurrence_pattern": "daily",
  "completed": false,
  "created_at": "2026-02-09T10:00:00Z"
}
```

### Step 2: Complete the task

```bash
curl -X PATCH "http://localhost:8000/api/tasks/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true
  }'
```

**Expected Result:**
- Task #1 marked as completed
- Task #2 auto-created with due date = tomorrow

### Step 3: Verify next occurrence was created

```bash
curl -X GET http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN"
```

**Expected**: You should see both Task #1 (completed) and Task #2 (pending, due tomorrow).

---

## Example 2: Weekly Task with End Date

**Goal**: Create a weekly task that stops after 3 months.

### Step 1: Create task via MCP tool

```python
# Via Python (for testing MCP tools directly)
from datetime import datetime, timedelta
from backend.src.mcp_tools.add_task import add_task, AddTaskParams

params = AddTaskParams(
    user_id="user-123",
    title="Team weekly review",
    description="Discuss sprint progress and blockers",
    priority="high",
    recurrence_pattern="weekly",
    recurrence_end_date=(datetime.utcnow() + timedelta(days=90)).isoformat()
)

result = await add_task(db, params)
print(result)
```

### Step 2: Verify recurrence settings

```bash
curl -X GET http://localhost:8000/api/tasks/1 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Team weekly review",
  "description": "Discuss sprint progress and blockers",
  "priority": "high",
  "is_recurring": true,
  "recurrence_pattern": "weekly",
  "recurrence_end_date": "2026-05-10T00:00:00Z"
}
```

---

## Example 3: Custom Interval (Every 3 Days)

**Goal**: Create a task that repeats every 3 days.

### Via API

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Water plants",
    "priority": "medium",
    "is_recurring": true,
    "recurrence_pattern": "every 3 days"
  }'
```

### Via AI Agent (Natural Language)

```bash
# Start chat
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to water plants every 3 days"
  }'
```

**Expected**: AI creates recurring task with pattern "every 3 days".

---

## Example 4: Set Existing Task as Recurring

**Goal**: Convert a one-time task to a recurring task.

### Step 1: Create a regular task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Take vitamins",
    "priority": "low"
  }'
```

### Step 2: Make it recurring via MCP tool

```python
from backend.src.mcp_tools.set_recurring import set_recurring

result = await set_recurring(
    user_id=1,
    task_id=1,
    pattern="daily"
)
print(result)
```

**Expected Response:**
```json
{
  "task_id": 1,
  "title": "Take vitamins",
  "is_recurring": true,
  "recurrence_pattern": "daily",
  "recurrence_end_date": null
}
```

---

## Example 5: Cancel Recurrence

**Goal**: Stop a task from repeating.

### Via MCP Tool

```python
from backend.src.mcp_tools.set_recurring import set_recurring

result = await set_recurring(
    user_id=1,
    task_id=1,
    pattern="none"  # Special pattern to cancel recurrence
)
print(result)
```

**Expected Response:**
```json
{
  "task_id": 1,
  "title": "Take vitamins",
  "is_recurring": false,
  "recurrence_pattern": null,
  "recurrence_end_date": null
}
```

### Via AI Agent

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Stop repeating task 1"
  }'
```

---

## Example 6: Complex Scenario - Monthly Reports for 1 Year

**Goal**: Create a monthly task that runs for exactly 12 months.

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Monthly sales report",
    "description": "Compile sales data, analyze trends, and create presentation",
    "priority": "high",
    "due_date": "2026-03-01T09:00:00Z",
    "is_recurring": true,
    "recurrence_pattern": "monthly",
    "recurrence_end_date": "2027-02-28T23:59:59Z"
  }'
```

**What happens:**
1. Task created with due date: March 1, 2026
2. Complete task #1 → Task #2 created for April 1, 2026
3. Complete task #2 → Task #3 created for May 1, 2026
4. ... continues for 12 months
5. Complete task #12 (Feb 1, 2027) → No next occurrence (end date reached)

---

## Testing Checklist

Use this checklist to validate all examples work:

### Basic Functionality
- [ ] Create daily recurring task
- [ ] Complete recurring task → next occurrence auto-created
- [ ] Create weekly recurring task
- [ ] Create monthly recurring task
- [ ] Create custom interval task (every N days/weeks/months)

### Advanced Features
- [ ] Set existing task as recurring
- [ ] Cancel recurrence (pattern="none")
- [ ] Create recurring task with end date
- [ ] End date reached → no more occurrences created
- [ ] AI agent understands "Add a daily task 'X'"
- [ ] AI agent understands "Make task recurring"
- [ ] AI agent understands "Stop repeating task"

### Edge Cases
- [ ] Complete same task twice → error (already completed)
- [ ] Rapid completion → no duplicate next occurrences (idempotency)
- [ ] Task with no due_date → uses completion timestamp
- [ ] Month-end recurrence (Jan 31 → Feb 28)
- [ ] Delete recurring task → no next occurrence created

### Performance
- [ ] Create 100 recurring tasks → completes in <10s
- [ ] Complete 100 recurring tasks concurrently → no duplicates
- [ ] List 1000 recurring tasks → completes in <100ms

---

## Common Patterns

### Daily Standup

```json
{
  "title": "Daily standup",
  "due_date": "tomorrow at 9am",
  "is_recurring": true,
  "recurrence_pattern": "daily",
  "priority": "high"
}
```

### Weekly Team Review

```json
{
  "title": "Weekly team review",
  "due_date": "next Friday at 2pm",
  "is_recurring": true,
  "recurrence_pattern": "weekly",
  "priority": "high"
}
```

### Monthly Budget Review

```json
{
  "title": "Monthly budget review",
  "due_date": "first day of next month",
  "is_recurring": true,
  "recurrence_pattern": "monthly",
  "priority": "medium"
}
```

### Quarterly Reports

```json
{
  "title": "Quarterly financial report",
  "description": "Prepare Q1 financial report for board meeting",
  "due_date": "April 1, 2026",
  "is_recurring": true,
  "recurrence_pattern": "every 3 months",
  "priority": "high"
}
```

### Temporary Project Task

```json
{
  "title": "Project standup",
  "description": "Daily standup for Project Phoenix",
  "is_recurring": true,
  "recurrence_pattern": "daily",
  "recurrence_end_date": "2026-06-30",
  "priority": "high"
}
```

---

## Troubleshooting

### Issue: "Invalid recurrence pattern" error

**Cause**: Pattern doesn't match supported formats.

**Solution**: Use one of:
- `daily`, `weekly`, `monthly`, `yearly`
- `every 3 days`, `every 2 weeks`, `every 6 months`

### Issue: Next occurrence not created

**Possible causes:**
1. **Task not recurring** → Check `is_recurring` is true
2. **End date reached** → Check `recurrence_end_date`
3. **Task not completed** → Verify task is marked complete

**Debug:**
```bash
# Check task details
curl -X GET http://localhost:8000/api/tasks/{task_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: Duplicate next occurrences

**Cause**: Concurrent completions.

**Status**: This should NOT happen due to unique database constraint.

**If it happens**: Report as bug with steps to reproduce.

---

## Next Steps

- **User Guide**: See `docs/user-guide-recurring.md` for comprehensive feature documentation
- **API Reference**: See `backend/docs/api.md` for detailed API documentation
- **Testing**: Run full test suite with `pytest tests/`

---

**Last Updated**: 2026-02-09
**Status**: ✅ Validated
**Phase**: V (Recurring Tasks)
