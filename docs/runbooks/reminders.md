# Reminders System Runbook

**Phase V - Due Dates & Reminders**
**Task: T212**

This runbook provides troubleshooting guidance for the reminders system in production.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Common Issues](#common-issues)
3. [Monitoring & Metrics](#monitoring--metrics)
4. [Troubleshooting Steps](#troubleshooting-steps)
5. [Emergency Procedures](#emergency-procedures)
6. [Contact Information](#contact-information)

---

## System Overview

### Architecture

```
Backend API (FastAPI)
    ↓
Dapr Cron (every 5 min)
    ↓
Reminder Check Endpoint (/api/internal/dapr/reminder-check)
    ↓
Kafka Producer → "reminders" topic
    ↓
Notification Service (3 replicas)
    ↓
Kafka Consumer (consumer group: notification-service-group)
    ↓
Multi-Channel Handlers (Email, Push, In-App)
    ↓
Dead Letter Queue (reminders.dlq)
```

### Key Components

| Component | Purpose | Health Check |
|-----------|---------|--------------|
| Backend API | Reminder scheduling | `/health` |
| Dapr Cron | Periodic trigger (5 min) | `dapr status -k` |
| Kafka/Redpanda | Event streaming | Check topic lag |
| Notification Service | Event processing | `/health` |
| SendGrid | Email delivery | API status page |
| Firebase | Push notifications | Firebase Console |
| PostgreSQL | State storage | Connection test |

---

## Common Issues

### Issue 1: No Reminders Being Sent

**Symptoms:**
- Users not receiving reminders
- `reminders_sent_total` metric not incrementing
- No events in `reminders` Kafka topic

**Possible Causes:**
1. Dapr cron not triggering
2. No tasks matching reminder criteria
3. Kafka producer failure
4. Database query timeout

**Resolution:**

```bash
# Step 1: Check if Dapr cron is running
kubectl get pods -l app=todo-backend
kubectl logs -l app=todo-backend -c daprd | grep cron

# Step 2: Manually trigger reminder check
kubectl port-forward svc/todo-backend 8000:8000
curl -X POST http://localhost:8000/api/internal/dapr/reminder-check

# Expected response:
# {"reminders_sent": N, "tasks_checked": M, "duration_ms": X}

# Step 3: Check Kafka topic for events
kubectl exec -it redpanda-0 -- rpk topic consume reminders --num 10

# Step 4: Check backend logs
kubectl logs -l app=todo-backend --tail=100 | grep reminder_check
```

**Prevention:**
- Monitor `reminder_checks_total` metric
- Alert if no checks in 10 minutes
- Set up Dapr healthz probes

---

### Issue 2: DLQ Growing Rapidly

**Symptoms:**
- `DLQHighMessageCount` alert firing
- `dlq_size` metric > 100
- Notifications failing consistently

**Possible Causes:**
1. SendGrid API key invalid/expired
2. SendGrid rate limit exceeded
3. Firebase credentials invalid
4. Network connectivity issues
5. Database unavailable

**Resolution:**

```bash
# Step 1: Check DLQ size
kubectl exec -it redpanda-0 -- rpk topic consume reminders.dlq --num 10

# Inspect failed messages
# Look for common error patterns

# Step 2: Check notification service logs
kubectl logs -l app=notification-service --tail=200 | grep -i error

# Common errors:
# - "401 Unauthorized" → Invalid API key
# - "429 Too Many Requests" → Rate limit
# - "Connection timeout" → Network issue

# Step 3: Verify external service credentials
kubectl get secret notification-service-secrets -o jsonpath='{.data.sendgrid-api-key}' | base64 -d
# Test SendGrid API key
curl https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer $SENDGRID_KEY" \
  -H "Content-Type: application/json" \
  -d '{"personalizations":[{"to":[{"email":"test@example.com"}]}],"from":{"email":"noreply@todoapp.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'

# Step 4: Reprocess DLQ messages (if credentials fixed)
# Create DLQ consumer to replay messages
python scripts/dlq_reprocessor.py --topic reminders.dlq --limit 100
```

**Prevention:**
- Rotate SendGrid API keys every 90 days
- Set up SendGrid webhook for bounces
- Monitor `notification_failures_total` metric
- Alert if DLQ > 10 messages

---

### Issue 3: Duplicate Notifications

**Symptoms:**
- Users receiving same reminder multiple times
- `notifications_sent_total` higher than expected
- Multiple entries in `reminder_sent` field

**Possible Causes:**
1. Kafka consumer group not coordinating
2. Multiple notification service replicas processing same message
3. Retry logic not checking `reminder_sent`

**Resolution:**

```bash
# Step 1: Check Kafka consumer group
kubectl exec -it redpanda-0 -- rpk group describe notification-service-group

# Expected: 1 member per partition, no lag

# Step 2: Check notification service replicas
kubectl get pods -l app=notification-service

# Expected: 3 replicas running

# Step 3: Check for duplicate processing in logs
kubectl logs -l app=notification-service --tail=500 | grep "event_id=<specific-event-id>"

# Should see event processed only once

# Step 4: Verify reminder_sent updates
# Query database for specific task
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT id, title, remind_before, reminder_sent FROM tasks WHERE id = <task-id>;"
```

**Prevention:**
- Use Kafka consumer groups correctly
- Ensure `reminder_sent` updates are atomic
- Add idempotency keys to notifications
- Monitor duplicate detection metrics

---

### Issue 4: High Notification Latency

**Symptoms:**
- `HighNotificationLatency` alert firing
- P95 latency > 5 seconds
- Users receiving reminders late

**Possible Causes:**
1. Kafka consumer lag
2. SendGrid API slow
3. Database connection pool exhausted
4. Too few notification service replicas

**Resolution:**

```bash
# Step 1: Check Kafka consumer lag
kubectl exec -it redpanda-0 -- rpk group describe notification-service-group

# If lag > 1000: Scale up replicas

# Step 2: Check notification service metrics
kubectl port-forward svc/notification-service 8001:8001
curl http://localhost:8001/metrics | grep notification_delivery_latency

# Step 3: Scale up notification service
kubectl scale deployment notification-service --replicas=5

# Step 4: Check external service status
# SendGrid: https://status.sendgrid.com/
# Firebase: https://status.firebase.google.com/
```

**Prevention:**
- Set HPA for notification service
- Monitor P95 latency
- Alert if latency > 2 seconds
- Use connection pooling

---

### Issue 5: Reminders Sent to Wrong Timezone

**Symptoms:**
- Users receiving reminders at wrong time
- Reminders sent at 9am UTC instead of 9am local

**Possible Causes:**
1. User timezone not set correctly
2. Date parser not using user timezone
3. UTC conversion error

**Resolution:**

```bash
# Step 1: Check user timezone in database
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT id, email, timezone FROM users WHERE email = '<user-email>';"

# Step 2: Verify due_date is stored in UTC
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT id, title, due_date, timezone('UTC', due_date) FROM tasks WHERE id = <task-id>;"

# Step 3: Check reminder calculation logic
# Backend code: src/routes/reminders.py
# Verify user.timezone is used

# Step 4: Update user timezone if incorrect
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "UPDATE users SET timezone = 'America/New_York' WHERE email = '<user-email>';"
```

**Prevention:**
- Validate timezone on user signup
- Store all dates in UTC
- Convert to user timezone only for display
- Add timezone tests

---

## Monitoring & Metrics

### Key Metrics

**Backend Metrics:**
```
# Reminder checks
reminder_checks_total{status="success"}
reminder_checks_total{status="error"}
reminder_check_duration_seconds

# Reminders sent
reminders_sent_total{reminder_type="24h"}
reminders_sent_total{reminder_type="1h"}

# Errors
reminder_errors_total{error_type="database_error"}
reminder_errors_total{error_type="kafka_error"}
```

**Notification Service Metrics:**
```
# Notifications sent
notifications_sent_total{channel="email", status="success"}
notifications_sent_total{channel="push", status="success"}
notifications_sent_total{channel="in_app", status="success"}

# Latency
notification_delivery_latency_seconds{channel="email"}

# Failures
notification_failures_total{channel="email", error_type="timeout"}

# DLQ
dlq_messages_total{reason="max_retries"}
dlq_size
```

**Kafka Metrics:**
```
# Consumer lag
kafka_consumer_lag

# Messages consumed
kafka_messages_consumed_total{topic="reminders"}
```

### Grafana Dashboards

**Reminders Overview Dashboard:**
- Reminders sent per hour
- Reminder check duration
- Success rate
- Error rate by type

**Notification Service Dashboard:**
- Notifications by channel
- P50/P95/P99 latency
- Failure rate
- DLQ size over time

**Kafka Dashboard:**
- Consumer lag
- Message throughput
- Partition distribution

### Alerts

**Critical Alerts (PagerDuty):**
- `DLQRapidGrowth` - DLQ growing > 10 msg/sec
- `KafkaConsumerLag` - Lag > 1000 messages
- `NotificationServiceDown` - 0 healthy replicas

**Warning Alerts (Slack):**
- `DLQHighMessageCount` - DLQ > 100 messages
- `HighNotificationFailureRate` - Failure rate > 5/sec
- `SlowReminderChecks` - Duration > 30s
- `HighNotificationLatency` - P95 > 5s

---

## Troubleshooting Steps

### Step-by-Step Diagnosis

**1. Is the system processing reminders?**
```bash
# Check reminder checks in last hour
curl http://backend-api:8000/metrics | grep reminder_checks_total
```

**2. Are events reaching Kafka?**
```bash
# Check Kafka topic
kubectl exec -it redpanda-0 -- rpk topic list
kubectl exec -it redpanda-0 -- rpk topic consume reminders --num 10
```

**3. Are notification services consuming?**
```bash
# Check consumer group
kubectl exec -it redpanda-0 -- rpk group list
kubectl exec -it redpanda-0 -- rpk group describe notification-service-group
```

**4. Are notifications being delivered?**
```bash
# Check notification metrics
curl http://notification-service:8001/metrics | grep notifications_sent_total
```

**5. Are there errors?**
```bash
# Check logs
kubectl logs -l app=notification-service --tail=100 | grep -i error
```

---

## Emergency Procedures

### Emergency 1: All Reminders Stopped

**Action:**
1. Check if backend is running
2. Manually trigger reminder check
3. Verify Dapr cron is working
4. Check database connectivity
5. Restart backend pods if needed

```bash
kubectl get pods -l app=todo-backend
kubectl logs -l app=todo-backend --tail=50
kubectl rollout restart deployment todo-backend
```

### Emergency 2: DLQ Overflow (> 1000 messages)

**Action:**
1. Stop notification service to prevent more DLQ entries
2. Investigate root cause (check logs)
3. Fix issue (update credentials, fix code, etc.)
4. Drain DLQ with reprocessing script
5. Resume notification service

```bash
kubectl scale deployment notification-service --replicas=0
# Fix issue
kubectl scale deployment notification-service --replicas=3
```

### Emergency 3: Database Connection Exhaustion

**Action:**
1. Check connection pool metrics
2. Scale up database connections
3. Check for slow queries
4. Restart backend pods to reset connections

```bash
# Check connections
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"
```

---

## Contact Information

### On-Call Rotation
- **Primary:** Backend Team (PagerDuty)
- **Secondary:** DevOps Team (PagerDuty)

### Escalation Path
1. On-call engineer (PagerDuty)
2. Team lead (Slack #oncall)
3. Engineering manager (Phone)

### Useful Links
- Grafana Dashboards: https://grafana.todoapp.com/dashboards/reminders
- Prometheus: https://prometheus.todoapp.com/
- Kafka UI: https://kafka-ui.todoapp.com/
- Logs (DataDog): https://app.datadoghq.com/logs
- SendGrid Status: https://status.sendgrid.com/
- Firebase Status: https://status.firebase.google.com/

### Slack Channels
- `#alerts-reminders` - Automated alerts
- `#oncall` - On-call coordination
- `#backend-team` - Backend team
- `#devops` - Infrastructure team

---

**Last Updated:** 2026-02-14
**Maintained By:** Backend Team
**Review Frequency:** Quarterly
