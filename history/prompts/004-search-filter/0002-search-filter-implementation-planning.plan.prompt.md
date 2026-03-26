---
id: 0002
title: search-filter-implementation-planning
stage: plan
date: 2026-02-14
surface: claude-code
model: claude-sonnet-4-5
feature: 004-search-filter
branch: 004-search-filter
user: apple
command: /sp.plan
labels: [planning, intermediate-features, phase-5]
links:
  spec: specs/004-search-filter/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - path: specs/004-search-filter/plan.md
    type: created
    lines: 153
  - path: specs/004-search-filter/research.md
    type: created
    lines: 950+
  - path: specs/004-search-filter/contracts/search_tasks_mcp.json
    type: created
    lines: 200+
  - path: specs/004-search-filter/quickstart.md
    type: created
    lines: 450+
tests:
  - none (planning phase - test specs documented in contracts and quickstart.md)
---

## Prompt

User requested planning for Task Search & Advanced Filtering feature (004-search-filter) after completing 003-task-tags planning.

**Context:**
- User completed planning for 003-task-tags feature (2,600+ lines)
- User explicitly requested: "Search/Filter feature (004) should be planned next"
- Feature specification completed and validated (227 lines)
- Branch: 004-search-filter (switched from 003-task-tags)
- Dependencies: Priority, Tags, and Due Dates features MUST be implemented first

**Planning Task:**
Execute implementation planning workflow to generate:
1. Technical Context analysis
2. Constitution Check validation
3. Phase 0: Research (7 research questions resolved)
4. Phase 1: Design & Contracts (quickstart guide, MCP contract)
5. Agent context update

## Response snapshot

**Phase 0: Outline & Research (research.md)** ✅

Completed comprehensive technical research covering 7 key areas:
1. **Keyword Search**: PostgreSQL ILIKE with functional indexes (user_id, LOWER(title/description))
2. **Multi-Field Filtering**: Dynamic WHERE clause building, AND logic between filter types, OR logic within tag filters
3. **Performance Optimization**: 5 composite indexes, pagination, query optimization (< 500ms for 10,000 tasks)
4. **Natural Language Search**: Regex patterns + GPT-4 fallback for complex queries
5. **Debounced Input**: Frontend debouncing (300ms) with useDebounce hook
6. **Keyword Highlighting**: Client-side React component (safe, no HTML injection)
7. **MCP Tool Contract**: Single search_tasks tool with all filter parameters (optional)

**Key Technical Decisions:**
- PostgreSQL ILIKE (not full-text search) - sufficient for < 10,000 tasks
- NO schema changes - all fields exist (title, description, completed, priority, tags, due_date)
- 5 NEW composite indexes - dramatic performance improvement
- Dynamic WHERE clause - flexible, database-optimized
- Frontend debouncing - prevents excessive API calls
- Single MCP tool - clear intent, all filters in one call

**Phase 1: Design & Contracts (plan.md, quickstart.md, contracts/)** ✅

1. **Plan (plan.md - 153 lines)**:
   - Technical Context: Python 3.13+, PostgreSQL ILIKE + indexes, Next.js 14
   - Constitution Check: All 13 principles validated, GATE PASSED
   - NO schema changes, only 5 indexes for performance
   - Project Structure: Backend service extension, frontend search components

2. **Quickstart Guide (quickstart.md - 450+ lines)**:
   - Prerequisites check (priority, tags, due dates MUST exist first)
   - 9-step implementation guide (8-12 hours total)
   - Database migration (5 composite indexes)
   - Service layer (search_and_filter_tasks method with dynamic WHERE)
   - Schemas (SearchRequest, SearchResponse)
   - REST API endpoint (GET /tasks/search)
   - MCP tool (search_tasks with all filters)
   - Agent prompt updates (regex patterns + examples)
   - 4 frontend components (SearchInput, FilterBar, HighlightedText, TaskList)
   - 2 frontend hooks (useDebounce, useSearch)
   - Testing checklist (backend, frontend, E2E)
   - Deployment guide and troubleshooting

3. **MCP Contract (search_tasks_mcp.json - 200+ lines)**:
   - All filter parameters optional
   - Natural language examples (5 scenarios)
   - Performance requirements (< 500ms for 1,000 tasks)
   - Agent prompt guidance
   - 6 test cases

**Constitution Check** ✅

All 13 principles validated:
- Principles I-IX: ✅ PASSED (no violations)
- Principles X-XIII (Event-Driven): ⚪ N/A (search/filter are synchronous queries, no Kafka/Dapr needed)

**Gate Result:** PASSED - Pure query feature with no state changes, uses existing fields with new indexes

**Technical Context** ✅

- Language: Python 3.13+ (Backend), TypeScript (Frontend)
- Stack: FastAPI, SQLModel, PostgreSQL ILIKE, Next.js 14, React
- Performance: < 500ms for 1,000 tasks, < 1s for 10,000 tasks
- NO schema changes (all fields exist)
- 5 NEW composite indexes for performance
- 1 NEW MCP tool (search_tasks with all filter parameters)

**Agent Context Update** ✅

Updated `CLAUDE.md` with Task Search & Filtering technology stack.

## Outcome

- ✅ Impact: Complete implementation plan ready for `/sp.tasks` - Second of 3 Intermediate features (Tags → Search/Filter → Sort)
- 🧪 Tests: Test specifications documented in quickstart.md (unit tests, integration tests, E2E scenarios)
- 📁 Files: Created 4 planning artifacts (plan.md, research.md, contracts/search_tasks_mcp.json, quickstart.md) - 1,750+ lines total
- 🔁 Next prompts: **CRITICAL:** Implement 003-task-tags first (dependency), then execute `/sp.tasks` for 004-search-filter
- 🧠 Reflection: Search/Filter depends on Tags being implemented. NO schema changes needed (all fields exist), but 5 indexes critical for performance. PostgreSQL ILIKE sufficient for < 10,000 tasks. Single search_tasks MCP tool with flexible parameters simplifies agent integration.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): Constitution Check - PASS (all principles satisfied, no violations)
- Prompt variant (if applicable): Standard `/sp.plan` workflow with comprehensive research phase
- Next experiment (smallest change to try): **CRITICAL DEPENDENCY:** Must implement 003-task-tags before implementing 004-search-filter (tags_filter parameter depends on tags feature)
