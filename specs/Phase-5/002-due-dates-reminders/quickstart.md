# Quickstart Guide: Due Dates & Reminders

**Feature**: 002-due-dates-reminders
**Date**: 2026-02-09
**Target Audience**: Developers integrating the reminder feature

## Overview

This guide provides step-by-step instructions for integrating and testing the Due Dates & Reminders feature. Follow these scenarios to verify the complete reminder flow from due date assignment to notification delivery.

---

## Prerequisites

- Backend API running on `http://localhost:8000`
- Notification microservice running (consumes from Kafka)
- Redpanda Kafka cluster accessible
- Dapr runtime installed with cron binding configured
- PostgreSQL database with migration applied
- Test user created with authentication token

**Environment Variables**:
```bash
# Backend
DATABASE_URL="postgresql://user:pass@localhost:5432/todo_db"
KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
OPENAI_API_KEY="sk-..."

# Notification Service
KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
SENDGRID_API_KEY="SG...."
FIREBASE_CREDENTIALS_PATH="/path/to/firebase-adminsdk.json"
```

---

## Scenario 1: Create Task with Due Date via Chatbot

**Goal**: User creates a task with a natural language due date.

### Step 1: Send Chat Message

```bash
curl -X POST http://localhost:8000/api/user-123/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add task \"Submit quarterly report\" due tomorrow at 5pm"
  }'
```

### Expected Response

```json
{
  "response": "Created task \"Submit quarterly report\" due Tomorrow at 5:00 PM. You'll receive reminders 24 hours and 1 hour before.",
  "conversation_id": "conv-123"
}
```

### Step 2: Verify in Database

```sql
SELECT id, title, due_date, remind_before, reminder_sent
FROM tasks
WHERE user_id = 'user-123'
  AND title = 'Submit quarterly report';
```

**Expected Result**:
```
 id  |          title          |       due_date        | remind_before | reminder_sent
-----+-------------------------+-----------------------+---------------+---------------
 42  | Submit quarterly report | 2026-02-10 17:00:00+00| ["24h", "1h"] | {}
```

### Step 3: Verify Frontend Display

Open browser → Navigate to http://localhost:3000 → Check task list

**Expected**: Task displays with blue due date badge "Tomorrow at 5:00 PM"

---

## Scenario 2: Reminder Check Triggers Notification

**Goal**: Dapr cron triggers reminder check, publishes event to Kafka, notification service delivers email.

### Step 1: Wait for Dapr Cron Trigger

Dapr cron binding runs every 5 minutes. Check logs:

```bash
# Backend logs
tail -f backend/logs/app.log | grep "reminder-check"

# Expected output:
# 2026-02-09 16:55:00 | INFO | Reminder check started
# 2026-02-09 16:55:02 | INFO | Found 3 tasks with pending reminders
# 2026-02-09 16:55:02 | INFO | Published 3 reminder events to Kafka
# 2026-02-09 16:55:03 | INFO | Reminder check completed in 3.2s
```

### Step 2: Verify Kafka Topic

```bash
# List messages in reminders topic
rpk topic consume reminders --num 10

# Expected output (JSON):
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": 42,
  "user_id": "user-123",
  "task_title": "Submit quarterly report",
  "due_date": "2026-02-10T17:00:00Z",
  "reminder_type": "24h",
  "priority": "medium",
  "channels": ["email", "in_app"],
  "user_timezone": "America/New_York",
  "timestamp": "2026-02-09T17:00:00Z"
}
```

### Step 3: Verify Notification Service Consumption

```bash
# Notification service logs
docker logs notification-service -f | grep "Consumed reminder event"

# Expected output:
# 2026-02-09 16:55:05 | INFO | Consumed reminder event: event_id=550e8400...
# 2026-02-09 16:55:05 | INFO | Sending email to user-123@example.com
# 2026-02-09 16:55:06 | INFO | Email sent successfully via SendGrid
# 2026-02-09 16:55:06 | INFO | Logged notification: task_id=42, channel=email, status=success
```

### Step 4: Verify Email Received

Check inbox for user-123@example.com:

**Subject**: Reminder: Task "Submit quarterly report" due tomorrow

**Body**:
```
Hi [Username],

This is a reminder about your task:

Task: Submit quarterly report
Due: Tomorrow at 5:00 PM (America/New_York)
Priority: Medium

Complete this task at: http://localhost:3000/tasks/42

Best regards,
Todo Chatbot Team
```

### Step 5: Verify Database Update

```sql
SELECT reminder_sent FROM tasks WHERE id = 42;
```

**Expected Result**:
```json
{"24h": "2026-02-09T17:00:00Z"}
```

```sql
SELECT * FROM notification_logs
WHERE task_id = 42
  AND reminder_type = '24h';
```

**Expected Result**:
```
 id | task_id | user_id | reminder_type | channel | status  | sent_at             | error_message | event_id
----+---------+---------+---------------+---------+---------+---------------------+---------------+----------
 1  | 42      | user-123| 24h           | email   | success | 2026-02-09 17:00:00 | NULL          | 550e8400...
```

---

## Scenario 3: Customize Reminder Intervals

**Goal**: User configures custom reminder intervals for a specific task.

### Step 1: Set Custom Reminders via Chatbot

```bash
curl -X POST http://localhost:8000/api/user-123/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Remind me about task 42 three days before and 2 hours before"
  }'
```

### Expected Response

```json
{
  "response": "Reminders set: 3 days before (Feb 7 at 5:00 PM) and 2 hours before (Feb 10 at 3:00 PM)"
}
```

### Step 2: Verify Database Update

```sql
SELECT remind_before, reminder_sent FROM tasks WHERE id = 42;
```

**Expected Result**:
```json
remind_before: ["3d", "2h"]
reminder_sent: {}  // Reset after interval change
```

### Step 3: Wait for Custom Reminder Delivery

**3 days before (Feb 7 at 5:00 PM)**:
- Dapr cron triggers reminder check
- Backend publishes event with `reminder_type: "3d"`
- Notification service sends email
- Database updated: `reminder_sent: {"3d": "2026-02-07T17:00:00Z"}`

**2 hours before (Feb 10 at 3:00 PM)**:
- Dapr cron triggers reminder check
- Backend publishes event with `reminder_type: "2h"`
- Notification service sends email
- Database updated: `reminder_sent: {"3d": "...", "2h": "2026-02-10T15:00:00Z"}`

---

## Scenario 4: Complete Task with Pending Reminders

**Goal**: User completes a task, future reminders are skipped.

### Step 1: Mark Task as Complete

```bash
curl -X POST http://localhost:8000/api/user-123/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Complete task 42"
  }'
```

### Expected Response

```json
{
  "response": "Task \"Submit quarterly report\" marked as complete!"
}
```

### Step 2: Verify Database Update

```sql
SELECT completed, reminder_sent FROM tasks WHERE id = 42;
```

**Expected Result**:
```
 completed | reminder_sent
-----------+---------------
 true      | {}
```

**Note**: `reminder_sent` is cleared to allow fresh reminders for recurring task next occurrence.

### Step 3: Verify Reminder Check Skips Completed Task

```bash
# Backend logs (next reminder check)
tail -f backend/logs/app.log | grep "Skipping completed task"

# Expected output:
# 2026-02-10 15:00:00 | DEBUG | Skipping completed task: id=42
```

No reminder events published for task 42 after completion.

---

## Scenario 5: Update Due Date (Resets Reminders)

**Goal**: User changes a task's due date, previously sent reminders are reset.

### Step 1: Update Due Date

```bash
curl -X POST http://localhost:8000/api/user-123/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Change task 42 due date to next Monday"
  }'
```

### Expected Response

```json
{
  "response": "Updated task due date to Monday, February 17 at 9:00 AM"
}
```

### Step 2: Verify Reminder Reset

```sql
SELECT due_date, reminder_sent FROM tasks WHERE id = 42;
```

**Expected Result**:
```
       due_date        | reminder_sent
-----------------------+---------------
 2026-02-17 09:00:00+00| {}
```

**Explanation**: Even if 24h reminder was already sent for old due date (Feb 10), it's cleared when due date changes. New 24h reminder will be sent for Feb 17 due date.

---

## Scenario 6: Notification Delivery Failure with Retry

**Goal**: Email send fails, system retries with exponential backoff.

### Step 1: Simulate SendGrid Failure

```python
# In notification service code (temporary for testing):
# services/notification/src/notification_handlers/email_handler.py

def send_email(to, subject, body):
    # Force failure for testing
    raise SendGridAPIError("Timeout: 503 Service Unavailable")
```

### Step 2: Trigger Reminder Check

Wait for Dapr cron trigger or manually trigger:

```bash
curl -X POST http://localhost:8000/api/internal/dapr/reminder-check \
  -H "dapr-app-id: backend-api"
```

### Step 3: Verify Retry Logic in Logs

```bash
# Notification service logs
docker logs notification-service -f

# Expected output:
# 2026-02-09 17:00:00 | INFO | Consumed reminder event: task_id=42
# 2026-02-09 17:00:01 | ERROR | Email send failed: Timeout (attempt 1/3)
# 2026-02-09 17:00:02 | INFO | Retrying in 1 second...
# 2026-02-09 17:00:03 | ERROR | Email send failed: Timeout (attempt 2/3)
# 2026-02-09 17:00:05 | INFO | Retrying in 2 seconds...
# 2026-02-09 17:00:07 | ERROR | Email send failed: Timeout (attempt 3/3)
# 2026-02-09 17:00:07 | ERROR | All retry attempts exhausted, logging failure
```

### Step 4: Verify Notification Log Entry

```sql
SELECT * FROM notification_logs WHERE task_id = 42 AND status = 'failed';
```

**Expected Result**:
```
 id | task_id | reminder_type | channel | status | error_message              | sent_at
----+---------+---------------+---------+--------+----------------------------+------------
 2  | 42      | 24h           | email   | failed | Timeout: 503 Service Unavailable | 2026-02-09...
```

### Step 5: Dead Letter Queue (Future Enhancement)

```bash
# Messages that fail all retries go to dead letter topic
rpk topic consume reminders.dlq --num 10

# Expected: Original ReminderEvent with failure metadata
```

---

## Scenario 7: Overdue Task Display in Frontend

**Goal**: Frontend displays overdue tasks with red badge.

### Step 1: Create Task with Past Due Date

```bash
curl -X POST http://localhost:8000/api/user-123/tasks \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Old task",
    "due_date": "2026-02-08T10:00:00Z"
  }'
```

### Step 2: Verify Frontend Display

Open browser → Navigate to http://localhost:3000

**Expected**:
- Task displays with red "OVERDUE" badge
- Text shows "Overdue by 1 day"
- Task title may have strikethrough styling (optional)

**React Component** (TaskItem.tsx):
```tsx
{task.is_overdue && (
  <span className="badge badge-danger">
    OVERDUE by {task.overdue_by}
  </span>
)}
```

---

## Scenario 8: Timezone Change Handling

**Goal**: User changes timezone, future reminders adjust accordingly.

### Step 1: Update User Timezone

```bash
curl -X PATCH http://localhost:8000/api/user-123/profile \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "timezone": "Europe/London"
  }'
```

### Step 2: Create Task with Due Date

```bash
curl -X POST http://localhost:8000/api/user-123/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add task \"Meeting\" due tomorrow at 2pm"
  }'
```

**Due Date Stored in DB** (UTC): `2026-02-10 14:00:00+00`

### Step 3: Verify Reminder Calculation

**User Timezone**: Europe/London (UTC+0)
**Due Date**: Tomorrow at 2pm → 2026-02-10 14:00:00 UTC

**24h Reminder**: Send at 2026-02-09 14:00:00 UTC (2pm London time)
**1h Reminder**: Send at 2026-02-10 13:00:00 UTC (1pm London time)

### Step 4: Change Timezone Again

```bash
curl -X PATCH http://localhost:8000/api/user-123/profile \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "timezone": "America/New_York"
  }'
```

**Same Due Date in DB** (unchanged): `2026-02-10 14:00:00+00`

**Frontend Display** (auto-adjusts):
- Old: "Tomorrow at 2:00 PM" (London)
- New: "Tomorrow at 9:00 AM" (New York, UTC-5)

**Reminders Already Sent**: Not affected (timestamps in DB are UTC)

**Future Reminders**: Calculated using new timezone for display in notification body

---

## Testing Checklist

### Backend API

- [ ] POST /api/{user_id}/tasks with due_date_natural
- [ ] POST /api/{user_id}/tasks/{id}/due-date (set_due_date)
- [ ] POST /api/{user_id}/tasks/{id}/reminders (set_reminder)
- [ ] POST /api/internal/dapr/reminder-check (cron endpoint)
- [ ] GET /api/{user_id}/tasks (includes due date and overdue status)
- [ ] PATCH /api/{user_id}/tasks/{id} (complete task, clear reminders)
- [ ] DELETE /api/{user_id}/tasks/{id}/due-date (clear due date)

### MCP Tools

- [ ] set_due_date: Natural language parsing works ("tomorrow", "next Friday")
- [ ] set_reminder: Custom intervals work ("3 days before", "30 minutes before")
- [ ] add_task: Create with due date and reminders in one command
- [ ] update_task: Update due date, resets reminder_sent
- [ ] complete_task: Clears reminder_sent, skips future checks
- [ ] list_tasks: Returns due_date_formatted and is_overdue

### Notification Microservice

- [ ] Consumes reminder events from Kafka
- [ ] Sends email via SendGrid
- [ ] Sends push notifications via Firebase (if configured)
- [ ] Stores in-app notifications in database
- [ ] Logs to notification_logs table
- [ ] Handles idempotency (duplicate event_id ignored)
- [ ] Retries failed deliveries with exponential backoff
- [ ] Sends to dead letter queue after 3 failed attempts

### Database

- [ ] Migration applies successfully (tasks extended, notification_logs created)
- [ ] Indexes created and used by queries (EXPLAIN ANALYZE verification)
- [ ] Unique constraint on notification_logs.event_id prevents duplicates
- [ ] Cascade deletes work (user deleted → tasks deleted → notification_logs deleted)
- [ ] JSONB fields store and query correctly (remind_before, reminder_sent)

### Frontend

- [ ] Task list displays due dates with human-readable format
- [ ] Overdue tasks show red badge
- [ ] Due date badge uses date-fns for formatting
- [ ] Timezone changes reflected immediately
- [ ] In-app notifications displayed (if implemented)

### Integration

- [ ] Full flow: Create task → Reminder check → Kafka event → Email delivery
- [ ] Dapr cron binding triggers on schedule (every 5 minutes)
- [ ] Multiple notification service replicas consume events without duplicates
- [ ] Kafka consumer group rebalancing works correctly
- [ ] Timezone changes don't break reminder calculations
- [ ] Recurring tasks create new occurrences with fresh reminders

---

**Quickstart Guide Status**: ✅ COMPLETE

**Next Steps**: Run `/sp.tasks` to generate detailed task breakdown for implementation.
