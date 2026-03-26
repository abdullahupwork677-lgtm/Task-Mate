---
id: 0002
title: task-tags-implementation-planning
stage: plan
date: 2026-02-14
surface: claude-code
model: claude-sonnet-4-5
feature: 003-task-tags
branch: 003-task-tags
user: apple
command: /sp.plan
labels: [planning, intermediate-features, phase-5]
links:
  spec: specs/003-task-tags/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - path: specs/003-task-tags/plan.md
    type: created
    lines: 150+
  - path: specs/003-task-tags/research.md
    type: created
    lines: 520+
  - path: specs/003-task-tags/data-model.md
    type: created
    lines: 850+
  - path: specs/003-task-tags/contracts/add_tag_mcp.json
    type: created
    lines: 250+
  - path: specs/003-task-tags/contracts/remove_tag_mcp.json
    type: created
    lines: 200+
  - path: specs/003-task-tags/contracts/list_tags_mcp.json
    type: created
    lines: 180+
  - path: specs/003-task-tags/quickstart.md
    type: created
    lines: 450+
tests:
  - none (planning phase - test specs documented in contracts and data-model.md)
---

## Prompt

User invoked `/sp.plan` for Task Tags & Categories feature (003-task-tags).

**Context:**
- User had previously completed planning for 005-task-sort feature
- User checked 003-task-tags and 004-search-filter directories and found only spec.md files
- User requested planning for both features, I recommended starting with 003-task-tags (no dependencies)
- User explicitly requested: "start with 003-task-tags"
- Feature specification completed and validated (218 lines)
- Branch: 003-task-tags (switched from 005-task-sort)

**Planning Task:**
Execute implementation planning workflow to generate:
1. Technical Context analysis
2. Constitution Check validation
3. Phase 0: Research (7 research questions resolved)
4. Phase 1: Design & Contracts (data model, MCP contracts, integration guide)
5. Agent context update

## Response snapshot

**Phase 0: Outline & Research (research.md)** ✅

Completed comprehensive technical research covering 7 key areas:
1. **JSON Array Storage**: PostgreSQL JSONB with GIN index (not separate table)
2. **Case-Insensitive Normalization**: Lowercase storage, prevents duplicates
3. **Color Generation**: Hash-based deterministic (MD5 → hex color + brightness adjustment)
4. **MCP Tools Architecture**: 3 NEW tools (add_tag, remove_tag, list_tags) + 3 EXTENDED tools (add_task, update_task, list_tasks)
5. **Natural Language Parsing**: Regex patterns + GPT-4 fallback for ambiguous cases
6. **Frontend Badge Component**: React component with inline styles, client-side hash generation
7. **Database Migration**: Add JSONB column with default empty array, GIN index for filtering

**Key Technical Decisions:**
- PostgreSQL JSONB array (not TEXT[], not separate table) - flexible, queryable, indexed
- Case-insensitive tags (lowercase normalization) - prevents "Work" vs "work" duplicates
- Hash-based colors (MD5 hex → brightness adjustment) - deterministic, infinite colors, readable
- 3 new + 3 extended MCP tools - clear intent, natural language aligned
- Backward compatible tool extensions (defaults work with existing code)

**Phase 1: Design & Contracts (data-model.md, contracts/, quickstart.md)** ✅

1. **Data Model (data-model.md - 850+ lines)**:
   - Schema change: Add tags JSONB column with default [], GIN index
   - SQLModel pattern: `tags: List[str] = Field(default=[], sa_column=Column(JSON))`
   - Query patterns: `.contains()` for single tag, `or_()` for multiple tags OR logic
   - Service layer: TagService (normalize, color generation, validation) + TaskService extensions
   - Pydantic schemas: TaskBase/Create/Update with tags validation, AddTagRequest, RemoveTagRequest, ListTagsResponse
   - Performance: GIN index gives 10-100x speedup for tag filtering
   - Migration: Alembic migration with JSONB column + GIN index (instant, backward compatible)
   - Frontend integration: TypeScript types, client-side color generation (matches backend)

2. **API Contracts (contracts/ - 3 files, 630+ lines)**:
   - **add_tag_mcp.json**: Add tags to existing task, deduplicate, enforce 20 tag limit
   - **remove_tag_mcp.json**: Remove tags from task, case-insensitive, non-existent tags silently ignored
   - **list_tags_mcp.json**: List all user's tags with counts and colors, sorted by usage
   - All contracts include: natural language examples, error handling, test cases, agent prompt guidance

3. **Integration Guide (quickstart.md - 450+ lines)**:
   - Step-by-step implementation (8 steps, 6-8 hours total)
   - Database migration with code snippets
   - SQLModel and schema updates
   - Tag service creation (normalize, color, validate)
   - Task service extensions (add/remove tags, filter by tags, list tags)
   - 3 new MCP tools + 3 extended MCP tools
   - Agent prompt updates
   - Frontend components (TagBadge, TagInput, TaskCard extensions)
   - Testing checklist (backend pytest, frontend Jest, E2E Playwright)
   - Deployment checklist and troubleshooting guide

**Constitution Check** ✅

All 13 principles validated:
- Principles I-IX: ✅ PASSED (no violations)
- Principles X-XIII (Event-Driven): ⚪ N/A (tags are synchronous CRUD, no Kafka/Dapr needed)

**Gate Result:** PASSED - Simple database extension with JSONB, MCP tool creation, no infrastructure changes

**Technical Context** ✅

- Language: Python 3.13+ (Backend), TypeScript (Frontend)
- Stack: FastAPI, SQLModel, PostgreSQL JSONB, Next.js 14, Tailwind, React
- Performance: < 100ms tag filtering, < 1ms color generation
- Schema change: Add tags JSONB column + GIN index
- 6 MCP tools: 3 new (add_tag, remove_tag, list_tags) + 3 extended (add_task, update_task, list_tasks)

**Agent Context Update** ✅

Updated `CLAUDE.md` with Task Tags feature technology stack.

## Outcome

- ✅ Impact: Complete implementation plan ready for `/sp.tasks` - First of 3 Intermediate features (Tags → Search/Filter → Sort)
- 🧪 Tests: Test specifications documented in contracts and data-model.md (unit tests, integration tests, E2E scenarios)
- 📁 Files: Created 7 planning artifacts (plan.md, research.md, data-model.md, 3 contracts, quickstart.md) - 2,600+ lines total
- 🔁 Next prompts: Execute `/sp.tasks` to generate task breakdown for implementation
- 🧠 Reflection: Task Tags is foundational for Search/Filter feature. JSONB with GIN index provides flexible, performant tag storage. Hash-based colors ensure consistent visual identity without database storage. All technical questions resolved in research phase.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): Constitution Check - PASS (all principles satisfied, no violations)
- Prompt variant (if applicable): Standard `/sp.plan` workflow with comprehensive research phase
- Next experiment (smallest change to try): Proceed to `/sp.tasks` for implementation task breakdown
