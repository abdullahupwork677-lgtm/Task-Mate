---
id: "0002"
title: "Recurring Tasks Task Generation"
stage: tasks
date: 2026-02-07
surface: cli
model: claude-opus-4-6
feature: 001-recurring-tasks
branch: 001-recurring-tasks
user: apple
command: /sp.tasks
labels: [tasks, recurring-tasks, phase-v, tdd, backend]
links:
  spec: specs/001-recurring-tasks/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/001-recurring-tasks/tasks.md
tests:
  - N/A (tasks phase - tests defined in tasks.md)
---

## Prompt

/sp.tasks

## Response snapshot

Generated comprehensive tasks.md at `specs/001-recurring-tasks/tasks.md`.

**Task Organization:**

**161 total tasks** organized into 12 phases:
1. **Phase 1: Setup** (5 tasks) - Project initialization
2. **Phase 2: Foundational** (17 tasks) - Database schema migration (CRITICAL - BLOCKS ALL)
3. **Phase 3: User Story 1** (22 tasks) - Set task as recurring via chat (P1, MVP)
4. **Phase 4: User Story 2** (41 tasks) - Auto-create next occurrence on completion (P1, MVP)
5. **Phase 5: User Story 3** (10 tasks) - Cancel/stop recurrence (P2)
6. **Phase 6: User Story 4** (9 tasks) - Set recurrence end date (P3)
7. **Phase 7: User Story 5** (13 tasks) - List recurring tasks (P2)
8. **Phase 8: Task Creation Ext** (12 tasks) - Create recurring task in one command
9. **Phase 9: Edge Cases** (12 tasks) - Robustness testing
10. **Phase 10: Frontend** (3 tasks) - Display updates
11. **Phase 11: Documentation** (11 tasks) - Polish
12. **Phase 12: Performance** (6 tasks) - Load testing

**TDD Approach:**
- Each user story phase organized: Tests (RED) → Implementation (GREEN) → Refactor
- Tests MUST fail before implementation
- 80+ tests planned across unit/integration/e2e layers

**MVP Scope:**
- Phases 1-4 + Phase 10 = 88 tasks
- Delivers core value: Set recurring + Auto-repeat on completion

**Parallel Opportunities:**
- Setup tasks (Phase 1): T002-T005 can run in parallel
- Test tasks within each phase marked [P] can run in parallel
- After Foundational completes: User Stories can be worked on in parallel

**Independent Testing:**
- Each user story has independent test criteria
- User Story 1: "Say 'Make task 5 weekly', verify is_recurring=True"
- User Story 2: "Complete daily task, verify new task created with due_date=tomorrow"
- User Story 3: "Say 'Stop repeating task 5', verify is_recurring=False"
- User Story 4: "Complete task on end_date, verify NO next occurrence created"
- User Story 5: "Say 'Show recurring tasks', verify only recurring returned"

**Technical Implementation:**
- Database: 4 new columns, 3 indexes (including unique constraint for idempotency)
- MCP Tools: 1 new (set_recurring), 3 modified (add_task, complete_task, list_tasks)
- Recurrence Engine: calculate_next_due_date with 7 pattern types
- Edge cases: Month-end, leap year, idempotency, timezone handling

**Format Compliance:**
- ✅ All tasks follow checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- ✅ Sequential task IDs (T001-T161)
- ✅ Parallel markers [P] for independent tasks
- ✅ Story labels [US1-US5] for user story tasks
- ✅ Exact file paths in every task description

## Outcome

- ✅ Impact: Complete task breakdown for recurring tasks feature with 161 actionable tasks organized by user story
- 🧪 Tests: 80+ tests planned (unit, integration, e2e, performance) following TDD red-green-refactor
- 📁 Files: 1 file (tasks.md with complete implementation roadmap)
- 🔁 Next prompts: Start TDD implementation with Phase 1 (Setup) and Phase 2 (Foundational), then Phase 3 (User Story 1 MVP)
- 🧠 Reflection: Tasks organized by user story for independent implementation. MVP clearly defined (88 tasks). TDD approach enforced with RED-GREEN-REFACTOR phases. All tasks have exact file paths and clear acceptance criteria.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Begin TDD implementation starting with Phase 1 Setup tasks
