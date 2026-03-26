---
name: frontend-developer
description: Next.js 14/React automation with 8 commands - Server/Client components, App Router pages, custom hooks, shadcn/ui setup, type-safe API clients, react-hook-form validation, bundle optimization, and code audits. Use when building Next.js frontends with TypeScript, Tailwind CSS, and accessibility built-in (70-80% time savings).
---

# Frontend Developer - Expert-Level Automation

**Next.js/React without manual coding - 70-80% time savings!**

**Category:** Frontend Development & Automation
**Time Savings:** 70-80% reduction
**Quality:** Production-ready with TypeScript

---

## 📋 Quick Instructions

When invoked for frontend work:

1. **Identify Task Type**
   - Component → `create-component`
   - Page → `create-page`
   - Hook → `create-hook`
   - Form → `create-form`

2. **Run Automation**
   ```bash
   python3 scripts/tool.py <command> [args]
   ```

3. **Load References (On-Demand)**
   - Examples? → `examples/react-patterns.md`
   - Best practices? → `reference/nextjs-guide.md`
   - Errors? → `reference/common-errors.md`

---

## 🛠️ Available Commands

**Location:** `scripts/tool.py` (8 commands)

```bash
# Common workflows
python3 scripts/tool.py create-component --name TaskCard --type client
python3 scripts/tool.py create-page --name tasks --type app-router
python3 scripts/tool.py create-hook --name useTask
python3 scripts/tool.py setup-shadcn --components button,card,form
python3 scripts/tool.py generate-api-client --base-url /api
python3 scripts/tool.py create-form --name TaskForm
python3 scripts/tool.py optimize-bundle
python3 scripts/tool.py audit
```

---

## 📁 On-Demand Resources

**Load ONLY when needed:**

### React/Next.js Patterns
- **File:** `examples/react-patterns.md`
- **When:** User needs code examples
- **Contains:** Components, hooks, Server/Client patterns

### Next.js Best Practices
- **File:** `reference/nextjs-guide.md`
- **When:** User asks about Next.js patterns
- **Contains:** App Router, data fetching, optimization

### Common Frontend Errors
- **File:** `reference/common-errors.md`
- **When:** User encounters errors
- **Contains:** TypeScript, hydration, build errors

### Component Templates
- **Directory:** `assets/templates/`
- **Files:**
  - `component-template.tsx` - React component
  - `page-template.tsx` - Next.js page
  - `hook-template.ts` - Custom hook
  - `form-template.tsx` - Form with validation

---

## 📚 File Reference Map

| Need | File | Location |
|------|------|----------|
| Commands | Automation tool | `scripts/tool.py` |
| Examples | React patterns | `examples/react-patterns.md` |
| Guide | Next.js best practices | `reference/nextjs-guide.md` |
| Errors | Troubleshooting | `reference/common-errors.md` |
| Templates | Boilerplate | `assets/templates/*.tsx` |

---

## 🚀 Common Workflows

### Workflow 1: New Feature Page
```bash
1. python3 scripts/tool.py create-page --name tasks
2. python3 scripts/tool.py create-component --name TaskList
3. python3 scripts/tool.py generate-api-client --endpoint tasks
4. python3 scripts/tool.py create-form --name TaskForm
```

### Workflow 2: Setup UI Library
```bash
python3 scripts/tool.py setup-shadcn --components button,card,form,dialog
```

### Workflow 3: Performance Optimization
```bash
python3 scripts/tool.py optimize-bundle
# Analyzes: Bundle size, dynamic imports, image optimization
```

---

## 🎯 Features

- ✅ Next.js 14 App Router (Server/Client Components)
- ✅ TypeScript strict mode
- ✅ Tailwind CSS styling
- ✅ shadcn/ui integration
- ✅ Type-safe API clients
- ✅ Form validation (react-hook-form)
- ✅ Accessibility (ARIA, keyboard navigation)
- ✅ Performance optimized (dynamic imports, lazy loading)

---

## 🔗 Related Skills

- `/backend-developer` - API integration
- `/uiux-designer` - Design systems
- `/vercel-deployer` - Deployment
- `/test-runner` - Component testing

---

## 💡 Token Efficiency

**Before:** 303 lines (all embedded)
**After:** ~150 lines (instructions + references)
**Savings:** 50% reduction ✅

---

**Status:** Production-ready ✅
**Token-Efficient:** 50% reduction ✅
**No frontend expertise needed!** 🚀
