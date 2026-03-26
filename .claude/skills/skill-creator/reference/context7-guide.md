# Context7 MCP Integration Guide

**Purpose:** Fetch official documentation when creating skills for NEW technologies

---

## When to Use Context7

**Use for:**
- New cloud technologies (Terraform, Pulumi, CloudFormation)
- New frameworks/libraries (SvelteKit, Remix, Astro)
- New DevOps tools (GitHub Actions, GitLab CI)
- New databases (Pinecone, Weaviate, TimescaleDB)
- Emerging technologies (LangChain, LlamaIndex)

**Skip when:**
- Well-known technologies you're expert in
- Updating existing skills
- Organizational/workflow skills (no external docs)

---

## Workflow

### Step 1: Resolve Library ID
```javascript
{
  "tool": "resolve-library-id",
  "input": {"libraryName": "terraform"}
}
```

### Step 2: Fetch Documentation
```javascript
{
  "tool": "get-library-docs",
  "input": {
    "context7CompatibleLibraryID": "terraform-id",
    "topic": "CLI commands, providers, modules, state, best practices",
    "tokens": 8000  // Comprehensive
  }
}
```

### Step 3: Extract Key Concepts
- Commands and CLI usage
- Common workflows
- Best practices
- Common errors + solutions
- Configuration requirements

---

## Pro Tips

1. **Request 8000 tokens** for comprehensive docs
2. **Use specific topics** in query (not just "documentation")
3. **Extract official examples** (don't invent)
4. **Verify command syntax** from docs

---

**Quality:** Context7 = 10/10 | WebSearch = 7/10
**Authority:** Official documentation only ✅
