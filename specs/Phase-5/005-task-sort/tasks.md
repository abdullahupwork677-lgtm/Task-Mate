# Implementation Tasks: Task Sorting

**Feature**: 005-task-sort
**Branch**: `005-task-sort`
**Created**: 2026-02-14
**Estimated Time**: 4-6 hours

---

## Task Summary

- **Total Tasks**: 36
- **Phases**: 7 (Setup → 4 User Stories → Polish)
- **Parallel Opportunities**: 18 tasks marked [P]
- **Dependencies**: Priority-based user story execution (P1 → P2)

**Task Distribution by Phase:**
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 0 tasks (all infrastructure exists)
- Phase 3 (US1 - Sort by Due Date): 6 tasks
- Phase 4 (US2 - Sort by Priority): 5 tasks
- Phase 5 (US3 - Sort by Created Date): 4 tasks
- Phase 6 (US4 - Sort Alphabetically): 5 tasks
- Phase 7 (Polish): 12 tasks

---

## Implementation Strategy

**MVP Scope** (Deliver First):
- Phase 1: Setup (database indexes)
- Phase 3: User Story 1 (Sort by Due Date - P1)
- Phase 4: User Story 2 (Sort by Priority - P1)

**Incremental Delivery** (After MVP):
- Phase 5: User Story 3 (Sort by Created Date - P2)
- Phase 6: User Story 4 (Sort Alphabetically - P2)
- Phase 7: Polish & Cross-Cutting

**Independent Testing**: Each user story phase includes all necessary components (backend service, MCP tool, AI agent, frontend UI) to be independently tested and delivered.

---

## Phase 1: Database Setup

**Goal**: Create database indexes for optimal sort performance

- [X] T001 Create Alembic migration for sort indexes in backend/alembic/versions/add_sort_indexes.py
- [X] T002 Add 4 composite indexes: (user_id, due_date NULLS LAST, created_at DESC), (user_id, priority, created_at DESC), (user_id, created_at DESC), (user_id, LOWER(title), created_at DESC)
- [X] T003 [P] Create SortParams schema in backend/src/schemas.py with sort_by and sort_direction enums
- [X] T004 Apply migration and verify indexes exist using alembic upgrade head

**Completion Criteria**: Database has 4 composite indexes for sort performance, SortParams schema exists ✅

---

## Phase 2: Foundational Components

**Note**: No foundational tasks needed - all infrastructure exists from previous phases (TaskService, list_tasks MCP tool, AI agent)

**Existing Infrastructure:**
- ✅ TaskService in backend/src/services/task_service.py
- ✅ list_tasks MCP tool in backend/src/mcp_tools/list_tasks.py
- ✅ AI agent in backend/src/ai_agent/agent.py
- ✅ Frontend task list component

---

## Phase 3: User Story 1 - Sort by Due Date (P1) 🎯 MVP

**Story Goal**: Users can sort tasks by due date (earliest/latest first) with tasks without due dates at the end

**Independent Test**: Create tasks with various due dates (Feb 10, Feb 15, Feb 20), sort by due date ascending/descending, verify correct order and nulls at end

### Backend Implementation

- [X] T005 [US1] Extend TaskService.search_and_filter_tasks with sort_by and sort_direction parameters in backend/src/services/task_service.py
- [X] T006 [US1] Implement due_date sort logic with NULLS LAST handling and created_at tiebreaker
- [X] T007 [US1] Update list_tasks MCP tool in backend/src/mcp_tools/list_tasks.py with sort_by and sort_direction parameters
- [X] T008 [US1] Add sort command patterns to AI agent prompt in backend/src/ai_agent/agent.py ("sort by due date", "show tasks by due date")

### Frontend Implementation

- [X] T009 [P] [US1] Create TaskSort component in frontend/src/components/TaskSort.tsx with sort dropdown UI
- [X] T010 [P] [US1] Create useTaskSort hook in frontend/src/hooks/useTaskSort.ts for sort state management

**US1 Completion Criteria**: Users can sort by due date (asc/desc), tasks without due dates appear at end, AI chatbot understands "sort by due date", tests pass ✅

---

## Phase 4: User Story 2 - Sort by Priority (P1) 🎯 MVP

**Story Goal**: Users can sort tasks by priority (high to low or low to high)

**Independent Test**: Create tasks with different priorities (high/medium/low), sort by priority, verify correct order (high → medium → low)

### Backend Implementation

- [X] T011 [US2] Implement priority sort logic in TaskService with CASE statement mapping (high=1, medium=2, low=3) - COMPLETED IN T005-T006
- [X] T012 [US2] Add priority reverse mapping for descending sort (low=1, medium=2, high=3) - COMPLETED IN T005-T006
- [X] T013 [US2] Update MCP tool with priority sort support - COMPLETED IN T007
- [X] T014 [US2] Add priority sort patterns to agent prompt ("sort by priority", "show high priority first") - COMPLETED IN T008

### Frontend Implementation

- [X] T015 [P] [US2] Add priority sort option to TaskSort component dropdown - COMPLETED IN T009

**US2 Completion Criteria**: Users can sort by priority (high to low / low to high), AI chatbot understands "sort by priority", tests pass ✅

---

## Phase 5: User Story 3 - Sort by Created Date (P2)

**Story Goal**: Users can sort tasks by creation date (newest/oldest first)

**Independent Test**: Create tasks at different times, sort by created date, verify chronological order (newest → oldest or reverse)

### Backend Implementation

- [X] T016 [US3] Implement created_at sort logic in TaskService (ascending and descending) - COMPLETED IN T005-T006
- [X] T017 [US3] Update MCP tool with created_at sort support - COMPLETED IN T007
- [X] T018 [US3] Add created_at sort patterns to agent prompt ("show newest tasks first", "oldest tasks first") - COMPLETED IN T008

### Frontend Implementation

- [X] T019 [P] [US3] Add created date sort option to TaskSort component - COMPLETED IN T009

**US3 Completion Criteria**: Users can sort by created date (newest/oldest first), default sort is created_at desc, tests pass ✅

---

## Phase 6: User Story 4 - Sort Alphabetically by Title (P2)

**Story Goal**: Users can sort tasks alphabetically by title (A-Z or Z-A) with case-insensitive sorting

**Independent Test**: Create tasks with various titles (Buy groceries, Call doctor, Attend meeting), sort A-Z, verify alphabetical order (Attend → Buy → Call)

### Backend Implementation

- [X] T020 [US4] Implement title sort logic in TaskService with LOWER() for case-insensitive sorting - COMPLETED IN T005-T006
- [X] T021 [US4] Add created_at tiebreaker for title sorting - COMPLETED IN T005-T006
- [X] T022 [US4] Update MCP tool with title sort support - COMPLETED IN T007
- [X] T023 [US4] Add title sort patterns to agent prompt ("sort alphabetically", "sort by name") - COMPLETED IN T008

### Frontend Implementation

- [X] T024 [P] [US4] Add title sort option to TaskSort component - COMPLETED IN T009

**US4 Completion Criteria**: Users can sort alphabetically (A-Z / Z-A), sorting is case-insensitive, tests pass ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Complete feature with testing, documentation, optimization, and production readiness

### Enhanced UX

- [X] T025 [P] Add visual sort indicators in TaskSort component (↑/↓ arrows for active sort) - COMPLETED IN T009
- [X] T026 [P] Implement sort direction toggle (click same column to reverse direction) - COMPLETED IN T009
- [X] T027 [P] Persist sort preferences in sessionStorage for session duration - COMPLETED IN T010
- [X] T028 [P] Add loading state during sort operations
- [X] T029 [P] Display active sort in UI (highlighted column + direction arrow) - COMPLETED IN T009

### Backend Validation & Error Handling

- [X] T030 [P] Add Pydantic validation for sort_by enum (due_date, priority, created_at, title) - COMPLETED IN T003
- [X] T031 [P] Add Pydantic validation for sort_direction enum (asc, desc) - COMPLETED IN T003
- [X] T032 [P] Handle invalid sort parameters with 422 validation error - COMPLETED IN T003 (Pydantic auto-validates)

### Testing

- [X] T033 [P] Create backend/tests/unit/test_task_sort.py testing all sort fields and directions
- [X] T034 [P] Create backend/tests/integration/test_sort_integration.py testing MCP tool with sort parameters
- [X] T035 [P] Create backend/tests/e2e/test_sort_e2e.py testing complete sort workflow via chatbot

### Documentation

- [X] T036 [P] Update backend/README.md and frontend/README.md with sort feature documentation and examples

**Phase 7 Completion Criteria**: All tests passing, documentation complete, sort indicators working, session persistence active, feature production-ready ✅

---

## Dependencies Between User Stories

```
Phase 1 (Setup) → Phase 2 (Foundational - NONE)
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
  Phase 3 (US1)              Phase 4 (US2)
  Sort by Due Date           Sort by Priority
  [P1 - Independent]         [P1 - Independent]
        ↓                           ↓
        └─────────────┬─────────────┘
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
  Phase 5 (US3)              Phase 6 (US4)
  Sort by Created Date       Sort Alphabetically
  [P2 - Independent]         [P2 - Independent]
        ↓                           ↓
        └─────────────┬─────────────┘
                      ↓
                 Phase 7 (Polish)
```

**Key Dependencies:**
- US1 (Sort by Due Date) + US2 (Sort by Priority) = **MVP** (must be completed first)
- US3 (Sort by Created Date), US4 (Sort Alphabetically) can be implemented in any order after MVP
- Phase 7 (Polish) requires all user stories complete

---

## Parallel Execution Opportunities

**Phase 1 (Setup)** - Can run in parallel:
- T003 (SortParams schema) [after T001, T002 complete]

**Phase 3 (US1)** - Can run in parallel:
- T009 (TaskSort component) || T010 (useTaskSort hook) [after backend T005-T008 complete]

**Phase 4 (US2)** - Can run in parallel:
- T015 (Priority sort option) [after backend T011-T014 complete]

**Phase 5 (US3)** - Can run in parallel:
- T019 (Created date sort option) [after backend T016-T018 complete]

**Phase 6 (US4)** - Can run in parallel:
- T024 (Title sort option) [after backend T020-T023 complete]

**Phase 7 (Polish)** - Can run in parallel:
- T025 (Sort indicators) || T026 (Direction toggle) || T027 (Session persistence) || T028 (Loading state) || T029 (Active sort display)
- T030 (Validation 1) || T031 (Validation 2) || T032 (Error handling)
- T033 (Unit tests) || T034 (Integration tests) || T035 (E2E tests) || T036 (Documentation)

---

## Testing Strategy

**Unit Tests** (Fast, isolated):
- Sort field validation (due_date, priority, created_at, title)
- Sort direction validation (asc, desc)
- NULL handling for due_date (NULLS LAST)
- Case-insensitive title sorting (LOWER())
- Priority CASE statement mapping
- Tiebreaker logic (created_at DESC)

**Integration Tests** (Database + API):
- Sort by each field individually
- Sort direction reversal
- Sort combined with filters (e.g., incomplete tasks sorted by priority)
- MCP tool with sort parameters
- Session persistence
- Invalid sort parameter handling

**E2E Tests** (Full workflow):
- Complete sort workflow via chatbot
- Natural language sort commands
- UI sort dropdown interaction
- Sort direction toggle
- Visual indicator display

---

## Performance Targets

- **Sort Query Execution**: < 200ms for 1,000 tasks (with indexes)
- **Sort Query Execution**: < 500ms for 10,000 tasks
- **Total User Experience**: < 2 seconds (1 click + 1 second render)
- **Database Indexes**: All 4 composite indexes created
- **Index Usage**: EXPLAIN ANALYZE confirms index-only scans

---

## Success Metrics

- ✅ All 36 tasks completed
- ✅ 4 user stories independently testable
- ✅ 100% test pass rate (unit + integration + e2e)
- ✅ 4 composite database indexes created
- ✅ < 200ms sort response for 1,000 tasks
- ✅ 95%+ natural language command accuracy
- ✅ Sort persists during session
- ✅ Visual indicators working (arrows, highlighting)
- ✅ Combined sort + filter works correctly

---

**Tasks File Complete**: 2026-02-14
**Ready for**: `/sp.implement` execution
**Estimated Completion**: 4-6 hours with parallel execution
