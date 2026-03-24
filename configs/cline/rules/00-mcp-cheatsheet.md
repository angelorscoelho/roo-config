# MCP Cheat Sheet — Tool Reference & Decision Protocol
# Global Cline Rule — install to ~/Documents/Cline/Rules/00-mcp-cheatsheet.md
# Applies to every conversation. Project .clinerules/ files layer on top.

---

## The Priority Ladder — Cost Ascending, Always Top-Down

Before ANY action, descend this ladder. Skip a level only when it cannot answer the question.

| # | MCP / Tool | Purpose | Cost | API Key? |
|---|-----------|---------|------|----------|
| 1 | **serena** | Semantic code intelligence — find, understand, edit symbols | Cheapest context | No |
| 2 | **fetch** | Fetch a known URL → clean Markdown | Free | No |
| 3 | **ref.tools** | Token-efficient doc lookups (95% fewer tokens than context7) | Tiny | Yes |
| 4 | **context7** | Version-accurate library/framework documentation | Low | No |
| 5 | **duckduckgo-mcp** | Real-time web search (CVEs, releases, comparisons) | Low | No |
| 6 | **crash-mcp** | Structured reasoning scaffold — prevents loop spirals | Negligible | No |
| 7 | **github** | Issue/PR/commit/context | Low | Yes |
| 8 | **read_file** | Cline native: read raw file bytes | Expensive | N/A |

**Skipping serena for a code question → read_file wastes money.**
**Skipping fetch for a URL → duckduckgo wastes money.**
**Skipping ref.tools/context7 for a library question → web search wastes money.**

---

## Tool Reference

### 1. serena — IDE-Grade Code Intelligence

Replaces file reads, grep loops, and blind recursion. Serena indexes the project with LSP/AST
and returns precise, token-efficient answers.

**Core tools:**

| Tool | When to use | Example |
|------|------------|---------|
| `find_symbol(name)` | Locate any function, class, method, type by name | `find_symbol("authenticate")` |
| `find_referencing_symbols(name)` | Find all callers/usages of a symbol | `find_referencing_symbols("parseToken")` |
| `get_symbols_overview(path)` | Top-level exports/imports/functions of a file or dir | `get_symbols_overview("src/api/users.ts")` |
| `search_for_pattern(pattern)` | Regex search across codebase | `search_for_pattern("api_key\s*=")` |
| `replace_symbol_body(name, body)` | Replace a function/class body precisely | |
| `insert_after_symbol(name, code)` | Insert code after a symbol definition | |
| `rename_symbol(name, new_name)` | Rename across entire codebase via LSP | |
| `list_dir(path)` | Shallow directory listing | Only when serena navigation fails |

**Memory tools** (persist context across sessions):

| Tool | When to use |
|------|------------|
| `onboarding()` | FIRST TIME in a new project — builds .serena/memories/ index |
| `write_memory(name, content)` | Save a decision, pattern, or key context for future sessions |
| `read_memory(name)` | Load a specific memory (only if relevant to current task) |
| `list_memories()` | See what memories exist — call at session start |

**Rules:**
- Call `list_memories()` at session start in a new project.
- Call `onboarding()` only ONCE per new project. Check `.serena/memories/` first.
- NEVER call `find_symbol` AND `read_file` on the same target in the same step.
- NEVER call the same serena tool twice for the same input in one session.

---

### 2. fetch — Free URL → Markdown

Zero cost. No API key. Converts any URL into clean Markdown. Runs instantly.

**Tool:** `fetch(url)` → returns cleaned Markdown

Use BEFORE duckduckgo-mcp whenever you have a specific URL (docs page, GitHub issue,
release notes, AWS error code page, RFC).

---

### 3. ref.tools — Token-Efficient Doc Lookups

95% fewer tokens than context7. Preferred doc lookup when API key is available.

**Tool:** `lookup(query)` — natural language query against curated doc index

**Requires:** `REF_TOOLS_API_KEY` environment variable.
**Fallback:** context7.

---

### 4. context7 — Version-Accurate Library Docs

**Always two steps:**
1. `resolve-library-id(library_name)` → e.g. `resolve-library-id("react")` → `/facebook/react`
2. `get-library-docs(library_id, topic?)` → e.g. `get-library-docs("/facebook/react", "hooks")`

Use when ref.tools is unavailable. Do NOT use for general web research.

---

### 5. duckduckgo-mcp — Real-Time Web Search

**Tool:** `search(query)` — returns top results with snippets.

- Max 2 searches per session.
- Query ≤7 words. Specific beats broad.
- FORBIDDEN when ref.tools or context7 can answer the same library question.

---

### 6. crash-mcp — Reasoning Scaffold

Structured, revisable thinking. Step schema:

```json
{
  "step_number": 1,
  "estimated_total": 5,
  "purpose": "analysis|action|validation|exploration|hypothesis|correction|planning",
  "context": "what we know so far",
  "thought": "the reasoning for this step",
  "outcome": "what this step concludes",
  "next_action": "what to do next",
  "rationale": "why",
  "revises_step": 2,
  "branch_from": 2,
  "branch_id": "option-a"
}
```

Use BEFORE: multi-hop taint analysis, complex debug chains (>3 steps), architecture
decisions with >4 trade-offs, orchestration decompositions with >5 sub-tasks.

Stop crash once the reasoning is settled. Do not crash through implementation steps.

---

### 7. github — Repository Context

Dynamic toolsets (`GITHUB_DYNAMIC_TOOLSETS=1`).

| Tool | When to use |
|------|------------|
| `get_issue(owner, repo, issue_number)` | Load issue requirements BEFORE planning |
| `get_pull_request(owner, repo, pr_number)` | Load PR for review or merge |
| `get_file_contents(owner, repo, path, ref?)` | Read file at specific branch/commit |
| `get_commit(owner, repo, sha)` | Understand intent of a commit |
| `create_issue(...)` | File a bug or task |
| `create_pull_request(...)` | Open a PR |

Use ONLY when a ticket/PR/commit number is explicitly referenced.
NEVER use github as a general search engine.

---

### 8. read_file — Cline Native (LAST RESORT)

Use ONLY when `serena: find_symbol` returns nothing for a symbol you know exists,
or when you need a specific line range from a file serena cannot navigate.

- NEVER call on the same path twice in one session.
- NEVER read: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `.env`, `*.pem`,
  `node_modules/**`, `dist/**`, `build/**`.
- NEVER use to "understand project structure." Use `serena: get_symbols_overview`.

---

## Decision Trees by Task Type

### "I need to understand some code"
```
1. serena: get_symbols_overview("{file or directory}")
2. serena: find_symbol("{name}") to drill in
3. serena: find_referencing_symbols("{name}") for callers
4. read_file("{file}", lines=X-Y) ONLY if serena returns empty AND symbol is known to exist
```

### "I need to implement/edit code"
```
1. serena: find_symbol("{target}") → exact location
2. serena: find_referencing_symbols("{target}") → impact radius
3. Cline edit tools with minimal diff (str_replace preferred)
4. serena: replace_symbol_body("{name}", body) for clean symbol-level edits
```

### "I need library/framework docs"
```
1. ref.tools: lookup("{query}") if REF_TOOLS_API_KEY set
2. ELSE context7: resolve-library-id("{lib}") → get-library-docs("{id}", "{topic}")
3. ONLY if neither works: fetch("{specific docs URL}")
4. LAST: duckduckgo-mcp: search("{lib} {version} {topic}")
```

### "I have a specific URL"
```
1. fetch("{url}") — always. Free. Instant.
2. Never use duckduckgo-mcp when you already have the URL.
```

### "I need to debug an error"
```
1. crash-mcp: form hypothesis (purpose=hypothesis)
2. serena: find_symbol("{symbol from stack trace}")
3. read_file("{file}", lines=error_line ± 20) — ONLY the error location
4. serena: find_referencing_symbols("{symbol}") → trace causality
5. ref.tools or context7: verify unexpected API behaviour
6. fetch or duckduckgo-mcp: known bug lookup (LAST RESORT)
```

### "I need current web information"
```
1. duckduckgo-mcp: search("{specific query ≤7 words}")
2. fetch("{URL from results}") for full article content
3. Stop after 2 searches. Synthesise and respond.
```

---

## Prohibited Patterns

| Pattern | Why | Correct Alternative |
|---------|-----|-------------------|
| `read_file` to understand structure | Reads entire file for partial info | `serena: get_symbols_overview` |
| `list_files` depth>1 as first action | Enumerates instead of navigating | `serena: get_symbols_overview` |
| `duckduckgo-mcp` when URL is known | Extra hop, lower quality | `fetch(url)` |
| `duckduckgo-mcp` for library API | Stale, hallucination-prone | `ref.tools` or `context7` |
| `find_symbol` + `read_file` same target | Double-counting context | One or the other |
| Any tool called twice with same input | Wasted tokens | Cache result mentally |
| `crash-mcp` during implementation | Reasoning when action is needed | Direct edit tools |
| `context7` when `ref.tools` available | 20x token overhead | `ref.tools` first |
