# Memory Bank Protocol
# Commit this file. Identical behaviour on every machine that clones the repo.

---

## Session Start — Mandatory Before Any Task

If `memory-bank/` exists at project root:

1. `serena: list_memories()` — check what Serena has indexed for this project.
2. Read `memory-bank/productContext.md` — silently.
3. Read `memory-bank/activeContext.md` — silently.
4. Read `memory-bank/systemPatterns.md` — silently (skip if unchanged since last session).
5. Emit ONE line: `[Memory Bank: Active — {project}, focus: {activeContext summary ≤10 words}]`
6. Do NOT read other memory-bank files unless the task explicitly requires them.

If `memory-bank/` does NOT exist: skip silently. Do not create it. Do not mention it.

If project is new (no `.serena/memories/` directory):
- Run `serena: onboarding()` once. Do not run again.

---

## During Session — Quick Reference

| Question type | First tool |
|--------------|------------|
| Find a symbol | `serena: find_symbol` |
| Who calls X? | `serena: find_referencing_symbols` |
| What's in this directory? | `serena: get_symbols_overview` |
| Search for a pattern | `serena: search_for_pattern` |
| I have a URL | `fetch(url)` |
| Library docs | `ref.tools: lookup` → fallback `context7` |
| Complex reasoning (>3 steps) | `crash-mcp` FIRST |
| Current web info | `duckduckgo-mcp` (max 2 searches) |
| GitHub issue/PR | `github: get_issue / get_pull_request` |
| Everything else | `read_file` — LAST RESORT |

---

## Session End — Update Memory Bank (UMB)

**Trigger:** User types `UMB`, `update memory bank`, or `save context`.

1. Update `memory-bank/activeContext.md` — what was worked on, blockers, next steps (≤5 bullets).
2. Update `memory-bank/decisionLog.md` — if an architectural or library decision was made.
3. Update `memory-bank/progress.md` — mark completed ✓, add newly discovered items.
4. Update `memory-bank/systemPatterns.md` — if a new coding convention was established.
5. Run `serena: write_memory("session_{date}", "{brief summary}")`.
6. Emit: `[Memory Bank: Updated — {list of files changed}]`

**NEVER:** write without UMB trigger, read same file twice per session,
put credentials in memory-bank files, create memory-bank if it doesn't exist.
