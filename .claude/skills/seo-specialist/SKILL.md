---
name: seo-specialist
description: Complete SEO automation with 6 commands - site audits (technical/on-page/off-page), keyword research with density analysis, XML sitemap generation, robots.txt configuration, schema markup (JSON-LD), and content optimization scoring. Use when launching websites, improving search rankings, or running SEO audits without SEO expertise (80-90% time savings, industry-standard practices automatically applied).
---

# SEO Specialist

**Complete SEO automation - No SEO expert needed!**

**Category:** Marketing & Growth
**Time Savings:** 80-90% reduction
**Quality:** Industry-standard SEO practices

---

## 📋 Quick Instructions

1. **Run SEO Audit**
   ```bash
   python3 scripts/tool.py audit --url https://example.com
   ```

2. **Keyword Research**
   ```bash
   python3 scripts/tool.py keywords --topic "task management"
   ```

3. **Generate Sitemap**
   ```bash
   python3 scripts/tool.py sitemap --url https://example.com
   ```

4. **Add Schema Markup**
   ```bash
   python3 scripts/tool.py schema --type Article
   ```

---

## 🛠️ Commands (6 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py audit --url https://example.com
python3 scripts/tool.py keywords --topic "your topic"
python3 scripts/tool.py sitemap --url https://example.com
python3 scripts/tool.py robots --rules default
python3 scripts/tool.py schema --type Article
python3 scripts/tool.py optimize --file content.html
```

---

## 📁 On-Demand Resources

### SEO Audit Checklist
- **File:** `reference/audit-checklist.md`
- **When:** Running site audits
- **Contains:** Technical, on-page, off-page checks

### Keyword Research Guide
- **File:** `reference/keyword-research.md`
- **When:** Finding target keywords
- **Contains:** Density analysis, competitor analysis

### Schema Markup Templates
- **Directory:** `assets/schema/`
- **Files:** Article, Product, Organization, Local Business

### Content Optimization
- **File:** `reference/content-scoring.md`
- **When:** Optimizing content
- **Contains:** Keyword placement, readability, meta tags

---

## 🚀 Common Workflows

### Workflow 1: New Website SEO Setup
```bash
1. python3 scripts/tool.py audit --url https://example.com
2. python3 scripts/tool.py sitemap --url https://example.com
3. python3 scripts/tool.py robots --rules default
4. python3 scripts/tool.py schema --type Organization
```

### Workflow 2: Content Optimization
```bash
1. python3 scripts/tool.py keywords --topic "your topic"
2. python3 scripts/tool.py optimize --file article.html
3. python3 scripts/tool.py schema --type Article
```

---

## 💡 Token Efficiency

**Before:** 889 lines
**After:** ~140 lines
**Savings:** 84% reduction ✅

---

**Status:** Production-ready ✅
**No SEO expertise needed!** 🚀
