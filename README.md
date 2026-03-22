# Roo Code Global Budget Config — v3

Upgrades cleanly from v1 and v2. Does NOT touch API keys.

## What's New in v3

- **Models corrected** to only those available in Roo Code's OpenRouter dropdown
- **Reasoning: None/Low/Medium** (not just ON/OFF) — prevents looping by using the minimum needed
- **Anti-loop protocol** baked into every mode's instructions (references Roo's Error & Repetition Limit)
- **Todo list tool** integrated into modes that need it (complex tasks, orchestration, debug)
- **`fetch` MCP server** added — free, official, converts any URL to Markdown (use before brave-search)
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

## File Map

```
roo-config/
├── install.py
└── configs/
    ├── custom_modes.yaml                        10 modes, MCP trees, anti-loop
    ├── 00-global-budget-rules.md                global rules all modes inherit
    ├── mcp_settings.json                        5 servers, zero credentials
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
| **fetch** | URL → Markdown. Free. Official. Use before brave-search | 1 |
| **context7** | Library/framework docs, version-accurate | ~5 |
| **github** | Issues, PRs, code — dynamic discovery, loads on demand | ~4 |
| **brave-search** | Web search, CVEs. Max 2/session | 1 |
| figma-dev-mode | Disabled | 0 |

**Total at session start: ~31 tools** (down from 68+ in original config)

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
