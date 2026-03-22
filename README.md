# roo-config

> Standardized, budget-aware AI development environment for [Roo Code](https://github.com/RooVetGI/roo-cline) and [Cline](https://github.com/cline/cline). Reproducible across machines. Free-tier ready.

## Motivation

Managed AI coding assistants — Anthropic Claude, GitHub Copilot, Cursor — abstract away model choice and charge premium prices for that convenience. This project takes the opposite position: **you choose the models, you control the cost, you own the configuration.**

The core problem this solves:

- **The €5 debug problem.** A single careless debug session with GPT-4 or Claude Sonnet can cost €5–20 because the model reads the entire codebase, loops on tool calls, and uses expensive reasoning on cheap questions. This config prevents that by binding each task mode to the cheapest model that can do the job, and enforcing a strict MCP tool priority ladder that replaces file reads with semantic search.

- **Configuration drift across machines.** When a developer switches machines or a new team member onboards, the AI assistant behaves differently — different models, different rules, no memory of previous decisions. This config is fully committed to the repository and installs identically on every machine in one command.

- **No control over tool usage.** Default AI assistants use whatever tool they want in whatever order. This config enforces a decision tree: semantic search before file reads, doc lookups before web searches, structured reasoning before free-form analysis.

The result is an alternative to managed AI tools that gives you **more capability, more predictability, and a fraction of the cost** — usable entirely with free-tier models if needed.

---

## What This Is

A one-command installer that sets up:

1. **10 specialized Roo Code agent modes** — each bound to the best model for its task, with explicit MCP tool decision trees, anti-loop rules, and temperature tuned to the task type.
2. **7 MCP servers** — a curated stack of free and nearly-free tools that replace expensive model behavior (semantic code search, documentation lookups, web search, reasoning scaffolds, GitHub integration).
3. **Memory bank** — a per-project file structure that gives the AI persistent context across sessions and machines. Eliminates the "explain the whole project again" tax at the start of every session.
4. **Global rules** — installed to `~/.roo/rules/` and applied to every session, enforcing tool discipline, anti-loop behavior, and output standards.

---

## Quick Start

```bash
# Install / upgrade (backs up existing files)
python install.py

# Preview without writing
python install.py --dry-run

# Rollback to previous install
python install.py --undo

# Initialize memory bank for a project
cd your-project
python path/to/roo-config/install.py --init-project
```

### Session Startup Workflow

At the start of every session, verify MCP servers are running:

#### Step 1: Check If Already Installed

```bash
# Confirm global install was run
type .install_log 2>nul

# Confirm global MCP settings exist
type %APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json 2>nul
```

If both exist → skip to Step 3.

#### Step 2: First-Time Install

```bash
python install.py
python install.py --install-mcp
```

#### Step 3: Verify

```bash
python install.py --test-mcp
```

✓ = server ready · ✗ = failed (check API keys or install errors)

---

## File Map

```
roo-config/
├── install.py
└── configs/
    ├── custom_modes.yaml                        10 modes with MCP trees and anti-loop rules
    ├── 00-global-budget-rules.md                global rules all modes inherit
    ├── mcp_settings.json                        7 servers (6 active + 1 disabled), no credentials
    └── project-template/
        ├── projectBrief.md
        ├── .roo/
        │   ├── mcp.json                         project-level MCP override (serena + ref.tools)
        │   └── rules/
        │       └── 01-memory-bank-protocol.md   MCP decision tree + memory bank protocol
        └── memory-bank/
            ├── productContext.md                what the project is (read every session)
            ├── activeContext.md                 current focus and next steps (read every session)
            ├── decisionLog.md                   architectural decisions (read on-demand)
            ├── progress.md                      what's done / in progress / backlog
            └── systemPatterns.md                coding conventions established for the project
```

---

## MCP Stack

| Server | Role | Cost | API Key |
|--------|------|------|---------|
| **serena** | Semantic LSP code search — replaces most file reads | Free | None |
| **fetch** | URL → Markdown. Free, official, instant | Free | None |
| **ref.tools** | Token-efficient doc lookups. 95% fewer tokens than Context7 | Free tier | `REF_TOOLS_API_KEY` |
| **context7** | Version-accurate library docs. Fallback when ref.tools unavailable | Free | None |
| **duckduckgo-mcp** | PRIMARY web search. Privacy-safe, no API key | Free | None |
| **crash-mcp** | Token-efficient reasoning scaffold for complex analysis | Free | None |
| **github** | Issues, PRs, commits — dynamic toolsets, loads on demand | Free | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| figma-dev-mode | Disabled by default. Enable per-project for UI work | — | — |

**MCP Priority Ladder** (use top-down, skip only if level above cannot answer):

```
1. serena        — code structure, symbols, patterns
2. fetch         — any specific URL → Markdown (free, instant)
3. ref.tools     — library/API docs (token-efficient, requires API key)
4. context7      — library/API docs (free fallback to ref.tools)
5. duckduckgo-mcp — web search (CVEs, releases, comparisons)
6. crash-mcp     — reasoning scaffold for complex multi-step analysis
7. github        — issue/PR/commit context
8. read_file     — LAST RESORT (only when serena returns nothing)
```

---

## Model Assignments

### Budget-Optimized (Paid — Recommended)

Set once per mode via Roo Code UI → Sticky Models → OpenRouter:

| Mode | Model | Temp | Reasoning | Provider Routing |
|------|-------|------|-----------|-----------------|
| 🏛️ Architect | `google/gemini-2.5-flash` | 0.3 | None | google-vertex |
| ⚡ Code | `minimax/minimax-m2.7` | 0.05 | None | [default] |
| ❓ Ask | `google/gemini-2.5-flash-lite` | 0.5 | None | google-vertex |
| 🐛 Debug | `deepseek/deepseek-v3.2` | 0.0 | **Low** | [default] |
| 🎯 Orchestrator | `minimax/minimax-m2.7` | 0.2 | None | [default] |
| 🔀 Merge Resolver | `deepseek/deepseek-v3.1-terminus` | 0.0 | None | [default] |
| 📄 Docs | `google/gemini-2.5-flash-lite` | 0.6 | None | google-vertex |
| 📋 User Story | `google/gemini-2.5-flash-lite` | 0.7 | None | google-vertex |
| ⚙️ DevOps | `deepseek/deepseek-v3.2` | 0.1 | **Low** | [default] |
| 🔒 Security | `deepseek/deepseek-v3.2` | 0.0 | **Medium** | [default] |

### Free Tier (OpenRouter `:free` variants — rate-limited, zero cost)

Same modes, different models. Set rate limit to **2 seconds** in Roo Code Advanced Settings when using free tier.

| Mode | Free Model | Temp | Notes |
|------|-----------|------|-------|
| 🏛️ Architect | `google/gemini-2.0-flash-exp:free` | 0.3 | 1M context, strong reasoning |
| ⚡ Code | `deepseek/deepseek-chat-v3-0324:free` | 0.05 | Best free coder, V3 quality |
| ❓ Ask | `google/gemma-3-27b-it:free` | 0.5 | Lightweight, fast Q&A |
| 🐛 Debug | `deepseek/deepseek-r1:free` | 0.0 | Reasoning model — set Error Limit to **2** |
| 🎯 Orchestrator | `meta-llama/llama-4-maverick:free` | 0.2 | Strong task planning |
| 🔀 Merge Resolver | `deepseek/deepseek-chat-v3-0324:free` | 0.0 | Deterministic diffs |
| 📄 Docs | `google/gemma-3-27b-it:free` | 0.6 | Good language quality |
| �� User Story | `mistralai/mistral-small-3.1-24b-instruct:free` | 0.7 | Structured output |
| ⚙️ DevOps | `meta-llama/llama-4-scout:free` | 0.1 | Infra-aware, efficient |
| 🔒 Security | `deepseek/deepseek-r1:free` | 0.0 | Deep taint analysis — set Error Limit to **2** |

> **Note on R1 free:** `deepseek/deepseek-r1:free` has no reasoning effort control (unlike the paid tier where you can set Low/Medium). Its internal thinking can loop. Mitigate by keeping Error & Repetition Limit at 2 when using it.

---

## Advanced Settings (per mode, set in Roo Code UI)

| Setting | Value | Why |
|---------|-------|-----|
| Enable todo list tool | ON | Structures multi-step tasks, prevents loop drift |
| Error & Repetition Limit | 3 (paid) / 2 (free R1) | Safety net against tool loops |
| Rate limit | 1s (paid) / 2s (free) | Prevents API rate-limit errors |
| Use custom temperature | ON | Values in model table above |
| OpenRouter Provider Routing | See model table | google-vertex for Gemini = faster routing |

---

## The €5 Debug Problem — Root Causes and Fixes

| Root cause | Fix in this config |
|-----------|-------------------|
| Model reads whole codebase first | Serena MCP-first rules — semantic search before any file read |
| Reasoning loops on debug tasks | V3.2 + Low reasoning effort (not R1, not High) |
| Context7 loads full library docs | fetch → specific URL first; ref.tools second; context7 last |
| No task structure → drift | Todo list tool mandatory for 3+ step tasks |
| Retries on failing commands | Anti-loop protocol + Error Limit = 3 |
| Expensive model on cheap tasks | gemini-2.5-flash-lite for Ask/Docs/UserStory |
| Complex reasoning burns tokens | crash-mcp scaffold before multi-hop taint/architecture analysis |

---

## Memory Bank

The memory bank gives the AI continuous context across sessions and machines. It lives in `memory-bank/` at the project root, is committed to the repository, and is read automatically at the start of every session.

### How It Works

**Session start (automatic):** The AI reads `productContext.md` and `activeContext.md` silently, then emits a single line:
```
[Memory Bank: Active — {project}, focus: {activeContext summary ≤10 words}]
```

This replaces the "explain the project from scratch" cost of every new session.

**Session end (triggered):** Type `UMB`, `update memory bank`, or `save context` to trigger a structured save. The AI updates only the files that changed:

- `activeContext.md` — what was worked on, blockers, next steps (updated every session)
- `decisionLog.md` — architectural decisions with rationale and rejected alternatives (updated when a decision is made)
- `progress.md` — completed / in-progress / backlog items (updated when status changes)
- `systemPatterns.md` — coding conventions established for the project (updated when a pattern is set)

### File Purposes

| File | Read | Written | Contains |
|------|------|---------|----------|
| `productContext.md` | Every session start | Rarely (project init only) | Tech stack, architecture summary, constraints |
| `activeContext.md` | Every session start | Every session end | Current focus, blockers, next steps |
| `systemPatterns.md` | Every session start | When convention established | Naming, error handling, API patterns |
| `decisionLog.md` | On demand | When decisions made | Dated ADRs — prevents re-litigating choices |
| `progress.md` | On demand | When status changes | Done / in-progress / backlog / tech debt |

### Consistent Behavior Across Machines

The `memory-bank/` directory and `.roo/rules/01-memory-bank-protocol.md` are both committed to the repository. Any machine that clones the repo gets:

1. The same session startup behavior (same rules file)
2. The same project context (same memory-bank files)
3. The same MCP tool decision trees (same rules file)

This means a developer on machine A can hand off to a developer on machine B — or to a fresh AI session — and the AI picks up exactly where things left off, with the same tools, the same conventions, and the same task context.

### Rules

- **NEVER** write to memory-bank without a UMB trigger or explicit user instruction.
- **NEVER** put code, API keys, or credentials into memory-bank files.
- **NEVER** create memory-bank if it doesn't exist — only scaffold it with `--init-project`.
- Read each file at most once per session (cache mentally, don't re-read).

### Setup

```bash
# Initialize for a new project (run once)
cd your-project
python path/to/roo-config/install.py --init-project

# Then fill in:
# - memory-bank/productContext.md  (tech stack, architecture, constraints)
# - projectBrief.md                (one-page summary for Serena onboarding)

# Commit everything
git add .roo/ memory-bank/ projectBrief.md
git commit -m "chore: initialize roo-config memory bank"
```

---

## MCP Server Installation

### Install All

```bash
python install.py --install-mcp
python install.py --test-mcp
```

### Individual Server Reference

#### serena
**Command:** `uvx --from git+https://github.com/oraios/serena serena start-mcp-server`
**API Key:** None
**Role:** Semantic LSP code search. Replaces most `read_file` calls. Always use first for code questions.

#### fetch
**Command:** `npx -y @modelcontextprotocol/server-fetch`
**API Key:** None
**Role:** Official MCP fetch — converts any URL to clean Markdown. Free, zero API key. Use before any search engine.

#### ref.tools
**Command:** HTTP — `https://api.ref.tools/mcp`
**API Key:** **`REF_TOOLS_API_KEY`** — get at [https://ref.tools](https://ref.tools)
**Role:** Token-efficient doc lookups. **95% fewer tokens than Context7.** Use before context7 when API key is set.

#### context7
**Command:** `npx -y @upstash/context7-mcp@latest`
**API Key:** None
**Role:** Version-accurate library documentation. Free fallback when ref.tools API key is not available.

#### duckduckgo-mcp
**Command:** `uvx --from duckduckgo-mcp duckduckgo-mcp`
**API Key:** None
**Role:** Primary web search. Privacy-safe, no API key. Replaces brave-search entirely.

#### crash-mcp
**Command:** `uvx --from crash-mcp crash-mcp`
**API Key:** None
**Role:** Token-efficient reasoning scaffold. Use before multi-hop taint analysis, complex debugging chains, or architecture review. Prevents runaway chain-of-thought token burn.

#### github
**Command:** Docker — `ghcr.io/github/github-mcp-server`
**API Key:** `GITHUB_PERSONAL_ACCESS_TOKEN` — [create at github.com/settings/tokens](https://github.com/settings/tokens) (scopes: `repo`, `read:org`, `read:user`)
**Role:** GitHub issues, PRs, commits. Dynamic toolsets = loads tools on demand (~4 at session start).

#### figma-dev-mode
**Command:** SSE — `http://127.0.0.1:3845/sse`
**API Key:** None
**Role:** Figma Dev Mode integration. Disabled by default. Enable per-project when doing UI work.

---

## Environment Variables

Set these **before** running MCP server commands. Restart VS Code after setting.

| Variable | Server | Required | Get Key At |
|----------|--------|----------|------------|
| `REF_TOOLS_API_KEY` | ref.tools | No (free tier available without) | https://ref.tools |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | github | Yes for GitHub features | https://github.com/settings/tokens |

### Windows PowerShell (this session)
```powershell
$env:REF_TOOLS_API_KEY = "ref_..."
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "ghp_..."
```

### Windows PowerShell (persist)
```
Win+R → sysdm.cpl → Advanced → Environment Variables → User variables → New
```

### macOS / Linux
```bash
export REF_TOOLS_API_KEY="ref_..."
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."
```

---

## Global MCP Settings Locations

| OS | Path |
|----|------|
| **Windows** | `%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json` |
| **macOS** | `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json` |
| **Linux** | `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json` |

---

## Known Limitations

- **duckduckgo-mcp rate limits** — DuckDuckGo may throttle aggressive queries. If search fails, try a more specific query or fall back to a `fetch` call on a known URL.
- **ref.tools optional** — The API key is optional (free tier without it), but without the key, context7 is used instead and consumes more tokens per lookup.
- **crash-mcp availability** — If `uvx --from crash-mcp crash-mcp` fails, the package may not be published under that name. Check [crash-mcp on PyPI](https://pypi.org/search/?q=crash-mcp) for the current package name and update `configs/mcp_settings.json`.
- **Free tier rate limits** — OpenRouter `:free` models share a rate-limited pool. Set rate limit to 2s per request in Roo Code Advanced Settings. Expect occasional 429 errors during peak hours.
- **Serena language support** — Serena requires a tree-sitter grammar for the project language. Supported: TypeScript, JavaScript, Python, Rust, Go, Java, C/C++. For unsupported languages, `read_file` is the fallback (not ideal, but necessary).
- **Windows path handling** — All paths in config files use forward slashes or `Path.home()` — no hardcoded Windows paths. If you encounter path issues on Windows, ensure you're running from a terminal with `%APPDATA%` set.

---

## Upgrade from v1/v2

```bash
python install.py          # backs up existing files, installs v3
python install.py --undo   # if anything breaks, restore backup
```

What changed in v3:
- Models corrected to only those available in Roo Code's OpenRouter dropdown
- Reasoning: None/Low/Medium (not just ON/OFF) — prevents looping
- Anti-loop protocol in every mode
- `duckduckgo-mcp` replaces `brave-search` as primary web search
- `crash-mcp` added as reasoning scaffold
- `ref.tools` added as token-efficient doc lookup
- Free tier model table added
- Memory bank protocol updated to use `duckduckgo-mcp` and `ref.tools`
- Hardcoded Windows paths removed — `uvx` used for Python MCP servers
