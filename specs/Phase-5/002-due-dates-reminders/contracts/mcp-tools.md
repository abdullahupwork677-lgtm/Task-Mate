# MCP Tool Contracts: Due Dates & Reminders

**Feature**: 002-due-dates-reminders
**Date**: 2026-02-09
**Protocol**: Model Context Protocol (MCP)

## Overview

This document specifies the MCP tools for managing due dates and reminders via the AI chatbot. Tools are registered with the OpenAI Agents SDK and callable through natural language commands.

---

## New MCP Tools

### 1. set_due_date

**Purpose**: Set or update a task's due date using natural language.

**Function Signature**:
```python
async def set_due_date(
    task_id: int,
    due_date_natural: str,
    user_id: str,
    db: Session
) -> Dict[str, Any]:
    """Set or update task due date with natural language parsing.

    Args:
        task_id: ID of the task to update
        due_date_natural: Natural language date (e.g., "tomorrow at 5pm", "next Friday")
        user_id: User ID for authorization
        db: Database session

    Returns:
        Dict containing updated task with formatted due date

    Raises:
        TaskNotFoundError: Task doesn't exist or user doesn't own it
        InvalidDateError: Date expression couldn't be parsed
    """
```

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "integer",
      "description": "ID of the task to update"
    },
    "due_date_natural": {
      "type": "string",
      "description": "Natural language due date (e.g., 'tomorrow at 5pm', 'next Friday at 2pm')"
    },
    "user_id": {
      "type": "string",
      "description": "User ID for authorization"
    }
  },
  "required": ["task_id", "due_date_natural", "user_id"]
}
```

**Output Schema**:
```json
{
  "task": {
    "id": 123,
    "title": "Submit report",
    "due_date": "2026-02-15T17:00:00Z",
    "due_date_formatted": "Tomorrow at 5:00 PM",
    "remind_before": ["24h", "1h"],
    "reminder_sent": {}
  },
  "message": "Due date set to Tomorrow at 5:00 PM. You'll receive reminders 24 hours and 1 hour before."
}
```

**Natural Language Examples**:
- "tomorrow at 5pm" → 2026-02-10 17:00:00 (user's timezone)
- "next Friday" → 2026-02-14 09:00:00 (defaults to 9am)
- "in 3 days" → 2026-02-12 00:00:00 (defaults to midnight)
- "Feb 15 at 2pm" → 2026-02-15 14:00:00
- "next Monday at 10:30am" → 2026-02-17 10:30:00

**Error Handling**:
- Invalid date → Return error message with examples
- Past date → Allow but warn user task is overdue
- Ambiguous date → Ask for clarification (e.g., "2/3" could be Feb 3 or Mar 2)

**AI Agent Usage**:
```
User: "Set task 5 due tomorrow at 5pm"
Agent: set_due_date(task_id=5, due_date_natural="tomorrow at 5pm", user_id="user-123")
Response: "Due date set to Tomorrow at 5:00 PM. You'll receive reminders 24 hours and 1 hour before."
```

---

### 2. set_reminder

**Purpose**: Configure custom reminder intervals for a task.

**Function Signature**:
```python
async def set_reminder(
    task_id: int,
    remind_before_natural: str,
    user_id: str,
    db: Session
) -> Dict[str, Any]:
    """Configure custom reminder intervals using natural language.

    Args:
        task_id: ID of the task to update
        remind_before_natural: Natural language intervals (e.g., "3 days before and 2 hours before")
        user_id: User ID for authorization
        db: Database session

    Returns:
        Dict containing updated task with reminder configuration

    Raises:
        TaskNotFoundError: Task doesn't exist or user doesn't own it
        InvalidIntervalError: Interval expression couldn't be parsed
        NoDueDateError: Task must have a due date to set reminders
    """
```

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "integer",
      "description": "ID of the task to update"
    },
    "remind_before_natural": {
      "type": "string",
      "description": "Natural language intervals (e.g., '3 days before and 2 hours before')"
    },
    "user_id": {
      "type": "string",
      "description": "User ID for authorization"
    }
  },
  "required": ["task_id", "remind_before_natural", "user_id"]
}
```

**Output Schema**:
```json
{
  "task": {
    "id": 123,
    "title": "Submit report",
    "due_date": "2026-02-15T17:00:00Z",
    "remind_before": ["3d", "2h"],
    "reminder_sent": {}
  },
  "message": "Reminders set: 3 days before (Feb 12 at 5:00 PM) and 2 hours before (Feb 15 at 3:00 PM)"
}
```

**Natural Language Examples**:
- "3 days before" → ["3d"]
- "2 hours before and 30 minutes before" → ["2h", "30m"]
- "1 week before, 1 day before, and 1 hour before" → ["1w", "1d", "1h"]
- "reset to defaults" → ["24h", "1h"]
- "no reminders" → []

**Error Handling**:
- Task has no due date → Error: "Task must have a due date to set reminders"
- Interval after due date → Error: "Reminder time cannot be after the due date"
- Invalid interval → Return error message with examples
- More than 5 intervals → Error: "Maximum 5 reminder intervals allowed"

**AI Agent Usage**:
```
User: "Remind me about task 5 three days before and 1 hour before"
Agent: set_reminder(task_id=5, remind_before_natural="3 days before and 1 hour before", user_id="user-123")
Response: "Reminders set: 3 days before (Feb 12 at 5:00 PM) and 1 hour before (Feb 15 at 4:00 PM)"
```

---

## Extended MCP Tools

### 3. add_task (Extended)

**Purpose**: Create a new task with optional due date and reminders.

**New Parameters**:
```python
due_date_natural: Optional[str] = None  # e.g., "tomorrow at 5pm"
remind_before_natural: Optional[str] = None  # e.g., "3 days before and 1 hour before"
```

**Example Usage**:
```python
# Old (still works):
add_task(title="Submit report", user_id="user-123")

# New with due date:
add_task(
    title="Submit report",
    due_date_natural="next Friday at 5pm",
    user_id="user-123"
)

# New with due date and custom reminders:
add_task(
    title="Submit report",
    due_date_natural="Feb 15 at 5pm",
    remind_before_natural="3 days before and 1 hour before",
    user_id="user-123"
)
```

**AI Agent Usage**:
```
User: "Add task 'Submit report' due tomorrow at 5pm"
Agent: add_task(title="Submit report", due_date_natural="tomorrow at 5pm", user_id="user-123")
Response: "Created task 'Submit report' due Tomorrow at 5:00 PM. Reminders will be sent 24 hours and 1 hour before."
```

**Backward Compatibility**: ✅ All existing parameters remain unchanged. New parameters are optional.

---

### 4. update_task (Extended)

**Purpose**: Update an existing task's details including due date.

**New Parameters**:
```python
due_date_natural: Optional[str] = None  # Update due date
clear_due_date: Optional[bool] = False  # Remove due date and reminders
```

**Example Usage**:
```python
# Update due date:
update_task(task_id=5, due_date_natural="next Monday", user_id="user-123")

# Clear due date:
update_task(task_id=5, clear_due_date=True, user_id="user-123")

# Update title and due date:
update_task(task_id=5, title="New title", due_date_natural="tomorrow", user_id="user-123")
```

**AI Agent Usage**:
```
User: "Change task 5 due date to next Monday"
Agent: update_task(task_id=5, due_date_natural="next Monday", user_id="user-123")
Response: "Updated task due date to Monday, February 17 at 9:00 AM"

User: "Remove due date from task 5"
Agent: update_task(task_id=5, clear_due_date=True, user_id="user-123")
Response: "Removed due date and reminders from task"
```

**Behavior**:
- If `due_date_natural` provided → Update due_date, reset reminder_sent
- If `clear_due_date=True` → Set due_date=NULL, remind_before=NULL, reminder_sent=NULL
- If neither provided → No changes to due date/reminders

**Backward Compatibility**: ✅ All existing parameters remain unchanged. New parameters are optional.

---

### 5. complete_task (Extended)

**Purpose**: Mark task as complete and handle reminder cleanup.

**Behavior Changes**:
- **Old**: Mark completed=True, create next occurrence if recurring
- **New**: Mark completed=True, create next occurrence if recurring, **clear reminder_sent field**

**No Parameter Changes**: Function signature unchanged for backward compatibility.

**Implementation**:
```python
# After marking task as complete:
task.completed = True
task.reminder_sent = {}  # Clear sent reminders (fresh start for next occurrence)
db.commit()

# Reminder check query automatically skips completed tasks:
# WHERE completed = FALSE
```

**AI Agent Usage**: No changes to user-facing behavior. Reminders simply stop being sent for completed tasks.

---

### 6. list_tasks (Extended)

**Purpose**: List user's tasks with due date and reminder information.

**Output Schema Changes**:

**Old**:
```json
{
  "tasks": [
    {
      "id": 123,
      "title": "Submit report",
      "completed": false,
      "priority": "high"
    }
  ]
}
```

**New** (backward compatible, adds optional fields):
```json
{
  "tasks": [
    {
      "id": 123,
      "title": "Submit report",
      "completed": false,
      "priority": "high",
      "due_date": "2026-02-15T17:00:00Z",
      "due_date_formatted": "Tomorrow at 5:00 PM",
      "is_overdue": false,
      "overdue_by": null,
      "remind_before": ["24h", "1h"],
      "reminders_sent": ["24h"]
    },
    {
      "id": 124,
      "title": "Old task",
      "completed": false,
      "priority": "medium",
      "due_date": "2026-02-08T10:00:00Z",
      "due_date_formatted": "Feb 8 at 10:00 AM",
      "is_overdue": true,
      "overdue_by": "1 day",
      "remind_before": ["24h", "1h"],
      "reminders_sent": ["24h", "1h"]
    }
  ]
}
```

**New Fields** (all optional, NULL if no due date):
- `due_date`: ISO 8601 timestamp (UTC)
- `due_date_formatted`: Human-readable string in user's timezone
- `is_overdue`: Boolean (true if past due date and not completed)
- `overdue_by`: Human-readable duration (e.g., "2 days", "3 hours")
- `remind_before`: Array of reminder intervals
- `reminders_sent`: Array of reminder types already sent

**Backward Compatibility**: ✅ Existing clients ignore new fields. All existing fields unchanged.

---

## MCP Tool Registration

**AI Agent System Prompt Extensions**:

```python
SYSTEM_PROMPT = """
You are a helpful task management assistant. You can help users manage tasks with due dates and reminders.

Available Commands:
- "Add task [title] due [date]" - Create task with due date
- "Set task [id] due [date]" - Update task due date
- "Remind me about task [id] [interval] before" - Configure reminders
- "Remove due date from task [id]" - Clear due date and reminders
- "Show my overdue tasks" - List tasks past their due date

Examples:
User: "Add task 'Submit report' due tomorrow at 5pm"
You: add_task(title="Submit report", due_date_natural="tomorrow at 5pm")

User: "Remind me about task 5 three days before"
You: set_reminder(task_id=5, remind_before_natural="3 days before")

User: "Which tasks are overdue?"
You: list_tasks(filter="overdue")

Date Parsing:
- Support formats: "tomorrow", "next Friday", "in 3 days", "Feb 15 at 2pm"
- Default time: 9am if not specified
- User timezone: {{user_timezone}} (e.g., America/New_York)

Reminders:
- Default: 24 hours and 1 hour before due date
- Custom: Users can specify any interval (e.g., "3 days before", "30 minutes before")
- Maximum: 5 reminder intervals per task
"""
```

**Tool Definitions** (OpenAI Agents SDK format):

```python
from openai import OpenAI

tools = [
    {
        "type": "function",
        "function": {
            "name": "set_due_date",
            "description": "Set or update a task's due date using natural language",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "Task ID"},
                    "due_date_natural": {"type": "string", "description": "Natural language date (e.g., 'tomorrow at 5pm')"},
                    "user_id": {"type": "string", "description": "User ID"}
                },
                "required": ["task_id", "due_date_natural", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Configure custom reminder intervals for a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "Task ID"},
                    "remind_before_natural": {"type": "string", "description": "Natural language intervals (e.g., '3 days before and 1 hour before')"},
                    "user_id": {"type": "string", "description": "User ID"}
                },
                "required": ["task_id", "remind_before_natural", "user_id"]
            }
        }
    },
    # ... existing tools (add_task, update_task, complete_task, list_tasks) ...
]

client = OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    tools=tools,
    tool_choice="auto"
)
```

---

## Testing Scenarios

### 1. Create task with due date
```python
# User command: "Add task 'Submit report' due tomorrow at 5pm"
result = add_task(
    title="Submit report",
    due_date_natural="tomorrow at 5pm",
    user_id="test-user"
)
assert result["task"]["due_date"] is not None
assert result["task"]["remind_before"] == ["24h", "1h"]  # Default reminders
```

### 2. Set custom reminders
```python
# User command: "Remind me about task 5 three days before and 1 hour before"
result = set_reminder(
    task_id=5,
    remind_before_natural="3 days before and 1 hour before",
    user_id="test-user"
)
assert result["task"]["remind_before"] == ["3d", "1h"]
assert result["task"]["reminder_sent"] == {}  # No reminders sent yet
```

### 3. Update due date (resets reminders)
```python
# User command: "Change task 5 due date to next Monday"
result = update_task(
    task_id=5,
    due_date_natural="next Monday",
    user_id="test-user"
)
assert result["task"]["due_date"] is not None
assert result["task"]["reminder_sent"] == {}  # Reset after due date change
```

### 4. Clear due date
```python
# User command: "Remove due date from task 5"
result = update_task(
    task_id=5,
    clear_due_date=True,
    user_id="test-user"
)
assert result["task"]["due_date"] is None
assert result["task"]["remind_before"] is None
assert result["task"]["reminder_sent"] is None
```

### 5. List tasks with overdue status
```python
# User command: "Show my tasks"
result = list_tasks(user_id="test-user")
overdue_tasks = [t for t in result["tasks"] if t.get("is_overdue")]
assert len(overdue_tasks) >= 0  # May have overdue tasks
for task in overdue_tasks:
    assert task["due_date"] < datetime.now(UTC)
    assert not task["completed"]
```

---

**MCP Tools Contract Status**: ✅ COMPLETE

**Next Steps**:
1. Generate REST API contracts in `contracts/openapi.yaml`
2. Generate Kafka event schemas in `contracts/kafka-events.md`
3. Create integration guide in `quickstart.md`
