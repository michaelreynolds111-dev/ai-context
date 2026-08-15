# Goose Recipe Contract — How state-update-guard Integrates with the Session-Close Recipe

**Source:** The Goose session-close recipe at
`agent-workdir/recipes/goose-recipe-session-close.yaml` (corrected version,
`phase_label` required).
**Purpose:** The exact two-file contract this skill must satisfy. Read this
before writing the update files so they match what Goose expects.

---

## The contract (do not change)

The Goose session-close recipe expects LibreChat to write zero, one, or two
files to `~/agent-workdir/` (the agent-workdir root, NOT a subdirectory):

| File Goose looks for | What it is | What Goose does with it |
|---|---|---|
| `~/agent-workdir/BUILD_STATE_UPDATE.md` | The **complete replacement** BUILD_STATE.md | `cp ~/agent-workdir/BUILD_STATE_UPDATE.md ~/ai-context/BUILD_STATE.md` |
| `~/agent-workdir/GOTCHAS_UPDATE.md` | GOTCHAS.md **additions** (append content, not the full file) | `cat ~/agent-workdir/GOTCHAS_UPDATE.md >> ~/ai-context/docs/GOTCHAS.md` |

Then Goose runs:
```bash
cd ~/ai-context && git add -A && git commit -m "session: {{phase_label}}" && git push
```

The `{{phase_label}}` is a **required parameter** Goose cannot derive — this
skill must output it.

**Critical constraints from the recipe:**
- `BUILD_STATE_UPDATE.md` is a **replacement**, not a diff. Goose `cp`s it over
  the existing file. If it's a partial file, the existing BUILD_STATE.md is
  destroyed. This is why the guard skill enforces "preserve ALL existing
  content."
- `GOTCHAS_UPDATE.md` is **append content only**. Goose `cat >>`s it. If you
  write the full GOTCHAS.md, it gets duplicated. Write only the new entries.
- If neither file exists, Goose stops and asks the user whether LibreChat wrote
  them yet. So at least `BUILD_STATE_UPDATE.md` must exist.
- Goose runs the gitleaks pre-commit hook. No secrets in any update file.

---

## Division of labor (do not change)

| Who | Does | Does NOT do |
|---|---|---|
| **LibreChat (this skill)** | Reads BUILD_STATE fresh, classifies claims, drafts the complete replacement, writes `BUILD_STATE_UPDATE.md` + optional `GOTCHAS_UPDATE.md` to `agent-workdir/`, outputs `phase_label` | Does NOT run git, does NOT write to `ai-context/`, does NOT sync skills |
| **Goose (session-close recipe)** | Fetches, checks sync, `cp`s the update, `cat >>`s GOTCHAS, commits, pushes, verifies push, syncs skills | Does NOT write BUILD_STATE content, does NOT classify claims, does NOT decide the phase_label |

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
/app/agent-workdir/BUILD_STATE_UPDATE.md   ← complete replacement BUILD_STATE.md
/app/agent-workdir/GOTCHAS_UPDATE.md       ← new GOTCHAS entries only (optional)
```

These are in `agent-workdir/` (read-write for LibreChat). Goose reads them from
`~/agent-workdir/` (same path — `agent-workdir` is mounted at the WSL2 home).

**Do NOT write to:**
- `/app/ai-context/BUILD_STATE.md` — read-only for LibreChat.
- `/app/ai-context/docs/GOTCHAS.md` — read-only for LibreChat.
- Any subdirectory of `agent-workdir/` — Goose looks at the root.

---

## Verification Goose performs (for your awareness)

After committing and pushing, Goose verifies:
1. `git fetch origin && git status` shows "up to date with origin/master".
2. The commit SHA is reported.
3. Skills are synced via `sync_skills.ps1` (Windows PowerShell — Goose tells
   the user to run it if Goose is in WSL2).

This skill does not perform these steps. But the self-audit checklist in
SKILL.md ensures the files Goose receives are correct, so Goose's verification
passes cleanly.

---

## Sequence diagram

```
LibreChat (this skill)                    Goose (session-close recipe)
─────────────────────                     ────────────────────────────
1. Read BUILD_STATE.md fresh
2. Classify session claims
   ([DONE] / [DISCUSSED] / [PLANNED])
3. Gate every [DONE] with evidence
4. Draft complete replacement
   (preserve all existing content)
5. Run self-audit checklist
6. Write BUILD_STATE_UPDATE.md
   Write GOTCHAS_UPDATE.md (if any)
7. Output phase_label + handoff line
                                          8.  User runs /close <phase_label>
                                          9.  Goose fetches, checks sync
                                          10. cp BUILD_STATE_UPDATE.md → BUILD_STATE.md
                                          11. cat GOTCHAS_UPDATE.md >> GOTCHAS.md
                                          12. git add -A && commit && push
                                          13. gitleaks hook runs
                                          14. Verify push (git status)
                                          15. Sync skills (sync_skills.ps1)
                                          16. Report commit SHA
```

---

*End of reference. The canonical Goose recipe lives at
`agent-workdir/recipes/goose-recipe-session-close.yaml`.*
