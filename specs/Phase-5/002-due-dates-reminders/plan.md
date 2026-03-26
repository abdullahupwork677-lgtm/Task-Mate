# Implementation Plan: Due Dates & Reminders

**Branch**: `002-due-dates-reminders` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/Phase-5/002-due-dates-reminders/spec.md`

## Summary

Implement a comprehensive task reminder system with natural language due date assignment, multi-channel notifications (email, push, in-app), and event-driven architecture using Kafka/Redpanda and Dapr. The system will send configurable reminders (default: 24h and 1h before due date) with timezone awareness, idempotent processing, and horizontal scalability. This feature extends the existing todo chatbot (Phase 3) and recurring tasks system (Phase 5 Part A) with persistent due dates, automated reminder checks via Dapr cron bindings, and a separate notification microservice consuming reminder events from Kafka.

**Technical Approach**: Extend existing Task model with 3 new fields (due_date, remind_before, reminder_sent), create new MCP tools for due date management, implement reminder check service triggered by Dapr cron (every 5 minutes), publish reminder events to Kafka "reminders" topic, and build standalone notification microservice to consume events and deliver notifications via multiple channels. Frontend will display due dates and overdue badges with human-readable formatting.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.109+, SQLModel 0.0.14+, aiokafka 0.8+, dateparser 1.2+, python-dateutil 2.8+, dapr-ext-fastapi 1.12+
- Notification Service: FastAPI 0.109+, aiokafka 0.8+, sendgrid 6.11+ (email), firebase-admin 6.4+ (push)
- Frontend: Next.js 14, React 18, TypeScript 5, date-fns 3.0+ (date formatting)

**Storage**:
- PostgreSQL 14+ via Neon Serverless (existing, extended schema)
- Tasks table: Add `due_date` (TIMESTAMP WITH TIME ZONE), `remind_before` (JSONB), `reminder_sent` (JSONB)
- New table: `notification_logs` for audit trail
- Database indexes: `idx_tasks_due_date`, `idx_tasks_reminders` (composite)

**Testing**:
- Backend: pytest 7.4+, pytest-asyncio 0.21+
- Unit tests: Date parsing, reminder calculation, interval validation
- Integration tests: MCP tools, Kafka publishing, database operations
- E2E tests: Full reminder flow from due date assignment to notification delivery

**Target Platform**:
- Backend API: Linux containers (Docker), deployed on Kubernetes
- Notification Service: Linux containers (Docker), deployed on Kubernetes with 3+ replicas
- Reminder Check Service: Dapr-enabled backend API with cron binding
- Frontend: Next.js 14 Server Components + Client Components, deployed on Vercel

**Project Type**: Web application (FastAPI backend + Next.js frontend + Notification microservice)

**Performance Goals**:
- Due date parsing: < 100ms for natural language input
- Reminder check (10k tasks): < 30 seconds per scan
- Notification delivery: p95 < 500ms from Kafka consumption to channel delivery
- Kafka throughput: Support 100,000 reminder events/day
- Database queries: < 50ms for due date lookups (with indexes)

**Constraints**:
- Reminder granularity: 5-minute intervals (Dapr cron)
- Timezone accuracy: Must handle all IANA timezones correctly
- Idempotency: Duplicate event processing must not send duplicate notifications
- Scalability: Support 1000+ concurrent users, horizontal scaling to 3+ notification service replicas
- Data consistency: reminder_sent field must prevent duplicate reminders even under concurrent processing

**Scale/Scope**:
- Expected users: 10,000+ users with reminder-enabled tasks
- Expected volume: 100,000+ reminder events per day
- Database scale: 1M+ tasks, 100K+ notification logs
- Microservices: 1 new notification service + Dapr integration on existing backend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Spec-Driven Development ✅
- **Status**: PASS
- **Validation**: Complete specification exists at `specs/Phase-5/002-due-dates-reminders/spec.md` with 5 user stories, 20 functional requirements, 13 success criteria, and 10 edge cases documented

### Principle II: Code Quality Standards ✅
- **Status**: PASS
- **Backend**: Will follow PEP 8, type hints, docstrings, max 50 lines per function
- **Frontend**: TypeScript strict mode, ESLint, Prettier, Server Components by default
- **Event-Driven Services**: Idempotent Kafka consumers, Pydantic event validation, dead letter queue for failures

### Principle III: Persistent Multi-User Storage ✅
- **Status**: PASS
- **Database**: Neon Serverless PostgreSQL (existing), extended schema with due_date, remind_before, reminder_sent
- **User Isolation**: reminder_sent field per task, notification_logs table with user_id for audit
- **Migrations**: Alembic migration to add new fields without data loss

### Principle IV: RESTful API Architecture ✅
- **Status**: PASS
- **Endpoints**: `/api/{user_id}/tasks` (extended), `/api/{user_id}/tasks/{id}/due-date` (new), `/api/{user_id}/tasks/{id}/reminders` (new)
- **MCP Tools**: set_due_date, set_reminder, add_task (extended), update_task (extended), list_tasks (extended)

### Principle V: JWT Authentication & Authorization ✅
- **Status**: PASS
- **Auth**: Existing JWT authentication preserved, all new endpoints require auth
- **User Isolation**: reminder_sent field scoped per task, notification_logs filtered by user_id

### Principle VI: AI Chatbot Natural Language Interface ✅
- **Status**: PASS
- **Natural Language**: dateparser library for "tomorrow at 5pm", "next Friday", "in 3 days"
- **AI Agent**: Extended system prompt to handle due date and reminder commands
- **MCP Integration**: New tools registered with OpenAI Agents SDK

### Principle VII: Container-First Development ✅
- **Status**: PASS
- **Containers**: Notification service as separate Docker container
- **Kubernetes**: Deploy to Minikube (local) and Oracle Cloud/GKE/AKS (production)
- **Helm**: Notification service Helm chart with configurable replicas

### Principle VIII: AIOps - Monitoring & Logging ✅
- **Status**: PASS
- **Structured Logging**: JSON logs for all reminder checks, notification deliveries, Kafka events
- **Metrics**: Prometheus metrics for reminder_sent_count, notification_delivery_latency, kafka_consumer_lag
- **Health Checks**: /health endpoint for Kubernetes liveness/readiness probes

### Principle IX: Helm Charts for Deployment ✅
- **Status**: PASS
- **Charts**: notification-service Helm chart with values for email/push credentials
- **Dapr**: Dapr sidecar injection for cron binding and Kafka pub/sub
- **ConfigMaps**: Kafka bootstrap servers, Dapr component configs

### Principle X: Event-Driven Architecture with Kafka ✅
- **Status**: PASS
- **Kafka Topic**: "reminders" topic with 3 partitions, 2 replication factor, 7-day retention
- **Producer**: Backend API publishes reminder events via aiokafka
- **Consumer**: Notification service consumes with consumer group "notification-service-group"
- **Idempotency**: event_id UUID in message, notification service tracks processed event_ids

### Principle XI: Dapr Distributed Application Runtime ✅
- **Status**: PASS
- **Cron Binding**: Dapr cron component triggers reminder check every 5 minutes
- **Pub/Sub**: Dapr Kafka pub/sub component for reminder events
- **State Store**: (Optional) Dapr state store for tracking processed event_ids
- **Secrets**: Dapr secrets for email/push notification credentials

### Principle XII: Advanced Task Features ✅
- **Status**: PASS
- **Due Dates**: Core capability for reminder system
- **Reminders**: Primary feature being implemented
- **Integration**: Works with existing recurring tasks (Phase 5 Part A), each occurrence has independent due date and reminders

### Principle XIII: Cloud Kubernetes Deployment ✅
- **Status**: PASS
- **Target**: Oracle Cloud OKE / GKE / AKS
- **CI/CD**: GitHub Actions workflow for automated deployment
- **Environment**: Staging + Production environments with separate Kafka topics

**Constitution Check Result**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/Phase-5/002-due-dates-reminders/
├── spec.md              # Feature specification (COMPLETE)
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output - Technology research and decisions
├── data-model.md        # Phase 1 output - Extended entities and relationships
├── quickstart.md        # Phase 1 output - Integration guide and testing scenarios
├── contracts/           # Phase 1 output - API contracts and event schemas
│   ├── openapi.yaml     # REST API extensions for due dates and reminders
│   ├── kafka-events.md  # Kafka event schemas (ReminderEvent)
│   └── mcp-tools.md     # MCP tool specifications
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Spec quality checklist (COMPLETE - ALL PASSED)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models.py                    # Extended: Task.due_date, remind_before, reminder_sent
│   │                                # New: NotificationLog model
│   ├── schemas.py                   # Extended: TaskCreate, TaskUpdate with due_date
│   │                                # New: ReminderEventSchema, NotificationLogSchema
│   ├── mcp_tools/
│   │   ├── set_due_date.py          # NEW: Set/update task due date with NLP
│   │   ├── set_reminder.py          # NEW: Configure custom reminder intervals
│   │   ├── add_task.py              # EXTENDED: Add due_date and remind_before params
│   │   ├── update_task.py           # EXTENDED: Support due_date updates
│   │   └── list_tasks.py            # EXTENDED: Return due_date and overdue status
│   ├── services/
│   │   ├── date_parser_service.py   # NEW: Natural language date parsing
│   │   ├── reminder_service.py      # NEW: Calculate reminder times, check due tasks
│   │   └── kafka_producer_service.py # NEW: Publish reminder events to Kafka
│   ├── routes/
│   │   └── reminders.py             # NEW: Dapr cron binding endpoint
│   ├── ai_agent/
│   │   ├── tools.py                 # EXTENDED: Register new MCP tools
│   │   └── system_prompt.py         # EXTENDED: Add due date/reminder examples
│   └── migrations/
│       └── versions/
│           └── 00X_add_due_date_reminder_fields.py  # NEW: Alembic migration
└── tests/
    ├── unit/
    │   ├── test_date_parser_service.py       # NEW: Test NLP date parsing
    │   ├── test_reminder_service.py          # NEW: Test reminder calculation
    │   └── test_kafka_producer_service.py    # NEW: Test event publishing
    ├── integration/
    │   ├── test_set_due_date.py              # NEW: Test set_due_date MCP tool
    │   ├── test_set_reminder.py              # NEW: Test set_reminder MCP tool
    │   ├── test_reminder_check_endpoint.py   # NEW: Test Dapr cron endpoint
    │   └── test_complete_task_reminders.py   # EXTENDED: Test reminder reset
    └── e2e/
        └── test_reminder_flow_e2e.py         # NEW: Full flow test

services/
└── notification/                            # NEW: Notification microservice
    ├── src/
    │   ├── main.py                          # FastAPI app with Kafka consumer
    │   ├── config.py                        # Config: Kafka, email, push credentials
    │   ├── kafka_consumer.py                # Kafka consumer for "reminders" topic
    │   ├── notification_handlers/
    │   │   ├── email_handler.py             # SendGrid email delivery
    │   │   ├── push_handler.py              # Firebase push notification delivery
    │   │   └── in_app_handler.py            # Store in-app notifications in DB
    │   ├── models.py                        # NotificationLog model (shared with backend)
    │   └── utils/
    │       ├── idempotency.py               # Track processed event_ids
    │       └── retry_logic.py               # Exponential backoff for retries
    ├── tests/
    │   ├── test_kafka_consumer.py
    │   ├── test_email_handler.py
    │   ├── test_push_handler.py
    │   └── test_idempotency.py
    ├── Dockerfile
    ├── requirements.txt
    └── README.md

frontend/
├── src/
│   ├── components/
│   │   ├── TaskItem.tsx                     # EXTENDED: Display due date and overdue badge
│   │   ├── DueDateBadge.tsx                 # NEW: Human-readable due date display
│   │   └── OverdueBadge.tsx                 # NEW: Red overdue indicator
│   ├── lib/
│   │   └── date-utils.ts                    # NEW: Date formatting utilities (date-fns)
│   └── types/
│       └── task.ts                          # EXTENDED: Add due_date, remind_before, reminder_sent
└── tests/
    └── components/
        ├── TaskItem.test.tsx                # EXTENDED: Test due date display
        └── DueDateBadge.test.tsx            # NEW: Test badge rendering

k8s/
└── notification-service/                    # NEW: Kubernetes manifests
    ├── deployment.yaml                      # Deployment with 3 replicas
    ├── service.yaml                         # Service for health checks
    ├── configmap.yaml                       # Kafka bootstrap servers
    ├── secrets.yaml                         # Email/push credentials (base64)
    └── dapr-components/
        ├── kafka-pubsub.yaml                # Dapr Kafka pub/sub component
        ├── cron-binding.yaml                # Dapr cron binding (5 minutes)
        └── secrets-store.yaml               # Dapr secrets component

helm/
└── notification-service/                    # NEW: Helm chart
    ├── Chart.yaml
    ├── values.yaml                          # Configurable: replicas, email provider, etc.
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        ├── configmap.yaml
        ├── secrets.yaml
        └── dapr-components.yaml
```

**Structure Decision**: Web application structure with separate notification microservice. Backend extends existing FastAPI app with new MCP tools and Dapr cron endpoint. Notification service is standalone Python FastAPI service consuming from Kafka. Frontend uses Next.js 14 Server Components for due date display with minimal client-side interactivity. All services containerized and deployed via Kubernetes/Helm.

## Complexity Tracking

> No constitution violations detected. All principles aligned with feature requirements.

## Phase 0: Research & Technology Decisions

**Status**: To be completed during `/sp.plan` execution

**Research Topics**:

1. **Natural Language Date Parsing**
   - Evaluate: dateparser vs python-dateutil vs Arrow
   - Decision criteria: Timezone support, natural language accuracy, performance
   - Test cases: "tomorrow at 5pm", "next Friday", "in 3 days", "2 weeks from now"

2. **Kafka Best Practices for Reminder Events**
   - Topic partitioning strategy (by user_id vs task_id vs round-robin)
   - Retention policy (7 days vs 30 days)
   - Message compression (lz4 vs snappy vs gzip)
   - Consumer group rebalancing for notification service replicas

3. **Dapr Cron Binding Configuration**
   - Cron expression for 5-minute intervals: `*/5 * * * *`
   - Reliability: What happens if cron trigger fails? Retry logic?
   - Concurrency: Can multiple cron triggers run simultaneously? Leader election needed?

4. **Notification Channel Integration**
   - Email: SendGrid vs AWS SES vs Mailgun (pros/cons, pricing)
   - Push: Firebase Cloud Messaging (FCM) vs Apple Push Notification service (APNs) integration
   - In-app: WebSocket vs polling vs database-backed notifications

5. **Idempotency Strategy**
   - Option A: Track event_id in Redis/Valkey with TTL (fast, eventual consistency)
   - Option B: Track event_id in PostgreSQL notification_logs table (durable, slower)
   - Option C: Use Kafka offset management only (consumer group commitment)
   - Decision criteria: Duplicate prevention guarantee, performance, operational complexity

6. **Timezone Handling**
   - Store due_date in UTC vs user's timezone vs TIMESTAMP WITH TIME ZONE
   - Calculate reminder times in UTC vs user's timezone
   - Handle daylight saving time transitions
   - Test edge cases: User travels across timezones, timezone database updates

7. **Database Index Optimization**
   - Composite index on (user_id, due_date) vs separate indexes
   - Partial index: `WHERE due_date IS NOT NULL AND completed = FALSE`
   - Analyze query patterns: Filter by due date range, sort by due date
   - Test with 10,000+ tasks per user

8. **Reminder Check Performance**
   - Query optimization: Batch query vs cursor-based streaming
   - Pagination: Fetch 1000 tasks at a time vs fetch all
   - Caching: Cache calculated reminder times vs recalculate every check
   - Concurrency: Process tasks in parallel threads vs sequential

**Output**: `research.md` documenting all technology decisions with rationale and alternatives considered.

## Phase 1: Design & Contracts

**Status**: To be completed during `/sp.plan` execution

### Data Model Extensions

**Output**: `data-model.md`

**Entities to Define**:

1. **Task (Extended)**
   - New fields: due_date, remind_before, reminder_sent
   - Validation rules: due_date must be future timestamp (allow past for completed tasks), remind_before array format
   - Relationships: Links to User (existing), parent_task_id (existing for recurring tasks)
   - State transitions: None (stateless reminders)

2. **NotificationLog (New)**
   - Fields: id, task_id, user_id, reminder_type, channel, status, sent_at, error_message
   - Purpose: Audit trail for debugging and analytics
   - Indexes: (task_id), (user_id), (sent_at)
   - Retention: 90 days (configurable)

3. **User (Extended)**
   - New fields: timezone, notification_preferences
   - Validation: timezone must be valid IANA timezone
   - Default: timezone='UTC', notification_preferences={'email': True, 'push': False, 'in_app': True}

4. **ReminderEvent (Kafka Message Schema)**
   - Fields: event_id, task_id, user_id, task_title, due_date, reminder_type, priority, channels, timestamp
   - Serialization: JSON with Pydantic validation
   - Partitioning key: user_id (for ordered processing per user)

### API Contracts

**Output**: `contracts/openapi.yaml`, `contracts/kafka-events.md`, `contracts/mcp-tools.md`

**REST API Extensions**:

1. `POST /api/{user_id}/tasks/{id}/due-date`
   - Request: `{"due_date": "2026-02-15T17:00:00Z"}` or `{"due_date_natural": "tomorrow at 5pm"}`
   - Response: `{"task": {...}, "due_date": "2026-02-15T17:00:00Z", "due_date_formatted": "Tomorrow at 5:00 PM"}`

2. `DELETE /api/{user_id}/tasks/{id}/due-date`
   - Clear due date and reminders
   - Response: `{"task": {...}, "due_date": null}`

3. `POST /api/{user_id}/tasks/{id}/reminders`
   - Request: `{"remind_before": ["24h", "1h"]}` or `{"remind_before_natural": "3 days before and 2 hours before"}`
   - Response: `{"task": {...}, "remind_before": ["24h", "1h"]}`

4. `POST /api/internal/dapr/reminder-check` (Dapr cron binding endpoint)
   - Triggered by Dapr cron every 5 minutes
   - Scans tasks with due dates, publishes reminder events to Kafka
   - Response: `{"tasks_checked": 1234, "reminders_sent": 56, "duration_ms": 2345}`

**MCP Tool Contracts**:

1. `set_due_date(task_id, due_date_natural, user_id)`
   - Input: Natural language date ("tomorrow at 5pm", "next Friday")
   - Output: Task with parsed due_date
   - Error handling: Invalid date expressions, past dates (warn but allow)

2. `set_reminder(task_id, remind_before_natural, user_id)`
   - Input: Natural language intervals ("3 days before", "30 minutes before")
   - Output: Task with remind_before array
   - Error handling: Invalid intervals, reminder time after due date

3. `add_task` (Extended)
   - New params: due_date_natural, remind_before_natural
   - Backward compatible: Optional params default to None

4. `complete_task` (Extended)
   - Existing behavior: Mark task complete, create next occurrence (recurring)
   - New behavior: Clear reminder_sent field, skip future reminder checks

**Kafka Event Schemas**:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": 123,
  "user_id": "user-abc-123",
  "task_title": "Submit quarterly report",
  "due_date": "2026-02-15T17:00:00Z",
  "reminder_type": "24h",
  "priority": "high",
  "channels": ["email", "push", "in_app"],
  "timestamp": "2026-02-14T17:00:00Z"
}
```

### Integration Guide

**Output**: `quickstart.md`

**Scenarios to Document**:

1. **Scenario 1**: User creates task with due date via chatbot
   - Command: "Add task 'Submit report' due tomorrow at 5pm"
   - Backend: Parse natural language → set due_date → store in DB
   - Frontend: Display task with "Tomorrow at 5:00 PM" badge

2. **Scenario 2**: Reminder check triggers notification
   - Dapr cron: Trigger reminder-check endpoint every 5 minutes
   - Backend: Query tasks due in 24h → publish ReminderEvent to Kafka
   - Notification service: Consume event → send email → update notification_logs

3. **Scenario 3**: User customizes reminder intervals
   - Command: "Remind me about task 5 three days before and 1 hour before"
   - Backend: Parse intervals → update remind_before field
   - Future reminders: Use custom intervals instead of defaults

4. **Scenario 4**: User completes task with pending reminders
   - Action: User marks task as complete
   - Backend: Set completed=True → clear reminder_sent → skip future checks

5. **Scenario 5**: Notification delivery failure with retry
   - Notification service: Consume event → email send fails (timeout)
   - Retry logic: Exponential backoff (1s, 2s, 4s) → retry 3 times
   - Failure: Log to notification_logs with error_message → dead letter queue

### Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh claude` to update CLAUDE.md with:
- New technology: dateparser, aiokafka, SendGrid, Firebase Admin SDK
- New microservice: notification-service with Kafka consumer
- New Dapr components: cron binding, Kafka pub/sub

**Phase 1 Complete**: data-model.md, contracts/, quickstart.md generated. Constitution Check re-validated (all gates still pass).

## Implementation Phases (Post-Planning)

**Note**: These phases are executed by `/sp.tasks` and `/sp.implement` commands after `/sp.plan` completes.

### Phase 2: Task Breakdown (/sp.tasks)
- Generate `tasks.md` with 100+ granular tasks across 12 phases
- Tasks organized by: Setup, Database, MCP Tools, Services, Notification Microservice, Frontend, Testing, Deployment
- Each task includes: ID, description, files affected, estimated time, dependencies

### Phase 3-14: Implementation (/sp.implement)
- Phase-by-phase execution following tasks.md
- TDD approach: Write tests first, watch them fail, implement, watch them pass
- Constitution compliance checks at each phase
- Continuous integration with existing codebase (no breaking changes)

---

**Plan Status**: Phase 0 (Research) and Phase 1 (Design & Contracts) to be executed next.

**Next Steps**:
1. Execute Phase 0 research tasks → generate `research.md`
2. Execute Phase 1 design tasks → generate `data-model.md`, `contracts/`, `quickstart.md`
3. Run `/sp.tasks` to generate implementation task breakdown
4. Run `/sp.implement` to execute tasks phase-by-phase
