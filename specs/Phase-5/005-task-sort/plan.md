# Implementation Plan: Task Sorting

**Branch**: `005-task-sort` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-task-sort/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Task Sorting enables users to organize their task list by different criteria (due date, priority, created date, alphabetically) for better task management. The feature uses database-level SQL ORDER BY operations for performance, supports both ascending and descending directions, and integrates with existing search/filter functionality. Default sort is created_at descending (newest first), with visual indicators showing active sort field and direction. AI chatbot recognizes natural language sort commands like "sort by due date" or "show tasks by priority".

## Technical Context

**Language/Version**: Python 3.13+ (Backend), TypeScript (Frontend Next.js 14)
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL (Neon Serverless), OpenAI Agents SDK, MCP SDK, Next.js 14, Tailwind CSS
**Storage**: Neon Serverless PostgreSQL (external to K8s) with Alembic migrations
**Testing**: pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E)
**Target Platform**: Linux server (Docker + Kubernetes), Modern browsers (Next.js SSR)
**Project Type**: Web application (separate backend + frontend)
**Performance Goals**: < 200ms for sorting up to 1,000 tasks, < 500ms for 10,000 tasks, < 2 seconds total user experience
**Constraints**: Database-level sorting only (no in-memory sorting), session-based sort persistence, works with existing search/filter results
**Scale/Scope**: Multi-user system with user isolation, existing database schema (no schema changes needed), MCP tool extension

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Spec-Driven Development ✅
- ✅ Complete specification exists: `specs/005-task-sort/spec.md`
- ✅ User stories and acceptance criteria defined
- ✅ No code implementation before approved specification

### Principle II: Code Quality Standards ✅
- ✅ Backend: PEP 8, type hints, docstrings, max 50 lines per function
- ✅ Frontend: TypeScript strict mode, ESLint, Server Components by default
- ✅ No quality violations expected (simple sorting feature)

### Principle III: Persistent Multi-User Storage ✅
- ✅ Uses existing Neon PostgreSQL database
- ✅ No schema changes required (all sortable fields exist: due_date, priority, created_at, title)
- ✅ User isolation enforced (sort only user's own tasks)

### Principle IV: RESTful API Architecture ✅
- ✅ Existing list_tasks endpoint will be extended with sort parameters
- ✅ Pydantic validation for sort_by and sort_direction
- ✅ JWT authentication on endpoint
- ✅ Proper HTTP status codes

### Principle V: Authentication & Security ✅
- ✅ Existing JWT authentication reused
- ✅ User isolation enforced (sort only user's tasks)
- ✅ No new security surface area

### Principle VI: AI Chatbot Architecture ✅
- ✅ MCP tool `list_tasks` will be extended with sort parameters
- ✅ Agent must understand: "sort by due date", "show tasks by priority"
- ✅ Natural language command parsing

### Principle VII: Container-First Deployment ✅
- ✅ Existing Docker containers work unchanged
- ✅ No new containers needed

### Principle VIII: AIOps-Enabled K8s ✅
- ✅ No K8s changes needed (backend changes only)

### Principle IX: Helm-Based Package Management ✅
- ✅ Existing Helm charts work unchanged

### Principles X-XIII: Phase V Event-Driven Architecture N/A
- ⚪ NO Kafka/Dapr needed - Sorting is synchronous database operation
- ⚪ NO new microservices needed
- ⚪ NO cloud deployment changes

### ✅ GATE RESULT: PASSED
**Rationale:** Task Sorting is a simple database-level operation (SQL ORDER BY) with no schema changes, no infrastructure changes, and no event-driven requirements. All existing principles are maintained.

## Project Structure

### Documentation (this feature)

```text
specs/005-task-sort/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 - Technical research
├── data-model.md        # Phase 1 - Data structures (N/A - no schema changes)
├── quickstart.md        # Phase 1 - Integration guide
├── contracts/           # Phase 1 - API contracts
│   ├── list_tasks.json  # Updated MCP tool contract with sort parameters
│   └── GET_tasks.yaml   # Updated REST endpoint with sort query params
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 - Implementation tasks (via /sp.tasks)
```

### Source Code (repository root)

**Web Application Structure:**

```text
backend/
├── src/
│   ├── models/          # NO CHANGES - Existing Task model has sortable fields
│   │   └── models.py    # Task model already has: due_date, priority, created_at, title
│   ├── services/        # EXTEND - Add sorting logic
│   │   └── task_service.py  # Add sort_tasks() method with SQL ORDER BY
│   ├── routes/          # EXTEND - Add sort query parameters
│   │   └── tasks.py     # Extend GET /api/{user_id}/tasks with sort_by, sort_direction
│   ├── schemas/         # EXTEND - Add sort DTOs
│   │   └── task_schemas.py  # Add SortParams DTO (sort_by, sort_direction)
│   ├── mcp_tools/       # EXTEND - Add sort parameters to list_tasks
│   │   └── list_tasks.py    # Extend list_tasks MCP tool with sort support
│   └── ai/              # EXTEND - Update agent prompt for sort commands
│       └── agent.py     # Add natural language sort examples
└── tests/
    ├── unit/            # NEW - Sort logic tests
    │   └── test_task_sort.py
    ├── integration/     # NEW - API + MCP tool tests
    │   └── test_sort_integration.py
    └── e2e/             # NEW - Full flow tests
        └── test_sort_e2e.py

frontend/
├── src/
│   ├── components/      # NEW - Sort UI components
│   │   └── TaskSort.tsx         # Sort dropdown/column headers
│   ├── app/             # EXTEND - Add sort state management
│   │   └── tasks/
│   │       └── page.tsx         # Add sort state and handlers
│   ├── hooks/           # NEW - Sort custom hooks
│   │   └── useTaskSort.ts       # Sort state management hook
│   └── lib/             # EXTEND - Add sort API calls
│       └── api.ts               # Add sort params to getTasks()
└── tests/
    └── components/      # NEW - Sort component tests
        └── TaskSort.test.tsx
```

**Structure Decision**: Web application with separate backend and frontend. Backend modifications are minimal (extend existing service/routes/MCP tools). Frontend adds new sort UI components. No database schema changes needed - all sortable fields already exist (due_date, priority, created_at, title).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected.** All constitution principles are satisfied. Feature uses existing infrastructure with minimal extensions.
