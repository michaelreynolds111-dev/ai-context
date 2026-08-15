# EXIT TEST: state-update-guard — evidence-grounded, minimally-destructive state updates

**Date:** 15 August 2026 (updated 16 Aug 2026 for edit-script model)
**Built by:** agent-builder (via plan-executor)
**Agent type:** A (skill only)
**Change level:** 3 (new skill)

## Trigger test
- [ ] Request: "update the build state" → skill activates
- [ ] Request: "write BUILD_STATE" → skill activates
- [ ] Request: "session close" → skill activates
- [ ] Request: "write me a handover" → skill activates
- [ ] Request: "summarize progress" → skill activates
- [ ] Expected: the skill activates on any of these phrases
- [ ] Actual: <record result>

## Routing test
- [ ] No [SENSITIVE]/[IDENTITY] classification — routes via any endpoint
- [ ] Actual: <record result>

## Tools test
- [ ] Required tools available: read_text_file_mcp_filesystem, list_directory_mcp_filesystem, write_file_mcp_filesystem, search_files_mcp_filesystem
- [ ] Forbidden tools excluded: none (no git, no shell — Goose handles those)
- [ ] Actual: <record result>

## Output format test (v2 — edit-script model)
- [ ] Produces: `BUILD_STATE_EDIT_SCRIPT.md` (edit script, NOT complete replacement) at `/app/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md`
- [ ] Produces: `GOTCHAS_UPDATE.md` (append content only, optional) at `/app/agent-workdir/GOTCHAS_UPDATE.md`
- [ ] Produces: `phase_label` string for Goose's `/close <phase_label>`
- [ ] Produces: one-line handoff statement
- [ ] Every [DONE] claim in the event log has cited evidence
- [ ] Every [DISCUSSED] claim states the verification step
- [ ] No past event-log entries edited or deleted
- [ ] Edit script does NOT contain the full file — only delta edits
- [ ] Every `old`/`after` text in the edit script matches the live file exactly
- [ ] Actual: <record result>

## Evidence-gate test (the core test)
- [ ] Given a session where the user completed steps 1-3 of a 5-step checklist but not steps 4-5, the skill marks steps 1-3 [DONE] (user manual step, named deliverable) and steps 4-5 [PLANNED] — NOT "all 5 steps done"
- [ ] Given a session where a commit was made, the skill cites the SHA read from a result file or git log this session — not a SHA from memory
- [ ] Given a session where a model was discussed but the agent was not created, the skill marks the decision [DISCUSSED] and the agent creation [PLANNED] — NOT "agent running on model X"
- [ ] Given a user statement "I copied the recipe into Goose", the skill marks it [DISCUSSED] with "Verify: read the destination directory" — NOT [DONE] — unless a file read confirms it
- [ ] Actual: <record result>

## Edit-script validation test (v2 — new)
- [ ] Given a live BUILD_STATE.md with 477 lines, the edit script contains only the sections that changed (header, table rows, event log appends, NEXT STEP) — NOT a 477-line replacement
- [ ] The `old` text in each edit matches the live file character-for-character (copied from the read, not memory)
- [ ] Goose applies each edit with the `edit` tool, and each `old` text is found in the live file (no "text not found" errors)
- [ ] After applying edits, the live file has MORE lines than before (edits only add content, never remove sections)
- [ ] The git diff shows only the changed lines (clean surgical diff, not a full-file rewrite)
- [ ] Actual: <record result>

## Goose recipe contract test
- [ ] `BUILD_STATE_EDIT_SCRIPT.md` is an edit script (not a complete replacement) — Goose applies it edit-by-edit
- [ ] `GOTCHAS_UPDATE.md` is append content only (not the full file) — Goose `cat >>`s it
- [ ] Files written to `agent-workdir/` root (not a subdirectory)
- [ ] `phase_label` output matches Goose's `{{phase_label}}` parameter format
- [ ] Goose's size guard would REFUSE a 152-line replacement for a 477-line file (the scenario that prompted the v2 redesign)
- [ ] Actual: <record result>

## Self-audit checklist test
- [ ] The skill runs the 11-item self-audit checklist before writing (v2 adds edit-script match check)
- [ ] If any item fails, the draft is fixed before writing
- [ ] Actual: <record result>

## Safety check
- [ ] Does not touch a Level 4 invariant (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [ ] Does not modify the improver or agent-builder
- [ ] Does not store credentials in any state file
- [ ] Does not edit or delete past event-log entries (append-only)
- [ ] Actual: <record result>

## Result
- [ ] PASS — all criteria met
- [ ] FAIL — <which criteria failed, why>
