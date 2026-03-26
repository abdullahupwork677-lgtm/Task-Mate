# Feature Specification: Due Dates & Reminders

**Feature Branch**: `002-due-dates-reminders`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Feature: Due Dates & Reminders - Notifications before 24 hours and 1 hour of task due date. Kafka event-driven architecture with separate notification microservice."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Due Date Assignment (Priority: P1)

As a user, I want to set a due date and time for my tasks so that I know when they need to be completed.

**Why this priority**: Core capability required for all reminder functionality. Without due dates, reminders cannot function. This is the foundation for the entire feature.

**Independent Test**: Can be fully tested by creating a task with a due date via the AI chatbot or API, verifying the due date is stored correctly, and listing tasks to see the due date displayed. Delivers immediate value by allowing users to track deadlines.

**Acceptance Scenarios**:

1. **Given** a user wants to create a task with a deadline, **When** they say "Add task 'Submit report' due tomorrow at 5pm", **Then** the system creates a task with due_date set to tomorrow at 17:00 in the user's timezone
2. **Given** a task exists without a due date, **When** the user says "Set task 5 due date to next Friday at 2pm", **Then** the system updates the task with the specified due date
3. **Given** a user lists their tasks, **When** tasks have due dates, **Then** the system displays each task's due date in a human-readable format (e.g., "Tomorrow at 5:00 PM", "Feb 15 at 2:00 PM")
4. **Given** a task has passed its due date, **When** the user views the task, **Then** the system visually indicates the task is overdue (e.g., red badge or "Overdue by 2 days")

---

### User Story 2 - 24-Hour Advance Reminder (Priority: P2)

As a user, I want to receive a reminder 24 hours before my task is due so that I have sufficient time to complete it.

**Why this priority**: Provides users with advance notice to plan their work. This is the primary reminder interval that most users find helpful for work tasks.

**Independent Test**: Can be fully tested by creating a task due in 25 hours, waiting for the reminder check cycle to run, and verifying the reminder notification is sent via the configured channels. Delivers value by reducing missed deadlines.

**Acceptance Scenarios**:

1. **Given** a task is due in exactly 24 hours, **When** the reminder check runs, **Then** the system sends a notification to the user via all enabled channels (email, push, in-app)
2. **Given** a task was sent a 24-hour reminder, **When** the reminder is delivered, **Then** the system marks `reminder_sent` with the timestamp to prevent duplicate reminders
3. **Given** a user completes a task before the 24-hour reminder, **When** the reminder check runs, **Then** the system skips sending the reminder for that completed task
4. **Given** a reminder is sent, **When** the user receives it, **Then** the notification includes the task title, due date/time, and priority level

---

### User Story 3 - 1-Hour Urgent Reminder (Priority: P2)

As a user, I want to receive a final reminder 1 hour before my task is due so that I don't forget at the last minute.

**Why this priority**: Provides urgent notification for tasks about to become overdue. Complements the 24-hour reminder for time-sensitive tasks.

**Independent Test**: Can be fully tested by creating a task due in 2 hours, waiting for the 1-hour reminder check, and verifying the urgent reminder is sent. Delivers value by catching tasks that might slip through.

**Acceptance Scenarios**:

1. **Given** a task is due in exactly 1 hour, **When** the reminder check runs, **Then** the system sends an urgent notification to the user
2. **Given** a task received both 24-hour and 1-hour reminders, **When** viewing reminder history, **Then** the system shows both reminder events with timestamps
3. **Given** a recurring task has a due date, **When** the 1-hour reminder is sent, **Then** the reminder specifies it's for the current occurrence only
4. **Given** a high-priority task is due in 1 hour, **When** the reminder is sent, **Then** the notification is marked as urgent/high-priority

---

### User Story 4 - Custom Reminder Intervals (Priority: P3)

As a user, I want to customize reminder intervals for specific tasks so that I receive reminders at times that work best for me.

**Why this priority**: Power-user feature that allows personalization. While valuable, the default 24h and 1h intervals satisfy most users' needs.

**Independent Test**: Can be fully tested by creating a task with custom reminder intervals (e.g., "3 days before", "30 minutes before"), verifying the custom intervals are stored, and checking that reminders are sent at the correct times.

**Acceptance Scenarios**:

1. **Given** a user creates a task, **When** they specify "Remind me 3 days before and 2 hours before", **Then** the system stores both custom reminder intervals for that task
2. **Given** a task has custom reminder intervals, **When** the reminder check runs, **Then** the system sends reminders according to the custom schedule instead of the default 24h/1h
3. **Given** a user wants to change reminder settings, **When** they say "Change task 10 reminder to 48 hours before", **Then** the system updates the reminder interval and cancels any previously scheduled reminders
4. **Given** a task has multiple custom reminders, **When** each reminder time arrives, **Then** the system sends separate notifications for each interval

---

### User Story 5 - Multi-Channel Notifications (Priority: P3)

As a user, I want to receive reminders via email, push notifications, and in-app alerts so that I don't miss important deadlines regardless of where I am.

**Why this priority**: Improves notification reliability and user reach. However, the core reminder functionality works with a single channel, making this an enhancement.

**Independent Test**: Can be fully tested by configuring multiple notification channels, triggering a reminder, and verifying the notification is delivered via all enabled channels simultaneously.

**Acceptance Scenarios**:

1. **Given** a user has enabled email and push notifications, **When** a reminder is triggered, **Then** the system sends the notification via both channels simultaneously
2. **Given** a user is logged into the web app, **When** a reminder is triggered, **Then** the system displays an in-app notification badge with the reminder count
3. **Given** a notification channel fails (e.g., email service down), **When** a reminder is sent, **Then** the system still delivers via other available channels and logs the failure
4. **Given** a user wants to customize channels, **When** they configure notification preferences, **Then** the system respects their choices for each reminder type

---

### Edge Cases

- **What happens when a task due date is in the past?** System marks task as overdue, does not send reminders, but allows user to still complete the task
- **What happens when a reminder time falls exactly at midnight or system downtime?** Reminder check runs on next scheduled interval (e.g., 5-minute cron), sends reminder within acceptable delay window (< 15 minutes)
- **What happens when a user changes a task's due date after a reminder was already sent?** System recalculates reminder schedule based on new due date, may send additional reminders if new date warrants them
- **What happens when a user's timezone changes (travel)?** System uses user's current timezone setting for all reminder calculations, future reminders adjust to new timezone
- **What happens when system clock skew occurs?** Reminder checks use database server time as source of truth, comparison logic tolerates small time differences (< 1 minute)
- **What happens when multiple tasks have reminders at the same time?** System batches notifications into a single digest message listing all tasks with reminders
- **What happens when a recurring task is completed and next occurrence is created?** Reminder schedule resets for new occurrence based on new due date, no reminders sent for completed occurrence
- **What happens when notification delivery fails?** System logs failure, retries with exponential backoff (3 attempts), marks reminder as failed if all retries exhausted
- **What happens when a user has hundreds of overdue tasks?** System limits reminder notifications to prevent spam, sends summary digest instead of individual reminders
- **What happens when reminder check service crashes mid-processing?** Kafka consumer group rebalancing ensures another instance picks up processing, idempotent message handling prevents duplicate reminders

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store due_date as a timestamp with timezone information for each task
- **FR-002**: System MUST allow users to set, update, and clear due dates via natural language commands (e.g., "due tomorrow at 5pm", "due next Friday", "remove due date")
- **FR-003**: System MUST parse natural language dates and times using dateparser library with timezone awareness
- **FR-004**: System MUST send reminder notifications 24 hours before a task's due date by default
- **FR-005**: System MUST send reminder notifications 1 hour before a task's due date by default
- **FR-006**: System MUST allow users to customize reminder intervals (e.g., "3 days before", "30 minutes before", "1 week before")
- **FR-007**: System MUST store reminder configuration in `remind_before` field as an array of intervals (e.g., ["24h", "1h"])
- **FR-008**: System MUST track sent reminders using `reminder_sent` field to prevent duplicate notifications
- **FR-009**: System MUST NOT send reminders for tasks that are already completed
- **FR-010**: System MUST NOT send reminders for tasks that have been deleted
- **FR-011**: System MUST support multiple notification channels: email, push notifications, and in-app alerts
- **FR-012**: System MUST publish reminder events to a Kafka topic named "reminders" with task details and notification channel information
- **FR-013**: A separate notification microservice MUST consume reminder events from the "reminders" Kafka topic
- **FR-014**: The notification microservice MUST handle delivery to email, push, and in-app notification channels
- **FR-015**: System MUST use Dapr cron binding to run periodic reminder checks every 5 minutes
- **FR-016**: System MUST calculate reminder times based on the user's configured timezone
- **FR-017**: System MUST display due dates in human-readable format (e.g., "Tomorrow at 5:00 PM", "Today at 3:00 PM", "Overdue by 2 days")
- **FR-018**: System MUST visually indicate overdue tasks in the frontend (e.g., red badge, strikethrough)
- **FR-019**: System MUST support updating due dates on existing tasks without affecting other task properties
- **FR-020**: System MUST prevent race conditions when multiple reminder check instances run simultaneously (idempotent processing)

### Key Entities

- **Task (Extended)**: Represents a todo item with new fields:
  - `due_date`: DateTime with timezone (nullable) - when the task must be completed
  - `remind_before`: JSON array of intervals (nullable) - custom reminder schedule (e.g., ["24h", "1h", "3d"])
  - `reminder_sent`: JSON object (nullable) - tracks which reminders have been sent with timestamps (e.g., {"24h": "2026-02-09T10:00:00Z", "1h": "2026-02-10T09:00:00Z"})
  - Relationships: Links to User (owner) and potentially parent Task (for recurring tasks)

- **ReminderEvent (Kafka Message)**: Event published when a reminder needs to be sent:
  - `event_id`: UUID - unique identifier for idempotency
  - `task_id`: Integer - task being reminded about
  - `user_id`: String - task owner
  - `task_title`: String - human-readable task description
  - `due_date`: DateTime - when task is due
  - `reminder_type`: String - which interval triggered this reminder (e.g., "24h", "1h", "custom_3d")
  - `priority`: String - task priority for notification urgency
  - `channels`: Array - which channels to notify (e.g., ["email", "push", "in_app"])
  - `timestamp`: DateTime - when event was created

- **User (Extended)**: User preferences related to reminders:
  - `timezone`: String - user's timezone (e.g., "America/New_York", "Europe/London")
  - `notification_preferences`: JSON object - which channels are enabled (e.g., {"email": true, "push": true, "in_app": true})
  - Default reminder intervals if custom ones not specified per task

- **NotificationLog (New)**: Audit trail for sent notifications:
  - `id`: Integer - primary key
  - `task_id`: Integer - task that triggered notification
  - `user_id`: String - recipient
  - `reminder_type`: String - which interval (e.g., "24h")
  - `channel`: String - delivery method (e.g., "email")
  - `status`: String - success/failed/pending
  - `sent_at`: DateTime - when notification was sent
  - `error_message`: String (nullable) - if delivery failed

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can set due dates on tasks in under 10 seconds using natural language commands
- **SC-002**: System accurately parses 95% of common date/time expressions (e.g., "tomorrow", "next Friday at 3pm", "in 2 days")
- **SC-003**: Reminder notifications are delivered within 5 minutes of the scheduled reminder time (e.g., 24-hour reminder delivered between 23h 55m and 24h 5m before due date)
- **SC-004**: Zero duplicate reminders are sent for the same task and reminder interval
- **SC-005**: System successfully delivers reminders to 99% of users with active notification channels
- **SC-006**: Users can customize reminder intervals in under 15 seconds via natural language
- **SC-007**: Notification microservice processes reminder events with p95 latency under 500ms from Kafka consumption to delivery
- **SC-008**: Reminder check service handles 10,000 tasks with due dates without performance degradation (check completes in under 30 seconds)
- **SC-009**: System supports 1000 concurrent users with reminder-enabled tasks without dropped notifications
- **SC-010**: Overdue tasks are visually distinguishable in the frontend within 1 second of page load
- **SC-011**: Users report 30% reduction in missed deadlines after using the reminder feature (measured via user survey)
- **SC-012**: System handles timezone changes without missing reminders or sending duplicates
- **SC-013**: Kafka topic retention and partitioning support 100,000 reminder events per day without message loss

## Assumptions

1. **User Timezone Configuration**: Users have their timezone configured in their profile. If not set, system defaults to UTC and prompts user to configure timezone on first reminder-enabled task.

2. **Notification Channel Availability**: At least one notification channel (email, push, or in-app) is available for each user. System validates this before allowing reminder configuration.

3. **Kafka Infrastructure**: Redpanda Kafka cluster is already running and accessible from both the backend API and notification microservice. Topic creation is automated.

4. **Dapr Setup**: Dapr runtime is installed and configured with cron binding support. Cron configuration can be deployed alongside the application.

5. **Reminder Granularity**: 5-minute check intervals are acceptable for reminder delivery (users won't expect second-precision for reminders).

6. **Default Reminder Intervals**: If users don't specify custom intervals, system defaults to 24h and 1h before due date. This satisfies 80% of use cases.

7. **Email Service Provider**: Email delivery is handled via a third-party service (e.g., SendGrid, AWS SES) with appropriate API keys configured in environment variables.

8. **Push Notification Infrastructure**: Push notifications use a service like Firebase Cloud Messaging (FCM) or Apple Push Notification service (APNs) with proper credentials configured.

9. **Database Schema Migration**: Alembic migration will add the three new fields (due_date, remind_before, reminder_sent) to the existing tasks table without data loss.

10. **Idempotency Strategy**: Reminder events include unique event_id, and notification microservice uses this for idempotent processing to prevent duplicate sends.

11. **Recurring Task Integration**: For recurring tasks, each occurrence has its own due date and reminder schedule. Reminders for completed occurrences are not sent.

12. **Task Completion Cleanup**: When a task is completed, the system immediately flags it to skip future reminder checks (soft delete from reminder processing).

## Dependencies

1. **Phase 5 Part A (Recurring Tasks)**: Due date field and recurring task infrastructure already implemented (COMPLETE)
2. **Kafka/Redpanda Cluster**: Must be deployed and accessible before implementing event publishing
3. **Dapr Runtime**: Must be installed with cron binding configured before scheduler can run
4. **Notification Service Providers**: Email and push notification services must be configured with API keys
5. **Timezone Database**: System must have up-to-date timezone database for accurate calculations
6. **Natural Language Date Parser**: `dateparser` Python library with timezone support
7. **Kafka Python Client**: `aiokafka` for asynchronous event publishing
8. **Dapr Python SDK**: For cron binding integration and pub/sub

## Out of Scope

1. **Snooze/Postpone Functionality**: Users cannot snooze reminders or postpone due dates via the notification itself (must use main app)
2. **Smart Reminder Timing**: System does not analyze user work patterns to suggest optimal reminder times
3. **Reminder Escalation**: No automatic escalation (e.g., if user doesn't respond to 24h reminder, don't send additional reminders before the 1h mark)
4. **SMS Notifications**: Text message notifications are not supported in this phase
5. **Slack/Teams Integration**: Third-party chat platform notifications are not included
6. **Reminder History UI**: Users cannot view a log of past reminders in the frontend (only in database)
7. **Bulk Reminder Configuration**: Cannot set default reminder intervals for all tasks at once (per-task configuration only)
8. **Calendar Integration**: No export to Google Calendar, Outlook, or iCal
9. **Notification Grouping/Digesting**: Multiple reminders at the same time are sent individually, not grouped into a digest
10. **Reminder Analytics**: No dashboard showing reminder delivery rates, open rates, or user engagement metrics

## Non-Functional Requirements

### Performance

- **NFR-001**: Reminder check service must complete full scan of due tasks in under 30 seconds for up to 10,000 tasks
- **NFR-002**: Notification microservice must process reminder events with p95 latency under 500ms
- **NFR-003**: Due date queries must use database indexes to maintain query time under 50ms
- **NFR-004**: Kafka topic must support 100,000 events per day with message loss under 1%

### Scalability

- **NFR-005**: System must support horizontal scaling of notification microservice instances (3 or more replicas)
- **NFR-006**: Reminder check service must support running multiple instances with leader election to prevent duplicate checks
- **NFR-007**: Kafka consumer group must rebalance gracefully when instances are added or removed

### Reliability

- **NFR-008**: Notification delivery must have retry logic with exponential backoff (3 attempts)
- **NFR-009**: Failed notifications must be logged with error details for debugging
- **NFR-010**: System must handle Kafka broker failures gracefully with automatic reconnection
- **NFR-011**: Reminder check service must have health check endpoint for Kubernetes liveness probes

### Security

- **NFR-012**: Reminder events must not contain sensitive user data (e.g., passwords, tokens)
- **NFR-013**: Notification channels must use encrypted connections (TLS for email, HTTPS for webhooks)
- **NFR-014**: User timezone and notification preferences must be stored securely with proper access controls

### Observability

- **NFR-015**: All reminder checks must log execution time and tasks processed
- **NFR-016**: Notification delivery must emit metrics (sent, failed, retry count) to monitoring system
- **NFR-017**: Kafka consumer lag must be tracked and alerted on if lag exceeds 1000 messages

## Implementation Notes

### Technology Stack

- **Backend API**: FastAPI (existing) - Extended with reminder management endpoints
- **Notification Microservice**: Python FastAPI service consuming from Kafka
- **Message Queue**: Redpanda (Kafka-compatible) - "reminders" topic with 3 partitions
- **Scheduler**: Dapr cron binding - Triggers reminder check every 5 minutes
- **Database**: PostgreSQL (existing) - Add 3 new columns to tasks table
- **Natural Language Parsing**: `dateparser` library with timezone support
- **Kafka Client**: `aiokafka` for async event publishing and consuming

### Database Schema Changes

```sql
-- Add to tasks table
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE tasks ADD COLUMN remind_before JSONB NULL DEFAULT '["24h", "1h"]';
ALTER TABLE tasks ADD COLUMN reminder_sent JSONB NULL DEFAULT '{}';

-- Create index for efficient reminder queries
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_tasks_reminders ON tasks(user_id, due_date)
  WHERE due_date IS NOT NULL AND completed = FALSE;

-- Notification logs table
CREATE TABLE notification_logs (
  id SERIAL PRIMARY KEY,
  task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
  user_id VARCHAR(100) NOT NULL,
  reminder_type VARCHAR(50) NOT NULL,
  channel VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL,
  sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  error_message TEXT NULL
);
CREATE INDEX idx_notification_logs_task ON notification_logs(task_id);
CREATE INDEX idx_notification_logs_user ON notification_logs(user_id);
```

### Kafka Topic Configuration

```yaml
Topic: reminders
Partitions: 3
Replication Factor: 2
Retention: 7 days
Compression: lz4
```

### Dapr Cron Configuration

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-check-cron
spec:
  type: bindings.cron
  metadata:
  - name: schedule
    value: "*/5 * * * *"  # Every 5 minutes
  - name: direction
    value: "input"
```

### MCP Tools to Add/Extend

1. **set_due_date** (NEW): Set or update due date for a task with natural language parsing
2. **set_reminder** (NEW): Configure custom reminder intervals for a task
3. **add_task** (EXTEND): Add due_date and remind_before parameters
4. **update_task** (EXTEND): Support updating due_date
5. **list_tasks** (EXTEND): Return due_date and reminder status in response

### Microservices Architecture

```
┌─────────────────┐
│   Backend API   │──┐
│   (FastAPI)     │  │ Publishes reminder events
└─────────────────┘  │
                     ↓
         ┌──────────────────────┐
         │  Kafka (Redpanda)    │
         │  Topic: "reminders"  │
         └──────────────────────┘
                     ↓
         ┌──────────────────────┐
         │  Notification Service│
         │  (Kafka Consumer)    │
         └──────────────────────┘
                ↓       ↓       ↓
         ┌──────┐  ┌──────┐  ┌──────┐
         │Email │  │Push  │  │In-App│
         └──────┘  └──────┘  └──────┘
```

---

**Next Steps**:
1. Run `/sp.plan` to create detailed implementation plan
2. Run `/sp.tasks` to break down into actionable tasks
3. Begin implementation starting with database migration and MCP tools
