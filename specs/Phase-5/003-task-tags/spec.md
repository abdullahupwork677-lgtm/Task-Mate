# Feature Specification: Task Tags & Categories

**Feature Branch**: `003-task-tags`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Feature: Task Tags & Categories - Organize tasks with custom labels. As a user, I want to organize my tasks with custom tags/labels (like work, home, personal, shopping, urgent) so that I can group related tasks together and find them easily."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Tags When Creating Tasks (Priority: P1)

Users can assign one or more custom tags to tasks when creating them through the AI chatbot using natural language commands.

**Why this priority**: This is the foundation of the tag system. Without the ability to add tags during task creation, users cannot begin organizing their tasks. It's the most critical functionality that enables all other tag-related features.

**Independent Test**: Can be fully tested by creating tasks with various tag combinations via chatbot (e.g., "add task buy groceries, tags: shopping, urgent") and verifying tags are correctly stored and displayed. Delivers immediate value by allowing users to categorize tasks from the start.

**Acceptance Scenarios**:

1. **Given** user is in chat interface, **When** user types "add task buy groceries, tags: shopping, urgent", **Then** system creates task with tags array ["shopping", "urgent"]
2. **Given** user is in chat interface, **When** user types "add task call mom" (no tags specified), **Then** system creates task with empty tags array []
3. **Given** user types "add task pay bills tags: finance, urgent, home", **When** task is created, **Then** system stores all three tags in lowercase: ["finance", "urgent", "home"]
4. **Given** user created a task with tags, **When** task is displayed in task list, **Then** task shows color-coded badges for each tag

---

### User Story 2 - Add/Remove Tags from Existing Tasks (Priority: P2)

Users can modify the tags on existing tasks by adding new tags or removing existing ones through natural language commands.

**Why this priority**: Tasks evolve over time, and their categorization needs change. This allows users to maintain accurate organization without recreating tasks. Essential for maintaining a well-organized task system.

**Independent Test**: Can be tested by creating a task, then adding/removing tags through chatbot and verifying changes are reflected. Delivers value by enabling flexible task organization.

**Acceptance Scenarios**:

1. **Given** task "Buy groceries" exists with tags ["shopping"], **When** user says "add tag urgent to task 5", **Then** system updates task tags to ["shopping", "urgent"]
2. **Given** task exists with tags ["work", "urgent", "meeting"], **When** user says "remove tag urgent from task 3", **Then** system updates tags to ["work", "meeting"]
3. **Given** user wants to add multiple tags, **When** user says "add tags home and family to task 2", **Then** system adds both tags to existing tags
4. **Given** task has tag "Work" (capitalized), **When** user tries to add tag "work" (lowercase), **Then** system recognizes duplication and skips (case-insensitive)

---

### User Story 3 - Filter Tasks by Tags (Priority: P2)

Users can view tasks filtered by one or multiple tags through natural language queries to the AI chatbot.

**Why this priority**: Enables users to focus on specific categories of tasks. Nice-to-have feature that enhances productivity but not critical for MVP. Users can still see all tasks and manually identify tags.

**Independent Test**: Can be tested by creating tasks with different tags, then requesting filtered views via chatbot. Delivers value by helping users focus on specific task categories.

**Acceptance Scenarios**:

1. **Given** user has tasks with mixed tags, **When** user asks "show me all work tasks", **Then** system displays only tasks containing "work" tag
2. **Given** user has tasks tagged with shopping, **When** user requests "list shopping and urgent tasks", **Then** system shows tasks with EITHER shopping OR urgent tags
3. **Given** user has 20 tasks but only 3 have "finance" tag, **When** user filters by finance, **Then** system returns exactly 3 tasks
4. **Given** no tasks exist with requested tag, **When** user asks "show personal tasks" and none exist, **Then** system responds "You have no tasks with tag 'personal'"

---

### User Story 4 - Visual Tag Indicators (Priority: P1)

Tasks display color-coded tag badges that are visually distinct, with consistent colors per tag across the application.

**Why this priority**: Visual indicators are essential for quick task scanning and categorization. Without this, users cannot easily identify task categories at a glance, defeating the purpose of the tag system.

**Independent Test**: Can be tested by viewing tasks with different tags and verifying badges display with consistent, distinct colors. Delivers immediate value through improved task visibility.

**Acceptance Scenarios**:

1. **Given** task has tag "work", **When** user views task in task list, **Then** task displays color-coded badge with label "work"
2. **Given** task has tags ["shopping", "urgent", "home"], **When** user views task, **Then** task displays three separate badges, each with distinct color
3. **Given** multiple tasks have "work" tag, **When** user views task list, **Then** all "work" badges show the same consistent color
4. **Given** user creates a new custom tag "exercise", **When** task with this tag is displayed, **Then** system auto-generates a color that is distinct from existing tags

---

### User Story 5 - List All Available Tags (Priority: P3)

Users can request a list of all tags currently in use across their tasks to understand available categories.

**Why this priority**: Helps users discover what tags they've created and maintain consistency. Useful for organizing but not critical for basic tag functionality.

**Independent Test**: Can be tested by creating tasks with various tags, then requesting tag list and verifying all unique tags are returned. Delivers value through better tag management.

**Acceptance Scenarios**:

1. **Given** user has tasks with tags ["work", "home", "urgent", "shopping"], **When** user asks "show me all my tags", **Then** system lists all unique tags: work, home, urgent, shopping
2. **Given** user has no tasks with tags, **When** user requests tag list, **Then** system responds "You haven't created any tags yet"
3. **Given** multiple tasks use the same tag, **When** user requests tag list, **Then** each tag appears only once (deduplicated)

---

### Edge Cases

- What happens when user tries to add duplicate tag to same task? System recognizes case-insensitive duplication (Work = work) and skips without error
- How does system handle very long tag names (e.g., 50+ characters)? System accepts but truncates display in UI to 20 characters with ellipsis, full name shown on hover
- What if user creates a tag with special characters (e.g., "work/home" or "urgent!!!")? System accepts alphanumeric and basic punctuation, normalizes to lowercase
- What happens when user has 100+ unique tags? System displays all tags in list but implements autocomplete in UI for easier selection
- How are tags handled when task is marked complete? Tags remain unchanged; completed tasks retain their tags for historical filtering
- What if user tries to filter by non-existent tag? System returns friendly "No tasks found with tag '[tagname]'"
- How does system handle emoji in tag names? System accepts unicode characters including emoji (e.g., "🏠 home" is valid)
- What happens when user deletes last task with a specific tag? Tag still exists in system (available for future use) unless explicitly deleted by user

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support custom user-defined tags with no predefined list
- **FR-002**: System MUST allow multiple tags per task (recommended 1-10 tags, no hard limit)
- **FR-003**: System MUST store tags as an array of strings in the tasks table (JSON field)
- **FR-004**: System MUST treat tags as case-insensitive (normalize to lowercase on storage: Work → work)
- **FR-005**: System MUST prevent duplicate tags on the same task
- **FR-006**: System MUST allow users to add tags when creating tasks via natural language: "add task [title], tags: [tag1, tag2]"
- **FR-007**: System MUST allow users to add tags to existing tasks via natural language: "add tag [tagname] to task [id]"
- **FR-008**: System MUST allow users to remove tags from existing tasks via natural language: "remove tag [tagname] from task [id]"
- **FR-009**: System MUST allow users to filter tasks by single tag: "show [tagname] tasks"
- **FR-010**: System MUST allow users to filter tasks by multiple tags (OR logic): "show [tag1] and [tag2] tasks"
- **FR-011**: System MUST display tags as color-coded badges in the task list UI
- **FR-012**: System MUST assign consistent colors to tags (same tag always gets same color)
- **FR-013**: System MUST auto-generate distinct colors for new tags using a deterministic algorithm (e.g., hash-based color generation)
- **FR-014**: System MUST provide a way to list all unique tags used across user's tasks
- **FR-015**: AI chatbot MUST recognize tag-related commands and extract tag names from natural language
- **FR-016**: System MUST include tags in MCP tool responses (add_task, update_task, list_tasks)
- **FR-017**: System MUST validate tag names (alphanumeric, spaces, basic punctuation, max 50 characters)
- **FR-018**: System MUST persist tags in database alongside other task attributes

### Key Entities

- **Task**: Existing entity that now includes a tags field
  - Attributes: id, user_id, title, description, completed, created_at, updated_at, priority, due_date, **tags** (new)
  - Tags format: JSON array of strings, e.g., ["work", "urgent", "shopping"]
  - Default tags: Empty array []
  - Tags are case-insensitive, stored in lowercase

- **Tag Badge**: Visual component (not stored in database)
  - Represents: Visual indicator of a tag on a task
  - Properties: tag_name (string), color (hex code, auto-generated), displayed in task list and task detail views

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add tags to tasks in under 5 seconds using natural language
- **SC-002**: Tag colors are visually distinguishable (minimum 12 distinct colors for common tags)
- **SC-003**: Users can successfully filter tasks by tags with 100% accuracy
- **SC-004**: System correctly interprets tag commands from natural language with 95% accuracy
- **SC-005**: Tag updates via chatbot complete within 2 seconds and are immediately reflected in UI
- **SC-006**: Users can identify task categories at a glance using tag badges (no need to read full task details)
- **SC-007**: Same tag always displays with the same color across all views (100% consistency)
- **SC-008**: System handles up to 100 unique tags per user without performance degradation

## Assumptions

- Users are familiar with tagging systems (common in email, notes, project management apps)
- Color-coding provides sufficient visual distinction (no icon-based tags needed for MVP)
- Database schema can be modified to add tags JSON field to tasks table
- AI chatbot has sufficient natural language processing to extract tag keywords
- Frontend framework supports dynamic badge components with custom colors
- No limit on number of unique tags system-wide (users create as many as needed)
- Tags are user-specific (not shared across users)
- Basic color palette (12-24 colors) is sufficient for common use cases
- Tags are used for categorization only (no advanced features like tag hierarchies or tag-based permissions)

## Scope

### In Scope

- Adding tags field (JSON array) to task data model
- Updating create_task MCP tool to accept tags parameter
- Updating update_task MCP tool to support adding/removing tags
- Creating add_tag MCP tool for adding tags to existing tasks
- Creating remove_tag MCP tool for removing tags from tasks
- Creating list_tags MCP tool to list all unique tags for a user
- Enhancing list_tasks MCP tool to support tag filtering (single or multiple tags)
- Training AI chatbot to recognize tag keywords in natural language
- Implementing color-coded tag badges in frontend
- Auto-generating consistent colors for tags using deterministic algorithm (e.g., hash-based)
- Supporting case-insensitive tag matching (Work = work)
- Preventing duplicate tags on same task

### Out of Scope

- Predefined tag categories (users define their own)
- Tag hierarchies or nested tags (e.g., Work > Projects > Client A)
- Tag-based permissions or access control
- Tag sharing between users
- Tag analytics or usage statistics
- Tag suggestions based on task content (AI-powered auto-tagging)
- Bulk tag operations (tagging multiple tasks at once)
- Tag renaming across all tasks (manual re-tagging only)
- Icon-based tags (text-only badges)
- Custom user-defined colors for tags (system auto-generates)
- Tag export/import functionality

## Dependencies

- Existing task CRUD operations (add, update, list)
- Existing MCP tools infrastructure
- AI chatbot with OpenAI Agents SDK integration
- Database migration capabilities (Alembic)
- Frontend component library for badge rendering
- Color generation algorithm (hash-based or predefined palette)

## Non-Functional Requirements

- **Performance**: Tag filtering should not add more than 100ms to task list query time
- **Scalability**: System should handle up to 100 unique tags per user without performance impact
- **Usability**: Tag badges should be readable at a glance (minimum 12px font size)
- **Accessibility**: Tag colors must maintain minimum WCAG 2.1 AA contrast ratio (4.5:1) against background
- **Maintainability**: Tag color generation should be deterministic (same tag always same color)
- **Security**: Tag operations must respect user isolation (users can only modify their own task tags)
- **Consistency**: Tag names are normalized to lowercase on storage to prevent case-sensitive duplicates

## Open Questions

*None at this time - specification is complete and ready for planning phase.*
