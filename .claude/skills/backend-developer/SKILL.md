---
name: backend-developer
description: FastAPI backend automation with 8 commands - CRUD endpoints, SQLModel models, Alembic migrations, JWT authentication, pytest tests, service layer patterns, database optimization, and OWASP security audits. Use when building FastAPI backends with production-ready code, user isolation, and comprehensive testing (80-90% time savings).
---

# Backend Developer

**FastAPI automation - No backend expertise needed!**

**Category:** Backend Development & Automation
**Time Savings:** 80-90% reduction
**Quality:** Production-ready with security

---

## 📋 Quick Instructions

1. **Identify Task**
   ```bash
   # Endpoint → scaffold-endpoint
   # Model → create-model
   # Auth → setup-auth
   # Tests → generate-tests
   ```

2. **Run Command**
   ```bash
   python3 scripts/tool.py <command> [args]
   ```

3. **Load References (On-Demand)**
   - Examples: `examples/fastapi-patterns.md`
   - Best practices: `reference/best-practices.md`
   - Errors: `reference/common-errors.md`

---

## 🛠️ Commands (8 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py scaffold-endpoint --resource tasks
python3 scripts/tool.py create-model --name Task
python3 scripts/tool.py generate-migration --message "Add tasks"
python3 scripts/tool.py setup-auth
python3 scripts/tool.py generate-tests --resource tasks
python3 scripts/tool.py create-service --name TaskService
python3 scripts/tool.py optimize-db
python3 scripts/tool.py audit
```

---

## 📁 On-Demand Resources

### FastAPI Patterns
- **File:** `examples/fastapi-patterns.md`
- **When:** Need code examples
- **Contains:** CRUD endpoints, SQLModel, dependency injection

### Best Practices
- **File:** `reference/best-practices.md`
- **When:** Need guidelines
- **Contains:** User isolation, service layers, security

### Troubleshooting
- **File:** `reference/common-errors.md`
- **When:** Encountering errors
- **Contains:** 20+ errors with fixes

### Templates
- **Directory:** `assets/templates/`
- **Files:** endpoint, model, service, test templates

---

## 🚀 Common Workflows

### Workflow 1: New CRUD API
```bash
1. python3 scripts/tool.py create-model --name Task
2. python3 scripts/tool.py generate-migration --message "Add Task"
3. python3 scripts/tool.py create-service --name Task
4. python3 scripts/tool.py scaffold-endpoint --resource tasks
5. python3 scripts/tool.py generate-tests --resource tasks
```

### Workflow 2: Add Authentication
```bash
python3 scripts/tool.py setup-auth
```

### Workflow 3: Security Audit
```bash
python3 scripts/tool.py audit
```

---

## 💡 Token Efficiency

**Before:** 611 lines
**After:** ~150 lines
**Savings:** 75% reduction ✅

---

**Status:** Production-ready ✅
**No backend expertise!** 🚀
