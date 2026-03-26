# **AGENTS.md**

## **Purpose**

This project uses **Spec-Driven Development (SDD)** — a workflow where **no agent is allowed to write code until the specification is complete and approved**.

All AI agents (Claude Code, GitHub Copilot, Gemini, local LLMs, etc.) must follow the **Spec-Kit Plus lifecycle**:

> **Constitution → Specify → Plan → Tasks → Implement**

This prevents "vibe coding," ensures alignment across agents, and guarantees that every implementation step maps back to an explicit requirement.

---

## **How Agents Must Work**

Every agent in this project MUST obey these rules:

1. **Never generate code without a referenced Task ID.**
2. **Never modify architecture without updating the implementation plan.**
3. **Never propose features without updating the spec (WHAT).**
4. **Never change approach without updating `.specify/memory/constitution.md` (Principles).**
5. **Every code file must contain a comment linking it to the Task and Spec sections.**
6. **Always use skills from `.claude/skills/` before writing code manually.**

If an agent cannot find the required spec, it must **stop and request it**, not improvise.

---

## **Spec-Kit Plus Workflow (Source of Truth)**

### **1. Constitution (WHY — Principles & Constraints)**

**File:** `.specify/memory/constitution.md`

Defines the project's non-negotiables:
- Architecture values (stateless, database-centric, horizontally scalable)
- Security rules (JWT auth, user isolation, password hashing)
- Tech stack constraints (FastAPI, Next.js, SQLModel, Neon PostgreSQL)
- Performance expectations (connection pooling, query optimization)
- Patterns allowed (MCP tools, OpenAI Agents SDK, skill-first development)

**Agents must check this before proposing solutions.**

---

### **2. Specify (WHAT — Requirements, User Stories & Acceptance Criteria)**

**Location:** `specs/<Phase>/<feature-number>-<feature-name>/spec.md`

**Example:** `specs/Phase-5/001-recurring-tasks/spec.md`

Contains:
- User journeys
- Feature requirements
- Acceptance criteria
- Domain rules
- Business constraints
- Database schema changes

**Agents must not infer missing requirements** — they must request clarification or propose specification updates.

---

### **3. Plan (HOW — Architecture, Components, Interfaces)**

**Location:** `specs/<Phase>/<feature-number>-<feature-name>/plan.md`

**Example:** `specs/Phase-5/001-recurring-tasks/plan.md`

Includes:
- Component breakdown
- APIs & schema diagrams
- Service boundaries
- System responsibilities
- High-level sequencing
- Technology stack decisions

**All architectural output MUST be generated from the Specify file.**

---

### **4. Tasks (BREAKDOWN — Atomic, Testable Work Units)**

**Location:** `specs/<Phase>/<feature-number>-<feature-name>/tasks.md`

**Example:** `specs/Phase-5/001-recurring-tasks/tasks.md`

Each Task must contain:
- Task ID (T001, T002, etc.)
- Clear description
- Preconditions
- Expected outputs
- Artifacts to modify
- Links back to Specify + Plan sections

**Agents implement only what these tasks define.**

---

### **5. Implement (CODE — Write Only What the Tasks Authorize)**

Agents now write code, but must:
- **Use skills from `.claude/skills/` directory first**
- Reference Task IDs in commits
- Follow the Plan exactly
- Not invent new features or flows
- Stop and request clarification if anything is underspecified

> **The golden rule:** **No task = No code. No skill = Manual code.**

---

## **Agent Behavior in This Project**

### **When generating code:**

Agents must reference:
```markdown
[Task]: T-003
[From]: specs/Phase-5/001-recurring-tasks/spec.md §2.1
[From]: specs/Phase-5/001-recurring-tasks/plan.md §3.4
[Skill]: /sp.database-schema-expander
```

### **When proposing architecture:**

Agents must reference:
```markdown
Update required in specs/<Phase>/<feature>/plan.md → add component X
```

### **When proposing new behavior or a new feature:**

Agents must reference:
```markdown
Requires update in specs/<Phase>/<feature>/spec.md (WHAT)
```

### **When changing principles:**

Agents must reference:
```markdown
Modify .specify/memory/constitution.md → Principle #X
```

### **When using reusable intelligence:**

Agents must reference:
```markdown
[Skill]: /sp.jwt-authentication
[Skill]: /sp.database-schema-expander
[Agent]: backend-developer (from .claude/agents/)
```

---

## **Agent Failure Modes (What Agents MUST Avoid)**

Agents are NOT allowed to:

❌ Freestyle code or architecture
❌ Generate missing requirements
❌ Create tasks on their own
❌ Alter stack choices without justification
❌ Add endpoints, fields, or flows that aren't in the spec
❌ Ignore acceptance criteria
❌ Produce "creative" implementations that violate the plan
❌ Write code manually when a skill exists in `.claude/skills/`
❌ Skip calling `/sp.skill-learner` after completing a feature

If a conflict arises between spec files, the hierarchy applies:

**Constitution > Specify > Plan > Tasks > Implementation**

---

## **Skill-First Development (MANDATORY)**

This project uses **43 reusable intelligence skills** located in `.claude/skills/`.

### **Before writing ANY code, agents MUST:**

1. Check `.claude/skills/` for applicable skills
2. Display skill plan with names
3. Wait for user approval
4. Execute skills with clear indicators:
   ```
   🔧 Using Skill: /sp.database-schema-expander
   Purpose: Add new tables with migrations
   Files Generated: backend/alembic/versions/xxx_add_recurring_tasks.py
   ✅ Skill Complete
   ```
5. After feature completion: **AUTO-CALL** `/sp.skill-learner`

**Skills Reference:** See `.claude/docs/skills-reference.md`
**Usage Scenarios:** See `.claude/docs/skills-scenarios.md`

---

## **Project Structure Overview**

```
todo_phase5/
├── AGENTS.md                          # This file (agent instructions)
├── CLAUDE.md                          # Claude Code project guide
├── .specify/                          # Spec-Kit Plus framework
│   ├── memory/constitution.md         # Core principles (WHY)
│   └── templates/                     # Spec templates
├── specs/                             # Feature specifications
│   ├── Phase-2/                       # Phase 2 specs
│   ├── Phase-3/                       # Phase 3 specs
│   └── Phase-5/                       # Phase 5 specs
│       └── 001-recurring-tasks/
│           ├── spec.md                # WHAT to build
│           ├── plan.md                # HOW to build
│           └── tasks.md               # Atomic tasks
├── .claude/                           # Reusable intelligence
│   ├── skills/                        # 43 reusable skills
│   ├── agents/                        # 17 FTE agents
│   └── docs/                          # Complete documentation
├── backend/                           # FastAPI backend
│   ├── CLAUDE.md                      # Backend-specific guide
│   └── src/
├── frontend/                          # Next.js frontend
│   ├── CLAUDE.md                      # Frontend-specific guide
│   └── app/
└── history/                           # PHRs & ADRs
    └── prompts/                       # Prompt history records
```

---

## **Developer–Agent Alignment**

Humans and agents collaborate, but the **spec is the single source of truth**.

### **Before every coding session, agents should:**

1. Read `.specify/memory/constitution.md`
2. Read `specs/<Phase>/<feature>/spec.md`
3. Read `specs/<Phase>/<feature>/plan.md`
4. Read `specs/<Phase>/<feature>/tasks.md`
5. Check `.claude/skills/` for applicable skills
6. Verify task ID before writing code

This ensures **predictable, deterministic development**.

---

## **Phase-Based Workflow**

This project follows the **Hackathon II: Evolution of Todo** structure:

| Phase | Focus | Spec Location |
|-------|-------|---------------|
| **Phase I** | Python Console App | `specs/Phase-1/` |
| **Phase II** | Full-Stack Web App | `specs/Phase-2/` |
| **Phase III** | AI Chatbot (MCP + OpenAI Agents) | `specs/Phase-3/` |
| **Phase IV** | Local Kubernetes (Minikube) | `specs/Phase-4/` |
| **Phase V** | Cloud Deployment (OKE + Kafka + Dapr) | `specs/Phase-5/` |

Each phase has its own specs directory with `spec.md`, `plan.md`, and `tasks.md`.

---

## **Integration with Claude Code**

This project uses **Claude Code** with specific guidelines in `CLAUDE.md`.

### **Key Claude Code Rules:**

1. **Skill-first approach** - Always check `.claude/skills/` first
2. **Show skill heading** before every skill use
3. **Auto-trigger `/sp.skill-learner`** after feature completion
4. **TDD** - Write tests FIRST, watch them FAIL, then implement
5. **SDD** - Spec-first for every feature
6. **PHR** - Create prompt history record after significant interactions

See `CLAUDE.md` for complete Claude Code instructions.

---

## **MCP Server Integration**

This project uses **Model Context Protocol (MCP)** for programmatic API control.

**Configured MCP Servers:**
- **context7** - Documentation search
- **vercel** - Deployment automation
- **github** - Git operations automation

**MCP-Enhanced Skills:**
- `/vercel-deployer` - Programmatic Vercel deployments
- `/github-specialist` - GitHub automation (PRs, issues, releases)

**Configuration:** `.claude/.mcp.json` (gitignored - contains API keys)

---

## **Quality Assurance Checklist**

Before marking any task complete, agents must verify:

- [ ] Task ID referenced in code/commits
- [ ] Spec requirements met
- [ ] Plan architecture followed
- [ ] Applicable skills used from `.claude/skills/`
- [ ] Tests written (if TDD specified)
- [ ] Constitution principles followed
- [ ] PHR created for significant work
- [ ] ADR created for architectural decisions
- [ ] `/sp.skill-learner` called after feature completion

---

## **Example: Correct Agent Workflow**

**User Request:** "Implement recurring tasks feature"

**Agent Response:**

```
1. Reading specs/Phase-5/001-recurring-tasks/spec.md... ✅
2. Reading specs/Phase-5/001-recurring-tasks/plan.md... ✅
3. Reading specs/Phase-5/001-recurring-tasks/tasks.md... ✅
4. Checking .claude/skills/ for applicable skills...

   Found applicable skills:
   - /sp.database-schema-expander (add new tables)
   - /sp.chatbot-endpoint (update chat API)
   - /sp.mcp-tool-builder (create new MCP tools)

5. Executing Task T-001: Add database schema fields

   🔧 Using Skill: /sp.database-schema-expander
   Purpose: Add is_recurring, recurrence_pattern fields to tasks table
   Files Generated: backend/alembic/versions/xxx_add_recurring_fields.py
   ✅ Skill Complete

6. Task T-001 complete. Moving to T-002...

[... continues through all tasks ...]

All tasks complete! ✅

🧠 Auto-calling /sp.skill-learner
Purpose: Capture learnings from recurring tasks implementation
Skills Updated: mcp-tool-builder.md (added recurring task pattern)
✅ Skills Evolution Complete
```

---

## **Example: Incorrect Agent Workflow (FORBIDDEN)**

**User Request:** "Implement recurring tasks feature"

**Agent Response (WRONG):**

```
Sure! Let me create the recurring tasks feature.

[Agent directly writes code without:]
- Reading spec.md ❌
- Reading plan.md ❌
- Reading tasks.md ❌
- Checking .claude/skills/ ❌
- Referencing Task IDs ❌
- Using applicable skills ❌
- Calling skill-learner afterwards ❌

[This is FORBIDDEN in this project!]
```

---

## **Conflict Resolution**

If specs conflict or are unclear:

1. **Stop** - Do not proceed with implementation
2. **Ask** - Request clarification from human
3. **Document** - Propose spec update
4. **Wait** - Get approval before continuing

**Never guess. Never improvise. Never "fill in the blanks."**

---

## **Success Metrics**

A well-behaved agent in this project:

✅ References Task IDs in all work
✅ Uses skills from `.claude/skills/` directory
✅ Follows Constitution principles
✅ Updates PHRs for significant work
✅ Suggests ADRs for architectural decisions
✅ Calls `/sp.skill-learner` after features
✅ Never writes code without a spec
✅ Never modifies architecture without approval
✅ Produces deterministic, reproducible results

---

## **Resources**

- **Complete Skills Reference:** `.claude/docs/skills-reference.md` (43 skills)
- **Usage Scenarios:** `.claude/docs/skills-scenarios.md`
- **Architect Guidelines:** `.claude/docs/architect-guidelines.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Claude Code Guide:** `CLAUDE.md`
- **Hackathon Requirements:** `Hackathon II - Todo Spec-Driven Development.md`

---

## **Remember**

> **"Spec-Driven Development means AI agents are architects, not improvisers."**

This project is designed to demonstrate that AI can build **production-grade, cloud-native systems** when given:
1. Clear specifications
2. Reusable intelligence (skills)
3. Strict development workflow
4. Quality enforcement

**No shortcuts. No guessing. No vibe coding.**

**Spec → Plan → Tasks → Skills → Implement → Learn.**

---

**Last Updated:** 2026-02-08
**Project:** Todo Chatbot Phase 5 (Hackathon II)
**Framework:** Spec-Kit Plus + Claude Code
**Status:** Production-ready workflow ✅
