---
name: state-update-guard
description: Use when writing or updating BUILD_STATE.md, GOTCHAS.md, or any build state file at session close. Triggers on "update the build state", "write BUILD_STATE", "session close", "what did we accomplish", "summarize progress", "write me a handover", or any request to record session progress. Enforces evidence-grounded, minimally-destructive state updates that never mistake discussed work for completed work. Pair with the build-session-close skill and the Goose session-close recipe.
---

# State Update Guard

## When to use
- "Update the build state" / "write BUILD_STATE"
- "Session close" / "wrap up" / "what did we accomplish"
- "Write me a handover" / "summarize progress"
- Any request to record what happened in a build session
- Before writing `BUILD_STATE_EDIT_SCRIPT.md` or `GOTCHAS_UPDATE.md` to `agent-workdir/`
- Whenever the build-session-close skill is active and you are about to produce the update

## Hard rules

- **Three-tier claim classification — mandatory.** Every claim about session work is classified into exactly one tier. There is no fourth tier, and nothing is left unclassified:
  - **[DONE]** — the work is verifiably complete. Requires cited evidence (see Evidence Gate below). If you cannot cite evidence, it is NOT DONE.
  - **[DISCUSSED]** — the work was talked about, planned, or the user reported doing it, but no tool result or commit confirms it. This includes "the user said they completed step N" when you have not verified the outcome of step N.
  - **[PLANNED]** — not started. On the roadmap but no action taken this session.

- **Evidence Gate for [DONE].** Before marking anything [DONE], you must cite one of:
  1. A **commit SHA** you read from a `GOOSE_RESULT_*.md`, a git log, or a file-info timestamp — not a SHA you remember.
  2. A **tool result** from this session — a `read_text_file_mcp_filesystem` or `list_directory_mcp_filesystem` call whose output confirms the file exists with the expected content.
  3. An **explicit user completion statement** that names the specific deliverable — but ONLY for manual steps the user alone can perform (e.g., "I clicked Save in the LibreChat UI"). "I did step 3" is NOT evidence for step 5.

- **Never promote [DISCUSSED] to [DONE].** If the only evidence is a user statement, it stays [DISCUSSED] until a tool result or commit confirms it. State explicitly what evidence is missing and what verification would promote it.

- **Distinguish user action from system state.** "Michael copied the recipe" is a user action ([DISCUSSED] unless you read the destination file and confirmed it). "The recipe is installed in Goose" is a system state that requires file verification. These are different claims — do not collapse them.

- **Ground against the live source.** Read `BUILD_STATE.md` fresh via `read_text_file_mcp_filesystem` before drafting the edit script. Never update from memory. Verify every [DONE] claim against the current file state: does the file exist? does it contain what we claim? does the commit SHA appear in the log?

- **Edit script, not complete replacement.** Write an edit script that specifies surgical changes to the live BUILD_STATE.md — find/replace for header lines, insertions for new table rows, appends for the event log, section replacements for NEXT STEP. Do NOT write a complete replacement file. The edit script is safer because Goose validates each edit against the live file before applying it, and untouched sections are guaranteed to survive.

- **Append-only event log.** Every session appends its events to the `## Session event log (append-only)` section of BUILD_STATE.md. Past entries are immutable. This is the provenance trail — it is what makes the state auditable. See `templates/SESSION_EVENT_LOG_TEMPLATE.md` for the exact format.

- **No invented progress.** If you cannot find evidence for a claim, say "not found" rather than inferring. State what was discussed, what was planned, and what is unverified. A gap in the record is honest; a filled gap with invented evidence is a false-completion claim.

- **Say "not verified" rather than guess.** When you are unsure whether something completed, label it [DISCUSSED] and state the verification step that would resolve it. Never round up to [DONE] to make the session look productive.

- **No-gotchas means no file.** If no new environment gotchas were discovered this session, do NOT write `GOTCHAS_UPDATE.md` at all. A missing file is the correct signal to Goose that there is nothing to append. Never write meta-commentary ("No new gotchas this session") as file content — the Goose recipe will append whatever bytes are in the file, including commentary.

- **Large files require multi-read.** `read_text_file_mcp_filesystem` truncates output that exceeds its character limit (~6 KB). If a read returns a `[truncated: ... chars exceeded ... limit]` marker, you have NOT seen the full file. Use the `head` and `tail` parameters across multiple reads to capture every section. Do NOT draft the edit script until you have read and can see every section of the live file. An edit script built from a truncated read will reference sections that don't match the live file, and Goose will reject the edits.

- **Lean writes — avoid output-token truncation.** When writing files via `write_file_mcp_filesystem`, keep each file write under ~3000 tokens of content. If a file would exceed that, split it: write a lean main file containing only the essential structure, and move bulky content into a separate companion file written in a second tool call. For `BUILD_STATE_EDIT_SCRIPT.md` specifically: keep `event_log_append` entries concise (one line each, per the template), and use `section_replace` only when the replacement content is under ~2000 tokens. If a section replacement would be large, break it into multiple smaller `field_update` edits instead.

## Standards

- **Tense:** Event-log entries in past tense ("Committed", "Staged", "Discussed"). Next-step in imperative ("Create", "Read", "Run").
- **Length:** Event-log entries are one line each. BUILD_STATE sections are preserved at their existing length.
- **Format:** Event log uses the template in `templates/SESSION_EVENT_LOG_TEMPLATE.md`. Edit script uses the format in `templates/BUILD_STATE_EDIT_SCRIPT_TEMPLATE.md`.
- **Provenance:** Every [DONE] entry ends with `— evidence: <source>`. Every [DISCUSSED] entry ends with `— evidence: user statement (unverified)` or `— evidence: none yet`.

## Process

1. **Read fresh — capture the FULL file.** Read `/app/ai-context/BUILD_STATE.md` via `read_text_file_mcp_filesystem`. State the current phase and sub-step aloud. Do NOT proceed from memory. If the output contains a `[truncated: ... chars exceeded ... limit]` marker, you have NOT seen the full file — use the `head` and `tail` parameters across multiple reads to capture every section before drafting. Do NOT proceed to step 2 until you can see the full file.

2. **Inventory session claims.** List everything that happened or was discussed this session. For each item, ask: *Is this DONE, DISCUSSED, or PLANNED?* Be honest — if the user said "I did X" but you did not verify X, it is DISCUSSED.

3. **Gate every [DONE] claim.** For each item you want to mark [DONE], produce the evidence:
   - If it's a commit: read the `GOOSE_RESULT_*.md` or run a file check. Cite the SHA.
   - If it's a file creation: `read_text_file_mcp_filesystem` or `list_directory_mcp_filesystem` to confirm the file exists with expected content.
   - If it's a manual user step: confirm the user's statement names the specific deliverable AND that the deliverable matches what you're claiming. "I copied the recipe" ≠ "the agent was created."

4. **Draft the event-log entries.** Write append-only entries per `templates/SESSION_EVENT_LOG_TEMPLATE.md`. Each entry: date, phase_label, tier tag, claim, evidence pointer.

5. **Draft the edit script.** Using the live BUILD_STATE.md content as your reference, produce an edit script per `templates/BUILD_STATE_EDIT_SCRIPT_TEMPLATE.md`. Each edit specifies:
   - `## header` — find/replace for the header line (date, sub-step)
   - `## table_row` — insert a new table row after a specified line (use the exact existing row as anchor)
   - `## field_update` — find/replace a specific field value (e.g., H3 status)
   - `## event_log_append` — lines to append to the "Session event log" section
   - `## section_replace` — replace an entire section (find the heading, replace everything until the next `## ` heading)

   For each edit, the `find` or `after` text MUST be copied from the live file read in step 1 — not from memory. Goose will reject edits where the find text doesn't match the live file.

6. **Run the self-audit checklist (validate before write).** Before writing the edit script, answer every item below. If any answer is "no" or "unsure", fix the draft before writing:
   - [ ] Did I read BUILD_STATE.md fresh (not from memory)?
   - [ ] Is every [DONE] claim backed by a cited tool result, commit SHA, or file read from THIS session?
   - [ ] Did any [DISCUSSED] claim get promoted to [DONE] without new evidence? (If yes → demote it.)
   - [ ] Does the edit script preserve all existing sections (no section deletions)?
   - [ ] Are new events appended to the event log (not rewriting or deleting past entries)?
   - [ ] Is the next step specific enough to start cold (a runnable action, not "continue setup")?
   - [ ] Did I distinguish user actions from system state (no collapsing "user did X" into "system is Y")?
   - [ ] Did I distinguish "discussed an improvement" from "implemented an improvement"?
   - [ ] Did I check every read for truncation markers and re-read with head/tail until the full file was captured?
   - [ ] If no new gotchas were found, did I NOT write GOTCHAS_UPDATE.md (rather than writing meta-commentary)?
   - [ ] Does every `find`/`after` text in the edit script match the live file exactly (copied from the read, not memory)?

7. **Write the files.** Write `BUILD_STATE_EDIT_SCRIPT.md` (the edit script) to `/app/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md`. If new environment gotchas were found, write `GOTCHAS_UPDATE.md` to `/app/agent-workdir/GOTCHAS_UPDATE.md` (each entry: Symptom / Root cause / Fix, no secrets). If NO new gotchas were found, do NOT write `GOTCHAS_UPDATE.md` — a missing file is the correct signal. Never write meta-commentary ("No new gotchas") as file content.

8. **State the phase_label.** Give the user the exact `phase_label` string for the Goose `/close` command (e.g., `state-update-guard-skill`, `phase-9-deferred-item-5`).

9. **State the handoff line.** One line: what to paste into project knowledge and what Goose will commit.

## Output format

- **BUILD_STATE_EDIT_SCRIPT.md** — the edit script, written to `/app/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md`. Contains structured find/replace/append operations that Goose applies to the live BUILD_STATE.md.
- **GOTCHAS_UPDATE.md** (optional) — new GOTCHAS entries, written to `/app/agent-workdir/GOTCHAS_UPDATE.md`.
- **phase_label** — the string for Goose's `/close <phase_label>` commit message.
- **Handoff line** — one line stating what to paste into project knowledge and what Goose commits.

## What this agent cannot do

- Cannot write directly to `/app/ai-context/` — read-only via filesystem MCP. Writes go to `/app/agent-workdir/` for Goose to promote.
- Cannot execute git commands — that is Goose's job (the session-close recipe).
- Cannot verify manual user steps it cannot read (e.g., LibreChat UI clicks) — these stay [DISCUSSED] with the verification step stated.
- Cannot store credentials or secret values in any state file.
- Cannot edit or delete past event-log entries — the log is append-only. Corrections are new entries.

## Integration with the Goose session-close recipe

This skill produces the files the Goose recipe expects:
- `~/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md` → Goose reads it, applies each edit to the live BUILD_STATE.md using find-and-replace, validates each edit landed, commits, pushes.
- `~/agent-workdir/GOTCHAS_UPDATE.md` → Goose does `cat >>` to `~/ai-context/docs/GOTCHAS.md` (if it exists and is non-empty).

The `phase_label` this skill outputs is the `{{phase_label}}` parameter Goose's recipe requires. Do NOT change the Goose recipe — this skill works within its existing contract.

For the full Goose recipe flow, see `references/GOOSE_RECIPE_CONTRACT.md`.
