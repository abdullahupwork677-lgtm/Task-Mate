# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 5: Recurring Tasks (Event-Driven Architecture)

#### Added
- **Recurring Tasks Feature**
  - Automatic task recurrence on completion
  - Support for daily, weekly, monthly, and yearly patterns
  - Custom intervals: "every N days", "every N weeks", "every N months"
  - Optional recurrence end dates
  - Auto-create next occurrence when recurring task is completed
  - Parent task tracking via `parent_task_id`

- **MCP Tools (Extended)**
  - `set_recurring` - Set existing task as recurring or cancel recurrence
  - `add_task` (extended) - Create recurring tasks in one command
  - `complete_task` (extended) - Auto-creates next occurrence for recurring tasks

- **Database Schema (6 new fields)**
  - `is_recurring` (Boolean) - Recurring task flag
  - `recurrence_pattern` (String) - Pattern: daily/weekly/monthly/yearly/custom
  - `recurrence_end_date` (DateTime) - Optional stop date
  - `parent_task_id` (Integer) - Links to parent task
  - `due_date` (DateTime) - Task due date (base for next occurrence)
  - `priority` (String) - Task priority (high/medium/low)

- **Database Indexes**
  - Composite index: `ix_tasks_user_recurring` on (user_id, is_recurring)
  - Unique constraint: `ix_tasks_parent_due_unique` on (parent_task_id, due_date)

- **Recurrence Engine**
  - Core date calculation service (`backend/src/services/recurrence_engine.py`)
  - Month-end edge case handling (Jan 31 → Feb 28/29)
  - Leap year support
  - Pattern validation and parsing
  - Natural language date support

- **AI Agent Natural Language**
  - "Add a daily task 'X'" → creates recurring task
  - "Make task 5 repeat weekly" → sets recurrence
  - "Stop repeating task 3" → cancels recurrence
  - Supports natural language end dates: "until next year", "for 3 months"

- **Frontend Display**
  - Blue recurrence badge (🔄 + pattern text)
  - Shows recurrence pattern on task items
  - Responsive mobile/desktop layout
  - TypeScript type definitions updated

- **Documentation**
  - API documentation (`backend/docs/api.md`)
  - User guide (`docs/user-guide-recurring.md`)
  - Quickstart guide (`specs/Phase-5/001-recurring-tasks/quickstart.md`)
  - Demo documentation (`specs/Phase-5/001-recurring-tasks/DEMO.md`)

#### Changed
- `add_task` MCP tool: Added `recurrence_pattern` and `recurrence_end_date` parameters
- `complete_task` MCP tool: Returns `next_occurrence` info when recurring task completed
- Task model: Extended with 6 new recurring-related fields
- Frontend Task type: Added optional recurrence fields
- Backend README: Updated with recurring tasks documentation

#### Fixed
- Edge case: Prevent re-completing already completed tasks
- Edge case: Handle tasks with no due_date (fallback to completion timestamp)
- Edge case: Month-end date arithmetic (using `dateutil.relativedelta`)
- Idempotency: Unique constraint prevents duplicate next occurrences

#### Security
- User isolation maintained for all recurring operations
- Pattern validation prevents injection attacks
- End date validation (must be in future)
- Recurrence pattern whitelist validation

#### Performance
- `calculate_next_due_date()`: < 10ms (target: < 10ms) ✅
- `complete_task()` with recurrence: ~150ms (target: < 200ms) ✅
- List 1000 recurring tasks: ~30ms (target: < 50ms) ✅
- Database indexes ensure efficient queries

#### Testing
- 161 total tests (all passing)
  - 49 unit tests (pattern validation, date calculation)
  - 77 integration tests (MCP tools, database operations)
  - 20 E2E tests (AI agent natural language)
  - 15 edge case tests (rapid completion, concurrency, month-end)
- Test coverage: > 95% for recurring features
- Edge case coverage: 15 scenarios validated

---

### Phase 3: AI-Powered Todo Chatbot

#### Added
- **AI Chat Endpoint** (`POST /api/{user_id}/chat`)
  - Stateless conversational interface for task management
  - Natural language processing via OpenAI Agents SDK
  - Conversation history persistence with user isolation
  - Support for multi-turn conversations

- **MCP Tools** (Model Context Protocol)
  - `add_task` - Create tasks via natural language
  - `list_tasks` - View tasks with status filtering
  - `complete_task` - Mark tasks as complete
  - `update_task` - Modify task details
  - `delete_task` - Remove tasks

- **Conversation Management**
  - Database models for Conversations and Messages
  - ConversationService for CRUD operations
  - Message history with chronological ordering
  - Automatic timestamp tracking

- **AI Agent Infrastructure**
  - OpenAI Agents SDK integration
  - Tool registration and orchestration
  - System prompt for task management assistant
  - Agent runner with error handling

- **Performance & Observability**
  - Production-ready connection pooling (pool_size=10, max_overflow=20)
  - Performance logging utilities with execution time tracking
  - Structured JSON logging for all services
  - Health endpoint with connection pool status
  - Load testing framework (target: p95 < 3s)

- **Error Handling & Resilience**
  - OpenAI API timeout handling with user-friendly messages
  - Database retry logic with exponential backoff
  - Input sanitization (message length limit: 10,000 chars)
  - Comprehensive error logging with context

#### Changed
- Database connection pool settings optimized for production load
- Health endpoint enhanced with pool metrics
- All service methods instrumented with performance logging
- Logging format changed to structured JSON for aggregation tools

#### Security
- User isolation enforced across all chat operations
- Path user_id validation against JWT claims
- Input sanitization for chat messages
- Cross-user data leakage prevention

#### Performance
- Connection pooling: 30 total connections (10 baseline + 20 overflow)
- Performance targets: p95 < 3s for chat endpoint, p95 < 100ms for DB queries
- Structured logging with minimal performance impact
- Efficient conversation history pagination (limit: 50 messages)

## [0.1.0] - 2024-12-30

### Phase 2: Backend API Foundation

#### Added
- FastAPI application with CORS configuration
- PostgreSQL database with SQLModel ORM
- Alembic database migrations
- User and Task models with relationships
- JWT authentication system
- Protected task API endpoints (CRUD operations)
- Health check endpoint
- Global error handling middleware
- Environment-based configuration

#### Security
- Password hashing with bcrypt
- JWT token-based authentication
- User isolation for all task operations
- Input validation with Pydantic

---

## Deployment Notes

### Phase 5 Requirements
- Python 3.13+
- PostgreSQL 14+
- Node.js 18+ (frontend)
- All Phase 3 requirements

### New Dependencies (Phase 5)
**Backend:**
- `python-dateutil>=2.8.2` - Date arithmetic for recurrence
- `dateparser>=1.2.0` - Natural language date parsing

**Frontend:**
- No new dependencies (TypeScript types extended)

### Database Migration (Phase 5)
```bash
# Run Phase 5 migrations
cd backend
alembic upgrade head

# Verify new columns added
psql -d your_database -c "\d tasks"

# Expected: is_recurring, recurrence_pattern, recurrence_end_date,
#           parent_task_id, due_date, priority columns
```

### Configuration (Phase 5)
```bash
# No new environment variables required
# Recurring tasks work out of the box with existing setup
```

### Testing Phase 5
```bash
# Run all Phase 5 tests
cd backend
source venv/bin/activate
pytest tests/ -k recurring -v

# Run specific test suites
pytest tests/unit/test_recurrence_engine.py -v
pytest tests/integration/test_set_recurring.py -v
pytest tests/integration/test_complete_task.py -v
pytest tests/integration/test_edge_cases.py -v
pytest tests/e2e/test_recurring_chatbot.py -v

# With coverage
pytest tests/ -k recurring --cov=src --cov-report=html
```

### Upgrading from Phase 3 to Phase 5
1. Pull latest code
2. Install new dependencies: `pip install -r requirements.txt`
3. Run Alembic migration: `alembic upgrade head`
4. Restart backend server
5. No frontend changes needed (backward compatible)

### Rollback (if needed)
```bash
# Rollback Phase 5 migration
alembic downgrade -1

# This removes recurrence fields but preserves existing tasks
# Note: Recurring task data will be lost
```

---

### Phase 3 Requirements
- Python 3.13+
- PostgreSQL 14+
- OpenAI API key
- Environment variables (see `.env.example`)

### New Dependencies
- `openai>=1.12.0` - OpenAI Agents SDK
- `mcp>=0.1.0` - Model Context Protocol
- `python-json-logger>=2.0.7` - Structured logging

### Migration
```bash
# Run Phase 3 migrations
alembic upgrade head

# Verify conversations and messages tables created
psql -d your_database -c "\dt"
```

### Configuration
```bash
# Required environment variables
OPENAI_API_KEY=sk-...
OPENAI_AGENT_MODEL=gpt-4o

# Optional performance tuning
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

---

**Contributors**: AI Chatbot Team (Phase 3 Hackathon)
**License**: MIT
