---
id: 0002
title: task-sort-implementation-planning
stage: plan
date: 2026-02-14
surface: claude-code
model: claude-sonnet-4-5
feature: 005-task-sort
branch: 005-task-sort
user: apple
command: /sp.plan
labels: [planning, intermediate-features, phase-5]
links:
  spec: specs/005-task-sort/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - path: specs/005-task-sort/plan.md
    type: created
    lines: 200+
  - path: specs/005-task-sort/research.md
    type: created
    lines: 450+
  - path: specs/005-task-sort/data-model.md
    type: created
    lines: 550+
  - path: specs/005-task-sort/contracts/GET_tasks.yaml
    type: created
    lines: 350+
  - path: specs/005-task-sort/contracts/list_tasks_mcp.json
    type: created
    lines: 400+
  - path: specs/005-task-sort/quickstart.md
    type: created
    lines: 600+
tests:
  - none (planning phase - test specs documented in contracts)
---

## Prompt

User invoked `/sp.plan` command for Task Sorting feature (005-task-sort).

**Context:**
- Feature specification completed and validated (spec.md, 176 lines)
- Checklist validation passed (100%)
- PHR for specification phase created
- Branch: 005-task-sort (currently checked out)

**Planning Task:**
Execute implementation planning workflow to generate:
1. Technical Context analysis
2. Constitution Check validation
3. Phase 0: Research (technical approach, SQL patterns, architecture decisions)
4. Phase 1: Design & Contracts (data model, API contracts, integration guide)
5. Agent context update

## Response snapshot

**Phase 0: Outline & Research (research.md)** ✅

Completed comprehensive technical research covering 7 key areas:
1. **SQL Sorting Best Practices**: PostgreSQL ORDER BY with secondary sort, NULL handling, case-insensitive sorting
2. **SQLModel/SQLAlchemy Implementation**: order_by() with asc()/desc(), nullslast(), func.lower(), case() for priority
3. **Database Index Strategy**: 4 new composite indexes for optimal performance
4. **MCP Tool Extension**: Extend list_tasks with sort_by and sort_direction parameters (backward compatible)
5. **Frontend Sort UI**: Column header click + dropdown combo, session-based persistence
6. **REST API Query Parameters**: Standard RESTful approach with Pydantic enums
7. **Performance Optimization**: Database-level sorting + pagination for large lists

**Key Technical Decisions:**
- NO schema changes needed - all sortable fields exist (due_date, priority, created_at, title)
- YES database indexes needed - 4 composite indexes for performance (< 200ms for 1,000 tasks)
- Backward compatible MCP tool extension (defaults to created_at desc)
- Session-based sort persistence (sessionStorage, not database)
- SQL ORDER BY with proper NULL handling, tiebreakers, case-insensitive title sorting

**Phase 1: Design & Contracts (data-model.md, contracts/, quickstart.md)** ✅

1. **Data Model (data-model.md)**:
   - NO schema changes required ✅
   - Documented existing sortable fields
   - 4 new composite indexes (Alembic migration required)
   - Sort configuration stored in session state (not database)
   - Comprehensive SQL patterns for each sort field
   - Pydantic DTOs for request/response validation

2. **API Contracts**:
   - **REST API (GET_tasks.yaml)**: OpenAPI 3.0 contract with sort query parameters, examples, error handling
   - **MCP Tool (list_tasks_mcp.json)**: Extended contract v2.0.0 with natural language examples, agent guidance, test cases

3. **Integration Guide (quickstart.md)**:
   - Backend: Service layer, REST API, MCP tool, Alembic migration
   - Frontend: Sort hook, UI components, API client integration
   - AI Agent: Prompt examples, natural language patterns
   - Testing: Unit tests, integration tests, E2E scenarios
   - Performance checklist

**Constitution Check** ✅

All 13 principles validated:
- Principles I-IX: ✅ PASSED (no violations)
- Principles X-XIII (Event-Driven): ⚪ N/A (sorting is synchronous CRUD, no Kafka/Dapr needed)

**Gate Result:** PASSED - Simple database-level operation, no infrastructure changes

**Technical Context** ✅

- Language: Python 3.13+ (Backend), TypeScript (Frontend)
- Stack: FastAPI, SQLModel, PostgreSQL, Next.js 14
- Performance: < 200ms for 1,000 tasks, < 500ms for 10,000 tasks
- No schema changes, session-based persistence

**Agent Context Update** ✅

Updated `CLAUDE.md` with Task Sorting feature technology stack.

## Outcome

- ✅ Impact: Complete implementation plan ready for `/sp.tasks` - Final Intermediate feature of Phase V (Tags, Search & Filter, Sort all spec'd + planned!)
- 🧪 Tests: Test specifications documented in contracts (unit tests, integration tests, E2E scenarios)
- 📁 Files: Created 6 planning artifacts (plan.md, research.md, data-model.md, 2 contracts, quickstart.md) - 2,550+ lines total
- 🔁 Next prompts: Execute `/sp.tasks` to generate task breakdown for implementation
- 🧠 Reflection: Task Sorting is the simplest of 3 Intermediate features - pure database operation with no schema changes, just 4 indexes. All technical questions resolved in research phase.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): Constitution Check - PASS (all principles satisfied, no violations)
- Prompt variant (if applicable): Standard `/sp.plan` workflow with comprehensive research phase
- Next experiment (smallest change to try): Proceed to `/sp.tasks` for implementation task breakdown
