# USAGE PATTERNS — LibreChat ↔ Goose Collaboration

**Purpose:** The definitive guide to how LibreChat and Goose work together on
the Backup AI System build. Read this alongside `AGENT_BOOTSTRAP.md` before
starting any task that involves both agents.

**Created:** 12 August 2026 (Deferred item 4 — integration polish)

---

## 1. THE CORE RULE: THINKING → LIBRECHAT, DOING → GOOSE

LibreChat is the **planner and verifier**. Goose is the **executor**.

| Capability | LibreChat | Goose |
|---|---|---|
| Read build docs (BUILD_STATE, plan, GOTCHAS) | ✅ via filesystem MCP (read-only) | ✅ via developer extension (read-write) |
| Write task instructions | ✅ to `agent-workdir/tasks/` | reads from there |
| Execute shell commands (WSL2, Docker, PowerShell) | ❌ no shell access | ✅ developer shell extension |
| Execute file operations in WSL2 | ❌ MCP filesystem can't write to WSL UNC | ✅ developer shell |
| Write results/reports | reads from `agent-workdir/outputs/` | ✅ writes there |
| Verify against exit tests | ✅ reads result files | reports completion |
| Update BUILD_STATE.md | ✅ writes update to agent-workdir, Goose or Michael commits | ✅ can commit directly via git |
| Web search | ✅ Tavily MCP | ❌ (not configured) |
| RAG / projects / memory | ✅ native | ❌ |
| MCP tools (filesystem, GitHub, Spotify) | ✅ | ✅ (different set) |

**The rule in one sentence:** LibreChat thinks, plans, and verifies; Goose
executes shell commands, file operations, and infrastructure changes.

---

## 2. THE HANDOFF PROTOCOL (FILE-BASED, NOT CONVERSATION)

LibreChat and Goose do not share a conversation. They share **files** in
`~/agent-workdir/`.

```
LibreChat (planner/verifier)              Goose (executor)
    │                                          │
    │  1. reads BUILD_STATE.md via MCP         │  reads BUILD_STATE.md via dev extension
    │  2. plans the task                      │
    │  3. writes GOOSE_TASK_<name>.md ────────►│  4. reads task file
    │                                          │  5. executes (shell, Docker, file ops)
    │  7. reads GOOSE_RESULT_<name>.md ◄───────│  6. writes result file
    │  8. verifies against exit test           │
    │  9. signs off or flags failures          │
    │ 10. updates BUILD_STATE.md               │  (or Goose updates it directly)
```

### Folder structure

```
~/agent-workdir/
├── tasks/           ← LibreChat writes GOOSE_TASK_<name>.md here
├── outputs/         ← Goose writes GOOSE_RESULT_<name>.md here
├── scripts/         ← shared utility scripts (diag, helpers, goose-task)
├── archive/         ← completed task/result pairs, moved after verification
├── prompts/         ← template library (symlinked from ai-context/prompts/)
└── librechat.yaml.updated  ← working copy of config for review
```

### File naming convention

| File | Who writes | Who reads |
|---|---|---|
| `GOOSE_TASK_<descriptive_name>.md` | LibreChat | Goose |
| `GOOSE_RESULT_<descriptive_name>.md` | Goose | LibreChat |
| `GOOSE_HANDOFF_REPORT.md` | LibreChat (initial assessment) | Goose |

Use `UPPER_SNAKE_CASE` for the name suffix. Keep names descriptive but short
(e.g. `PHASE_9A_TAILSCALE_STT`, `MONGO_DURABILITY_FIX`, `DOCKER_ANOMALY_VERIFY`).

### Archival

After LibreChat verifies a result and updates BUILD_STATE.md, move the
task+result pair to `archive/`:

```bash
mv ~/agent-workdir/tasks/GOOSE_TASK_<name>.md ~/agent-workdir/archive/
mv ~/agent-workdir/outputs/GOOSE_RESULT_<name>.md ~/agent-workdir/archive/
```

For multi-phase work, group archives into subdirectories:
`archive/phase-9a-9b/` (already established).

---

## 3. TASK FILE FORMAT

A `GOOSE_TASK_<name>.md` file must contain enough context for Goose to execute
autonomously without reading the full build history. Use the template at
`prompts/GOOSE_TASK_TEMPLATE.md` (or `~/agent-workdir/prompts/`).

Required sections:
- **Context** — why the task exists, what phase it's part of
- **Objective** — one sentence: what "done" looks like
- **Prerequisites** — what to read first, what state must be true
- **Steps** — concrete, copy-pasteable steps
- **Success criteria (exit test)** — checkable conditions
- **Constraints** — hard rules that apply, what NOT to do
- **Output** — where to write the result and what to include

---

## 4. RESULT FILE FORMAT

Goose writes `GOOSE_RESULT_<name>.md` to `~/agent-workdir/outputs/` after
execution. Use the template at `prompts/GOOSE_RESULT_TEMPLATE.md`.

Required sections:
- **Status** — ✅ PASSED / ⚠️ PARTIAL / ❌ FAILED
- **Summary** — what happened
- **Steps executed** — what was done
- **Commands run** — trimmed output (see GOTCHAS — don't paste >2000 tokens)
- **Exit test results** — checkboxes with evidence
- **System state after execution** — what changed
- **Follow-up needed** — items for LibreChat or Michael

---

## 5. THE `goose-task` ALIAS

A WSL2 shell function that scaffolds new GOOSE_TASK and GOOSE_RESULT files from
templates.

**Location:** `~/agent-workdir/scripts/goose-task.sh` (sourced from `~/.bashrc`)

**Usage:**
```bash
goose-task <descriptive_name>     # creates tasks/GOOSE_TASK_<NAME>.md from template
goose-task --list                 # lists pending tasks in tasks/
goose-task --result <name>        # creates outputs/GOOSE_RESULT_<NAME>.md from template
goose-task --help                  # shows help
```

To install:
```bash
echo 'source ~/agent-workdir/scripts/goose-task.sh' >> ~/.bashrc
```

---

## 6. SKILL INDEX IN AGENT PROMPTS

LibreChat agents that may need to hand off work to Goose should include a
skill-index line in their instructions, pointing to the skills directory.
This lets the agent know what capabilities are available for delegation.

Add this block to the end of any LibreChat agent's instructions that might
delegate to Goose:

```
## Skill index (for Goose delegation)
The following skills are available for Goose execution. If a user request
requires shell/Docker/infrastructure work, write a GOOSE_TASK file to
~/agent-workdir/tasks/ referencing the relevant skill:
- clinical-writing: clinical note formatting and submission standards
- household-admin: household administration tasks (no tools, identity-protected)
- powershell-sysadmin: Windows sysadmin, scheduled tasks, PowerShell automation
- seddon-family-law-drafter: family law document drafting
- seddon-financial-forensics: financial forensic analysis
- session-close: build session close-out procedure
- build-session-close: build session close-out (backup AI system)
- workplace-law-research: workplace law research and citation
Skills live at ~/ai-context/skills/<name>/SKILL.md. Read the SKILL.md before
writing the task file to understand Goose's capabilities and constraints.
```

---

## 7. WHEN TO USE WHICH PATTERN

### Pattern A: Full handoff (plan → execute → verify)
Use when the task is complex, multi-step, or touches infrastructure.

1. LibreChat reads BUILD_STATE, plans the task
2. LibreChat writes `GOOSE_TASK_<name>.md` to `tasks/`
3. Michael runs Goose (or Goose picks it up): `goose-task` reads the file
4. Goose executes, writes `GOOSE_RESULT_<name>.md` to `outputs/`
5. LibreChat reads the result, verifies against exit test
6. State update + archive

### Pattern B: Direct Goose execution (no LibreChat planning)
Use when Michael knows exactly what needs doing and just wants Goose to do it.

1. Michael tells Goose directly (or writes a task file)
2. Goose executes
3. Goose writes result file
4. LibreChat verifies if needed

### Pattern C: LibreChat-only (no Goose)
Use when the task is research, writing, RAG, memory, or chat — no shell/Docker.

1. LibreChat does the work directly
2. No handoff needed

### Pattern D: Goose-only (no LibreChat)
Use when the task is pure sysadmin and doesn't need planning or verification.

1. Michael tells Goose directly
2. Goose executes
3. No result file needed (unless it changes build state)

---

## 8. ANTI-PATTERNS (DO NOT)

- **Don't** try to make Goose call LibreChat's Agents API — Goose is an agent,
  not a model consumer. The file handoff is the integration.
- **Don't** try to make LibreChat call Goose headless as a custom endpoint —
  this is technically possible (Option 4) but out of scope for this polish item.
  It's a future enhancement if the file handoff proves insufficient.
- **Don't** share memory between LibreChat and Goose — they have separate
  memory systems. State lives in files (BUILD_STATE.md, memory/).
- **Don't** use IPC or webhooks — the file handoff is deliberately simple and
  debuggable. Every handoff is a file you can read.
- **Don't** let Goose execute without reading GOTCHAS.md if the task touches
  Docker, WSL, shell, or MCP — past sessions fought hard for those facts.

---

## 9. EXIT TEST FOR THIS INTEGRATION

The integration is considered "polished" when:

- [x] `tasks/` and `outputs/` folders have README files explaining the protocol
- [x] `prompts/` library exists with task and result templates
- [x] `goose-task` alias is available in WSL2
- [x] Skill-index lines are drafted for LibreChat agent instructions
- [x] This document (USAGE_PATTERNS.md) is committed to ai-context
- [x] One real task executed end-to-end through the plan→execute→verify pattern

The final checkbox was the live exit test — the Docker anomaly verify task
(`GOOSE_TASK_DOCKER_ANOMALY_VERIFY.md`) was executed through the full
plan→execute→verify pattern on 13 Aug 2026. Result:
`GOOSE_RESULT_DOCKER_ANOMALY_VERIFY.md`. Verdict: not an anomaly — the
`admin-panel` container image is `registry.librechat.ai/clickhouse/librechat-admin-panel:latest`,
a legitimate LibreChat component hosted under the ClickHouse GitHub org.

**All exit test checkboxes checked — Deferred item 4 PASSED (13 Aug 2026).**
