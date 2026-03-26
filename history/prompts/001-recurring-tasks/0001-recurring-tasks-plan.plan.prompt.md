---
id: "0001"
title: "Recurring Tasks Implementation Plan"
stage: plan
date: 2026-02-07
surface: cli
model: claude-opus-4-6
feature: 001-recurring-tasks
branch: 001-recurring-tasks
user: apple
command: /sp.plan
labels: [plan, recurring-tasks, phase-v, backend]
links:
  spec: specs/001-recurring-tasks/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/001-recurring-tasks/plan.md
  - specs/001-recurring-tasks/research.md (moved from root)
  - specs/001-recurring-tasks/implementation-summary.md (moved from root)
tests:
  - N/A (plan phase - tests come in TDD red phase)
---

## Prompt

/sp.plan

## Response snapshot

Created complete implementation plan at `specs/001-recurring-tasks/plan.md`.

**Plan Deliverables:**

**Phase 0 (Research) - COMPLETE:**
- ✅ research.md - Comprehensive research (400+ lines)
- ✅ implementation-summary.md - Quick reference
- 8 key technical decisions documented
- No new dependencies needed (python-dateutil, dateparser already in stack)

**Phase 1 (Design) - COMPLETE:**
- ✅ Data model: Task entity extended with 4 new fields
- ✅ API contracts: 4 JSON contracts (1 new, 3 extended)
- ✅ Quickstart guide with code examples
- ✅ Constitution check: ALL principles passed

**Technical Approach:**
- Database: 4 new columns (is_recurring, recurrence_pattern, recurrence_end_date, parent_task_id)
- Indexes: 3 new (composite user_recurring, parent_task_id, unique constraint for idempotency)
- MCP Tools: 1 new (set_recurring), 3 modified (add_task, complete_task, list_tasks)
- Date library: python-dateutil (rrule, relativedelta) + dateparser
- Idempotency: Unique constraint on (parent_task_id, due_date)

**Implementation Roadmap:**
- Phase A: Database Schema (1-2 days)
- Phase B: Recurrence Engine (2-3 days)
- Phase C: MCP Tools (2 days)
- Phase D: NLP Integration (1-2 days)
- Phase E: Testing & Docs (1-2 days)
- **Total: 7-10 days**

## Outcome

- ✅ Impact: Complete implementation plan with research, data model, contracts, quickstart
- 🧪 Tests: 80+ tests planned (unit, integration, e2e)
- 📁 Files: 3 files (plan.md, research.md, implementation-summary.md)
- 🔁 Next prompts: /sp.tasks to generate tasks.md, then TDD implementation (red → green → refactor)
- 🧠 Reflection: Used backend-developer agent for research (haiku model for speed). All technical decisions made with rationale. Constitution check passed all principles.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Generate tasks.md and start TDD red phase
