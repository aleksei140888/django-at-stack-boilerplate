---
name: memory
description: Writing to the project memory (docs/agents.md) — when a decision or edge case is worth recording, in what shape, and where else the signal has to land (a test, a playbook, CLAUDE.md). Use at the end of a task, and whenever CI failed, a user reported a bug, the architect corrected the approach, or a playbook disagreed with the code.
---

# Project memory (`docs/agents.md`)

`docs/agents.md` is memory between sessions: architectural decisions with the
alternatives that were rejected, edge cases, non-obvious framework behaviour. It
is not a work log — routine changes that follow existing conventions, ordinary
CRUD and cosmetics do not belong there.

## When to write

- A decision was made where real alternatives existed → record the choice **and
  why not the other one**.
- A non-trivial edge case, or behaviour of a framework or library that is not
  what its documentation would lead you to expect.
- Something cost noticeably more time than it should have.
- A pattern that worked and is not in `CLAUDE.md`, but will come up again.
- The architect pushed back or corrected the approach.
- Something noticed **in passing, outside the task** — undocumented behaviour of
  a dependency, technical debt, a strange shape in real data. One line in
  "Incidental observations" at the top of the file, no structure needed, no
  waiting for a better moment.

## Shape

A new section carries the date in its heading (`## Short title (2026-08)`) and a
matching line in the index at the top of the file. Structure:

**Context** (what you were doing) → **Decision** (what you chose) →
**Reason** (why not the alternative).

Show code only as the minimal example that reproduces the trap, not as a retelling
of the diff.

Write for someone who arrives in six months with no memory of this task. Name the
symptom they will see, not only the cause — "the page rendered unstyled" is what
they will search for; "Tailwind source detection" is what they will find once
they are already reading.

## Closing the feedback loop

When the reason for the entry is an **external signal** rather than something you
worked out while implementing, writing it down does not finish the job. Each
signal has a second destination, and it belongs in the **same commit** as the fix:

| Signal | Second destination |
|---|---|
| CI or a test failed and exposed a wrong assumption | A regression test for exactly that case. Reverting CI to green without one means the next run is unprotected |
| A user reported a bug the tests missed | A test that reproduces the bug |
| A playbook in `docs/playbooks/` led you the wrong way (stale step, disagrees with the code) | Fix the playbook in the same commit. A memory note only if the discrepancy is subtle |
| An edge case already described in `docs/agents.md` recurred | Extend the existing entry — its description or example was incomplete — do not add a duplicate |
| The pattern turned out to be a convention, not a one-off | `CLAUDE.md`, one line under Conventions |

A signal that does not reach a test, a playbook or the memory file means the same
class of mistake repeats in the next session. Breaking that loop is what costs the
most time in hindsight.
