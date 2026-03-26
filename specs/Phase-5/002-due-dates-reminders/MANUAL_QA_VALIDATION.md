# Manual QA Validation Guide - T214

**Feature:** Due Dates & Reminders
**Phase:** Phase 12 - Testing & Documentation
**Task:** T214
**Date:** 2026-02-14
**Status:** Ready for validation

---

## Prerequisites Checklist

Before starting manual QA, ensure all services are running:

### 1. Backend API
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload

# Verify: http://localhost:8000/health should return {"status": "healthy"}
```

### 2. PostgreSQL Database
```bash
# Verify connection
psql $DATABASE_URL -c "SELECT version();"

# Verify migration applied
psql $DATABASE_URL -c "\d tasks" | grep -E "due_date|remind_before|reminder_sent"
```

### 3. Kafka/Redpanda (Optional for full flow)
```bash
# If using Redpanda locally:
rpk cluster info

# If using Kafka:
kafka-topics --list --bootstrap-server localhost:9092
```

### 4. Notification Service (Optional for full flow)
```bash
cd services/notification
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py

# Verify logs show: "Notification service started"
```

### 5. Frontend (Optional for UI validation)
```bash
cd frontend
npm install
npm run dev

# Verify: http://localhost:3000
```

### 6. Authentication Token
```bash
# Create test user and get JWT token
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "qa-test@example.com",
    "password": "TestPassword123!",
    "name": "QA Test User"
  }'

# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "qa-test@example.com",
    "password": "TestPassword123!"
  }'

# Save token for subsequent requests
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
export USER_ID="user-123"  # From registration response
```

---

## Scenario 1: Create Task with Due Date via Chatbot

**✅ Goal:** User creates a task with natural language due date.

### Test Steps:

1. **Send chat message:**
   ```bash
   curl -X POST http://localhost:8000/api/${USER_ID}/chat \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Add task \"Submit quarterly report\" due tomorrow at 5pm"
     }'
   ```

2. **Verify response:**
   - ✅ Response contains: "Created task \"Submit quarterly report\""
   - ✅ Response mentions due date: "Tomorrow at 5:00 PM"
   - ✅ Response mentions reminders: "24 hours and 1 hour before"

3. **Verify database:**
   ```sql
   SELECT id, title, due_date, remind_before, reminder_sent
   FROM tasks
   WHERE user_id = '${USER_ID}'
     AND title = 'Submit quarterly report';
   ```

   Expected:
   - ✅ due_date is set (tomorrow 5pm in UTC)
   - ✅ remind_before = ["24h", "1h"]
   - ✅ reminder_sent = {}

4. **Verify frontend (if running):**
   - ✅ Open http://localhost:3000
   - ✅ Task displays with blue due date badge "Tomorrow at 5:00 PM"

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Scenario 2: Reminder Check Triggers Notification

**✅ Goal:** Dapr cron triggers reminder check, publishes to Kafka, notification delivered.

### Test Steps:

1. **Manually trigger reminder check (if Dapr not running):**
   ```bash
   curl -X POST http://localhost:8000/api/internal/dapr/reminder-check \
     -H "dapr-app-id: backend-api" \
     -H "Content-Type: application/json"
   ```

2. **Verify backend logs:**
   ```bash
   tail -f backend/logs/app.log | grep "reminder-check"
   ```

   Expected output:
   - ✅ "Reminder check started"
   - ✅ "Found X tasks with pending reminders"
   - ✅ "Published X reminder events to Kafka"
   - ✅ "Reminder check completed"

3. **Verify Kafka topic (if Redpanda running):**
   ```bash
   rpk topic consume reminders --num 10
   ```

   Expected:
   - ✅ JSON event with task_id, user_id, task_title
   - ✅ reminder_type = "24h"
   - ✅ channels array includes "email" and/or "in_app"
   - ✅ event_id is UUID format

4. **Verify notification service (if running):**
   ```bash
   docker logs notification-service -f | grep "Consumed reminder event"
   ```

   Expected:
   - ✅ "Consumed reminder event: event_id=..."
   - ✅ "Sending email to ..."
   - ✅ "Email sent successfully" OR "In-app notification stored"

5. **Verify database update:**
   ```sql
   SELECT reminder_sent FROM tasks WHERE id = [task_id];
   ```

   Expected:
   - ✅ reminder_sent contains: {"24h": "2026-02-14T..."}

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Scenario 3: Customize Reminder Intervals

**✅ Goal:** User configures custom reminder intervals (3 days, 2 hours).

### Test Steps:

1. **Set custom reminders via chatbot:**
   ```bash
   curl -X POST http://localhost:8000/api/${USER_ID}/chat \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Remind me about task [task_id] three days before and 2 hours before"
     }'
   ```

2. **Verify response:**
   - ✅ Response confirms: "Reminders set: 3 days before ... and 2 hours before ..."

3. **Verify database:**
   ```sql
   SELECT remind_before, reminder_sent FROM tasks WHERE id = [task_id];
   ```

   Expected:
   - ✅ remind_before = ["3d", "2h"]
   - ✅ reminder_sent = {} (reset after interval change)

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Scenario 4: Complete Task with Pending Reminders

**✅ Goal:** Completed tasks skip future reminders.

### Test Steps:

1. **Mark task as complete:**
   ```bash
   curl -X POST http://localhost:8000/api/${USER_ID}/chat \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Complete task [task_id]"
     }'
   ```

2. **Verify response:**
   - ✅ Response confirms: "Task ... marked as complete!"

3. **Verify database:**
   ```sql
   SELECT completed, reminder_sent FROM tasks WHERE id = [task_id];
   ```

   Expected:
   - ✅ completed = true
   - ✅ reminder_sent = {} (cleared for recurring tasks)

4. **Verify reminder check skips task:**
   - ✅ Trigger reminder check again
   - ✅ Logs show: "Skipping completed task: id=[task_id]"
   - ✅ No new reminder events published

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Scenario 5: Update Due Date (Resets Reminders)

**✅ Goal:** Changing due date resets previously sent reminders.

### Test Steps:

1. **Update due date:**
   ```bash
   curl -X POST http://localhost:8000/api/${USER_ID}/chat \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Change task [task_id] due date to next Monday"
     }'
   ```

2. **Verify response:**
   - ✅ Response confirms new due date: "Monday, February 17 at 9:00 AM"

3. **Verify database:**
   ```sql
   SELECT due_date, reminder_sent FROM tasks WHERE id = [task_id];
   ```

   Expected:
   - ✅ due_date is updated to next Monday
   - ✅ reminder_sent = {} (reset for new due date)

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Scenario 6: Notification Delivery Failure with Retry

**✅ Goal:** Failed notifications retry with exponential backoff.

### Test Steps:

**Note:** This requires temporarily breaking SendGrid/notification delivery or using mock failure.

1. **Simulate failure (optional - skip if no access to notification service):**
   - Comment out SendGrid API key in .env
   - OR modify email_handler.py to raise exception

2. **Trigger reminder check:**
   ```bash
   curl -X POST http://localhost:8000/api/internal/dapr/reminder-check \
     -H "dapr-app-id: backend-api"
   ```

3. **Verify retry logs (if notification service running):**
   ```bash
   docker logs notification-service -f
   ```

   Expected:
   - ✅ "Email send failed: ... (attempt 1/3)"
   - ✅ "Retrying in 1 second..."
   - ✅ "Email send failed: ... (attempt 2/3)"
   - ✅ "Retrying in 2 seconds..."
   - ✅ "Email send failed: ... (attempt 3/3)"
   - ✅ "All retry attempts exhausted"

4. **Verify notification_logs:**
   ```sql
   SELECT * FROM notification_logs WHERE status = 'failed';
   ```

   Expected:
   - ✅ Record exists with status = 'failed'
   - ✅ error_message contains failure reason

**Status:** [ ] PASS / [ ] FAIL / [ ] SKIPPED (no notification service)
**Notes:** _______________________________________________

---

## Scenario 7: Overdue Task Display in Frontend

**✅ Goal:** Frontend displays overdue tasks with red badge.

### Test Steps:

1. **Create task with past due date:**
   ```bash
   curl -X POST http://localhost:8000/api/${USER_ID}/tasks \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Old task",
       "description": "This is overdue",
       "due_date": "2026-02-08T10:00:00Z"
     }'
   ```

2. **Verify frontend (if running):**
   - ✅ Open http://localhost:3000
   - ✅ Task displays with red "OVERDUE" badge
   - ✅ Text shows "Overdue by X days"

   **If frontend not running, verify API response:**
   ```bash
   curl -X GET http://localhost:8000/api/${USER_ID}/tasks \
     -H "Authorization: Bearer ${TOKEN}"
   ```

   Expected JSON:
   - ✅ Task has `is_overdue: true`
   - ✅ Task has `overdue_by: "1 day"` or similar

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Scenario 8: Timezone Change Handling

**✅ Goal:** User timezone changes affect future reminder calculations.

### Test Steps:

1. **Check current user timezone:**
   ```bash
   curl -X GET http://localhost:8000/api/${USER_ID}/profile \
     -H "Authorization: Bearer ${TOKEN}"
   ```

2. **Update timezone:**
   ```bash
   curl -X PATCH http://localhost:8000/api/${USER_ID}/profile \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "timezone": "Europe/London"
     }'
   ```

3. **Create task with due date:**
   ```bash
   curl -X POST http://localhost:8000/api/${USER_ID}/chat \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Add task \"Meeting\" due tomorrow at 2pm"
     }'
   ```

4. **Verify due date stored in UTC:**
   ```sql
   SELECT due_date, user_id FROM tasks WHERE title = 'Meeting';
   ```

   Expected:
   - ✅ due_date is in UTC: "2026-02-15 14:00:00+00"

5. **Change timezone again:**
   ```bash
   curl -X PATCH http://localhost:8000/api/${USER_ID}/profile \
     -H "Authorization: Bearer ${TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{
       "timezone": "America/New_York"
     }'
   ```

6. **Verify frontend display adjusts (if running):**
   - ✅ Same due date in DB (UTC unchanged)
   - ✅ Frontend display shows adjusted time (9:00 AM New York vs 2:00 PM London)

   **If frontend not running, verify API response:**
   ```bash
   curl -X GET http://localhost:8000/api/${USER_ID}/tasks \
     -H "Authorization: Bearer ${TOKEN}"
   ```

   Expected:
   - ✅ Task due_date_formatted reflects new timezone

**Status:** [ ] PASS / [ ] FAIL
**Notes:** _______________________________________________

---

## Summary: Manual QA Results

### Scenario Results:
- [ ] Scenario 1: Create Task with Due Date - PASS / FAIL
- [ ] Scenario 2: Reminder Check Triggers Notification - PASS / FAIL / SKIPPED
- [ ] Scenario 3: Customize Reminder Intervals - PASS / FAIL
- [ ] Scenario 4: Complete Task with Pending Reminders - PASS / FAIL
- [ ] Scenario 5: Update Due Date (Resets Reminders) - PASS / FAIL
- [ ] Scenario 6: Notification Delivery Failure - PASS / FAIL / SKIPPED
- [ ] Scenario 7: Overdue Task Display - PASS / FAIL
- [ ] Scenario 8: Timezone Change Handling - PASS / FAIL

### Overall Status:
- **Total Scenarios:** 8
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___ (notification service scenarios if not running)

### Issues Found:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Recommendations:
- _______________________________________________
- _______________________________________________

---

## T214 Completion Criteria

**✅ T214 is COMPLETE when:**
1. All 8 scenarios have been tested
2. Results documented above
3. Critical failures (if any) have been triaged
4. Task marked as [X] in tasks.md

**Note:** Scenarios 2 and 6 can be SKIPPED if Kafka/notification service not running. Focus on backend API and database validation scenarios (1, 3, 4, 5, 7, 8) which require only the backend API.

---

**Prepared by:** Claude Code
**Date:** 2026-02-14
**Status:** Ready for validation
**Next Task:** T214 completion or bug fixing based on QA results
