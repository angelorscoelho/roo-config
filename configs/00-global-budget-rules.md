# Global Budget Rules v3 — All Roo Code Modes
# Installed to: ~/.roo/rules/00-global-budget-rules.md
# These apply to EVERY mode globally. Project .roo/rules/ files add on top.

## Session Startup — MCP Server Validation

**CORRECT Workflow (in order):**

### Step 1: Check If Already Installed
Before suggesting installation, ALWAYS check metadata first:

```bash
# Check for install log (confirms global install was run)
type .install_log 2>nul

# Check if global MCP settings exist
type %APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cite_mcp_settings.json 2>nul
```

**If `.install_log` exists AND global MCP settings exist → SKIP to Step 3**

### Step 2: If NOT Already Installed
```bash
# First time on a machine — global install
python install.py

# Then MCP servers
python install.py --install-mcp
```

### Step 3: Verify
```bash
python install.py --test-mcp
```

**Quick validation** — check the test output:
- ✓ = server ready
- ✗ = server failed (check API key env vars or install errors)

**Goal:** One command to ensure all MCP servers are live before starting any task. This prevents the "€5 debug problem" where agents waste time because search/doc tools aren't available.

**Goal:** One command to ensure all MCP servers are live before starting any task. This prevents the "€5 debug problem" where agents waste time because search/doc tools aren't available.

## ⚠️ Security Absolutes
- NEVER read .env, *.pem, *secret*, *credential*, *_key* files under any circumstance.
- NEVER output credentials, tokens, or API keys in any response or tool call.
- NEVER read mcp_settings.json — it may reference sensitive environment variables.

## MCP Priority Ladder — Cost Ascending, Use Top-Down
ALWAYS descend this ladder. Skip levels only if the level above cannot answer the question.

1. serena — structural code intelligence (find_symbol, find_referencing_symbols, get_symbols_overview, search_for_pattern)
2. fetch — any specific URL → clean Markdown. FREE. Use before any search engine.
3. context7 — library/framework/API documentation. Version-accurate. No hallucination.
4. duckduckgo-mcp — real-time web search (CVEs, releases, comparisons). No API key required.
5. github — issue/PR/commit context. Only when ticket number is referenced.
6. read_file — LAST RESORT. Only when serena explicitly returns nothing.

Skipping serena for a code question and going straight to read_file wastes money.
Skipping fetch for a URL question and going straight to duckduckgo-mcp wastes money.

## Anti-Loop Rules — MANDATORY
- Error & Repetition Limit in Roo Code is set to 3. This is your safety net.
- Do NOT wait for the limit to trigger. Self-enforce: same approach failing twice = STOP.
- When halting: emit "HALT: [reason]. State: [what was tried]. Options: [list alternatives]."
- Never silently retry a failed tool call with identical arguments. Change the approach or escalate.
- Reasoning effort is set deliberately per mode (None/Low/Medium). Do NOT mentally override it by re-reasoning the same evidence repeatedly.

## Todo List Tool — Usage Policy
- ENABLED globally in Roo Code Advanced Settings.
- REQUIRED for: any task with more than 3 steps, any multi-file change, any multi-command sequence.
- Update the todo list BEFORE starting each step, not after.
- A completed todo list is proof of structured execution. An absent todo list is a loop risk.

## Tool Call Discipline
- Never call read_file on the same path twice in one session.
- Never call list_files deeper than depth=1 as a first action. Use serena: get_symbols_overview.
- Never call list_files on: node_modules/, .git/, dist/, build/, __pycache__, .venv/, vendor/.
- Tool call error? Log it. Retry ONCE with corrected call. Three failures = halt and ask user.
- JSON/XML malformed response? Do NOT retry same call. Report raw error. Ask for guidance.

## Output Discipline
- Never output a full file when a targeted diff suffices.
- Never restate the user's question before answering.
- No closing pleasantries. End with the deliverable.
- No filler: "Now let's move on to...", "Great question!", "Certainly!".

## Context Management
- Conversation content takes priority over file reads. Check conversation first.
- FORBIDDEN files (unless task is explicitly about them): package-lock.json, yarn.lock,
  poetry.lock, pnpm-lock.yaml, tsconfig.json, webpack.config.js, vite.config.ts.

## Autonomous Step Limit
- Maximum 5 consecutive autonomous steps without user confirmation.
- After step 5: checkpoint. Emit progress summary. Ask to continue.
- This applies regardless of how simple each step seems.
