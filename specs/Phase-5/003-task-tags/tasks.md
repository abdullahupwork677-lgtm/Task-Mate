# Implementation Tasks: Task Tags & Categories

**Feature**: 003-task-tags
**Branch**: `003-task-tags`
**Created**: 2026-02-14
**Estimated Time**: 6-8 hours

---

## Task Summary

- **Total Tasks**: 45
- **Phases**: 8 (Setup → 5 User Stories → Polish)
- **Parallel Opportunities**: 18 tasks marked [P]
- **Dependencies**: Priority-based user story execution

**Task Distribution by Phase:**
- Phase 1 (Setup): 6 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (US1 - Add Tags on Create): 8 tasks
- Phase 4 (US4 - Visual Tag Indicators): 6 tasks
- Phase 5 (US2 - Add/Remove Tags): 6 tasks
- Phase 6 (US3 - Filter by Tags): 5 tasks
- Phase 7 (US5 - List All Tags): 4 tasks
- Phase 8 (Polish): 6 tasks

---

## Implementation Strategy

**MVP Scope** (Deliver First):
- Phase 1-2: Setup + Foundational (required infrastructure)
- Phase 3: User Story 1 (Add tags when creating tasks)
- Phase 4: User Story 4 (Visual indicators - required for MVP UX)

**Incremental Delivery** (After MVP):
- Phase 5: User Story 2 (Modify existing task tags)
- Phase 6: User Story 3 (Filter by tags)
- Phase 7: User Story 5 (List all tags)
- Phase 8: Polish & Cross-Cutting

**Independent Testing**: Each user story phase includes all necessary components (models, services, MCP tools, UI) to be independently tested and delivered.

---

## Phase 1: Project Setup

**Goal**: Initialize database schema, create tag service foundation

- [X] T001 Create Alembic migration for tags JSONB column in backend/alembic/versions/add_tags_to_tasks.py
- [X] T002 Add tags field to Task model in backend/src/models.py with List[str] type and JSON column
- [X] T003 [P] Add tags field to TaskBase, TaskCreate, TaskUpdate schemas in backend/src/schemas.py with Pydantic validation
- [X] T004 [P] Create TagService class in backend/src/services/tag_service.py with normalize_tags, generate_tag_color, validate_tag methods
- [X] T005 [P] Create tag utility functions in backend/src/utils/color_generator.py for hash-based color generation
- [X] T006 Apply migration and verify tags column exists with GIN index using alembic upgrade head

**Completion Criteria**: Database has tags JSONB column + GIN index, Task model has tags field, TagService exists ✅

---

## Phase 2: Foundational Components

**Goal**: Create shared schemas and extend task service with tag operations

- [X] T007 [P] Create tag-specific schemas in backend/src/schemas/tag.py (AddTagRequest, RemoveTagRequest, ListTagsResponse, TagInfo)
- [X] T008 Extend TaskService in backend/src/services/task_service.py with add_tags_to_task method
- [X] T009 Extend TaskService with remove_tags_from_task method
- [X] T010 Extend TaskService with list_user_tags method using jsonb_array_elements_text

**Completion Criteria**: Tag schemas defined, TaskService has 3 new methods for tag operations ✅

---

## Phase 3: User Story 1 - Add Tags When Creating Tasks (P1)

**Story Goal**: Users can assign tags to tasks during creation via chatbot ("add task buy groceries, tags: shopping, urgent")

**Independent Test**: Create tasks with various tag combinations via chatbot and verify tags are stored and displayed

### Backend Implementation

- [X] T011 [US1] Extend add_task MCP tool in backend/src/mcp_tools/add_task.py to accept optional tags parameter
- [X] T012 [US1] Update add_task tool contract in backend/src/mcp_tools/add_task.py with tags schema and examples
- [X] T013 [US1] Update agent prompt in backend/src/ai_agent/agent.py with tag creation examples ("add task X, tags: A, B")
- [X] T014 [US1] Add regex pattern for tag suffix parsing (N/A - LLM handles extraction via natural language)

### Testing

- [X] T015 [P] [US1] Create test_tag_normalization.py in backend/tests/unit/ with cases for lowercase, dedup, validation
- [X] T016 [P] [US1] Create test_add_task_with_tags.py in backend/tests/integration/ with API tests for tag creation
- [X] T017 [P] [US1] Create test_chatbot_tag_parsing.py in backend/tests/integration/ for natural language tag extraction

**US1 Completion Criteria**: Tasks can be created with tags via chatbot, tags are normalized and stored, tests pass

---

## Phase 4: User Story 4 - Visual Tag Indicators (P1)

**Story Goal**: Tasks display color-coded badges with consistent, distinct colors

**Independent Test**: View tasks with different tags and verify badges display with consistent colors

### Frontend Implementation

- [X] T018 [P] [US4] Create TagBadge component in frontend/src/components/TagBadge.tsx with inline styles and color generation
- [X] T019 [P] [US4] Create tag color utilities in frontend/src/utils/tagColors.ts matching backend hash algorithm
- [X] T020 [P] [US4] Add tags field to Task type in frontend/lib/types.ts as string array
- [X] T021 [US4] Update TaskCard component in frontend/components/TaskItem.tsx to display tag badges
- [X] T022 [P] [US4] Create TagBadge.test.tsx in frontend/tests/unit/ testing color generation and rendering
- [X] [US4] Create tagColors.test.ts in frontend/tests/unit/ verifying hash algorithm matches backend

**US4 Completion Criteria**: Tasks display color-coded tag badges, colors are consistent per tag, tests pass

---

## Phase 5: User Story 2 - Add/Remove Tags from Existing Tasks (P2)

**Story Goal**: Users can modify tags on existing tasks ("add tag urgent to task 5", "remove tag work from task 3")

**Independent Test**: Create task, add/remove tags via chatbot, verify changes reflected

### Backend Implementation

- [X] T024 [US2] Create add_tag MCP tool in backend/src/mcp_tools/add_tag.py calling task_service.add_tags_to_task
- [X] T025 [US2] Create remove_tag MCP tool in backend/src/mcp_tools/remove_tag.py calling task_service.remove_tags_from_task
- [X] T026 [US2] Register add_tag and remove_tag tools in backend/src/ai/agent.py tools list
- [X] T027 [US2] Add regex patterns for "add tag X to task N" and "remove tag X from task N" in backend/src/ai/agent.py

### Testing

- [X] T028 [P] [US2] Create test_add_remove_tags_api.py in backend/tests/integration/ testing tag modification endpoints
- [X] T029 [P] [US2] Create test_tag_edge_cases.py in backend/tests/integration/ for duplicate detection, case-insensitive matching

**US2 Completion Criteria**: Users can add/remove tags from existing tasks via chatbot, duplicate detection works, tests pass

---

## Phase 6: User Story 3 - Filter Tasks by Tags (P2)

**Story Goal**: Users can view filtered tasks by tags ("show work tasks", "list shopping and urgent tasks")

**Independent Test**: Create tasks with different tags, request filtered views, verify correct tasks returned

### Backend Implementation

- [X] T030 [US3] Extend list_tasks MCP tool in backend/src/mcp_tools/list_tasks.py with tag_filter parameter
- [X] T031 [US3] Update TaskService.get_user_tasks in backend/src/services/task_service.py to support tag filtering with OR logic
- [X] T032 [US3] Add regex patterns for "show [tag] tasks" in backend/src/ai/agent.py
- [X] T033 [US3] Update agent prompt in backend/src/ai/agent.py with tag filtering examples

### Testing

- [X] T034 [P] [US3] Create test_tag_filtering.py in backend/tests/integration/ testing single and multiple tag filters with OR logic

**US3 Completion Criteria**: Users can filter tasks by single or multiple tags via chatbot, OR logic works, tests pass

---

## Phase 7: User Story 5 - List All Available Tags (P3)

**Story Goal**: Users can request list of all tags ("show me all my tags")

**Independent Test**: Create tasks with various tags, request tag list, verify all unique tags returned

### Backend Implementation

- [X] T035 [US5] Create list_tags MCP tool in backend/src/mcp_tools/list_tags.py calling task_service.list_user_tags
- [X] T036 [US5] Register list_tags tool in backend/src/ai/agent.py tools list
- [X] T037 [US5] Add regex pattern for "show all tags" in backend/src/ai/agent.py

### Testing

- [X] T038 [P] [US5] Create test_list_tags.py in backend/tests/integration/ testing tag listing with counts and colors

**US5 Completion Criteria**: Users can list all tags via chatbot with counts and colors, tests pass

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Complete feature with comprehensive testing, documentation, and production readiness

### Frontend Polish

- [X] T039 [P] Create TagInput component in frontend/src/components/TagInput.tsx for tag entry with autocomplete
- [X] T040 [P] Create useTags hook in frontend/src/hooks/useTags.ts for tag management state

### E2E Testing

- [X] T041 [P] Create test_tag_workflow.py in backend/tests/e2e/ testing complete tag lifecycle via chatbot

### Documentation

- [X] T042 [P] Update backend README.md with tag feature documentation and MCP tool examples
- [X] T043 [P] Update frontend README.md with TagBadge and TagInput component usage

### Production Readiness

- [X] T044 Verify all 6 MCP tools (3 new + 3 extended) registered and working
- [X] T045 Run full test suite (unit + integration + e2e) and verify 100% pass rate

**Phase 8 Completion Criteria**: All tests passing, documentation complete, feature production-ready

---

## Dependencies Between User Stories

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
        ┌─────────────┴─────────────┐
        ↓                           ↓
  Phase 3 (US1)              Phase 3 (US1)
  Add Tags on Create         Add Tags on Create
        ↓                           ↓
  Phase 4 (US4)              Phase 4 (US4)
  Visual Indicators          Visual Indicators
        ↓                           ↓
        └─────────────┬─────────────┘
                      ↓
        ┌─────────────┴─────────────┬─────────────┐
        ↓                           ↓             ↓
  Phase 5 (US2)              Phase 6 (US3)   Phase 7 (US5)
  Add/Remove Tags            Filter Tags     List Tags
  (depends on US1+US4)       (depends on US1) (depends on US1)
        ↓                           ↓             ↓
        └─────────────┬─────────────┴─────────────┘
                      ↓
                 Phase 8 (Polish)
```

**Key Dependencies:**
- US1 (Add Tags) + US4 (Visual Indicators) = **MVP** (must be completed first)
- US2 (Modify Tags) depends on US1 + US4 being complete
- US3 (Filter) depends on US1 being complete
- US5 (List) depends on US1 being complete
- All user stories must complete before Phase 8 (Polish)

---

## Parallel Execution Opportunities

**Phase 1 (Setup)** - Can run in parallel:
- T003 (schemas) || T004 (TagService) || T005 (color utils) [after T002 completes]

**Phase 2 (Foundational)** - Can run in parallel:
- T007 (tag schemas) is independent and can run anytime

**Phase 3 (US1)** - Can run in parallel:
- T015 (unit tests) || T016 (integration tests) || T017 (chatbot tests) [after backend implementation]

**Phase 4 (US4)** - Can run in parallel:
- T018 (TagBadge) || T019 (color utils) || T020 (types) [independent]
- T022 (TagBadge tests) || T023 (color tests) [after components complete]

**Phase 5 (US2)** - Can run in parallel:
- T028 (integration tests) || T029 (edge case tests) [after MCP tools complete]

**Phase 6 (US3)** - Can run in parallel:
- T034 (filtering tests) [after backend implementation]

**Phase 7 (US5)** - Can run in parallel:
- T038 (list tags tests) [after MCP tool complete]

**Phase 8 (Polish)** - Can run in parallel:
- T039 (TagInput) || T040 (useTags hook) || T041 (E2E tests) || T042 (backend docs) || T043 (frontend docs)

---

## Testing Strategy

**Unit Tests** (Fast, isolated):
- Tag normalization (lowercase, deduplication)
- Color generation (deterministic, consistent)
- Tag validation (alphanumeric, max length)
- Frontend color utilities (matches backend algorithm)

**Integration Tests** (Database + API):
- Create task with tags via API
- Add/remove tags from existing tasks
- Filter tasks by single/multiple tags
- List all user tags with counts
- Chatbot natural language parsing

**E2E Tests** (Full workflow):
- Complete tag lifecycle via chatbot
- Visual badge display and consistency
- Tag modification workflow
- Filter and list operations

---

## Performance Targets

- **Tag Filtering**: < 100ms (with GIN index)
- **Color Generation**: < 1ms (client-side hash)
- **Tag Addition**: < 2s end-to-end (chatbot → database → UI)
- **Tag Normalization**: < 1ms (Python lowercase + dedup)

---

## Success Metrics

- ✅ All 45 tasks completed
- ✅ 5 user stories independently testable
- ✅ 100% test pass rate (unit + integration + e2e)
- ✅ 6 MCP tools working (3 new + 3 extended)
- ✅ Tags display with consistent colors
- ✅ < 100ms tag filtering performance
- ✅ 95%+ natural language command accuracy

---

**Tasks File Complete**: 2026-02-14
**Ready for**: `/sp.implement` execution
**Estimated Completion**: 6-8 hours with parallel execution
