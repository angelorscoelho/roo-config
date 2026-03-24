# Global Agent Discipline Rules
# Install to: ~/Documents/Cline/Rules/01-agent-discipline.md

---

## Session Startup — MCP Validation

Before any task, verify MCP servers are live. A missing MCP server causes silent
fallthrough to expensive alternatives for the entire session.

```bash
cat .install_log 2>/dev/null && echo "INSTALLED"
python install.py --test-mcp
```

- ✓ = server ready
- ✗ = check API key env vars or run `python install.py --install-mcp`

If serena is unavailable: every code question becomes expensive. Alert the user.

---

## Anti-Loop Rules — MANDATORY

1. **Same approach failing twice = STOP.** Emit:
   ```
   HALT: [reason]. Tried: [what was attempted]. Options: [list 2–3 alternatives].
   ```

2. **JSON/XML malformed tool response?** Do NOT retry. Report raw error. Ask user.

3. **Reasoning loops** (re-analysing same evidence twice): Emit:
   ```
   REASONING HALT: [state what is known]. Continuing would loop. User input needed.
   ```

4. **Shell command fails twice** (same command, same args): STOP. Report state.

5. **Max 5 consecutive autonomous steps** without user confirmation. After step 5:
   emit progress summary, ask to continue. No exceptions.

---

## Todo List — Usage Policy

- Required for any task with >3 steps, any multi-file change, any multi-command sequence.
- Create the todo list **before** starting the first step.
- Update each item before starting the next step.

---

## Tool Call Discipline

- Never call `read_file` on the same path twice in one session.
- Never call `list_files` depth>1 as first action. Use `serena: get_symbols_overview`.
- Never call `list_files` on: `node_modules/`, `.git/`, `dist/`, `build/`, `__pycache__/`, `.venv/`.
- Tool error? Log it. Retry ONCE with corrected call. Three failures = halt and ask user.

**Forbidden reads** (unless task is explicitly about these files):
```
package-lock.json   yarn.lock   pnpm-lock.yaml   poetry.lock
tsconfig.json       webpack.config.js              vite.config.ts
.env                *.pem        *secret*           *credential*
*_key*              mcp_settings.json              cline_mcp_settings.json
```

---

## Security Absolutes

- NEVER read `.env`, `*.pem`, `*secret*`, `*credential*`, `*_key*` under any circumstance.
- NEVER output credentials, tokens, or API keys in any response or tool call.
- NEVER read MCP settings files — they may reference sensitive environment variables.
- NEVER run destructive cloud/infra commands without a confirmation prompt:
  ```
  ⚠️ DESTRUCTIVE: [exact command]. Effect: [what changes]. Confirm? (yes/no)
  ```

---

## Output Discipline

- Never output a full file when a targeted diff suffices.
- Never restate the user's question before answering.
- No filler: "Now let's move on to...", "Great question!", "Certainly!", "Absolutely!".
- No closing pleasantries. End with the deliverable.
- Lead with the direct answer. Caveats follow.