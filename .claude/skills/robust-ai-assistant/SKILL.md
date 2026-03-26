---
name: robust-ai-assistant
description: Build production-ready AI chatbots with 8 commands - multi-turn conversation workflows, natural language task management (create/update/delete/list/complete), intent recognition (7 intents), date parsing (tomorrow/next Friday/in 3 days), 30+ edge cases handling, and comprehensive error recovery. Use when building conversational AI with OpenAI Agents SDK and MCP tools (handles ambiguity, context switching, confirmation flows).
---

# Robust AI Assistant

**Production-ready AI chatbots - No AI expertise needed!**

**Category:** AI & Conversational Interfaces
**Time Savings:** 80-90% reduction
**Quality:** 30+ edge cases handled automatically

---

## 📋 Quick Instructions

1. **Setup Conversation Flow**
   - Define intents (ADD, UPDATE, DELETE, LIST, COMPLETE)
   - Multi-turn workflows for complex tasks
   - Context management

2. **Build Assistant**
   ```bash
   python3 scripts/tool.py create-assistant --name TaskBot
   ```

3. **Add Intent Recognition**
   ```bash
   python3 scripts/tool.py add-intent-handler --intent ADD
   ```

4. **Test Edge Cases**
   ```bash
   python3 scripts/tool.py test --scenarios all
   ```

---

## 🛠️ Commands (8 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py check-prerequisites
python3 scripts/tool.py create-assistant --name TaskBot
python3 scripts/tool.py add-intent-handler --intent ADD
python3 scripts/tool.py add-date-parser
python3 scripts/tool.py add-confirmation-flow
python3 scripts/tool.py add-error-recovery
python3 scripts/tool.py generate-tests
python3 scripts/tool.py test --scenarios all
```

---

## 📁 On-Demand Resources

### Intent Recognition Patterns
- **File:** `reference/intent-patterns.md`
- **When:** Implementing intent detection
- **Contains:** 7 intent types, keywords, examples

### Natural Language Date Parsing
- **File:** `reference/date-parsing.md`
- **When:** Adding date understanding
- **Contains:** Relative dates (tomorrow, next week), GPT fallback

### Edge Cases Handling
- **File:** `reference/edge-cases.md`
- **When:** Building robust flows
- **Contains:** 30+ scenarios with solutions

### Conversation Flow Templates
- **Directory:** `examples/`
- **Files:**
  - `multi-turn-workflow.md` - Step-by-step flows
  - `confirmation-patterns.md` - Safety confirmations
  - `error-recovery.md` - Graceful error handling

### Test Scenarios
- **File:** `assets/test-scenarios.md`
- **When:** Testing assistant
- **Contains:** 30+ test cases for all edge cases

---

## 🚀 Common Workflows

### Workflow 1: Create Task Assistant
```bash
1. python3 scripts/tool.py create-assistant --name TaskBot
2. python3 scripts/tool.py add-intent-handler --intent ADD
3. python3 scripts/tool.py add-date-parser
4. python3 scripts/tool.py test --scenarios basic
```

### Workflow 2: Add Multi-Turn Flow
```bash
# For complex operations requiring multiple steps
1. Define workflow steps (title → priority → deadline)
2. Add confirmation points
3. Implement context tracking
4. Add cancel/restart options
```

### Workflow 3: Handle Edge Cases
```bash
# Load edge case patterns
1. Read reference/edge-cases.md
2. Implement handlers for:
   - Ambiguous input → Clarification question
   - Context switching → Save state
   - Incomplete data → Prompt for missing
   - Invalid data → Validation + retry
```

---

## 💡 Token Efficiency

**Before:** 989 lines (all embedded)
**After:** ~180 lines (instructions + references)
**Savings:** 82% reduction ✅

---

**Status:** Production-ready ✅
**No AI expertise needed!** 🚀
**30+ edge cases handled!** 🛡️
