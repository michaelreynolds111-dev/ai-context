# BUILD_FLOWS — Agent Types, Change Paths, and Goose Handoff

**Source:** `docs/V0_8_7_CAPABILITIES.md` (change paths) + `docs/USAGE_PATTERNS.md` (collaboration model), both committed at `ai-context/docs/`.
**Purpose:** The step-by-step flows for each agent type (A–E), including the Goose task planning and the dynamic-vs-staged change path for each.
**Last derived:** 14 August 2026.

---

## 1. THE FIVE AGENT TYPES

| Type | What it is | Needs infra? | Change path |
|---|---|---|---|
| **A** | Skill only (just a SKILL.md) | No | Staged (git commit) — no restart |
| **B** | Skill + MCP server | Yes — new MCP server | Staged (librechat.yaml restart) OR dynamic (UI allowlist) |
| **C** | Skill + model/endpoint | Yes — endpoint config | Staged (librechat.yaml restart) OR dynamic (admin panel override) |
| **D** | Skill + LibreChat agent | Yes — agent definition in MongoDB | Dynamic (API PATCH or admin panel) — no restart |
| **E** | Skill + infrastructure | Yes — scheduled tasks, Docker, etc. | Staged (Goose executes infra) |

---

## 2. CHANGE PATHS (FROM V0_8_7_CAPABILITIES.md)

### 2.1 Dynamic path (no restart)

| Capability | Mechanism | What it enables |
|---|---|---|
| Agent instructions | API PATCH to agent endpoint | Update system prompts, routing rules, tool lists — live |
| Skills (UI-registered) | Admin panel / agent UI | Author, edit, import, sync skills — live |
| MCP server registration | Admin panel UI | Add MCP servers to the allowlist — live |
| Model / endpoint overrides | Admin panel per-role/group config | Swap models, change endpoints per role or group — live |
| Feature flags | Admin panel | Toggle features without restart |

### 2.2 Staged path (restart required)

| Capability | Mechanism | Why restart |
|---|---|---|
| `librechat.yaml` changes | Edit file → restart `api` container | YAML is parsed at startup |
| Endpoint definitions | `librechat.yaml` `endpoints:` block | Parsed at startup |
| Memory block `validKeys` | `librechat.yaml` `memory:` block | Parsed at startup |

### 2.3 Decision rule

```
Can the change be applied via admin panel or API PATCH?
  YES → Dynamic path (stage in staging-librechat/ for review, apply live)
  NO  → Staged path (stage in staging-librechat/, validate, promote, restart)
```

For `ai-context/` changes (skills, docs, GOTCHAS): always staged via
`staging-ai-context/`, promoted via git commit. These are version-controlled
documents, not live-applied.

---

## 3. FLOW FOR EACH AGENT TYPE

### Type A — Skill only (no infra)

```
1. Scaffold SKILL.md → staging-ai-context/skills/{name}/SKILL.md
2. Review (user)
3. Commit: cd ~/ai-context && git add skills/{name}/ && git commit -m "Add {name} skill" && git push
4. Sync to Goose: & "C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1"
5. Register in LibreChat via admin panel (dynamic, no restart) — if desired
6. Exit test
```

**Change path:** Staged (git commit). **No restart.**

### Type B — Skill + MCP server

```
1. Scaffold SKILL.md → staging-ai-context/skills/{name}/SKILL.md
2. Write GOOSE_TASK for MCP server setup → agent-workdir/tasks/
3. Goose stages MCP server definition in staging-librechat/ (or registers via UI)
4. If librechat.yaml change: restart api container (staged path)
   If UI allowlist: no restart (dynamic path)
5. Review (user)
6. Commit skill + config
7. Exit test (verify MCP tools appear)
```

**Change path:** Staged (librechat.yaml restart) OR dynamic (UI allowlist).
**GOTCHAS to check:** MCP server auth requirements, env-var token requirements.

### Type C — Skill + model/endpoint

```
1. Scaffold SKILL.md → staging-ai-context/skills/{name}/SKILL.md
2. If per-role/group override: apply via admin panel (dynamic, no restart)
   If global default: stage librechat.yaml change → restart (staged path)
3. Review (user)
4. Commit skill + config
5. Exit test (verify the agent routes to the right model/endpoint)
```

**Change path:** Dynamic (admin panel override) OR staged (librechat.yaml restart).

### Type D — Skill + LibreChat agent

```
1. Scaffold SKILL.md → staging-ai-context/skills/{name}/SKILL.md
2. Create the agent definition in MongoDB via admin panel (dynamic, no restart)
   OR via API PATCH to the agent endpoint
3. Attach the skill to the agent
4. Review (user)
5. Commit skill
6. Exit test (verify the agent invokes the skill correctly)
```

**Change path:** Dynamic (API PATCH or admin panel). **No restart.**

### Type E — Skill + infrastructure

```
1. Scaffold SKILL.md → staging-ai-context/skills/{name}/SKILL.md
2. Write GOOSE_TASK for the infrastructure setup → agent-workdir/tasks/
   (scheduled tasks, Docker, services, etc.)
3. Goose executes the infra setup
4. Review (user)
5. Commit skill
6. Exit test (verify the infra works end-to-end)
```

**Change path:** Staged (Goose executes infra). **GOTCHAS to check:** WSL2
distro targeting, quoting layers, Docker boot races, sudo hangs.

---

## 4. THE GOOSE HANDOFF (FROM USAGE_PATTERNS.md)

### 4.1 The core rule
LibreChat is the **planner and verifier**. Goose is the **executor**.
LibreChat thinks, plans, verifies; Goose executes shell commands, file
operations, and infrastructure changes.

### 4.2 The handoff (file-based, not conversation)

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
```

### 4.3 Folders
- `~/agent-workdir/tasks/` — LibreChat writes GOOSE_TASK_<name>.md here
- `~/agent-workdir/outputs/` — Goose writes GOOSE_RESULT_<name>.md here
- `~/agent-workdir/scripts/` — shared utility scripts (incl. `goose-task` alias)
- `~/agent-workdir/archive/` — completed task/result pairs, moved after verification
- `~/agent-workdir/prompts/` — template library

### 4.4 GOOSE_TASK file required sections
- **Context** — why the task exists, what phase it's part of
- **Objective** — one sentence: what "done" looks like
- **Prerequisites** — what to read first, what state must be true
- **Steps** — concrete, copy-pasteable steps
- **Success criteria (exit test)** — checkable conditions
- **Constraints** — hard rules that apply, what NOT to do
- **Output** — where to write the result and what to include

### 4.5 The `goose-task` alias
A WSL2 shell function that scaffolds new GOOSE_TASK and GOOSE_RESULT files:
```bash
goose-task <descriptive_name>     # creates tasks/GOOSE_TASK_<NAME>.md from template
goose-task --list                 # lists pending tasks in tasks/
goose-task --result <name>        # creates outputs/GOOSE_RESULT_<NAME>.md from template
```

---

## 5. ANTI-PATTERNS (DO NOT)

- Don't make Goose call LibreChat's Agents API — file handoff is the integration.
- Don't make LibreChat call Goose headless as a custom endpoint — out of scope.
- Don't share memory between LibreChat and Goose — state lives in files.
- Don't use IPC or webhooks — the file handoff is deliberately simple.
- Don't let Goose execute without reading GOTCHAS.md if the task touches
  Docker, WSL, shell, or MCP.

---

*End of build flows. Re-read `docs/V0_8_7_CAPABILITIES.md` and
`docs/USAGE_PATTERNS.md` (both committed at `ai-context/docs/`) if the
LibreChat version or handoff model changes.*
