# Todo Backend API

FastAPI backend for Todo application - Phase V (Recurring Tasks)

## Features

### Core Features
- REST API for task management (CRUD operations)
- Authentication (signup, login, JWT-protected endpoints)
- SQLModel ORM with PostgreSQL
- Neon Serverless Database integration
- Pydantic validation
- Health check endpoint
- User isolation (all tasks scoped to authenticated user)

### Phase V: Advanced Features 🆕

#### Recurring Tasks
- **Set tasks as recurring** via natural language (daily/weekly/monthly/custom)
- **Auto-create next occurrence** when recurring task is completed
- **Custom recurrence patterns** (every N days/weeks/months)
- **Recurrence end dates** (stop after specific date)
- **Idempotency** via unique database constraints
- **AI agent integration** with natural language understanding
- **MCP tools** for recurring task management

#### Due Dates & Reminders ⏰
- **Set due dates** with time for tasks
- **Customizable reminder intervals** (24h, 1h, or custom)
- **Multi-channel notifications** (email via SendGrid, push via Firebase, in-app)
- **Event-driven architecture** with Kafka/Redpanda for reminder processing
- **Dapr cron binding** for periodic reminder checks (every 5 minutes)
- **Timezone-aware reminders** respecting user's local timezone
- **No duplicate reminders** with idempotency tracking
- **Auto-stop on completion** - Reminders cease when task is completed
- **Notification microservice** - Separate service for multi-channel delivery
- **Dead Letter Queue** for failed notification handling with retry logic

#### Task Tags & Categories 🏷️
- **Create tasks with tags** via natural language ("add task X, tags: work, urgent")
- **Add/remove tags** from existing tasks ("add tag important to task 5")
- **Filter tasks by tags** with OR logic ("show work or urgent tasks")
- **List all available tags** with usage counts and colors
- **Deterministic color generation** - Same tag always has same color
- **Tag normalization** - Automatic lowercase conversion and deduplication
- **User isolation** - Tags are scoped to authenticated user
- **Autocomplete** - Frontend suggests existing tags as you type
- **Visual badges** - Color-coded tag display with consistent styling
- **Performance optimized** - GIN index on tags column for fast filtering

**MCP Tools:**
- `add_task` (extended) - Create tasks with tags
- `add_tag` - Add tags to existing task
- `remove_tag` - Remove tags from task
- `list_tasks` (extended) - Filter by tags (OR logic)
- `list_tags` - List all unique tags with counts and colors

**Examples:**
```python
# Create task with tags
User: "add task buy groceries, tags: shopping, groceries"
Agent: Calls add_task(title="buy groceries", tags=["shopping", "groceries"])

# Add tags to existing task
User: "add tag urgent to task 5"
Agent: Calls add_tag(task_id=5, tags=["urgent"])

# Filter by tags (OR logic)
User: "show work or urgent tasks"
Agent: Calls list_tasks(tag_filter=["work", "urgent"])
Returns: Tasks with work OR urgent tag

# List all tags
User: "show all my tags"
Agent: Calls list_tags()
Returns: [
  {"name": "work", "color": "#3b82f6", "count": 15},
  {"name": "urgent", "color": "#ef4444", "count": 10},
  {"name": "shopping", "color": "#10b981", "count": 7}
]
```

#### Task Search & Advanced Filtering 🔍

**Feature 004-search-filter** - Multi-criteria search with pagination

- **Keyword search** - Search in title and description (case-insensitive, partial matching)
- **Status filtering** - Filter by completed/incomplete status
- **Priority filtering** - Filter by high/medium/low priority
- **Tags filtering** - Filter by tags with OR logic (any task with selected tags)
- **Due date filtering** - Filter by overdue/today/this week/this month/no due date
- **Combined filters** - Use AND logic between filter types
- **Pagination** - Page-based results (default 20 per page, configurable 10-100)
- **Result summaries** - Human-readable filter descriptions
- **Performance optimized** - Composite indexes for < 500ms queries (1,000 tasks)

**Database Indexes:**
```sql
CREATE INDEX idx_tasks_user_completed ON tasks (user_id, completed);
CREATE INDEX idx_tasks_user_priority ON tasks (user_id, priority);
CREATE INDEX idx_tasks_user_tags ON tasks (user_id, tags);
CREATE INDEX idx_tasks_user_due_date ON tasks (user_id, due_date);
CREATE INDEX idx_tasks_user_title ON tasks (user_id, title);
```

**MCP Tools:**
- `search_tasks` - Multi-criteria search with all filters

**API Endpoint:**
```
GET /api/search
  ?keyword=grocery            # Search in title/description
  &status_filter=incomplete   # all | completed | incomplete
  &priority_filter=high       # all | high | medium | low
  &tags_filter=work,urgent    # Comma-separated tags (OR logic)
  &due_date_filter=today      # all | overdue | today | this_week | this_month | no_due_date
  &page=1                     # Page number (1-indexed)
  &page_size=20               # Results per page (10-100)
```

**Examples:**

```python
# Simple keyword search
User: "search for grocery"
Agent: Calls search_tasks(keyword="grocery")
Response: "Found 5 tasks matching 'grocery': ..."

# Filter by status
User: "show incomplete tasks"
Agent: Calls search_tasks(status_filter="pending")
Response: "Found 12 incomplete tasks: ..."

# Filter by priority
User: "show high priority tasks"
Agent: Calls search_tasks(priority_filter="high")
Response: "Found 8 high priority tasks: ..."

# Filter by tags (OR logic)
User: "show work or urgent tasks"
Agent: Calls search_tasks(tags_filter=["work", "urgent"])
Response: "Found 15 tasks tagged with work or urgent: ..."

# Filter by due date
User: "show overdue tasks"
Agent: Calls search_tasks(due_date_filter="overdue")
Response: "Found 3 overdue tasks: ..."

User: "what tasks are due today?"
Agent: Calls search_tasks(due_date_filter="today")
Response: "Found 2 tasks due today: ..."

# Combined filters (AND logic between types)
User: "search grocery in incomplete high priority tasks"
Agent: Calls search_tasks(
  keyword="grocery",
  status_filter="pending",
  priority_filter="high"
)
Response: "Found 1 task matching 'grocery' (incomplete high priority): ..."

User: "show incomplete work tasks that are overdue"
Agent: Calls search_tasks(
  status_filter="pending",
  tags_filter=["work"],
  due_date_filter="overdue"
)
Response: "Found 2 incomplete work tasks (overdue): ..."
```

**Response Format:**
```json
{
  "tasks": [...],
  "total_count": 25,
  "filtered_count": 20,
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  },
  "applied_filters": {
    "keyword": "grocery",
    "status": "incomplete",
    "priority": "high",
    "tags": ["work"],
    "due_date": "today",
    "summary": "Showing 5 matching 'grocery' incomplete high priority work tasks due today"
  }
}
```

**Performance:**
- Keyword search: < 200ms
- Single filter: < 300ms
- Combined filters: < 500ms (1,000 tasks)
- Pagination: < 100ms per page

**Filter Logic:**
- **AND logic** between filter types (keyword AND status AND priority AND tags AND due_date)
- **OR logic** within tags filter (tag1 OR tag2 OR tag3)
- **Case-insensitive** keyword matching
- **Partial match** for keywords (substring search)

---

#### Task Sorting 🔢

**Feature 005-task-sort** - Database-level SQL ORDER BY sorting with multiple criteria

- **Sort by due date** - Earliest/latest first, tasks without due dates appear at end
- **Sort by priority** - High → medium → low (or reverse)
- **Sort by created date** - Newest/oldest first (default sort)
- **Sort by title** - A-Z or Z-A (case-insensitive)
- **Session persistence** - Sort preferences saved for browser session
- **Visual indicators** - Active sort field and direction displayed
- **Natural language support** - AI chatbot understands "sort by due date", "show high priority first"
- **Performance optimized** - Composite indexes for < 200ms sorting (1,000 tasks)

**Database Indexes:**
```sql
-- PostgreSQL (production)
CREATE INDEX idx_tasks_user_due_date ON tasks (user_id, due_date NULLS LAST, created_at DESC);
CREATE INDEX idx_tasks_user_priority ON tasks (user_id, priority, created_at DESC);
CREATE INDEX idx_tasks_user_created ON tasks (user_id, created_at DESC);
CREATE INDEX idx_tasks_user_title ON tasks (user_id, LOWER(title), created_at DESC);

-- SQLite (development) - simplified without NULLS LAST / DESC / LOWER()
CREATE INDEX idx_tasks_user_due_date ON tasks (user_id, due_date, created_at);
CREATE INDEX idx_tasks_user_priority ON tasks (user_id, priority, created_at);
CREATE INDEX idx_tasks_user_created ON tasks (user_id, created_at);
CREATE INDEX idx_tasks_user_title ON tasks (user_id, title, created_at);
```

**MCP Tools:**
- `list_tasks` - List tasks with optional sorting
- `search_tasks` - Search/filter tasks with optional sorting (combines with filters)

**API Parameters:**
```
sort_by: due_date | priority | created_at | title (default: created_at)
sort_direction: asc | desc (default: field-specific)
```

**Default Sort Directions:**
| Sort Field | Default Direction | Reasoning |
|------------|------------------|-----------|
| `created_at` | `desc` | Newest tasks first (default) |
| `due_date` | `asc` | Earliest deadlines first |
| `priority` | `asc` | High → medium → low |
| `title` | `asc` | A → Z alphabetical |

**Examples:**

```python
# Sort by due date (earliest first)
User: "sort my tasks by due date"
Agent: Calls list_tasks(sort_by="due_date", sort_direction="asc")
Response: "Here are your tasks sorted by due date (earliest first): ..."

# Sort by priority (high to low)
User: "show high priority first"
Agent: Calls list_tasks(sort_by="priority", sort_direction="asc")
Response: "Here are your tasks sorted by priority (high → medium → low): ..."

# Sort by created date (newest first) - DEFAULT
User: "show my tasks"
Agent: Calls list_tasks(sort_by="created_at", sort_direction="desc")
Response: "Here are your tasks (newest first): ..."

# Sort alphabetically (A-Z)
User: "sort alphabetically"
Agent: Calls list_tasks(sort_by="title", sort_direction="asc")
Response: "Here are your tasks sorted A-Z: ..."

# Combine with search/filter
User: "search grocery and sort by priority"
Agent: Calls search_tasks(
  keyword="grocery",
  sort_by="priority",
  sort_direction="asc"
)
Response: "Found 5 tasks matching 'grocery', sorted by priority: ..."

User: "show incomplete tasks sorted by due date"
Agent: Calls search_tasks(
  status_filter="pending",
  sort_by="due_date",
  sort_direction="asc"
)
Response: "Found 12 incomplete tasks, sorted by due date: ..."
```

**Sorting Logic:**

| Sort Field | SQL Implementation | Tiebreaker | Special Handling |
|------------|-------------------|------------|------------------|
| `due_date` | `ORDER BY due_date NULLS LAST` | `created_at DESC` | Tasks without due dates appear at end |
| `priority` | `CASE priority WHEN 'high' THEN 1...` | `created_at DESC` | Enum mapped to integers (high=1, medium=2, low=3) |
| `created_at` | `ORDER BY created_at` | None | Unique enough, no tiebreaker needed |
| `title` | `ORDER BY LOWER(title)` | `created_at DESC` | Case-insensitive sorting |

**Performance:**
- Sort query execution: < 200ms (1,000 tasks with indexes)
- Sort query execution: < 500ms (10,000 tasks with indexes)
- Index-only scans used for optimal performance
- Tiebreaker column (created_at) ensures deterministic ordering

---

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Neon database URL
```

3. Run migrations:
```bash
uv run alembic upgrade head
```

4. Start server:
```bash
uv run uvicorn src.main:app --reload
```

### Dapr Setup (Phase V - Event-Driven Architecture)

**Dapr** (Distributed Application Runtime) provides cron bindings for periodic reminder checks and Kafka pub/sub for event streaming.

#### Local Development with Dapr

1. **Install Dapr CLI**:
```bash
# macOS/Linux
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash

# Windows
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"

# Verify installation
dapr --version
```

2. **Initialize Dapr**:
```bash
dapr init
```

This installs Dapr runtime, Redis (state store), and Zipkin (tracing).

3. **Run Backend with Dapr Sidecar**:
```bash
# Terminal 1: Start backend with Dapr
dapr run \
  --app-id backend-api \
  --app-port 8000 \
  --dapr-http-port 3500 \
  --components-path ./dapr-components \
  -- uvicorn src.main:app --reload

# Terminal 2: Check Dapr status
dapr list
```

4. **Configure Dapr Components** (Local):

Create `backend/dapr-components/` directory:

```bash
mkdir -p dapr-components
```

**Cron Binding** (`dapr-components/cron-binding.yaml`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-check-cron
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: "@every 5m"
```

**Kafka Pub/Sub** (`dapr-components/kafka-pubsub.yaml`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "localhost:9092"
    - name: consumerGroup
      value: "backend-api-group"
```

5. **Test Cron Trigger** (Manual):
```bash
# Trigger reminder check via Dapr
curl -X POST http://localhost:3500/v1.0/bindings/reminder-check-cron \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Kubernetes Deployment with Dapr

1. **Install Dapr on Kubernetes**:
```bash
# Add Dapr Helm repo
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update

# Install Dapr
helm upgrade --install dapr dapr/dapr \
  --namespace dapr-system \
  --create-namespace \
  --wait

# Verify installation
kubectl get pods -n dapr-system
```

2. **Enable Dapr in Deployment**:

Add Dapr annotations to `k8s/oke/backend-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "backend-api"
        dapr.io/app-port: "8000"
        dapr.io/log-level: "info"
```

3. **Deploy Dapr Components**:
```bash
# Apply cron binding
kubectl apply -f k8s/notification-service/dapr-components/cron-binding.yaml

# Apply Kafka pub/sub
kubectl apply -f k8s/notification-service/dapr-components/kafka-pubsub.yaml

# Apply secrets store
kubectl apply -f k8s/notification-service/dapr-components/secrets-store.yaml

# Verify components
kubectl get components -n default
```

4. **Check Dapr Sidecar Logs**:
```bash
# View Dapr sidecar logs
kubectl logs -l app=backend-api -c daprd

# Filter for cron events
kubectl logs -l app=backend-api -c daprd | grep cron

# Filter for pub/sub events
kubectl logs -l app=backend-api -c daprd | grep pubsub
```

#### Dapr Endpoints

**Cron Binding Endpoint**:
- **Local**: `POST http://localhost:3500/v1.0/bindings/reminder-check-cron`
- **In-cluster**: Triggered automatically by Dapr every 5 minutes
- **Backend handler**: `/api/internal/dapr/reminder-check`

**Kafka Pub/Sub**:
- **Publish**: Uses Dapr pub/sub API to send events to `reminders` topic
- **Subscribe**: Notification service subscribes via Kafka consumer group

#### Troubleshooting Dapr

**Issue: Cron not triggering**
```bash
# Check Dapr sidecar is running
kubectl get pods -l app=backend-api

# Check Dapr logs
kubectl logs -l app=backend-api -c daprd | grep cron

# Manually trigger cron
curl -X POST http://localhost:3500/v1.0/bindings/reminder-check-cron -d '{}'
```

**Issue: Kafka connection fails**
```bash
# Check Kafka component
kubectl get components reminder-check-cron -o yaml

# Test Kafka connectivity from pod
kubectl exec -it <backend-pod> -- nc -zv redpanda 9092

# Check Dapr pub/sub logs
kubectl logs -l app=backend-api -c daprd | grep kafka
```

**Issue: Component not loading**
```bash
# Describe component
kubectl describe component reminder-check-cron

# Check Dapr operator logs
kubectl logs -n dapr-system -l app=dapr-operator
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication

- Signup: `POST /api/auth/signup`
- Login: `POST /api/auth/login`
- Current user (protected): `GET /api/auth/me` (Authorization: Bearer <token>)

## Recurring Tasks (Phase V)

### Quick Start

**Set a task as recurring**:
```python
# Via AI agent (natural language)
"Make task 5 repeat daily"
"Set task 7 to repeat every 3 days"
"Make task 10 recurring weekly until next year"

# Via MCP tool (programmatic)
from src.mcp_tools.set_recurring import set_recurring

await set_recurring(
    user_id=1,
    task_id=5,
    pattern="daily"
)
```

**Create recurring task in one command**:
```python
# Via AI agent (natural language)
"Add a daily task 'Morning standup'"
"Create a weekly team review"

# Via MCP tool (programmatic)
from src.mcp_tools.add_task import add_task

await add_task(
    user_id="user-123",
    title="Morning exercise",
    recurrence_pattern="daily"
)
```

**Complete task (auto-creates next occurrence)**:
```python
# Via AI agent (natural language)
"Complete task 5"

# Result: Task 5 marked complete, Task 6 auto-created for next day
```

### Supported Recurrence Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| `daily` | Every day | "Make task daily" |
| `weekly` | Every week | "Repeat weekly" |
| `monthly` | Every month | "Monthly task" |
| `yearly` | Every year | "Repeat yearly" |
| `every N days` | Every N days | "Repeat every 3 days" |
| `every N weeks` | Every N weeks | "Every 2 weeks" |
| `every N months` | Every N months | "Every 6 months" |
| `none` | Cancel recurrence | "Stop repeating" |

### Key Features

1. **Auto-Create Next Occurrence**:
   - When you complete a recurring task, the next occurrence is automatically created
   - Inherits title, description, priority, and recurrence settings
   - Links to parent task via `parent_task_id`

2. **Natural Language Support**:
   - AI agent understands phrases like "daily task", "repeat weekly", "every 3 days"
   - No need to remember exact API parameters

3. **Recurrence End Dates**:
   - Set optional end date: "until next year", "for 6 months", "2027-12-31"
   - Recurrence stops automatically when end date is reached

4. **Idempotency**:
   - Safe for concurrent operations (unique database constraint)
   - Completing the same task twice won't create duplicate next occurrences

5. **User Isolation**:
   - All operations enforce user authentication
   - Users can only access/modify their own tasks

### MCP Tools

| Tool | Purpose | Documentation |
|------|---------|---------------|
| `set_recurring` | Set existing task as recurring | `docs/api.md#set_recurring` |
| `add_task` | Create new task (with optional recurrence) | `docs/api.md#add_task-with-recurrence` |
| `complete_task` | Mark complete + auto-create next | `docs/api.md#complete_task-auto-create-next-occurrence` |

### Database Schema

Phase V adds 6 new fields to the `tasks` table:

```sql
ALTER TABLE tasks ADD COLUMN is_recurring BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN recurrence_pattern VARCHAR(100);
ALTER TABLE tasks ADD COLUMN recurrence_end_date TIMESTAMP;
ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(id);
ALTER TABLE tasks ADD COLUMN due_date TIMESTAMP;
ALTER TABLE tasks ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';

-- Indexes for performance
CREATE INDEX ix_tasks_user_recurring ON tasks(user_id, is_recurring);
CREATE UNIQUE INDEX ix_tasks_parent_due_unique ON tasks(parent_task_id, due_date);
```

### Examples

**Example 1: Daily standup**
```python
# Create daily recurring task
await add_task(
    user_id="user-123",
    title="Daily standup",
    due_date="tomorrow at 9am",
    recurrence_pattern="daily"
)

# Complete today's standup
# → Tomorrow's standup auto-created at 9am
```

**Example 2: Weekly team review**
```python
# Set existing task as weekly recurring
await set_recurring(
    user_id=1,
    task_id=10,
    pattern="weekly"
)

# Complete this week's review
# → Next week's review auto-created
```

**Example 3: Monthly reports (with end date)**
```python
# Create monthly task that ends in 1 year
await add_task(
    user_id="user-123",
    title="Monthly report",
    recurrence_pattern="monthly",
    recurrence_end_date="1 year from now"
)

# After 12 completions, recurrence stops automatically
```

### Testing

```bash
# Run all recurring tasks tests
pytest tests/ -k recurring

# Run unit tests (recurrence engine)
pytest tests/unit/test_recurrence_engine.py

# Run integration tests (MCP tools)
pytest tests/integration/test_set_recurring.py
pytest tests/integration/test_complete_task.py

# Run edge case tests
pytest tests/integration/test_edge_cases.py

# Run E2E tests (AI agent)
pytest tests/e2e/test_recurring_chatbot.py
```

### Documentation

- **API Reference**: `docs/api.md` - Complete API documentation
- **User Guide**: `docs/user-guide-recurring.md` - User-facing guide
- **Quickstart**: `specs/Phase-5/001-recurring-tasks/quickstart.md` - Quick examples
- **Testing**: `specs/Phase-5/001-recurring-tasks/FRONTEND_TESTING.md` - Frontend integration

---

## Due Dates & Reminders (Phase V) ⏰

### Quick Start

**Set due date with reminders**:
```python
# Via AI agent (natural language)
"Set task 5 due tomorrow at 2pm with reminders"
"Task 10 is due Friday at 5pm, remind me 24 hours and 1 hour before"

# Via MCP tool (programmatic)
from src.mcp_tools.set_reminder import set_reminder

await set_reminder(
    user_id="user-123",
    task_id=5,
    due_date="2026-02-15T14:00:00Z",
    remind_before=["24h", "1h"]
)
```

**Create task with due date in one command**:
```python
# Via AI agent (natural language)
"Add task 'Submit report' due tomorrow at 5pm"
"Create task 'Team meeting' for Friday 9am with reminder"

# Via MCP tool (programmatic)
from src.mcp_tools.add_task import add_task

await add_task(
    user_id="user-123",
    title="Submit quarterly report",
    due_date="tomorrow at 5pm",
    remind_before=["24h", "1h"]
)
```

### Architecture

**Event-Driven Flow**:
```
Backend API (FastAPI)
    ↓
Dapr Cron (every 5 min) → /api/internal/dapr/reminder-check
    ↓
Query tasks needing reminders → Kafka Producer
    ↓
Kafka Topic: "reminders"
    ↓
Notification Service (3 replicas) → Kafka Consumer
    ↓
Multi-Channel Handlers (Parallel)
    ├─→ Email (SendGrid)
    ├─→ Push (Firebase)
    └─→ In-App (Database)
    ↓
Dead Letter Queue (DLQ) for failures
```

### Reminder Intervals

| Interval | Description | Example |
|----------|-------------|---------|
| `24h` | 24 hours before due date | "Remind me a day before" |
| `1h` | 1 hour before due date | "Remind me an hour before" |
| `2h` | 2 hours before due date | "2 hours before" |
| `30m` | 30 minutes before due date | "30 minutes before" |
| Custom | Any interval string | "3 days before", "1 week before" |

### Key Features

1. **Timezone-Aware Reminders**:
   - Respects user's timezone from `users.timezone` field
   - Due dates stored in UTC, displayed in user's local time
   - Reminders sent at correct local time

2. **No Duplicate Reminders**:
   - `reminder_sent` field tracks sent reminders
   - Idempotency ensures each reminder sent exactly once
   - Safe for concurrent operations

3. **Multi-Channel Delivery** (Parallel Execution):
   - Email via SendGrid (configurable from address)
   - Push notifications via Firebase Cloud Messaging
   - In-app notifications stored in database
   - Uses `asyncio.gather()` for 3x performance improvement

4. **Dapr Integration**:
   - Cron binding triggers reminder checks every 5 minutes
   - Kafka pub/sub component for event streaming
   - Kubernetes secrets integration for credentials

5. **Dead Letter Queue (DLQ)**:
   - Failed notifications retry 3 times with exponential backoff (1s, 2s, 4s)
   - After max retries, sent to `reminders.dlq` topic
   - Prometheus alerts for high DLQ message count

### Database Schema

Phase V adds 3 reminder-related fields to the `tasks` table:

```sql
ALTER TABLE tasks ADD COLUMN remind_before TEXT[];  -- Array of intervals: ['24h', '1h']
ALTER TABLE tasks ADD COLUMN reminder_sent JSONB DEFAULT '{}';  -- Tracks sent: {"24h": "2026-02-14T10:00:00Z"}

-- Index for efficient reminder queries
CREATE INDEX ix_tasks_reminders ON tasks (due_date, completed)
WHERE due_date IS NOT NULL AND NOT completed;
```

### Examples

**Example 1: Report deadline with reminders**
```python
# Create task with due date and reminders
await add_task(
    user_id="user-123",
    title="Submit Q1 financial report",
    description="Deadline: EOD Friday",
    due_date="2026-02-21T17:00:00Z",  # Friday 5pm UTC
    remind_before=["24h", "1h"]
)

# System behavior:
# - Thursday 5pm: Send "24h reminder" email/push/in-app
# - Friday 4pm: Send "1h reminder" email/push/in-app
```

**Example 2: Meeting reminder**
```python
# Set existing task with due date
await set_reminder(
    user_id=1,
    task_id=10,
    due_date="2026-02-15T09:00:00Z",  # Tomorrow 9am
    remind_before=["1h"]
)

# System behavior:
# - Tomorrow 8am: Send "1h reminder" to all channels
```

**Example 3: Custom reminder intervals**
```python
# Create task with custom intervals
await add_task(
    user_id="user-123",
    title="Project presentation",
    due_date="next Friday at 2pm",
    remind_before=["1 week", "1 day", "1 hour"]
)

# System sends reminders:
# - 1 week before
# - 1 day before
# - 1 hour before
```

### Notification Channels

**Email (SendGrid)**:
- Configurable from address: `SENDGRID_FROM_EMAIL`
- Subject: "Reminder: [Task Title]"
- Body: Task details, due date, time remaining
- Retry logic: 3 attempts with exponential backoff

**Push Notifications (Firebase)**:
- Requires Firebase credentials file
- Sends to user's registered device tokens
- Notification title: "Task Reminder"
- Deep links to task detail view

**In-App Notifications**:
- Stored in database `notifications` table
- User sees in notification center
- Marked as read when clicked
- Persists for 30 days

### Dapr Configuration

**Cron Binding** (`k8s/notification-service/dapr-components/cron-binding.yaml`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-check-cron
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: "@every 5m"  # Every 5 minutes
```

**Kafka Pub/Sub** (`k8s/notification-service/dapr-components/kafka-pubsub.yaml`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "redpanda:9092"
    - name: consumerGroup
      value: "notification-service-group"
```

### Testing

```bash
# Run reminder system tests
pytest tests/ -k reminder

# Run notification service tests
pytest services/notification/tests/ -v

# Run performance tests (10k tasks, 1k notifications)
pytest backend/tests/performance/test_reminder_load.py -v

# Run integration tests (timezone, recurring, replicas)
pytest backend/tests/integration/test_phase12_integration.py -v

# Run edge case tests (overdue, completion, date changes)
pytest backend/tests/integration/test_edge_cases.py -v

# Run DLQ tests
pytest services/notification/tests/test_dlq.py -v
```

### Monitoring & Observability

**Backend Metrics** (Prometheus):
```
reminder_checks_total{status="success"}           # Reminder check runs
reminders_sent_total{reminder_type="24h"}         # Reminders by type
reminder_check_duration_seconds                   # Query duration
reminder_errors_total{error_type="kafka_error"}   # Error tracking
```

**Notification Service Metrics**:
```
notifications_sent_total{channel="email", status="success"}  # By channel
notification_delivery_latency_seconds{channel="email"}       # Latency tracking
notification_failures_total{channel="email", error_type="timeout"}
dlq_messages_total{reason="max_retries"}                     # DLQ tracking
dlq_size                                                     # Current DLQ size
```

**Health Checks**:
```bash
# Backend health
curl http://localhost:8000/health

# Notification service health
curl http://localhost:8001/health

# Expected response:
{
  "status": "healthy",
  "checks": {
    "kafka": "connected",
    "database": "connected",
    "consumer_running": true
  }
}
```

### Troubleshooting

**Issue: No reminders being sent**
1. Check Dapr cron is running: `kubectl logs -l app=backend -c daprd | grep cron`
2. Manually trigger: `curl -X POST http://localhost:8000/api/internal/dapr/reminder-check`
3. Check Kafka topic: `kubectl exec -it redpanda-0 -- rpk topic consume reminders --num 10`

**Issue: High DLQ message count**
1. Check notification service logs: `kubectl logs -l app=notification-service | grep -i error`
2. Verify SendGrid API key: `kubectl get secret notification-service-secrets`
3. Inspect DLQ messages: `kubectl exec -it redpanda-0 -- rpk topic consume reminders.dlq --num 10`

**Issue: Duplicate reminders**
1. Check consumer group: `kubectl exec -it redpanda-0 -- rpk group describe notification-service-group`
2. Verify `reminder_sent` updates in database
3. Check logs for duplicate event processing

### Production Runbook

For comprehensive troubleshooting and operational procedures, see:
- **Runbook**: `docs/runbooks/reminders.md` - Complete production guide
- **Notification Service**: `services/notification/README.md` - Service documentation

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# App
DEBUG=true
API_V1_PREFIX=/api
SERVICE_NAME=backend-api

# Auth (Feature 2)
BETTER_AUTH_SECRET=generate-with-python-secrets-token_urlsafe-32
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=7

# Kafka/Redpanda (Phase V - Reminders)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_REMINDERS_TOPIC=reminders
KAFKA_DLQ_TOPIC=reminders.dlq

# Dapr Configuration (Phase V)
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
DAPR_REMINDER_CHECK_SCHEDULE=@every 5m

# Logging & Monitoring (Phase V)
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true
```

### Notification Service Environment Variables

For the separate notification microservice (`services/notification/`):

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=notification-service-group
KAFKA_REMINDERS_TOPIC=reminders
KAFKA_DLQ_TOPIC=reminders.dlq

# Email (SendGrid)
SENDGRID_API_KEY=SG.your-api-key-here
SENDGRID_FROM_EMAIL=noreply@todoapp.com
SENDGRID_FROM_NAME=Todo App Reminders

# Push Notifications (Firebase)
FIREBASE_CREDENTIALS=/path/to/firebase-service-account.json

# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Logging
LOG_LEVEL=INFO
SERVICE_NAME=notification-service

# Retry Configuration
MAX_RETRIES=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
```

### Generating Secrets

```bash
# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SendGrid API key
# Visit: https://app.sendgrid.com/settings/api_keys

# Generate Firebase credentials
# Visit: https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk
```

## Project Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── db.py                # Database connection
│   ├── models.py            # SQLModel entities
│   ├── schemas.py           # Pydantic schemas
│   ├── routes/              # API endpoints
│   │   ├── tasks.py         # Task CRUD
│   │   ├── auth.py          # Authentication
│   │   ├── metrics.py       # Prometheus metrics (Phase V)
│   │   └── internal/        # Internal Dapr endpoints
│   │       └── dapr_routes.py  # Reminder check cron
│   ├── services/            # Business logic
│   │   ├── recurrence_engine.py    # Recurring tasks logic
│   │   └── reminder_service.py     # Reminder logic (Phase V)
│   ├── utils/               # Utilities (Phase V)
│   │   ├── logger.py        # Structured JSON logging
│   │   └── metrics.py       # Prometheus metrics
│   └── middleware/          # Error handling
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── performance/         # Performance tests (Phase V)
│   └── e2e/                 # End-to-end tests
├── dapr-components/         # Local Dapr components
└── alembic/                 # Database migrations

services/notification/       # Notification microservice (Phase V)
├── src/
│   ├── main.py              # FastAPI app
│   ├── kafka_consumer.py    # Kafka consumer
│   ├── dlq_handler.py       # Dead Letter Queue
│   ├── handlers/
│   │   ├── email_handler.py     # SendGrid integration
│   │   ├── push_handler.py      # Firebase integration
│   │   └── in_app_handler.py    # Database storage
│   └── utils/
│       ├── logger.py        # Structured logging
│       └── metrics.py       # Prometheus metrics
└── tests/                   # Notification tests
```

## Tech Stack

**Core**:
- Python 3.13+
- FastAPI
- SQLModel
- PostgreSQL (Neon Serverless)
- UV (package manager)
- Alembic (migrations)

**Phase V - Event-Driven Architecture**:
- **Kafka/Redpanda** - Event streaming platform
- **aiokafka** - Async Kafka client for Python
- **Dapr** - Distributed application runtime (cron, pub/sub, secrets)
- **SendGrid** - Email delivery (notifications)
- **Firebase Cloud Messaging** - Push notifications
- **Structlog** - Structured JSON logging
- **Prometheus** - Metrics collection and monitoring

**Deployment**:
- **Docker** - Container runtime
- **Kubernetes (OKE)** - Container orchestration on Oracle Cloud
- **Helm** - Kubernetes package manager
- **kubectl** - Kubernetes CLI

