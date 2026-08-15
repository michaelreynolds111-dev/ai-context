# Goose Recipe Contract — How state-update-guard Integrates with the Session-Close Recipe

**Source:** The Goose session-close recipe at
`agent-workdir/recipes/goose-recipe-session-close.yaml` (v1.0.1, edit-script model).
**Purpose:** The exact contract this skill must satisfy. Read this before writing
the update files so they match what Goose expects.

---

## The contract (v2 — edit-script model)

The Goose session-close recipe expects LibreChat to write zero, one, or two
files to `~/agent-workdir/` (the agent-workdir root, NOT a subdirectory):

| File Goose looks for | What it is | What Goose does with it |
|---|---|---|
| `~/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md` | **Edit script** — structured find/replace/append operations | Goose reads the live BUILD_STATE.md, applies each edit with the `edit` tool, validates each edit landed (find text matched), commits, pushes |
| `~/agent-workdir/BUILD_STATE_UPDATE.md` | **Complete replacement** (FALLBACK only — triggers size guard) | Goose compares line counts: if replacement < 80% of existing, REFUSES. Otherwise `cp` overwrites. |
| `~/agent-workdir/GOTCHAS_UPDATE.md` | GOTCHAS.md **additions** (append content, not the full file) | Goose pre-checks GOTCHAS.md is non-empty, then `cat >>` appends. Post-checks it's still non-empty. |

**PREFERRED format:** `BUILD_STATE_EDIT_SCRIPT.md` (edit script).
**FALLBACK format:** `BUILD_STATE_UPDATE.md` (complete replacement with size guard).

Always produce the edit script unless you cannot (e.g., the file needs a complete
restructure). The edit script is safer because:
- Goose validates each edit against the live file (find text must match)
- Untouched sections are guaranteed to survive (Goose only applies specified edits)
- The git diff is clean and auditable (only changed lines appear)
- Smaller handoff file (only deltas, not the full 477-line BUILD_STATE.md)

---

## Why the edit-script model replaced complete replacement

The complete-replacement model (`cp BUILD_STATE_UPDATE.md → BUILD_STATE.md`) was
inherently fragile:

1. **Silent data loss.** If LibreChat truncated the read or missed a section,
   the replacement silently dropped it. A 152-line "replacement" for a 477-line
   file would destroy 325 lines of history.
2. **No validation.** Goose's `cp` was blind — it had no way to check the
   replacement was complete or sane.
3. **Large context consumption.** LibreChat had to fit the entire BUILD_STATE.md
   in its context window, increasing the risk of truncation and recursion limits.

The edit-script model fixes all three: Goose validates, untouched sections
survive by default, and the handoff file is proportional to the session's
actual work.

---

## Edit script format

See `templates/BUILD_STATE_EDIT_SCRIPT_TEMPLATE.md` for the exact format. Summary:

```markdown
# BUILD_STATE_EDIT_SCRIPT

## header
old: "**Last updated:** 13 August 2026 (old text)"
new: "**Last updated:** 16 August 2026 (new text)"

## table_row
after: "| **9a — Remote mobile access + STT** | **✅ PASSED** | ... |"
add: "| **9B — MongoDB durability + backup** | **✅ PASSED** | ... |"

## field_update
old: "- H3: Password manager — UNDECIDED"
new: "- H3: Password manager — **RESOLVED: Bitwarden**"

## event_log_append
- 2026-08-15 [state-update-guard-skill] [DONE] Built skill — evidence: commit 8470dcc

## section_replace
section: "## NEXT STEP"
content: |
  New next step content here.
```

Goose applies each edit using the `edit` tool (find-and-replace). If any `old`
or `after` text is not found in the live file, Goose STOPS and reports the
mismatch — this means the edit script is stale (the file drifted since
LibreChat read it).

---

## Division of labor (do not change)

| Who | Does | Does NOT do |
|---|---|---|
| **LibreChat (this skill)** | Reads BUILD_STATE fresh, classifies claims, drafts the edit script, writes `BUILD_STATE_EDIT_SCRIPT.md` + optional `GOTCHAS_UPDATE.md` to `agent-workdir/`, outputs `phase_label` | Does NOT run git, does NOT write to `ai-context/`, does NOT sync skills, does NOT write complete replacement files (use edit script) |
| **Goose (session-close recipe)** | Fetches, checks sync, reads edit script, applies each edit to live BUILD_STATE.md with validation, `cat >>`s GOTCHAS (with pre/post checks), commits, pushes, verifies push, syncs skills | Does NOT write BUILD_STATE content, does NOT classify claims, does NOT decide the phase_label |

This division is deliberate: LibreChat is the planner (it saw the conversation);
Goose is the executor (it has shell + git access). The file handoff is the
integration boundary. Do not blur it.

---

## The phase_label

Goose's recipe requires a `phase_label` parameter. It cannot derive it because
it didn't see the LibreChat conversation. This skill must output the exact
string.

**Format:** lowercase, hyphenated, descriptive of the session's primary work.
**Examples:**
- `state-update-guard-skill`
- `phase-9-deferred-item-5`
- `agent-builder-meta-agent`
- `bitwarden-h3-resolution`

**Rule:** One label per session. It becomes the commit message:
`session: <phase_label>`. If the session did multiple distinct things, pick the
most significant.

---

## What this skill writes (exact paths)

```
/app/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md   ← edit script (PREFERRED)
/app/agent-workdir/BUILD_STATE_UPDATE.md       ← complete replacement (FALLBACK only — not recommended)
/app/agent-workdir/GOTCHAS_UPDATE.md           ← new GOTCHAS entries only (optional)
```

These are in `agent-workdir/` (read-write for LibreChat). Goose reads them from
`~/agent-workdir/` (same path — `agent-workdir` is mounted at the WSL2 home).

**Do NOT write to:**
- `/app/ai-context/BUILD_STATE.md` — read-only for LibreChat.
- `/app/ai-context/docs/GOTCHAS.md` — read-only for LibreChat.
- Any subdirectory of `agent-workdir/` — Goose looks at the root.

---

## Guards Goose performs (for your awareness)

The recipe v1.0.1 includes these safety guards:

1. **Edit validation:** Each `old`/`after` text in the edit script must match
   the live file. If it doesn't, Goose stops and reports the mismatch.
2. **Size guard (fallback mode only):** If using complete replacement, the
   replacement must be >= 80% of the existing file's line count. If smaller,
   Goose refuses to apply.
3. **GOTCHAS.md pre-check:** Verifies GOTCHAS.md is non-empty before appending.
   If empty, restores from git first.
4. **GOTCHAS.md post-check:** Verifies GOTCHAS.md is still non-empty after
   appending. If empty, reports an error.
5. **Line count check (edit mode):** After applying edits, verifies the line
   count is >= the pre-edit count. If the file shrank significantly, reports
   an error.

This skill does not perform these steps — they are Goose's safety net. But the
self-audit checklist in SKILL.md ensures the edit script is correct, so Goose's
guards pass cleanly.

---

## Sequence diagram

```
LibreChat (this skill)                    Goose (session-close recipe)
─────────────────────                     ────────────────────────────
1. Read BUILD_STATE.md fresh
2. Classify session claims
   ([DONE] / [DISCUSSED] / [PLANNED])
3. Gate every [DONE] with evidence
4. Draft edit script (find/replace/append)
5. Run self-audit checklist
6. Write BUILD_STATE_EDIT_SCRIPT.md
   Write GOTCHAS_UPDATE.md (if any)
7. Output phase_label + handoff line
                                          8.  User runs /close <phase_label>
                                          9.  Goose fetches, checks sync
                                          10. Read edit script + live BUILD_STATE.md
                                          11. Apply each edit (edit tool, validate find text)
                                          12. Pre-check GOTCHAS.md non-empty
                                          13. cat GOTCHAS_UPDATE.md >> GOTCHAS.md
                                          14. Post-check GOTCHAS.md non-empty
                                          15. git add -A && commit && push
                                          16. gitleaks hook runs
                                          17. Verify push (git status)
                                          18. Sync skills (sync_skills.ps1)
                                          19. Report commit SHA + guard results
```

---

*End of reference. The canonical Goose recipe lives at
`agent-workdir/recipes/goose-recipe-session-close.yaml` (v1.0.1).*
