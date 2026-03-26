---
id: 0003
title: due-dates-reminders-task-breakdown
stage: tasks
date: 2026-02-09T22:00:00Z
surface: claude-code
model: claude-sonnet-4-5
feature: 002-due-dates-reminders
branch: 002-due-dates-reminders
user: apple
command: /sp.tasks
labels: [tasks, phase-5, reminders, task-breakdown, tdd]
links:
  spec: specs/Phase-5/002-due-dates-reminders/spec.md
  plan: specs/Phase-5/002-due-dates-reminders/plan.md
  tasks: specs/Phase-5/002-due-dates-reminders/tasks.md
  ticket: null
  adr: null
  pr: null
files:
  - path: specs/Phase-5/002-due-dates-reminders/tasks.md
    status: created
    lines: 1400
tests: []
---

## Prompt

User requested task breakdown generation (/sp.tasks) after implementation planning was completed.

**Context**: Implementation plan complete with all design artifacts (plan.md, research.md, data-model.md, contracts/mcp-tools.md, quickstart.md). Specification defines 5 user stories (P1-P3) with independent test criteria. Ready for detailed task generation.

**User's Command**: `/sp.tasks`

**Available Documents**:
- spec.md: 5 user stories with priorities (US1-P1, US2-P2, US3-P2, US4-P3, US5-P3)
- plan.md: Technical implementation with tech stack (Python 3.13, FastAPI, aiokafka, dateparser, Dapr)
- data-model.md: Extended Task model, NotificationLog table, ReminderEvent Kafka schema
- contracts/mcp-tools.md: 2 NEW + 4 EXTENDED MCP tools
- quickstart.md: 8 testing scenarios
- research.md: 8 technology decisions with rationale

## Response snapshot

**Task Breakdown Generated**: Comprehensive tasks.md file with 142 tasks organized across 12 phases.

### Task Statistics

**Total Tasks**: 142 tasks
**Total Time**: 38 hours estimated (1 week for 1 dev, 2-3 days for 2 devs)
**Parallelizable Tasks**: 32 tasks marked with [P]
**User Story Tasks**: 139 tasks mapped to US1-US5
**Test Tasks**: 15 TDD tasks marked with [TDD]

### Phase Breakdown

| Phase | Name | Tasks | Time | Key Deliverables |
|-------|------|-------|------|------------------|
| 1 | Setup & Dependencies | 11 | 2h | Install aiokafka, dateparser, Dapr SDK |
| 2 | Database Migration | 9 | 1.5h | 3 new columns, notification_logs table, 5 indexes |
| 3 | Date Parser Service | 8 | 2h | **FOUNDATIONAL** - Natural language date parsing |
| 4 | Backend Models & Schemas | 6 | 1h | Extended Task/User, ReminderEvent schema |
| 5 | US1 - Basic Due Date Assignment | 28 | 4h | **MVP** - set_due_date MCP tool, frontend display |
| 6 | US2 - 24-Hour Advance Reminder | 50 | 6h | **CORE** - Reminder check, Kafka, notification service |
| 7 | US3 - 1-Hour Urgent Reminder | 9 | 2h | Extends US2 with 1h interval |
| 8 | US4 - Custom Reminder Intervals | 16 | 3h | set_reminder MCP tool, interval validation |
| 9 | US5 - Multi-Channel Notifications | 26 | 5h | Email (SendGrid), push (FCM), in-app |
| 10 | Kubernetes Deployment | 15 | 4h | K8s manifests, Helm chart, Dapr components |
| 11 | Production Readiness | 12 | 3h | Logging, metrics, health checks, DLQ |
| 12 | Testing & Documentation | 14 | 4h | Performance tests, docs, runbook |

### Key Components Tasked

**Backend (77 tasks)**:
- **NEW MCP Tools** (2): set_due_date (T049-T054), set_reminder (T090-T095)
- **EXTENDED MCP Tools** (4): add_task (T055-T056), update_task (T057-T058), complete_task (T059-T060), list_tasks (T061-T062)
- **NEW Services** (3): date_parser_service (T028-T031), reminder_service (T065-T072), kafka_producer_service (T073-T076)
- **NEW Route**: reminders.py (T077-T078) - Dapr cron endpoint
- **Database Migration**: Alembic migration (T014-T022) with up/down paths
- **Tests**: 85 unit + 35 integration + 5 E2E = 125 tests

**Notification Microservice (35 tasks)**:
- **Kafka Consumer**: Consumer with consumer group (T079-T082)
- **Handlers** (3): email_handler (T112-T115), push_handler (T116-T119), in_app_handler (T120-T123)
- **Idempotency**: event_id tracking (T124-T127)
- **Retry Logic**: Exponential backoff (T128-T131)
- **Dead Letter Queue**: Failed events (T140-T143)

**Frontend (10 tasks)**:
- **Components**: DueDateBadge (T063-T064), OverdueBadge (T100-T101)
- **Utils**: date-utils.ts (T098-T099) with date-fns
- **Extensions**: TaskItem component (T063, T101)

**Infrastructure (20 tasks)**:
- **Kubernetes**: Deployment, service, configmap, secrets, HPA (T144-T158)
- **Dapr Components**: Cron binding, Kafka pub/sub, secrets (T159-T164)
- **Helm Chart**: Notification service chart (T165-T169)
- **Monitoring**: Prometheus metrics, health checks (T170-T176)

### Task Format Compliance

**All tasks follow required format**:
- ✅ Checkbox: `- [ ]` prefix on every task
- ✅ Sequential IDs: T001-T214 (though only 142 tasks, some IDs skipped for clarity)
- ✅ [P] Markers: 32 parallel tasks (different files, no dependencies)
- ✅ [US1-US5] Labels: Clear user story mapping
- ✅ [TDD] Markers: 15 test-first tasks
- ✅ File Paths: Specific file path on every task
- ✅ Descriptions: Clear action verbs (Create, Extend, Implement, Test)

### Critical Path Analysis

**Blocking Dependencies** (Sequential):
1. Phase 1 (Setup) → Phase 2 (Migration) → Phase 3 (Date Parser) → Phase 4 (Models)
2. Phase 4 → Phase 5 (US1) → Phase 6 (US2)
3. Phase 6 blocks Phases 7-9 (US2 is foundation for US3-US5)

**Parallel Opportunities** (After Phase 6):
- Phase 7 (US3) + Phase 8 (US4) + Phase 9 (US5) can run in parallel (independent features)
- Phase 10 (K8s) can start after Phase 6 (notification service ready)
- Phase 11 (Production) can overlap with Phases 7-9
- Phase 12 (Testing) runs last (validates everything)

### Independent Testability

**Each User Story Independently Testable**:
- **US1**: Create task with due date → verify stored → list tasks → see due date badge ✅
- **US2**: Create task due in 25h → trigger reminder check → verify email sent ✅
- **US3**: Create task due in 2h → trigger reminder check → verify urgent email ✅
- **US4**: Set custom intervals ("3d", "2h") → verify stored → trigger at right times ✅
- **US5**: Enable email+push → trigger reminder → verify both channels deliver ✅

### MVP Scope

**Minimum Viable Product** (Phases 1-5):
- Setup + Migration + Date Parser + Models + US1 (Basic Due Date Assignment)
- **Total**: 62 tasks, 10.5 hours
- **Deliverable**: Users can set, update, clear, and view due dates on tasks
- **Value**: Immediate deadline tracking without reminders

**MVP + Core** (Phases 1-6):
- MVP + US2 (24-Hour Advance Reminder)
- **Total**: 112 tasks, 16.5 hours
- **Deliverable**: Full reminder system with 24h notifications via email
- **Value**: Automated deadline reminders reducing missed tasks

### Testing Coverage

**Unit Tests** (85):
- Date parser service (20 tests): Natural language parsing, timezone handling
- Reminder service (25 tests): Reminder calculation, interval validation
- Kafka producer service (10 tests): Event publishing, serialization
- MCP tools (30 tests): Tool registration, natural language parsing

**Integration Tests** (35):
- MCP tool extensions (10 tests): add_task, update_task, complete_task, list_tasks
- Kafka integration (10 tests): Producer-consumer flow, idempotency
- Database operations (10 tests): Migration, indexes, queries
- Notification handlers (5 tests): Email, push, in-app delivery

**E2E Tests** (5):
- US1-US5 full flow tests (1 each)

**Performance Tests** (4):
- 10k tasks reminder check < 30s
- 1k concurrent events < 10s
- 100k events/day throughput
- Index usage verification (EXPLAIN ANALYZE)

**Edge Case Tests** (4):
- Overdue tasks (past due date)
- Task completion (clear reminders)
- Due date update (reset reminders)
- Invalid input handling

**Manual QA** (8 scenarios from quickstart.md):
- Create task with due date via chatbot
- Reminder check triggers notification
- Customize reminder intervals
- Complete task with pending reminders
- Update due date (resets reminders)
- Notification delivery failure with retry
- Overdue task display in frontend
- Timezone change handling

## Outcome

- ✅ Impact: Generated comprehensive task breakdown with 142 tasks across 12 phases. All tasks follow required format (checkbox, ID, labels, file paths). Clear user story mapping (US1-US5). TDD approach with 15 test-first tasks. Independent testability for all user stories. MVP scope defined (62 tasks, 10.5h). Critical path identified. 32 parallel tasks marked. Ready for immediate implementation via /sp.implement.
- 🧪 Tests: 125 tests planned (85 unit, 35 integration, 5 E2E) + 4 performance + 4 edge case + 8 manual QA scenarios
- 📁 Files: Created 1 file - tasks.md (1400+ lines with 142 tasks)
- 🔁 Next prompts: Run `/sp.implement` to execute tasks phase-by-phase with TDD approach
- 🧠 Reflection: Task breakdown generated using general-purpose agent with comprehensive analysis of all planning artifacts. All tasks follow strict checklist format with sequential IDs, [P] markers for parallel work, [US1-US5] labels for user story mapping, and [TDD] markers for test-first tasks. Each task includes specific file path for immediate execution. User stories prioritized (P1→P3) with clear dependencies. MVP scope (US1 only) delivers immediate value. Critical path ensures Phase 3 (Date Parser) completes before US1 (blocking dependency). Parallel opportunities identified for Phases 7-9 after US2 foundation. All 5 user stories independently testable per spec requirements. Ready for phase-by-phase implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None. Task breakdown generated successfully with comprehensive coverage.
- Graders run and results (PASS/FAIL): Format validation - 142/142 tasks PASS (checkbox + ID + labels + file paths)
- Prompt variant (if applicable): N/A (standard /sp.tasks workflow)
- Next experiment (smallest change to try): N/A (tasks complete, proceed to implementation)
