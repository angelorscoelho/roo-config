# Roo Code Global Budget Config — v3

Upgrades cleanly from v1 and v2. Does NOT touch API keys.

## What's New in v3

- **Models corrected** to only those available in Roo Code's OpenRouter dropdown
- **Reasoning: None/Low/Medium** (not just ON/OFF) — prevents looping by using the minimum needed
- **Anti-loop protocol** baked into every mode's instructions (references Roo's Error & Repetition Limit)
- **Todo list tool** integrated into modes that need it (complex tasks, orchestration, debug)
- **`fetch` MCP server** added — free, official, converts any URL to Markdown (use before duckduckgo-mcp)
- **Advanced settings guidance** per mode (provider routing, temp, rate limit, error limit)
- **Why NOT DeepSeek R1 for Debug/Security**: R1's uncontrolled internal thinking loops more aggressively than V3.2 + Low/Medium reasoning effort

## Quick Start

```bash
# Upgrade from v1/v2 (safe, backs up existing files)
python install.py

# Preview first
python install.py --dry-run

# Rollback
python install.py --undo

# New project scaffold
cd your-project
python path/to/roo-config/install.py --init-project
```

### MCP Server Validation (Run at Start of Every Session)

**CORRECT Workflow (in order):**

#### Step 1: Check If Already Installed
Before suggesting installation, ALWAYS check metadata first:

```bash
# Check for install log (confirms global install was run)
type .install_log 2>nul

# Check if global MCP settings exist
type %APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cite_mcp_settings.json 2>nul
```

**If `.install_log` exists AND global MCP settings exist → SKIP to Step 3**

#### Step 2: If NOT Already Installed
```bash
# First time on a machine — global install
python install.py

# Then MCP servers
python install.py --install-mcp
```

#### Step 3: Verify
```bash
python install.py --test-mcp
```

**Quick check:** Look for ✓ in test output = server ready. Look for ✗ = failed (check API keys or install errors).

## File Map

```
roo-config/
├── install.py
└── configs/
    ├── custom_modes.yaml                        10 modes, MCP trees, anti-loop
    ├── 00-global-budget-rules.md                global rules all modes inherit
    ├── mcp_settings.json                        5 servers (4 active + 1 disabled), zero credentials
    └── project-template/
        ├── projectBrief.md
        ├── .roo/
        │   ├── mcp.json                         Serena project override
        │   └── rules/
        │       └── 01-memory-bank-protocol.md   MCP tree + memory bank
        └── memory-bank/
            ├── productContext.md
            ├── activeContext.md
            ├── decisionLog.md
            ├── progress.md
            └── systemPatterns.md
```

## MCP Stack

| Server | Role | Tool count at start |
|--------|------|---------------------|
| **serena** | Semantic LSP code search — replaces most file reads | ~20 |
| **fetch** | URL → Markdown. Free. Official. Use before duckduckgo-mcp | 1 |
| **context7** | Library/framework docs, version-accurate | ~5 |
| **ref.tools** | Token-efficient doc lookups. 95% fewer tokens than Context7 | ~3 |
| **duckduckgo-mcp** | PRIMARY: Privacy-safe web search. No API key required | 1 |
| **crash-mcp** | Token-efficient reasoning scaffold | ~5 |
| **github** | Issues, PRs, code — dynamic discovery, loads on demand | ~4 |
| figma-dev-mode | Disabled | 0 |

**Total at session start: ~40 tools** (down from 68+ in original config)

## Model Assignments

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

## Advanced Settings (per mode, set in Roo Code UI)

- **Enable todo list tool** → ON
- **Error & Repetition Limit** → 3
- **Rate limit** → 1s
- **Use custom temperature** → ON (use values from table above)
- **OpenRouter Provider Routing** → see table (google-vertex for Gemini models = faster/cheaper routing)

## The €5 Debug Problem — Root Causes and Fixes

| Root cause | Fix in this config |
|-----------|-------------------|
| Model reads whole codebase first | Serena MCP-first rules in every mode |
| Reasoning loops on debug tasks | V3.2 + Low (not R1, not High) |
| Context7 loads full library docs | fetch → specific URL first; context7 second |
| No task structure → drift | Todo list tool mandatory for 3+ step tasks |
| Retries on failing commands | Anti-loop protocol + Error Limit = 3 |
| Expensive model on cheap tasks | gemini-2.5-flash-lite for Ask/Docs/UserStory |

## MCP Server Installation

This section outlines the process for installing Python-based MCP servers, incorporating lessons learned from recent development sessions.

### Key Lessons Learned

1. **Virtual Environment Requirement**: The `uv pip` command requires an active virtual environment. If no virtual environment is found, the installation will fail with an error message like "No virtual environment found."
2. **Installation Workflow**:
   - First, create a virtual environment using the command:
     ```bash
     uv venv
     ```
   - Once the virtual environment is created and activated, you can install packages using:
     ```bash
     uv pip install <package_name>
     ```
     Replace `<package_name>` with the actual name of the MCP server package you wish to install.
3. **Configuration**: After installation, MCP servers should be registered in the project's configuration file. Add the server details to `configs/mcp_settings.json` following the specified command format.

---

## TL;DR — MCP Server Quick Reference

Run `python install.py --install-mcp` to install all servers, then `python install.py --test-mcp` to verify connectivity.

### serena
**Install:** `uvx --from git+https://github.com/oraios/serena serena start-mcp-server`
**API Key:** None
**TL;DR:** Semantic LSP code search. Replaces most `read_file` calls. `uvx` verified automatically ✓

### fetch
**Install:** `npx -y @modelcontextprotocol/server-fetch`
**API Key:** None
**TL;DR:** Official MCP fetch — converts any URL to clean Markdown. Free, zero API key ✓

### context7
**Install:** `npx -y @upstash/context7-mcp@latest`
**API Key:** None
**TL;DR:** Version-accurate library documentation. Use for API lookups after trying fetch ✓

### ref.tools ⭐ REQUIRES API KEY
**Install:** `npx -y @upstash/ref-tools-mcp`
**API Key:** **`REF_TOOLS_API_KEY`** — Get at [https://ref.tools](https://ref.tools)
**TL;DR:** Token-efficient doc lookups. **95% fewer tokens than Context7.** Set `REF_TOOLS_API_KEY` env var before running install ✓

### duckduckgo-mcp
**Install:** `uv pip install duckduckgo-mcp` (in project's .venv)
**API Key:** None
**TL;DR:** PRIMARY web search. Privacy-safe, no API key required. Use instead of brave-search ✓

### crash-mcp
**Install:** `uv pip install crash-mcp` (in project's .venv)
**API Key:** None
**TL;DR:** Token-efficient reasoning scaffold. Replaces verbose chain-of-thought ✓

### github
**Install:** Docker image pulled at runtime (no manual install needed)
**API Key:** `GITHUB_PERSONAL_ACCESS_TOKEN` — [Create at github.com/settings/tokens](https://github.com/settings/tokens)
**Scopes:** `repo`, `read:org`, `read:user`
**TL;DR:** GitHub issues, PRs, code. Docker handles the rest ✓

### memory-bank (Project Template, not an MCP server)
**Install:** Run `python install.py --init-project` per project
**API Key:** None
**TL;DR:** Memory bank scaffolding — not an MCP server but a project template with `.roo/`, `memory-bank/`, and `projectBrief.md` ✓

### figma-dev-mode
**Install:** Disabled by default — enable per-project when doing UI work
**API Key:** None
**TL;DR:** Uncomment in `mcp_settings.json` when needed ✓

---

## Lessons Learned

### Discovery: Config Drift
The project's `configs/mcp_settings.json` and `install.py` had drifted from the actual global settings (`%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cite_mcp_settings.json`).

**Discrepancies found:**
| Server | In Project Docs | In Actual Global |
|--------|-----------------|------------------|
| `duckduckgo` | ✓ | ✗ (never installed) |
| `Ref` | ✓ | ✗ (never installed) |
| `fetch` | `python -m mcp_server_fetch` | `npx @modelcontextprotocol/server-fetch` |

**Fix:** Updated both `configs/mcp_settings.json` and `install.py` to match actual global settings.

### MCP Server Naming Convention
- **npm packages**: Use full package name with `@` scope (e.g., `@modelcontextprotocol/server-fetch`)
- **uvx packages**: Use `--from <package>` syntax
- **Python module**: Use `python -m <module>` only if pip-installed globally/in venv

### Global MCP Settings Location (Roo Code)
- **Windows:** `%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cite_mcp_settings.json`
- **macOS:** `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`
- **Linux:** `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`

### duckduckgo-mcp is the primary search solution
Privacy-safe web search without API keys. Replaces brave-search as the default search tool.

### fetch is free and official
The `@modelcontextprotocol/server-fetch` package is:
- **Free** — no API key required
- **Official** — from the MCP protocol creators
- **Efficient** — converts any URL to clean Markdown, use before duckduckgo-mcp

---

## Environment Variables Setup

**⚠️ CRITICAL: Set these BEFORE running MCP server commands:**

### Required API Keys

| Variable | Server | Get Key At | Notes |
|----------|--------|------------|-------|
| **`REF_TOOLS_API_KEY`** | ref.tools | https://ref.tools | **95% fewer tokens than Context7** |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | github | https://github.com/settings/tokens | Scopes: repo, read:org, read:user |

### Windows PowerShell (this session only)
```powershell
$env:REF_TOOLS_API_KEY = "ref_..."
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "ghp_..."
```

### Windows PowerShell (persist across sessions)
```
Win+R → sysdm.cpl → Advanced → Environment Variables → User variables → New
```

### macOS/Linux
```bash
export REF_TOOLS_API_KEY="ref_..."
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."
```

**After setting env vars, restart VS Code** — it does not inherit mid-session changes.
