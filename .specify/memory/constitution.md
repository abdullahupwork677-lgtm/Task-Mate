<!--
  ==========================================================================
  SYNC IMPACT REPORT
  ==========================================================================
  Version Change: 6.2.0 → 7.0.0 (MAJOR)
  Ratification Date: 2025-12-09
  Last Amended: 2026-02-07

  CHANGES IN THIS VERSION (7.0.0):

  Reason for MAJOR bump:
    - Title changed: "Todo Hackathon Phase IV" → "Todo Hackathon Phase V"
    - Scope expanded from deployment-only to FEATURE + EVENT-DRIVEN + CLOUD
    - Removed Phase IV scope restrictions (NO feature changes)
    - Added 4 new core principles (X, XI, XII, XIII)
    - Redefined acceptance criteria and quality gates entirely

  Added Principles:
    - Principle X: Event-Driven Architecture with Kafka (Redpanda)
    - Principle XI: Dapr Distributed Application Runtime
    - Principle XII: Advanced Task Features (Recurring Tasks + Reminders)
    - Principle XIII: Cloud Kubernetes Deployment (Oracle Cloud/DOKS/GKE/AKS)

  Modified Sections:
    - Title & Scope Statement: Phase IV → Phase V (full feature + cloud)
    - Technology Stack: Added Kafka/Redpanda, Dapr, aiokafka, Oracle Cloud
    - Project Structure: Added dapr/, kafka/, notification-service/, recurring-service/
    - Development Workflow: Added event-driven + advanced features workflow
    - Acceptance Criteria: Full Phase V criteria with advanced features + cloud
    - Phase V Skills: Added message-queue-integration, microservices-patterns, etc.
    - TDD Section: Updated for event-driven and advanced feature testing

  Removed Sections:
    - "CRITICAL SCOPE STATEMENT - PHASE IV" (no longer deployment-only)
    - "What Phase IV DOES NOT DO" restrictions
    - Phase IV-specific Docker/K8s requirement sections (merged into expanded scope)

  Retained (Unchanged):
    - Principles I-IX (Spec-Driven, Code Quality, Storage, REST API,
      Auth, AI Chatbot, Container-First, AIOps, Helm)
    - Reusable Intelligence Skills enforcement
    - Auto Skill Learning (mandatory)
    - Skill Heading Display (mandatory)
    - Digital Agent Factory
    - Governance section

  Templates Requiring Updates:
    ✅ plan-template.md - No changes needed (generic)
    ✅ spec-template.md - No changes needed (generic)
    ✅ tasks-template.md - No changes needed (generic)

  Follow-up TODOs:
    - Create specs/features/recurring-tasks.md
    - Create specs/features/reminders.md
    - Create specs/features/kafka-events.md
    - Create specs/features/dapr-integration.md
    - Create specs/kubernetes/cloud-deployment.md
  ==========================================================================
-->

# Todo Hackathon Phase V Constitution
<!-- Advanced Cloud Deployment + Event-Driven Architecture + Advanced Features -->

## Phase V Scope Statement

**Phase V is FULL-SCOPE: Advanced features, event-driven architecture, Dapr integration, and cloud Kubernetes deployment.**

### What Phase V DOES:

#### Part A: Advanced Features
- ✅ Implement Recurring Tasks (auto-reschedule repeating tasks)
- ✅ Implement Due Dates & Time Reminders (before due date notifications)
- ✅ Implement Intermediate features (Priorities, Tags, Search, Filter, Sort)
- ✅ Extend database models for recurring/reminder fields
- ✅ Extend MCP tools for advanced task operations
- ✅ Update AI agent to handle recurring/reminder natural language commands

#### Part B: Event-Driven Architecture
- ✅ Add Kafka (via Redpanda) for event streaming
- ✅ Implement Dapr for distributed application runtime
- ✅ Create Notification Service (Kafka consumer for reminders)
- ✅ Create Recurring Task Service (Kafka consumer for task recurrence)
- ✅ Publish task events to Kafka topics
- ✅ Dapr Pub/Sub, State, Bindings (cron), Secrets, Service Invocation

#### Part C: Deployment
- ✅ Deploy to Minikube with Dapr sidecar injection
- ✅ Deploy to cloud Kubernetes (Oracle Cloud/DOKS/GKE/AKS)
- ✅ Use Kafka on Redpanda (local Docker + Redpanda Cloud)
- ✅ Set up CI/CD pipeline using GitHub Actions
- ✅ Configure monitoring and logging

### What Phase V Builds On (Phase I-IV - PROTECTED):
- ✅ All Phase I-III features work unchanged
- ✅ All Phase IV infrastructure (Docker, Helm, Minikube) is reused
- ✅ Phase V EXTENDS, never BREAKS existing functionality

---

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
**All features MUST be specification-first:**
- Every feature starts with a complete specification document in `/specs` folder
- Specifications organized by type: features, api, database, ui, kubernetes
- Specifications MUST include user stories and acceptance criteria
- No code implementation without approved specification
- Claude Code MUST reference specifications during implementation
- Specs MUST be updated if requirements change
- Monorepo structure with layered CLAUDE.md files
- **Phase V Addition**: Event-driven and advanced feature specs required

### II. Full-Stack Code Quality Standards
**Code quality is mandatory across the stack:**

**Backend (Python/FastAPI):**
- Follow PEP 8 style guidelines strictly
- Type hints required for all function signatures
- Docstrings for all classes and public methods
- Maximum function length: 50 lines
- Single Responsibility Principle for all functions and classes

**Frontend (Next.js/TypeScript):**
- Follow TypeScript strict mode
- Use ESLint and Prettier configurations
- Server Components by default, Client Components only when needed
- Reusable component patterns
- Descriptive component and variable names

**Event-Driven Services (Phase V):**
- Each Kafka consumer MUST be a standalone service
- Services MUST be idempotent (safe to replay events)
- All event schemas MUST be validated with Pydantic
- Dead letter queues for failed event processing

### III. Persistent Multi-User Storage
**Database persistence with extended schema:**
- All task data stored in Neon Serverless PostgreSQL
- SQLModel ORM for database operations
- User isolation - each user sees only their tasks
- Proper database migrations and schema management (Alembic)
- Connection pooling and efficient queries
- No hardcoded connection strings (use environment variables)
- **Phase V**: Extended schema for recurring tasks, due dates, reminders, priorities, tags
- Database remains external to K8s cluster (Neon Serverless)

### IV. RESTful API Architecture
**Backend API standards:**
- All routes under `/api/` prefix
- Consistent endpoint naming: `/api/{user_id}/tasks`
- Use proper HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Pydantic models for request/response validation
- Proper HTTP status codes (200, 201, 400, 401, 404, 500)
- JWT token authentication on all endpoints
- Comprehensive error handling with HTTPException
- **Phase V**: Extended endpoints for recurring tasks, reminders, priorities, search/filter

### V. Authentication & Security
**Multi-user security is mandatory:**
- Better Auth for user signup/signin
- JWT tokens for API authentication
- Shared secret between frontend and backend (BETTER_AUTH_SECRET)
- User ID verification on every API request
- Task ownership enforcement (users only access their data)
- Token expiry and refresh mechanism
- No exposed secrets in code (use .env files)
- Secrets managed via Kubernetes Secrets
- **Phase V**: Dapr Secrets Management for all credentials

### VI. AI Chatbot Architecture (Phase III - EXTENDED in Phase V)
**Stateless AI-powered chatbot with advanced capabilities:**
- OpenAI Agents SDK for AI logic
- MCP (Model Context Protocol) tools for task operations
- Stateless chat endpoint with database-persisted conversation state
- Conversation/Message models in database
- Agent uses MCP tools to manage tasks
- Natural language task management
- All existing MCP tools: add_task, list_tasks, complete_task, update_task, delete_task
- **Phase V Extensions**:
  - New MCP tools: set_recurring, set_reminder, set_priority, add_tag, search_tasks
  - Agent MUST understand: "Remind me before due date", "Make this weekly"
  - Agent MUST handle: priority assignment, tag management, search queries
  - Agent MUST handle: "Show high priority tasks", "Filter by tag work"

### VII. Container-First Deployment
**All services MUST be containerized:**
- Frontend and backend MUST have production-ready Dockerfiles
- Multi-stage builds for optimized image sizes
- Docker Compose for local multi-container development
- Container images scannable (no P1/P2 vulnerabilities)
- Images tagged with git commit SHA for traceability
- **Phase V**: Additional containers for Notification Service and Recurring Task Service
- **Phase V**: Redpanda container for local Kafka development

**Docker Requirements:**
- Base images: `python:3.13-slim` for backend services, `node:20-alpine` for frontend
- Non-root users in production containers
- `.dockerignore` files to exclude unnecessary files
- Health check endpoints exposed

### VIII. AIOps-Enabled Kubernetes Operations
**AI-assisted Kubernetes operations are MANDATORY:**
- Use `kubectl-ai` for generating K8s manifests
- Use `Kagent` for cluster analysis and optimization
- Use Docker AI Agent (Gordon) for Docker operations (if available)
- AI-generated manifests MUST be reviewed before applying
- All AIOps interactions documented in PHR

### IX. Helm-Based Package Management
**Helm charts for deployment management:**
- Helm charts MUST be created for all services
- Charts MUST support minikube and cloud K8s environments
- Values files for environment-specific configuration
- Chart versioning aligned with application versions
- **Phase V**: Separate Helm charts or subcharts for new services (notification, recurring)
- **Phase V**: Dapr annotations in Helm templates

### X. Event-Driven Architecture with Kafka (NEW - Phase V)
**Kafka (via Redpanda) for decoupled event streaming:**

**Kafka Topics:**

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `task-events` | Chat API (MCP Tools) | Recurring Task Service, Audit | All task CRUD operations |
| `reminders` | Chat API (when due date set) | Notification Service | Scheduled reminder triggers |
| `task-updates` | Chat API | WebSocket Service (future) | Real-time client sync |

**Event Schema (Pydantic-validated):**

| Field | Type | Description |
|-------|------|-------------|
| event_type | string | "created", "updated", "completed", "deleted" |
| task_id | integer | The task ID |
| task_data | object | Full task object |
| user_id | string | User who performed action |
| timestamp | datetime | When event occurred |

**Requirements:**
- Use `aiokafka` for async Kafka producer/consumer
- Local development: Redpanda Docker container (single binary, Kafka-compatible)
- Cloud: Redpanda Cloud Serverless (free tier)
- All events MUST include user_id for isolation
- Consumer services MUST be idempotent
- Dead letter topic for failed messages
- Connection via SASL_SSL for cloud, PLAINTEXT for local

### XI. Dapr Distributed Application Runtime (NEW - Phase V)
**Dapr abstracts infrastructure behind HTTP APIs:**

**Dapr Building Blocks Used:**

| Building Block | Use Case | Component Type |
|----------------|----------|----------------|
| **Pub/Sub** | Kafka abstraction for event publishing | `pubsub.kafka` |
| **State Management** | Conversation state caching | `state.postgresql` |
| **Service Invocation** | Frontend → Backend with retries + mTLS | Built-in |
| **Bindings (Cron)** | Scheduled reminder checks | `bindings.cron` |
| **Secrets Management** | API keys, DB credentials | `secretstores.kubernetes` |

**Requirements:**
- Install Dapr on Minikube: `dapr init -k`
- Each service MUST have Dapr sidecar annotation in K8s deployment
- Publish events via Dapr HTTP API (`http://localhost:3500/v1.0/publish/...`)
- NO direct Kafka library usage in application code (Dapr abstracts it)
- Dapr component YAML files in `dapr/components/` directory
- Cron binding for reminder checks every 5 minutes

**Dapr Sidecar Annotations:**
```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "<service-name>"
  dapr.io/app-port: "<port>"
```

### XII. Advanced Task Features (NEW - Phase V)
**Recurring Tasks and Reminders are the primary new features:**

**Recurring Tasks:**
- Users MUST be able to set tasks as recurring (daily, weekly, monthly, custom)
- When a recurring task is completed, the next occurrence is auto-created
- Recurrence pattern stored in database (`recurrence_pattern` field)
- Recurring Task Service (Kafka consumer) handles auto-creation
- MCP tool: `set_recurring(task_id, pattern)` where pattern = daily/weekly/monthly/custom
- Natural language: "Make this a weekly task", "Repeat every Monday"

**Due Dates & Reminders:**
- Users MUST be able to set due dates with time on tasks
- Reminders MUST be sent BEFORE the due date (configurable: 1hr, 1day, etc.)
- Reminder events published to Kafka `reminders` topic
- Notification Service (Kafka consumer) processes reminders
- Dapr cron binding checks for upcoming reminders every 5 minutes
- MCP tool: `set_reminder(task_id, remind_before)` where remind_before = duration
- Natural language: "Remind me 1 hour before", "Set due date to Friday 5pm"

**Intermediate Features (Priorities, Tags, Search, Filter, Sort):**
- Priority levels: high, medium, low (stored in `priority` field)
- Tags/Categories: work, home, personal, custom (stored as JSON array)
- Search by keyword across title and description
- Filter by status, priority, tag, due date range
- Sort by due_date, priority, created_at, alphabetical

**Database Schema Extensions:**

| Field | Type | Table | Description |
|-------|------|-------|-------------|
| `due_date` | datetime (nullable) | tasks | Task deadline |
| `priority` | string (default: "medium") | tasks | high/medium/low |
| `tags` | JSON array (nullable) | tasks | Category labels |
| `is_recurring` | boolean (default: false) | tasks | Recurring flag |
| `recurrence_pattern` | string (nullable) | tasks | daily/weekly/monthly/custom |
| `recurrence_end_date` | datetime (nullable) | tasks | When recurrence stops |
| `remind_before` | integer (nullable) | tasks | Minutes before due_date |
| `reminder_sent` | boolean (default: false) | tasks | Whether reminder was sent |
| `parent_task_id` | integer (nullable) | tasks | Links recurring instances |

### XIII. Cloud Kubernetes Deployment (NEW - Phase V)
**Production-grade cloud K8s deployment:**

**Target Platforms (choose one or more):**
- Oracle Cloud (OKE) - primary target per user request
- DigitalOcean Kubernetes (DOKS) - $200 credit for 60 days
- Google Cloud (GKE) - $300 credit for 90 days
- Azure (AKS) - $200 credit for 30 days

**Cloud Requirements:**
- All services deployed to cloud K8s cluster
- Dapr installed on cloud cluster with full building blocks
- Kafka via Redpanda Cloud (Serverless free tier)
- CI/CD pipeline via GitHub Actions
- TLS/HTTPS for all public endpoints
- Monitoring and logging configured
- Resource limits and auto-scaling policies
- Ingress controller for routing

**CI/CD Pipeline:**
- GitHub Actions for build, test, deploy
- Automated Docker image builds on push
- Helm-based deployment to cloud K8s
- Staging → Production promotion workflow
- Secret management via GitHub Secrets + K8s Secrets

---

## Technology Stack Requirements

### Existing Technologies (Phase I-IV - EXTENDED)

**Frontend:**
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Better Auth with JWT

**Backend:**
- **Framework**: FastAPI
- **Language**: Python 3.13+
- **ORM**: SQLModel
- **Package Manager**: UV
- **AI Framework**: OpenAI Agents SDK
- **MCP**: Official MCP SDK

**Database:**
- **Service**: Neon Serverless PostgreSQL (EXTERNAL - not in K8s)
- **Schema Management**: Alembic migrations

**Infrastructure (Phase IV):**
- **Container Runtime**: Docker (Docker Desktop)
- **Local K8s**: Minikube
- **Package Manager**: Helm Charts
- **AI DevOps**: kubectl-ai, Kagent

### Phase V Technologies (NEW)

**Event Streaming:**
- **Kafka**: Redpanda (Kafka-compatible, no Zookeeper)
- **Local**: Redpanda Docker container
- **Cloud**: Redpanda Cloud Serverless (free tier)
- **Python Client**: aiokafka (async Kafka client)

**Distributed Runtime:**
- **Dapr**: Distributed Application Runtime v1.14+
- **Dapr CLI**: For local and K8s initialization
- **Dapr Components**: Pub/Sub, State, Bindings, Secrets

**Cloud Kubernetes:**
- **Primary**: Oracle Cloud (OKE) per user requirement
- **Alternative**: DOKS / GKE / AKS
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana (or cloud-native)

**Testing:**
- **Backend**: pytest, pytest-asyncio
- **Frontend**: Jest, React Testing Library
- **Integration**: Docker Compose-based integration tests
- **E2E**: Playwright or Cypress (optional)

---

## Phase V Project Structure Additions

```
/
├── [EXISTING - Phase I-IV]
│   ├── frontend/           # Next.js app (extended with priority/tag UI)
│   ├── backend/            # FastAPI app (extended with advanced features)
│   ├── specs/              # Specifications
│   ├── docker/             # Docker configurations
│   ├── helm/               # Helm charts
│   ├── k8s/                # Raw K8s manifests
│   └── scripts/            # Deployment scripts
│
├── [NEW - Phase V Additions]
│   ├── backend/
│   │   ├── src/
│   │   │   ├── models/         # Extended: recurring, reminder fields
│   │   │   ├── mcp_tools/      # Extended: new MCP tools
│   │   │   ├── events/         # NEW: Kafka event publishing
│   │   │   │   ├── producer.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── __init__.py
│   │   │   └── services/       # Extended: recurring, reminder logic
│   │   └── alembic/
│   │       └── versions/       # NEW: migration for advanced fields
│   │
│   ├── services/               # NEW: Microservices
│   │   ├── notification/       # NEW: Reminder notification consumer
│   │   │   ├── Dockerfile
│   │   │   ├── main.py
│   │   │   ├── requirements.txt
│   │   │   └── tests/
│   │   └── recurring/          # NEW: Recurring task consumer
│   │       ├── Dockerfile
│   │       ├── main.py
│   │       ├── requirements.txt
│   │       └── tests/
│   │
│   ├── dapr/                   # NEW: Dapr configuration
│   │   └── components/
│   │       ├── kafka-pubsub.yaml
│   │       ├── statestore.yaml
│   │       ├── reminder-cron.yaml
│   │       └── kubernetes-secrets.yaml
│   │
│   ├── helm/
│   │   └── todo-app/
│   │       ├── values-cloud.yaml       # NEW: Cloud K8s values
│   │       └── templates/
│   │           ├── notification-deployment.yaml  # NEW
│   │           ├── notification-service.yaml     # NEW
│   │           ├── recurring-deployment.yaml     # NEW
│   │           ├── recurring-service.yaml        # NEW
│   │           ├── redpanda-deployment.yaml      # NEW (local only)
│   │           └── dapr-components.yaml          # NEW
│   │
│   ├── .github/
│   │   └── workflows/
│   │       ├── ci.yaml                 # NEW: CI pipeline
│   │       └── deploy.yaml             # NEW: CD pipeline
│   │
│   ├── docker/
│   │   ├── docker-compose.kafka.yml    # NEW: Redpanda for local dev
│   │   └── docker-compose.full.yml     # NEW: All services together
│   │
│   └── specs/
│       ├── features/
│       │   ├── recurring-tasks.md      # NEW
│       │   ├── reminders.md            # NEW
│       │   ├── priorities-tags.md      # NEW
│       │   └── search-filter-sort.md   # NEW
│       ├── events/
│       │   └── kafka-events.md         # NEW
│       └── kubernetes/
│           └── cloud-deployment.md     # NEW
```

---

## Development Workflow - Phase V

### Phase V Workflow (Spec-Driven + Test-Driven)

1. **Specification Phase**
   - Write specs for each advanced feature (recurring, reminders, priorities, etc.)
   - Write specs for event-driven architecture
   - Write specs for cloud deployment
   - Get specs approved before implementation

2. **Database Extension Phase**
   - Create Alembic migration for new fields
   - Test migration forward and backward
   - Verify existing data is preserved

3. **Advanced Features Phase (TDD)**
   - Write tests FIRST for each new feature
   - Tests MUST FAIL before implementation
   - Implement feature
   - Tests MUST PASS after implementation
   - Order: Priorities/Tags → Search/Filter/Sort → Due Dates → Recurring → Reminders

4. **MCP Tools Extension Phase**
   - Extend MCP tools for new capabilities
   - Test AI agent handles new natural language commands
   - Verify existing MCP tools still work

5. **Event-Driven Phase**
   - Set up Redpanda locally (Docker)
   - Implement Kafka producer in backend
   - Create Notification Service (consumer)
   - Create Recurring Task Service (consumer)
   - Test event flow end-to-end

6. **Dapr Integration Phase**
   - Install Dapr on Minikube
   - Configure Dapr components (Pub/Sub, State, Cron, Secrets)
   - Replace direct Kafka calls with Dapr Pub/Sub
   - Test Dapr cron binding for reminders
   - Verify all services work with Dapr sidecars

7. **Cloud Deployment Phase**
   - Set up cloud K8s cluster (Oracle Cloud/DOKS/GKE/AKS)
   - Install Dapr on cloud cluster
   - Configure Redpanda Cloud
   - Deploy all services via Helm
   - Configure CI/CD pipeline
   - Verify all functionality in cloud

### Quality Gates - Phase V

**Before considering Phase V complete:**
- [ ] All Phase I-IV functionality works unchanged
- [ ] Recurring tasks implemented and tested
- [ ] Due date reminders implemented and tested
- [ ] Priorities, tags, search, filter, sort implemented and tested
- [ ] MCP tools extended for all new features
- [ ] AI chatbot handles all new natural language commands
- [ ] Kafka events publishing on task operations
- [ ] Notification Service consuming and processing reminders
- [ ] Recurring Task Service consuming and auto-creating tasks
- [ ] Dapr installed and configured on Minikube
- [ ] Dapr Pub/Sub working for Kafka abstraction
- [ ] Dapr cron binding triggering reminder checks
- [ ] Cloud K8s cluster provisioned
- [ ] All services deployed to cloud
- [ ] CI/CD pipeline working
- [ ] TLS/HTTPS configured
- [ ] Monitoring and logging configured

---

## Test-Driven Development (TDD) - Phase V

### TDD for Advanced Features

**Write tests FIRST, watch them FAIL, then implement:**

```python
# tests/test_recurring_tasks.py - WRITE FIRST
def test_create_recurring_task():
    """Task with recurrence pattern is created successfully."""
    task = create_task(title="Weekly meeting", recurrence_pattern="weekly")
    assert task.is_recurring is True
    assert task.recurrence_pattern == "weekly"

def test_complete_recurring_creates_next():
    """Completing a recurring task auto-creates next occurrence."""
    task = create_recurring_task(pattern="daily")
    complete_task(task.id)
    next_task = get_next_occurrence(task.id)
    assert next_task is not None
    assert next_task.due_date == task.due_date + timedelta(days=1)

def test_reminder_before_due_date():
    """Reminder event is published before due date."""
    task = create_task(due_date=future_time, remind_before=60)
    reminders = get_pending_reminders()
    assert any(r.task_id == task.id for r in reminders)
```

### TDD for Event-Driven Architecture

```python
# tests/test_kafka_events.py - WRITE FIRST
async def test_task_created_publishes_event():
    """Creating a task publishes event to task-events topic."""
    task = await create_task(title="Test")
    events = await consume_events("task-events", timeout=5)
    assert any(e["event_type"] == "created" and e["task_id"] == task.id
               for e in events)

async def test_notification_service_processes_reminder():
    """Notification service processes reminder events."""
    await publish_reminder_event(task_id=1, remind_at=now())
    # Verify notification service processed it
    result = await get_notification_status(task_id=1)
    assert result.status == "sent"
```

### TDD for Dapr Integration

```python
# tests/test_dapr_integration.py - WRITE FIRST
async def test_dapr_pubsub_publishes():
    """Events published via Dapr Pub/Sub reach Kafka."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3500/v1.0/publish/kafka-pubsub/task-events",
            json={"event_type": "test", "task_id": 999}
        )
        assert response.status_code == 204

async def test_dapr_cron_triggers_reminder_check():
    """Dapr cron binding triggers reminder check endpoint."""
    # Simulate Dapr cron trigger
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/reminder-cron"
        )
        assert response.status_code == 200
```

---

## Phase III+ Requirements: Reusable Intelligence Skills (MANDATORY)

### CRITICAL ENFORCEMENT POLICY - SKILL-FIRST DEVELOPMENT

**THIS IS A NON-NEGOTIABLE REQUIREMENT FROM PROJECT TEACHERS/INSTRUCTORS**

The use of reusable intelligence skills is **MANDATORY** for ALL work. This is a religious enforcement policy.

### ABSOLUTE REQUIREMENTS (MUST FOLLOW)

#### 1. Skills Are MANDATORY, Not Optional
- ✅ **REQUIRED**: Use existing skills for ALL implementation
- ❌ **VIOLATION**: Manual implementation when a skill exists
- ✅ **REQUIRED**: Create new skills for missing capabilities
- ❌ **VIOLATION**: Implementing without skill-based approach

#### 2. Terminal Output Is MANDATORY (RELIGIOUS ENFORCEMENT)

**BEFORE using ANY skill, Claude MUST show this heading:**

```text
╔══════════════════════════════════════════════════════════════╗
║  🔧 USING SKILL: /sp.skill-name                              ║
╠══════════════════════════════════════════════════════════════╣
║  Purpose: [What this skill does]                             ║
║  Constitution Check: ✓ Passed                                ║
╚══════════════════════════════════════════════════════════════╝
```

**AFTER skill completes, show:**

```text
┌──────────────────────────────────────────────────────────────┐
│  ✅ SKILL COMPLETE: /sp.skill-name                           │
├──────────────────────────────────────────────────────────────┤
│  Files Generated/Modified:                                   │
│    - path/to/file1                                           │
│    - path/to/file2                                           │
│  Time: [duration]                                            │
└──────────────────────────────────────────────────────────────┘
```

**If skill is NOT shown before use = VIOLATION**

#### 3. Skill Planning Is MANDATORY
Before implementing ANY work:
1. ✅ **STEP 1**: Analyze tasks
2. ✅ **STEP 2**: Map to existing skills
3. ✅ **STEP 3**: Display skill execution plan
4. ✅ **STEP 4**: Wait for user approval
5. ✅ **STEP 5**: Execute using skills
6. ✅ **STEP 6**: Report usage in PHR

---

### Skills Reference (44+ Available)

**Location**: All skills are in `.claude/skills/` directory

#### Phase V Priority Skills

| Skill | When to Use | Output |
|-------|-------------|--------|
| `/sp.message-queue-integration` | Kafka/Redpanda setup, producers, consumers | Event schemas, consumer services |
| `/sp.microservices-patterns` | Event-driven architecture patterns | Service structure, circuit breakers |
| `/sp.database-schema-expander` | Add recurring/reminder fields | Alembic migration, models |
| `/sp.mcp-tool-builder` | New MCP tools for advanced features | MCP tool implementations |
| `/sp.container-orchestration` | K8s deployment, Helm, Dapr | K8s manifests, Helm charts |
| `/sp.infrastructure-as-code` | Cloud K8s provisioning | IaC templates |
| `/sp.devops-engineer` | CI/CD, Docker, deployment | GitHub Actions, Dockerfiles |
| `/sp.deployment-automation` | Automated deployment | deploy.sh scripts |
| `/sp.production-checklist` | Cloud deployment validation | Checklist report |
| `/sp.backend-developer` | Advanced feature implementation | Backend code |
| `/sp.frontend-developer` | UI for priorities, tags, reminders | Frontend components |
| `/sp.edge-case-tester` | Test recurring/reminder edge cases | Test cases |
| `/sp.qa-engineer` | End-to-end testing | Test suites |

#### Other Available Skills (Full List)

**Workflow & Planning (6):**
- `/sp.specify`, `/sp.plan`, `/sp.tasks`, `/sp.implement`, `/sp.new-feature`, `/sp.skill-learner`

**Core Implementation (6):**
- `/sp.mcp-tool-builder`, `/sp.ai-agent-setup`, `/sp.chatbot-endpoint`, `/sp.conversation-manager`, `/sp.database-schema-expander`, `/sp.robust-ai-assistant`

**Foundation (6):**
- `/sp.jwt-authentication`, `/sp.user-isolation`, `/sp.password-security`, `/sp.pydantic-validation`, `/sp.connection-pooling`, `/sp.transaction-management`

**Role-Based (7):**
- `/sp.backend-developer`, `/sp.frontend-developer`, `/sp.fullstack-architect`, `/sp.database-engineer`, `/sp.devops-engineer`, `/sp.security-engineer`, `/sp.uiux-designer`

**Quality & Testing (3):**
- `/sp.edge-case-tester`, `/sp.ab-testing`, `/sp.qa-engineer`

**Production & Deployment (5):**
- `/sp.performance-logger`, `/sp.structured-logging`, `/sp.deployment-automation`, `/sp.production-checklist`, `/sp.vercel-deployer`

**Modern Architecture (10):**
- `/sp.caching-strategy`, `/sp.api-contract-design`, `/sp.message-queue-integration`, `/sp.observability-apm`, `/sp.microservices-patterns`, `/sp.infrastructure-as-code`, `/sp.feature-flags-management`, `/sp.websocket-realtime`, `/sp.graphql-api`, `/sp.container-orchestration`

---

## AUTO SKILL LEARNING - MANDATORY (NON-NEGOTIABLE)

### CRITICAL: Feature is NOT Complete Until Skill-Learner Runs

**This is RELIGIOUS enforcement. A feature is INCOMPLETE without skill learning.**

### Auto-Trigger Condition

`/sp.skill-learner` MUST be **AUTOMATICALLY** called when:
1. ✅ Feature implementation is complete
2. ✅ User has tested the feature and is satisfied
3. ✅ System tests have passed

**The system (Claude) MUST auto-invoke skill-learner without user asking for it.**

### Complete Feature Implementation Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: SKILL PLANNING (Before implementation)                 │
├─────────────────────────────────────────────────────────────────┤
│  📋 Feature: [Feature Name]                                     │
│  Skills Required: [List skills to use]                          │
│  Waiting for approval... ✋                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: SKILL EXECUTION (During implementation)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ╔═══════════════════════════════════════════════════════════╗  │
│  ║  🔧 USING SKILL: /sp.skill-name                           ║  │
│  ╠═══════════════════════════════════════════════════════════╣  │
│  ║  Purpose: [What this skill does]                          ║  │
│  ║  Constitution Check: ✓ Passed                             ║  │
│  ╚═══════════════════════════════════════════════════════════╝  │
│                                                                 │
│  [... skill execution happens here ...]                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ✅ SKILL COMPLETE: /sp.skill-name                        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  Files Generated:                                         │  │
│  │    - path/to/file1                                        │  │
│  │    - path/to/file2                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: FEATURE TESTING (TDD - Tests written FIRST)            │
├─────────────────────────────────────────────────────────────────┤
│  🧪 Running tests...                                            │
│  ✅ All tests passed                                            │
│  👤 User verification: "Feature works correctly"                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: AUTO SKILL LEARNING (MANDATORY - AUTO-TRIGGERED)       │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Skill Learning Session (AUTO-TRIGGERED)                     │
│  Feature Completed: [Feature Name]                              │
│  Skills Used: [list]                                            │
│  Learnings Captured: [list]                                     │
│  Skills Updated: [list]                                         │
│  🧠 Skills Evolution Complete                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  ✅ FEATURE FULLY COMPLETE                                      │
│  (Only after skill-learner has run)                             │
└─────────────────────────────────────────────────────────────────┘
```

### What Skill-Learner MUST Capture

| Category | Question | Action |
|----------|----------|--------|
| **Bug Fixes** | Did you fix any bugs during implementation? | Add solution pattern to relevant skill |
| **Edge Cases** | Did you discover edge cases not in skill? | Add test case to skill |
| **Patterns** | Did you discover a better approach? | Document pattern in skill |
| **Code Templates** | Did you write reusable code? | Add as template to skill |
| **Corrections** | Was original skill guidance wrong? | Correct the skill |
| **Checklists** | What steps should be remembered? | Add checklist items |

### Skill Update Targets (Phase V Focus)

| Skill Used | Update With |
|------------|-------------|
| `/sp.message-queue-integration` | Redpanda setup issues, Kafka config patterns |
| `/sp.microservices-patterns` | Event schema issues, consumer idempotency patterns |
| `/sp.database-schema-expander` | Migration rollback issues, new field patterns |
| `/sp.mcp-tool-builder` | Tool parameter issues, new tool patterns |
| `/sp.container-orchestration` | Dapr sidecar issues, Helm chart patterns |
| `/sp.infrastructure-as-code` | Cloud K8s provisioning issues |
| `/sp.devops-engineer` | CI/CD patterns, GitHub Actions issues |

### Auto-Trigger Rules

**Claude MUST auto-invoke `/sp.skill-learner` when:**

1. **User says feature is working:**
   - "Chal gaya" / "It's working"
   - "Test kar liya" / "Tested it"
   - "Feature complete ho gaya"
   - "All good" / "Sab theek hai"

2. **Tests pass:**
   - All unit tests pass
   - Integration tests pass
   - Manual verification successful

3. **Implementation complete:**
   - All tasks in tasks.md marked done
   - No pending items

---

## Digital Agent Factory (17 FTE Agents)

### Phase V Priority Agents

| Agent | Skills | Use For |
|-------|--------|---------|
| **backend-developer** | 6 skills | Advanced features, MCP tools, Kafka |
| **devops-engineer** | 6 skills | Docker, K8s, Helm, CI/CD, Dapr |
| **fullstack-architect** | 8 skills | Event-driven architecture design |
| **cloud-architect** | 7 skills | Cloud K8s, Dapr, Redpanda Cloud |
| **database-engineer** | 5 skills | Schema extensions, migrations |
| **frontend-developer** | 5 skills | Priority/tag/search UI components |

### All Available Agents

**Orchestration (1):** orchestrator
**Backend (5):** backend-developer, database-engineer, security-engineer, qa-engineer, devops-engineer
**Frontend (3):** frontend-developer, uiux-designer, vercel-deployer
**Cross-Cutting (2):** fullstack-architect, github-specialist
**Enterprise (5):** data-engineer, technical-writer, cloud-architect, api-architect, product-manager

---

## Phase V Acceptance Criteria

**Phase V is complete when:**

### Part A: Advanced Features
1. ✅ Recurring tasks: create, complete (auto-creates next), cancel recurrence
2. ✅ Due dates: set, update, remove due dates on tasks
3. ✅ Reminders: set remind_before duration, notification sent before due
4. ✅ Priorities: set high/medium/low, filter by priority
5. ✅ Tags: add/remove tags, filter by tag
6. ✅ Search: keyword search across title and description
7. ✅ Filter: by status, priority, tag, due date range
8. ✅ Sort: by due_date, priority, created_at, alphabetical
9. ✅ MCP tools extended for all new features
10. ✅ AI chatbot handles all new natural language commands
11. ✅ Database migration created and tested
12. ✅ All existing Phase I-IV functionality works unchanged

### Part B: Event-Driven Architecture
13. ✅ Redpanda running locally (Docker)
14. ✅ Task events published to Kafka on CRUD operations
15. ✅ Notification Service consuming reminder events
16. ✅ Recurring Task Service consuming task-completed events
17. ✅ Dapr installed on Minikube
18. ✅ Dapr Pub/Sub working for Kafka
19. ✅ Dapr cron binding for scheduled reminder checks
20. ✅ Dapr Secrets Management for credentials
21. ✅ All services deployed to Minikube with Dapr sidecars

### Part C: Cloud Deployment
22. ✅ Cloud K8s cluster provisioned (Oracle Cloud/DOKS/GKE/AKS)
23. ✅ Dapr installed on cloud cluster
24. ✅ Redpanda Cloud configured
25. ✅ All services deployed to cloud
26. ✅ CI/CD pipeline via GitHub Actions
27. ✅ TLS/HTTPS configured
28. ✅ Monitoring and logging configured
29. ✅ README includes cloud setup instructions

### Verification Tests

```bash
# After deployment, verify all functionality:
# Phase I-III (existing)
# 1. User can sign up/login
# 2. User can create tasks
# 3. User can list tasks
# 4. User can update tasks
# 5. User can delete tasks
# 6. User can complete tasks
# 7. AI chatbot responds to natural language
# 8. All existing MCP tools work via chat
#
# Phase V (new)
# 9. User can set task priority (high/medium/low)
# 10. User can add/remove tags
# 11. User can search tasks by keyword
# 12. User can filter tasks by status/priority/tag
# 13. User can sort tasks by various criteria
# 14. User can set due dates on tasks
# 15. User can set reminders (before due date)
# 16. User receives reminder notifications
# 17. User can create recurring tasks
# 18. Completing recurring task auto-creates next occurrence
# 19. AI chatbot handles: "Make this weekly"
# 20. AI chatbot handles: "Remind me 1 hour before"
# 21. AI chatbot handles: "Show high priority tasks"
# 22. AI chatbot handles: "Filter by tag work"
# 23. Kafka events flow correctly
# 24. Dapr services work with sidecars
# 25. Cloud deployment accessible via public URL
```

---

## Governance

### Constitution Authority
- This constitution supersedes all other development practices
- Phase V is FULL-SCOPE: features + event-driven + cloud
- All changes MUST use skill-based approach
- Deviations require documented justification

### Amendment Procedure
1. Propose amendment with rationale
2. Review against project goals
3. Update constitution with proper versioning
4. Document in ADR if architecturally significant

### Version Policy
- **MAJOR**: Breaking changes to principles or scope redefinition
- **MINOR**: New sections added or materially expanded guidance
- **PATCH**: Clarifications, typo fixes, non-semantic refinements

### Compliance Review
- Constitution check MUST pass before any implementation
- Every PR MUST reference which principles it satisfies
- Quarterly review of principles for relevance (or per-phase)

---

**Version**: 7.0.0 | **Ratified**: 2025-12-09 | **Last Amended**: 2026-02-07 (Phase V: Advanced Features + Event-Driven + Cloud Deployment)
