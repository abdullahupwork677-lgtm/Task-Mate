---
name: test-runner
description: Automated pytest execution with 10 commands - unit/integration/E2E tests, coverage reports with thresholds, parallel execution (3-4x faster with pytest-xdist), watch mode for TDD, and specific test targeting. Use for consistent Python test execution without manual pytest commands (70-80% time savings).
---

# Test Runner

**Automated pytest - No testing expertise needed!**

---

## 📋 Quick Instructions

1. **Choose Test Type**
   - All → `run-all`
   - Unit (fast) → `run-unit`
   - Coverage → `run-coverage`
   - Parallel → `run-parallel`

2. **Run Command**
   ```bash
   python3 scripts/tool.py <command>
   ```

3. **Load References (On-Demand)**
   - Test patterns → `reference/pytest-patterns.md`
   - Coverage guide → `reference/coverage-guide.md`

---

## 🛠️ Commands (10 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py run-all          # All tests
python3 scripts/tool.py run-unit         # Unit tests (fastest ~10s)
python3 scripts/tool.py run-integration  # Integration tests (~30s)
python3 scripts/tool.py run-e2e          # E2E tests (~60s)
python3 scripts/tool.py run-coverage     # Tests + coverage report
python3 scripts/tool.py run-specific tests/unit/test_sort.py
python3 scripts/tool.py run-parallel     # 3-4x faster!
python3 scripts/tool.py watch            # Auto re-run on changes
```

---

## 📁 On-Demand Resources

- **File:** `reference/pytest-patterns.md` - When: Need test patterns
- **File:** `reference/coverage-guide.md` - When: Coverage questions
- **File:** `examples/test-examples.py` - When: Need test examples

---

## 🚀 Common Workflows

### Development (Fast)
```bash
python3 scripts/tool.py run-unit  # 10s feedback
```

### Pre-Commit (Complete)
```bash
python3 scripts/tool.py run-coverage --min-coverage 80
```

### CI/CD (Parallel)
```bash
python3 scripts/tool.py run-parallel  # 3-4x faster
```

---

## 💡 Token Efficiency

**Before:** 622 lines
**After:** ~100 lines
**Savings:** 84% ✅

---

**Status:** Production-ready ✅
**Parallel: 3-4x faster!** ⚡
