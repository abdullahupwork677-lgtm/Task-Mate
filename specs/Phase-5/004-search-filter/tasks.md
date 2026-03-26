# Implementation Tasks: Task Search & Advanced Filtering

**Feature**: 004-search-filter
**Branch**: `004-search-filter`
**Created**: 2026-02-14
**Estimated Time**: 8-12 hours

---

## Task Summary

- **Total Tasks**: 52
- **Phases**: 9 (Setup → 6 User Stories → Polish)
- **Parallel Opportunities**: 22 tasks marked [P]
- **Dependencies**: Priority-based user story execution (P1 → P2 → P3)

**Task Distribution by Phase:**
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (US1 - Keyword Search): 7 tasks
- Phase 4 (US2 - Status Filter): 5 tasks
- Phase 5 (US3 - Priority Filter): 4 tasks
- Phase 6 (US4 - Tags Filter): 5 tasks
- Phase 7 (US5 - Due Date Filter): 7 tasks
- Phase 8 (US6 - Combined Filters): 6 tasks
- Phase 9 (Polish): 9 tasks

---

## Implementation Strategy

**MVP Scope** (Deliver First):
- Phase 1-2: Setup + Foundational (required infrastructure)
- Phase 3: User Story 1 (Keyword Search - P1)
- Phase 4: User Story 2 (Status Filter - P1)

**Incremental Delivery** (After MVP):
- Phase 5: User Story 3 (Priority Filter - P2)
- Phase 6: User Story 4 (Tags Filter - P2)
- Phase 7: User Story 5 (Due Date Filter - P2)
- Phase 8: User Story 6 (Combined Filters - P3)
- Phase 9: Polish & Cross-Cutting

**Independent Testing**: Each user story phase includes all necessary components (backend, MCP tools, AI agent, frontend) to be independently tested and delivered.

---

## Phase 1: Project Setup

**Goal**: Initialize database indexes, create search schemas foundation

- [X] T001 Create Alembic migration for composite indexes in backend/alembic/versions/add_search_indexes.py
- [X] T002 Add 5 composite indexes: (user_id, completed), (user_id, priority), (user_id, tags), (user_id, due_date), (user_id, title) for efficient filtering
- [X] T003 [P] Create SearchRequest schema in backend/src/schemas/search.py with keyword, status_filter, priority_filter, tags_filter, due_date_filter, pagination parameters
- [X] T004 [P] Create SearchResponse schema in backend/src/schemas/search.py with tasks array, total_count, filtered_count, pagination info, applied_filters summary
- [X] T005 Apply migration and verify indexes exist using alembic upgrade head

**Completion Criteria**: Database has 5 composite indexes for search, SearchRequest/SearchResponse schemas exist ✅

---

## Phase 2: Foundational Components

**Goal**: Create search service foundation and query builder utilities

- [X] T006 [P] Create QueryBuilder utility class in backend/src/utils/query_builder.py with methods for dynamic WHERE clause construction
- [X] T007 Extend TaskService in backend/src/services/task_service.py with search_and_filter_tasks method signature
- [X] T008 [P] Create frontend SearchFilters type in frontend/src/types/search.ts with all filter parameters
- [X] T009 [P] Create frontend SearchResults type in frontend/src/types/search.ts matching backend SearchResponse

**Completion Criteria**: QueryBuilder utility exists, TaskService has search method stub, Frontend types defined ✅

---

## Phase 3: User Story 1 - Keyword Search in Tasks (P1)

**Story Goal**: Users can search tasks by keyword (title/description) with case-insensitive partial matching

**Independent Test**: Create tasks with various titles/descriptions, search with keywords, verify correct matches returned

### Backend Implementation

- [X] T010 [US1] Implement keyword search logic in TaskService.search_and_filter_tasks using PostgreSQL ILIKE for title and description columns
- [X] T011 [US1] Create search_tasks MCP tool in backend/src/mcp_tools/search_tasks.py with keyword parameter
- [X] T012 [US1] Register search_tasks tool in backend/src/ai_agent/tools.py with natural language examples
- [X] T013 [US1] Update agent prompt in backend/src/ai_agent/agent.py with search command patterns ("search grocery", "find report")

### Frontend Implementation

- [X] T014 [P] [US1] Create SearchInput component in frontend/src/components/SearchInput.tsx with debounced input (300ms)
- [X] T015 [P] [US1] Create useDebounce hook in frontend/src/hooks/useDebounce.ts for 300ms delay
- [X] T016 [P] [US1] Create useSearch hook in frontend/src/hooks/useSearch.ts with keyword state and API integration

**US1 Completion Criteria**: Users can search by keyword, results are case-insensitive partial matches, debounced input works, tests pass

---

## Phase 4: User Story 2 - Filter by Completion Status (P1)

**Story Goal**: Users can filter tasks to show only completed, incomplete, or all tasks

**Independent Test**: Create mix of completed/incomplete tasks, apply status filter, verify correct subset shown

### Backend Implementation

- [X] T017 [US2] Extend TaskService.search_and_filter_tasks with status_filter parameter (boolean: true/false/null)
- [X] T018 [US2] Update search_tasks MCP tool with status_filter parameter
- [X] T019 [US2] Add status filter patterns to agent prompt ("show completed tasks", "incomplete only")

### Frontend Implementation

- [X] T020 [P] [US2] Create FilterBar component in frontend/src/components/FilterBar.tsx with status dropdown
- [X] T021 [P] [US2] Extend useSearch hook with status filter state

**US2 Completion Criteria**: Users can filter by status (all/completed/incomplete), filters combine with keyword search, tests pass

---

## Phase 5: User Story 3 - Filter by Priority (P2)

**Story Goal**: Users can filter tasks by priority level (high/medium/low/all)

**Independent Test**: Create tasks with different priorities, filter by priority, verify correct subset shown

### Backend Implementation

- [X] T022 [US3] Extend TaskService.search_and_filter_tasks with priority_filter parameter
- [X] T023 [US3] Update search_tasks MCP tool with priority_filter parameter
- [X] T024 [US3] Add priority filter patterns to agent prompt ("show high priority", "medium priority tasks")

### Frontend Implementation

- [X] T025 [P] [US3] Add priority filter dropdown to FilterBar component

**US3 Completion Criteria**: Users can filter by priority, combines with keyword and status filters, tests pass

---

## Phase 6: User Story 4 - Filter by Tags (P2)

**Story Goal**: Users can filter tasks by one or multiple tags with OR logic

**Independent Test**: Create tasks with various tags, filter by tag(s), verify correct tasks returned

### Backend Implementation

- [X] T026 [US4] Extend TaskService.search_and_filter_tasks with tags_filter parameter (array, OR logic)
- [X] T027 [US4] Update search_tasks MCP tool with tags_filter parameter
- [X] T028 [US4] Add tag filter patterns to agent prompt ("show work tasks", "work or urgent tasks")

### Frontend Implementation

- [X] T029 [P] [US4] Add tag multi-select dropdown to FilterBar component
- [X] T030 [P] [US4] Integrate with existing useTags hook from 003-task-tags feature for autocomplete

**US4 Completion Criteria**: Users can filter by tags with OR logic, combines with other filters, tests pass

---

## Phase 7: User Story 5 - Filter by Due Date Range (P2)

**Story Goal**: Users can filter by due date categories (overdue/today/this_week/this_month/no_due_date)

**Independent Test**: Create tasks with various due dates, apply date filter, verify correct subset returned

### Backend Implementation

- [X] T031 [US5] Implement date range calculation helper in backend/src/utils/date_utils.py for overdue, today, this_week, this_month
- [X] T032 [US5] Extend TaskService.search_and_filter_tasks with due_date_filter parameter
- [X] T033 [US5] Update search_tasks MCP tool with due_date_filter parameter
- [X] T034 [US5] Add due date filter patterns to agent prompt ("show overdue tasks", "tasks due today")

### Frontend Implementation

- [X] T035 [P] [US5] Add due date filter dropdown to FilterBar component with preset options
- [X] T036 [P] [US5] Implement date range calculation logic in frontend/src/utils/dateFilters.ts
- [X] T037 [P] [US5] Add "no due date" filter option

**US5 Completion Criteria**: Users can filter by due date categories, handles timezone correctly, combines with other filters, tests pass

---

## Phase 8: User Story 6 - Combined Filters (P3)

**Story Goal**: Users can combine multiple filters simultaneously with AND logic

**Independent Test**: Apply multiple filters together, verify results match all criteria

### Backend Implementation

- [X] T038 [US6] Verify AND logic between all filter types in TaskService.search_and_filter_tasks
- [X] T039 [US6] Add combined filter examples to agent prompt ("search report in incomplete work tasks due today")
- [X] T040 [US6] Implement applied_filters summary in SearchResponse

### Frontend Implementation

- [X] T041 [P] [US6] Add active filters summary display in SearchInput or FilterBar
- [X] T042 [P] [US6] Add "Clear all filters" button
- [X] T043 [P] [US6] Display result count with filter summary ("Showing 5 incomplete work tasks")

**US6 Completion Criteria**: Multiple filters work together with AND logic, users see active filters summary, tests pass

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Complete feature with testing, documentation, optimization, and production readiness

### Performance Optimization

- [X] T044 [P] Implement pagination in TaskService.search_and_filter_tasks (page, page_size parameters)
- [X] T045 [P] Add pagination controls to frontend TaskList component
- [X] T046 [P] Verify composite indexes are being used with EXPLAIN ANALYZE

### Enhanced UX

- [X] T047 [P] Create HighlightedText component in frontend/src/components/HighlightedText.tsx for keyword highlighting in search results
- [X] T048 [P] Add empty state message when no results found ("No tasks found matching your criteria")
- [X] T049 [P] Add loading spinner during search

### Testing

- [X] T050 [P] Create backend/tests/integration/test_search_api.py testing all filter combinations
- [X] T051 [P] Create backend/tests/e2e/test_search_workflow.py testing complete search workflow via chatbot

### Documentation

- [X] T052 [P] Update backend/README.md and frontend/README.md with search feature documentation and examples

**Phase 9 Completion Criteria**: All tests passing, documentation complete, performance optimized (< 500ms for 1,000 tasks), feature production-ready

---

## Dependencies Between User Stories

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
  Phase 3 (US1)              Phase 4 (US2)
  Keyword Search             Status Filter
  [P1 - Independent]         [P1 - Independent]
        ↓                           ↓
        └─────────────┬─────────────┘
                      ↓
        ┌─────────────┴─────────────┬─────────────┐
        ↓                           ↓             ↓
  Phase 5 (US3)              Phase 6 (US4)   Phase 7 (US5)
  Priority Filter            Tags Filter     Date Filter
  [P2 - Independent]         [P2 - Requires  [P2 - Independent]
                              003-task-tags]
        ↓                           ↓             ↓
        └─────────────┬─────────────┴─────────────┘
                      ↓
                 Phase 8 (US6)
                 Combined Filters
                 [P3 - Requires all filters]
                      ↓
                 Phase 9 (Polish)
```

**Key Dependencies:**
- US1 (Keyword Search) + US2 (Status Filter) = **MVP** (must be completed first)
- US3, US4, US5 can be implemented in any order after MVP
- US4 (Tags Filter) requires 003-task-tags feature to be complete
- US6 (Combined Filters) requires all other user stories complete
- Phase 9 (Polish) requires all user stories complete

---

## Parallel Execution Opportunities

**Phase 1 (Setup)** - Can run in parallel:
- T003 (SearchRequest schema) || T004 (SearchResponse schema) [after T001, T002 complete]

**Phase 2 (Foundational)** - Can run in parallel:
- T006 (QueryBuilder) || T008 (Frontend types) || T009 (Frontend results type)

**Phase 3 (US1)** - Can run in parallel:
- T014 (SearchInput) || T015 (useDebounce) || T016 (useSearch) [after backend T010-T013 complete]

**Phase 4 (US2)** - Can run in parallel:
- T020 (FilterBar) || T021 (useSearch extension) [after backend T017-T019 complete]

**Phase 5 (US3)** - Can run in parallel:
- T025 (Priority dropdown) [after backend T022-T024 complete]

**Phase 6 (US4)** - Can run in parallel:
- T029 (Tag dropdown) || T030 (useTags integration) [after backend T026-T028 complete]

**Phase 7 (US5)** - Can run in parallel:
- T035 (Date dropdown) || T036 (Date calculations) || T037 (No due date option) [after backend T031-T034 complete]

**Phase 8 (US6)** - Can run in parallel:
- T041 (Filter summary) || T042 (Clear filters button) || T043 (Result count) [after backend T038-T040 complete]

**Phase 9 (Polish)** - Can run in parallel:
- T044 (Pagination backend) || T045 (Pagination frontend) || T046 (Index verification)
- T047 (HighlightedText) || T048 (Empty state) || T049 (Loading spinner)
- T050 (Integration tests) || T051 (E2E tests) || T052 (Documentation)

---

## Testing Strategy

**Unit Tests** (Fast, isolated):
- Keyword search parsing (case-insensitive, partial match)
- Date range calculations (overdue, today, this_week, etc.)
- QueryBuilder dynamic WHERE clause generation
- Filter combination logic (AND between types, OR within tags)
- Frontend debounce hook behavior

**Integration Tests** (Database + API):
- Search by keyword only
- Filter by each criteria individually
- Combined filters (all combinations)
- Pagination behavior
- Applied filters summary
- User isolation enforcement

**E2E Tests** (Full workflow):
- Complete search workflow via chatbot
- Natural language search commands
- Multiple filter application
- Result display with highlighting

---

## Performance Targets

- **Keyword Search**: < 200ms (with ILIKE + index on title)
- **Single Filter**: < 300ms (with composite indexes)
- **Combined Filters**: < 500ms for 1,000 tasks, < 1s for 10,000 tasks
- **Pagination**: < 100ms per page navigation
- **Debounce**: 300ms delay for optimal UX

---

## Success Metrics

- ✅ All 52 tasks completed
- ✅ 6 user stories independently testable
- ✅ 100% test pass rate (unit + integration + e2e)
- ✅ 1 new MCP tool working (search_tasks)
- ✅ 5 composite indexes created
- ✅ < 500ms search response for 1,000 tasks
- ✅ 95%+ natural language command accuracy
- ✅ Debounced input (300ms) for better UX
- ✅ Keyword highlighting in results
- ✅ Pagination working for large result sets

---

**Tasks File Complete**: 2026-02-14
**Ready for**: `/sp.implement` execution
**Estimated Completion**: 8-12 hours with parallel execution
