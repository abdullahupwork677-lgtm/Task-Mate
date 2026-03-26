# Implementation Plan: Task Search & Advanced Filtering

**Branch**: `004-search-filter` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-search-filter/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Task Search & Advanced Filtering enables users to search tasks by keyword (title/description) and filter by multiple criteria (status, priority, tags, due date) with AND/OR logic. The feature uses PostgreSQL ILIKE for case-insensitive substring search, composite indexes for performance, dynamic WHERE clause building for flexible filtering, and debounced input (300ms) for optimal UX. AI chatbot recognizes natural language search commands ("search grocery in incomplete work tasks") using regex patterns + GPT-4 fallback. Keyword highlighting in search results, pagination for large lists, and < 500ms response time for 10,000 tasks.

## Technical Context

**Language/Version**: Python 3.13+ (Backend), TypeScript (Frontend Next.js 14)
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL (ILIKE + indexes), OpenAI Agents SDK, MCP SDK, Next.js 14, React, Tailwind CSS
**Storage**: Neon Serverless PostgreSQL with composite indexes for efficient filtering (no schema changes, existing fields used)
**Testing**: pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E)
**Target Platform**: Linux server (Docker + Kubernetes), Modern browsers (Next.js SSR)
**Project Type**: Web application (separate backend + frontend)
**Performance Goals**: < 500ms search results for 1,000 tasks, < 1s for 10,000 tasks, debounced input (300ms), pagination for scalability
**Constraints**: PostgreSQL ILIKE (no full-text extension), AND logic between filter types, OR logic within tag filters, user isolation enforced
**Scale/Scope**: Multi-user system, up to 10,000 tasks per user, 1 new MCP tool (search_tasks), 5 new composite indexes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Spec-Driven Development ✅
- ✅ Complete specification exists: `specs/004-search-filter/spec.md`
- ✅ User stories and acceptance criteria defined (6 user stories, 18 functional requirements)
- ✅ No code implementation before approved specification

### Principle II: Code Quality Standards ✅
- ✅ Backend: PEP 8, type hints, docstrings, max 50 lines per function
- ✅ Frontend: TypeScript strict mode, ESLint, React component patterns
- ✅ Dynamic query building with SQLModel, proper index usage

### Principle III: Persistent Multi-User Storage ✅
- ✅ Uses existing Neon PostgreSQL database
- ✅ NO schema changes required (all fields exist: title, description, completed, priority, tags, due_date)
- ✅ 5 NEW composite indexes for efficient filtering
- ✅ User isolation enforced (user_id in WHERE clause)

### Principle IV: RESTful API Architecture ✅
- ✅ New endpoint: GET /api/tasks/search with query parameters
- ✅ Pydantic validation for search parameters
- ✅ JWT authentication on all endpoints
- ✅ Proper HTTP status codes

### Principle V: Authentication & Security ✅
- ✅ Existing JWT authentication reused
- ✅ User isolation enforced (users only search their own tasks)
- ✅ Input validation (keyword max 200 chars, enum validation for filters)
- ✅ No SQL injection risk (parameterized queries, SQLModel ORM)

### Principle VI: AI Chatbot Architecture ✅
- ✅ 1 NEW MCP tool: `search_tasks` with all filter parameters
- ✅ Agent must understand: "search grocery in incomplete work tasks", "find overdue high priority items"
- ✅ Natural language parsing with regex + GPT-4 fallback

### Principle VII: Container-First Deployment ✅
- ✅ Existing Docker containers work with minor changes (new migration for indexes)
- ✅ No new containers needed

### Principle VIII: AIOps-Enabled K8s ✅
- ✅ No K8s changes needed (backend/frontend changes only)

### Principle IX: Helm-Based Package Management ✅
- ✅ Existing Helm charts work unchanged

### Principles X-XIII: Phase V Event-Driven Architecture N/A
- ⚪ NO Kafka/Dapr needed - Search/filter are synchronous query operations
- ⚪ NO new microservices needed
- ⚪ NO cloud deployment changes

### ✅ GATE RESULT: PASSED
**Rationale:** Task Search & Filtering is a pure query feature (no state changes). Uses existing database fields with new composite indexes for performance. Single search_tasks MCP tool with flexible parameters. No event-driven requirements, no infrastructure changes. PostgreSQL ILIKE + indexes handle < 10,000 tasks efficiently.

## Project Structure

### Documentation (this feature)

```text
specs/004-search-filter/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   └── task_service.py       # EXTEND: search_and_filter_tasks method
│   ├── api/
│   │   └── tasks.py              # EXTEND: GET /tasks/search endpoint
│   ├── mcp_tools/
│   │   └── search_tasks.py       # NEW: search_tasks MCP tool
│   ├── schemas/
│   │   └── search.py             # NEW: SearchRequest, SearchResponse schemas
│   └── alembic/
│       └── versions/
│           └── add_search_indexes.py  # NEW: Add 5 composite indexes
└── tests/
    ├── unit/
    │   ├── test_search_parsing.py
    │   └── test_query_builder.py
    ├── integration/
    │   ├── test_search_api.py
    │   └── test_combined_filters.py
    └── e2e/
        └── test_search_workflow.py

frontend/
├── src/
│   ├── components/
│   │   ├── SearchInput.tsx       # NEW: Debounced search input
│   │   ├── FilterBar.tsx         # NEW: Status/priority/tags/date filters
│   │   ├── HighlightedText.tsx   # NEW: Keyword highlighting
│   │   └── TaskList.tsx          # EXTEND: Display search results with count
│   ├── hooks/
│   │   ├── useDebounce.ts        # NEW: Debounce hook (300ms)
│   │   └── useSearch.ts          # NEW: Search state management
│   └── types/
│       └── search.ts             # NEW: SearchFilters, SearchResults types
└── tests/
    ├── unit/
    │   ├── SearchInput.test.tsx
    │   ├── FilterBar.test.tsx
    │   └── HighlightedText.test.tsx
    └── integration/
        └── SearchWorkflow.test.tsx
```

**Structure Decision**: Web application (Option 2) with separate backend and frontend. Backend implements efficient search with PostgreSQL ILIKE + composite indexes, creates search_tasks MCP tool with all filter parameters. Frontend creates debounced SearchInput, FilterBar for multi-criteria filtering, and HighlightedText for keyword highlighting. No schema changes, only 5 new indexes for performance.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected.** Constitution Check passed with all 13 principles satisfied. This feature:
- Uses existing backend/frontend structure (no new projects)
- Leverages existing database fields (no schema changes, only indexes)
- Single new MCP tool with flexible parameters
- No event-driven complexity (synchronous query operations)
- No infrastructure changes required
- PostgreSQL ILIKE sufficient for < 10,000 tasks (no full-text extension needed)
