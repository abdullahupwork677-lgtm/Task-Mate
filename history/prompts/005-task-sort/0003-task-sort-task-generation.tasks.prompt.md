---
id: "0003"
title: "task-sort-task-generation"
stage: "tasks"
date: "2026-02-14"
surface: "claude-code"
model: "claude-sonnet-4-5"
feature: "005-task-sort"
branch: "005-task-sort"
user: "apple"
command: "/sp.tasks"
labels: ["tasks", "task-generation", "task-sorting"]
links:
  spec: "specs/005-task-sort/spec.md"
  ticket: null
  adr: null
  pr: null
files:
  - path: "specs/005-task-sort/tasks.md"
    action: "created"
    lines: 403
tests: []
---

## Prompt

User requested: `/sp.tasks @../specs/005-task-sort/`

Command executed task generation workflow for feature 005-task-sort (Task Sorting).

Input context:
- spec.md: 4 user stories (US1-US4) with priorities P1 (due date, priority) and P2 (created date, alphabetical)
- plan.md: Database-level SQL ORDER BY implementation, no schema changes, 4 composite indexes needed
- data-model.md: Detailed sort field mapping, NULL handling, case-insensitive title sorting, priority enum mapping

Requirements:
- Sort by due_date (earliest/latest first, nulls last)
- Sort by priority (high/medium/low with CASE mapping)
- Sort by created_at (newest/oldest first, default sort)
- Sort by title (A-Z/Z-A, case-insensitive)
- Visual indicators (arrows), session persistence
- AI chatbot natural language commands
- Performance: < 200ms for 1,000 tasks

## Response snapshot

Generated tasks.md with 36 tasks organized across 7 phases:

**Phase 1: Database Setup (4 tasks)**
- Alembic migration for 4 composite indexes
- SortParams schema with enums

**Phase 2: Foundational (0 tasks)**
- No new infrastructure needed - all exists

**Phase 3: US1 - Sort by Due Date (6 tasks)**
- Backend: TaskService extension, NULLS LAST handling, tiebreaker logic
- Frontend: TaskSort component, useTaskSort hook
- MCP tool + AI agent integration

**Phase 4: US2 - Sort by Priority (5 tasks)**
- Backend: CASE statement mapping (high=1, medium=2, low=3)
- Frontend: Priority sort option
- MCP tool + AI agent patterns

**Phase 5: US3 - Sort by Created Date (4 tasks)**
- Backend: created_at asc/desc
- Frontend: Created date option

**Phase 6: US4 - Sort Alphabetically (5 tasks)**
- Backend: LOWER() for case-insensitive
- Frontend: Title sort option

**Phase 7: Polish (12 tasks)**
- UX: Visual indicators, direction toggle, session persistence
- Validation: Pydantic enums, error handling
- Testing: Unit, integration, E2E tests
- Documentation: README updates

**MVP Scope:** Phase 1 + Phase 3 + Phase 4 (due date + priority sorting)

**Parallel Opportunities:** 18 tasks marked [P]

**Estimated Time:** 4-6 hours

## Outcome

- ✅ Impact: Complete task breakdown for Task Sorting feature (36 tasks, 7 phases)
- 🧪 Tests: Unit, integration, E2E test tasks included in Phase 7 (T033-T035)
- 📁 Files: 1 file created (specs/005-task-sort/tasks.md, 403 lines)
- 🔁 Next prompts: `/sp.implement specs/005-task-sort/` to execute tasks
- 🧠 Reflection: Simple feature with no schema changes - primarily extending existing service/MCP tool/UI with sort parameters. Database indexes critical for performance (< 200ms target).

## Evaluation notes (flywheel)

- Failure modes observed: None - straightforward feature with clear requirements
- Graders run and results (PASS/FAIL): Format validation PASS (all tasks follow checklist format with [ID] [P?] [Story?] description + file path)
- Prompt variant (if applicable): Standard task generation workflow
- Next experiment (smallest change to try): N/A - workflow successful
