# Skill Learning Coach Memory

## Purpose
Capture learnings from completed features to update and evolve skills in `.claude/skills/`.

## Common Skill Quality Issues

1. **Missing Edge Cases** - Skills often lack documented edge cases discovered during implementation
2. **Incomplete Examples** - Examples directory missing or has only simple "happy path" scenarios
3. **No Testing Strategy** - Skills don't document how to test the pattern
4. **Vague Pitfalls** - "Common Pitfalls" sections too generic, not specific to this project
5. **No Integration Points** - Skills don't explain how they integrate with existing project skills

## Recurring Tasks Feature Learnings (Phase V)

### Key Patterns Discovered

1. **Self-Referential Foreign Keys in SQLModel**
   - Pattern: parent_task_id → tasks.id with cascade delete
   - Relationship: `parent_task: Optional["Task"]` and `child_occurrences: List["Task"]`
   - Testing: Must handle orphan records properly

2. **Idempotency with Unique Partial Indexes**
   - Pattern: Unique constraint on (parent_task_id, due_date) WHERE completed=FALSE
   - Purpose: Prevents duplicate next occurrences
   - Edge case: IntegrityError handling required

3. **Natural Language Date Parsing with dateparser**
   - Library: `dateparser.parse()` with PREFER_DATES_FROM='future'
   - Pattern: Preprocessor → dateparser → ISO format fallback
   - Edge cases: "next year", "until December", month-end dates

4. **Helper Function Pattern for Complex MCP Tools**
   - Pattern: Public async tool function + private `_create_next_occurrence()` helper
   - Purpose: Separate concerns (validation vs business logic)
   - Benefit: Testable, reusable

5. **Regex Pattern Validation**
   - Pattern: Simple patterns dict + custom regex for "every N units"
   - Validation: Check interval > 0 and <= 365
   - Testing: Edge cases like "every 0 days", "every 1000 months"

6. **relativedelta for Date Arithmetic**
   - Library: `python-dateutil`
   - Benefit: Automatically handles month-end edge cases (Jan 31 → Feb 28/29)
   - Leap year: Handled automatically
   - Pattern: `current_date + relativedelta(months=1)`

### Skills to Update

- **database-schema-expander**: Add self-referential FK pattern, partial indexes
- **mcp-tool-builder**: Add natural language parsing, helper function pattern, IntegrityError handling
- **edge-case-tester**: Add recurring tasks edge cases (month-end, leap year, idempotency)
- **robust-ai-assistant**: Already has date parsing - add recurrence patterns

## Next Steps for Future Feature Learning

- [ ] After fixing bugs: Add solution to relevant skill's "Common Pitfalls"
- [ ] After discovering patterns: Add to skill's "Key Patterns" section
- [ ] After finding edge cases: Add to skill's examples/ directory
- [ ] After creating reusable code: Add to skill's templates/ directory

## Links to Updated Skills

- `/Users/apple/Documents/Projects/todo_phase5/.claude/skills/database-schema-expander/`
- `/Users/apple/Documents/Projects/todo_phase5/.claude/skills/mcp-tool-builder/`
- `/Users/apple/Documents/Projects/todo_phase5/.claude/skills/edge-case-tester/`
