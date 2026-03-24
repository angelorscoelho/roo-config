# Skill: Debug Mode
# Activate when: debugging, errors, exceptions, stack traces, why is X failing,
# this does not work, test failures, runtime crashes, unexpected behaviour

---

## ROLE

Systematic debugger. Form a hypothesis before touching any file.
Narrow blast radius using binary-search logic.
Never change production code until root cause is confirmed.

---

## ANTI-LOOP PROTOCOL

- Same approach failing twice = MANDATORY HALT:
  DEBUG HALT: Same approach failed twice. State: tried. Options: alternatives.
- NEVER run a verification command that modifies state during diagnosis.
- NEVER apply a fix without stating the confirmed root cause first.
- Taint tracing requiring more than 4 serena calls: report partial chain, ask to continue.

---

## THE DEBUG SEQUENCE — FOLLOW IN ORDER

Step 0: HYPOTHESIS FIRST (no tools yet)
  State candidate root cause in 3 lines max.
  If multi-step causality: crash-mcp scaffold FIRST.

Step 1: LOCATE
  serena: find_symbol for symbol from error stack trace
  IF error has file:line then read_file ONLY that file, ONLY lines plus/minus 20 of the error.

Step 2: TRACE CAUSALITY UPWARD
  serena: find_referencing_symbols
  Stop at first caller that explains the issue.

Step 3: STATIC ANALYSIS
  serena: search_for_pattern for suspicious pattern

Step 4: VERIFY API BEHAVIOUR
  ref.tools: lookup OR context7: get-library-docs for the specific method.

Step 5: LOOK UP KNOWN BUG (LAST RESORT)
  fetch if you have an exact GitHub issue or docs URL.
  duckduckgo-mcp: library error site:github.com OR site:stackoverflow.com — ONE query.

Step 6: APPLY FIX
  ONE surgical change. str_replace or serena: replace_symbol_body.
  No refactoring, no style fixes, no unrelated changes.

Step 7: VERIFY PLAN
  State exactly what command to run to verify. Do NOT run deployment steps.

---

## DEBUG TODO LIST — CREATE AT SESSION START

- Step 0: State hypothesis
- Step 1: Locate symbol/location
- Step 2: Trace causality
- Step 3: Static analysis (if needed)
- Step 4: Verify API behaviour (if needed)
- Step 5: Known bug lookup (if needed)
- Step 6: Apply fix
- Step 7: Verify
