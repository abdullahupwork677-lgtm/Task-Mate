# Implementation Plan: Task Tags & Categories

**Branch**: `003-task-tags` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-task-tags/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Task Tags & Categories enables users to organize tasks with custom labels (work, home, personal, shopping, urgent) for easy grouping and filtering. The feature adds a JSON array field to store tags, extends MCP tools for tag management, and implements color-coded visual badges with deterministic hash-based color generation. AI chatbot recognizes natural language tag commands ("add task buy groceries, tags: shopping, urgent"). Tags are case-insensitive, user-specific, and support filtering by single or multiple tags with OR logic.

## Technical Context

**Language/Version**: Python 3.13+ (Backend), TypeScript (Frontend Next.js 14)
**Primary Dependencies**: FastAPI, SQLModel, PostgreSQL (Neon Serverless), OpenAI Agents SDK, MCP SDK, Next.js 14, Tailwind CSS, React
**Storage**: Neon Serverless PostgreSQL with JSONB field for tags array, GIN index for filtering
**Testing**: pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E)
**Target Platform**: Linux server (Docker + Kubernetes), Modern browsers (Next.js SSR)
**Project Type**: Web application (separate backend + frontend)
**Performance Goals**: < 100ms for tag filtering, < 1ms for color generation, < 5 seconds for tag addition via chatbot
**Constraints**: Hash-based deterministic colors, case-insensitive tags, user isolation enforced, JSON array storage
**Scale/Scope**: Up to 100 unique tags per user, multi-user system, 6 MCP tools (3 new + 3 extended)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Spec-Driven Development ✅
- ✅ Complete specification exists: `specs/003-task-tags/spec.md`
- ✅ User stories and acceptance criteria defined (5 user stories, 18 functional requirements)
- ✅ No code implementation before approved specification

### Principle II: Code Quality Standards ✅
- ✅ Backend: PEP 8, type hints, docstrings, max 50 lines per function
- ✅ Frontend: TypeScript strict mode, ESLint, React component patterns
- ✅ Hash function deterministic, tag normalization consistent

### Principle III: Persistent Multi-User Storage ✅
- ✅ Uses existing Neon PostgreSQL database
- ✅ Schema change required: Add `tags` JSONB column with default `[]`
- ✅ GIN index for efficient tag filtering
- ✅ User isolation enforced (tags filtered by user_id)

### Principle IV: RESTful API Architecture ✅
- ✅ Extend existing endpoints with tags support
- ✅ Pydantic validation for tag arrays
- ✅ JWT authentication on all endpoints
- ✅ Proper HTTP status codes

### Principle V: Authentication & Security ✅
- ✅ Existing JWT authentication reused
- ✅ User isolation enforced (users only manage their own tags)
- ✅ Input validation (alphanumeric + basic punctuation, max 50 chars)
- ✅ No XSS risk (tags sanitized on display)

### Principle VI: AI Chatbot Architecture ✅
- ✅ 3 NEW MCP tools: `add_tag`, `remove_tag`, `list_tags`
- ✅ 3 EXTENDED MCP tools: `add_task`, `update_task`, `list_tasks`
- ✅ Agent must understand: "add task X, tags: A, B" and "add tag X to task 5"
- ✅ Natural language parsing with regex + GPT-4 fallback

### Principle VII: Container-First Deployment ✅
- ✅ Existing Docker containers work with minor changes (new migration)
- ✅ No new containers needed

### Principle VIII: AIOps-Enabled K8s ✅
- ✅ No K8s changes needed (backend/frontend changes only)

### Principle IX: Helm-Based Package Management ✅
- ✅ Existing Helm charts work unchanged

### Principles X-XIII: Phase V Event-Driven Architecture N/A
- ⚪ NO Kafka/Dapr needed - Tags are synchronous CRUD operations
- ⚪ NO new microservices needed
- ⚪ NO cloud deployment changes

### ✅ GATE RESULT: PASSED
**Rationale:** Task Tags is a straightforward database extension (add JSONB column) with MCP tool creation. No event-driven requirements, no infrastructure changes. Hash-based color generation is deterministic and stateless.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
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
│   ├── models/
│   │   └── task.py               # Add tags: List[str] field
│   ├── schemas/
│   │   ├── task.py               # Add tags to TaskBase, TaskCreate, TaskUpdate, TaskResponse
│   │   └── tag.py                # NEW: AddTagRequest, RemoveTagRequest, ListTagsResponse
│   ├── services/
│   │   ├── task_service.py       # Extend with tag operations
│   │   └── tag_service.py        # NEW: Tag normalization, color generation
│   ├── api/
│   │   └── tasks.py              # Extend routes with tag endpoints
│   ├── mcp_tools/
│   │   ├── add_tag.py            # NEW: add_tag MCP tool
│   │   ├── remove_tag.py         # NEW: remove_tag MCP tool
│   │   ├── list_tags.py          # NEW: list_tags MCP tool
│   │   ├── add_task.py           # EXTEND: Add tags parameter
│   │   ├── update_task.py        # EXTEND: Add tags parameter
│   │   └── list_tasks.py         # EXTEND: Add tag_filter parameter
│   ├── utils/
│   │   └── color_generator.py    # NEW: Hash-based color generation
│   └── alembic/
│       └── versions/
│           └── add_tags_to_tasks.py  # NEW: Add tags JSONB column + GIN index
└── tests/
    ├── unit/
    │   ├── test_tag_normalization.py
    │   ├── test_color_generator.py
    │   └── test_tag_service.py
    ├── integration/
    │   ├── test_tag_api.py
    │   └── test_tag_filtering.py
    └── e2e/
        └── test_tag_workflow.py

frontend/
├── src/
│   ├── components/
│   │   ├── TagBadge.tsx          # NEW: Tag badge with color
│   │   ├── TagInput.tsx          # NEW: Tag input component
│   │   └── TaskCard.tsx          # EXTEND: Display tags
│   ├── utils/
│   │   └── tagColors.ts          # NEW: Client-side hash color generation
│   ├── hooks/
│   │   └── useTags.ts            # NEW: Tag management hook
│   └── types/
│       └── task.ts               # EXTEND: Add tags: string[]
└── tests/
    ├── unit/
    │   ├── TagBadge.test.tsx
    │   └── tagColors.test.ts
    └── integration/
        └── TagInput.test.tsx
```

**Structure Decision**: Web application (Option 2) with separate backend and frontend. Backend implements tag storage with JSONB, creates 3 new MCP tools and extends 3 existing tools. Frontend creates reusable TagBadge and TagInput components. Hash-based color generation implemented in both backend (Python) and frontend (TypeScript) for consistency.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected.** Constitution Check passed with all 13 principles satisfied. This feature:
- Uses existing backend/frontend structure (no new projects)
- Leverages PostgreSQL JSONB native support (no external dependencies)
- Extends existing MCP tools (backward compatible)
- No event-driven complexity (synchronous CRUD operations)
- No infrastructure changes required
