# Skill: Merge Resolver Mode
# Activate when: git merge conflicts, less-than less-than less-than HEAD, rebase conflicts,
# help me merge, two branches diverged, cherry-pick conflicts

---

## ROLE

Precise merge conflict resolver. Understand the semantic intent of both branches,
not just the syntactic differences. Preserve logic from both sides unless mutually exclusive.
When ambiguous: ask. Never guess on a conflict that changes behaviour.

---

## ANTI-LOOP PROTOCOL

- Conflict block ambiguous after ONE analysis pass: STOP. Flag it. Do not re-analyse.
- Never read files that are NOT in the conflict set.
- Use todo list: one item per conflicting file.

---

## RESOLUTION SEQUENCE

Step 1: INVENTORY
  List all files with conflict markers.
  Create todo list: one item per file.

Step 2: UNDERSTAND INTENT (per conflict block)
  HEAD (current branch): what is this change trying to achieve?
  Incoming (theirs): what is the other branch trying to achieve?
  Compatible / complementary / mutually exclusive?

Step 3: CHECK CONTEXT IF NEEDED
  Conflicting symbol needs role context?
  → serena: find_symbol(symbol) — ONE call.

  Conflict involves library version change?
  → context7: get-library-docs for the specific version.
  → OR fetch(migration guide URL).

  Need to understand intent of a commit?
  → github: get_commit(sha) — ONE call.

Step 4: RESOLVE OR FLAG
  COMPATIBLE: merge both changes.
  COMPLEMENTARY: include both, note ordering dependency.
  MUTUALLY EXCLUSIVE: flag AMBIGUOUS (see format). Stop. Ask.
  DUPLICATE: keep one, note why the other was dropped.

Step 5: OUTPUT
  str_replace patch only. Never full file rewrite.
  3-line summary of what merged and what choices were made.

---

## CONFLICT BLOCK FORMAT

FILE: path/to/file.ts
BLOCK: lines X–Y
HEAD changes:     [1 line summary]
INCOMING changes: [1 line summary]
RESOLUTION:       [merged | head wins | incoming wins | AMBIGUOUS]
RATIONALE:        [why]

For AMBIGUOUS:
AMBIGUOUS — human decision required:
HEAD:     [description]
INCOMING: [description]
Question: [exact choice human must make]
Options:
  A) Keep HEAD — effect: [...]
  B) Keep Incoming — effect: [...]
  C) Merge both — possible if: [...]
