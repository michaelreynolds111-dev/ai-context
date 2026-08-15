# BUILD_STATE_UPDATE.md Template

**Source:** state-update-guard skill.
**Purpose:** The structure the complete replacement BUILD_STATE.md must follow.
Goose `cp`s this file over the existing BUILD_STATE.md, so it must be complete.

---

## Critical rule

`BUILD_STATE_UPDATE.md` is a **complete replacement**. Goose runs:
```bash
cp ~/agent-workdir/BUILD_STATE_UPDATE.md ~/ai-context/BUILD_STATE.md
```

If this file is partial, the existing BUILD_STATE.md is **destroyed**. Therefore:
- **Preserve every existing section** — copy them verbatim from the fresh read.
- **Preserve every table row** — do not drop completed phases from the status table.
- **Preserve every existing event-log entry** — append new ones below, never edit.
- **Update only** the sections where a verified change occurred.

---

## Document structure (preserve this)

```markdown
# BUILD STATE

**Last updated:** <YYYY-MM-DD> (<one-line description of this session's primary work>)
**Current phase:** Phase <N> — <name> (§<section>)
**Current sub-step:** <current sub-step>

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| <preserve all existing rows> | | | |
| <add new row only if a phase status changed> | | | |

## Environment facts (confirmed)
- <preserve all existing facts>
- <add new facts only if verified this session — mark with **bold** or a note>

## Session event log (append-only)

<!-- Past entries are immutable. Append new entries below. Never edit or delete. -->

- <preserve all existing entries verbatim>
- <YYYY-MM-DD> [<phase_label>] [<TIER>] <claim> — evidence: <source>
- <new entries for this session>

## <Preserve all existing session-history sections>
## <e.g., "2026-08-12 — Deferred item 4: ...">
## <e.g., "2026-08-09 — Phase 8 Validation ...">
## <etc. — copy verbatim>

## Open questions
- <preserve existing>
- <add new questions raised this session>

## NEXT STEP
<one specific, runnable action — not "continue setup">
```

---

## What to update (and what NOT to)

| Section | Update when | Do NOT |
|---|---|---|
| Last updated / Current phase / sub-step | Always — reflect this session | Invent a phase change that didn't happen |
| Phase status table | A phase status actually changed (verified) | Mark a phase PASSED without exit-test evidence |
| Environment facts | A new fact was verified via tool result | Add a fact from discussion alone |
| Session event log | Always — append this session's entries | Edit or delete past entries |
| Session-history sections | A new session's work (append a new section) | Rewrite or delete past session sections |
| Open questions | New questions were raised | Remove questions that are still open |
| NEXT STEP | Always — the cold-start action | Write "continue setup" or "TBD" |

---

## The self-audit checklist (run before writing)

Before writing `BUILD_STATE_UPDATE.md`, answer every item. If any is "no" or
"unsure", fix the draft:

- [ ] Did I read BUILD_STATE.md fresh via `read_text_file_mcp_filesystem` (not from memory)?
- [ ] Is every [DONE] claim backed by a cited tool result, commit SHA, or file read from THIS session?
- [ ] Did any [DISCUSSED] claim get promoted to [DONE] without new evidence? (If yes → demote it.)
- [ ] Does the replacement preserve all existing sections, table rows, and event-log entries?
- [ ] Are new events appended to the event log (not rewriting or deleting past entries)?
- [ ] Is the next step specific enough to start cold (a runnable action, not "continue setup")?
- [ ] Did I distinguish user actions from system state (no collapsing "user did X" into "system is Y")?
- [ ] Did I distinguish "discussed an improvement" from "implemented an improvement"?

If all items pass, write the file to `/app/agent-workdir/BUILD_STATE_UPDATE.md`.

---

*End of template.*
