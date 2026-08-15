# Session Event Log Template

**Source:** state-update-guard skill.
**Purpose:** The exact format for append-only event-log entries in BUILD_STATE.md.

---

## Where the log lives

BUILD_STATE.md has a section:

```markdown
## Session event log (append-only)

<!-- Past entries are immutable. Append new entries below. Never edit or delete. -->
```

Every session appends its entries below the last entry. Past entries are never
edited or deleted. If a prior entry was wrong, append a correction entry that
references it (e.g., `Correction for 2026-08-15 entry: ...`).

---

## Entry format

Each entry is a single line:

```
- <YYYY-MM-DD> [<phase_label>] [<TIER>] <claim> — evidence: <source>
```

### Fields

| Field | Value | Example |
|---|---|---|
| `YYYY-MM-DD` | Session date | `2026-08-15` |
| `phase_label` | The session's phase_label (same string Goose uses for the commit) | `state-update-guard-skill` |
| `TIER` | `[DONE]`, `[DISCUSSED]`, or `[PLANNED]` | `[DONE]` |
| `claim` | One sentence, past tense, naming the specific deliverable | `Committed 3 doc fixes (plan-executor index, model line, stale refs)` |
| `source` | The evidence pointer (see EVIDENCE_GATE.md) | `commit 1e8f27a` |

### Evidence pointer formats

| Evidence type | Format | Example |
|---|---|---|
| Commit | `commit <sha>` | `commit 1e8f27a` |
| Tool result | `<tool> on <path> showed <result>` | `list_directory_mcp_filesystem on /app/ai-context/skills showed 9 dirs` |
| File read | `read_text_file_mcp_filesystem on <path> confirmed <what>` | `read_text_file_mcp_filesystem on .../SKILL.md confirmed 9-skill index` |
| User manual step | `user stated "<exact statement>"` | `user stated "I clicked Save on the Build Coordinator agent"` |
| Unverified user statement | `user statement (unverified). Verify: <step>` | `user statement (unverified). Verify: read /app/ai-context/skills/<name>/SKILL.md` |
| None yet | `none yet. Verify: <step>` | `none yet. Verify: check agent model setting in LibreChat` |

---

## Example: a session's event-log block

```markdown
## Session event log (append-only)

<!-- Past entries are immutable. Append new entries below. Never edit or delete. -->

- 2026-08-12 [deferred-item-4] [DONE] Committed USAGE_PATTERNS.md + prompts/ library — evidence: commit <sha> (read from GOOSE_RESULT_*)
- 2026-08-12 [deferred-item-4] [DONE] goose-task alias installed in WSL2 — evidence: user stated "alias works, tested with docker-anomaly task"
- 2026-08-12 [deferred-item-4] [DONE] Docker anomaly verified end-to-end — evidence: GOOSE_RESULT_DOCKER_ANOMALY_VERIFY.md reports admin-panel is legitimate LibreChat component
- 2026-08-15 [state-update-guard-skill] [DONE] Staged state-update-guard skill (SKILL.md + 2 references + 2 templates) — evidence: write_file_mcp_filesystem on staging-ai-context/skills/state-update-guard/ confirmed
- 2026-08-15 [state-update-guard-skill] [DISCUSSED] Build Coordinator agent created in LibreChat — evidence: user statement (unverified). Verify: open the agent and confirm model is deepseek-ai/DeepSeek-V4-Flash-0731
- 2026-08-15 [state-update-guard-skill] [PLANNED] Build Coordinator agent test (read BUILD_STATE + follow agent-builder process) — evidence: none yet. Verify: start new chat with Build Coordinator, send test prompt
```

---

## Rules

1. **One line per entry.** If a claim needs more than one line, it's two claims.
2. **Past tense.** "Committed", "Staged", "Discussed", "Decided".
3. **Never edit or delete past entries.** Corrections are new entries:
   ```
   - 2026-08-15 [correction] [DONE] Correction for 2026-08-15 entry claiming agent created: agent was NOT created. Demoted to [DISCUSSED]. — evidence: read_text_file_mcp_filesystem on LibreChat config found no agent named "Build Coordinator"
   ```
4. **Every entry has a tier tag.** No untagged entries.
5. **Every [DONE] entry has evidence.** No evidence = not [DONE].
6. **[DISCUSSED] entries state the verification step.** The next session should
   know exactly what to check to promote it.

---

*End of template.*
