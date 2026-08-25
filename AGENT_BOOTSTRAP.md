# AGENT BOOTSTRAP — Backup AI System Build

**Purpose:** Single entry point for any agent (LibreChat or Goose) taking over work on the self-hosted Backup AI System build. Read this first, then follow its instructions.

**Created:** 10 August 2026
**Last updated:** 27 August 2026 — §7 refined to LibreChat model-switch framing
**Live state:** Always read `BUILD_STATE.md` fresh — this file is a pointer, not a snapshot.

---

## 1. SESSION OPENING RITUAL (mandatory)

Before doing anything else:

1. **Read `BUILD_STATE.md`** — the live progress tracker. State the current phase and sub-step aloud before proceeding.
2. **Read the relevant phase section** in `BACKUP_AI_MASTER_BUILD_PLAN.md` (the spine doc).
3. **Check `docs/GOTCHAS.md`** if touching anything a past session already fought with (Node, PowerShell↔WSL↔Docker quoting, Docker volumes, MCP auth).
4. **Never proceed on memory.** Always read the file fresh.

### How to read the files

| Agent | Access method | Path |
|---|---|---|
| **LibreChat** | Filesystem MCP (read-only) | `/app/ai-context/` |
| **Goose** | Developer extension (read/write) | `~/ai-context/` (WSL2) or `\\wsl.localhost\Ubuntu-24.04\home\michael\ai-context\` (UNC) |
| **Any agent** | GitHub (fallback) | `michaelreynolds111-dev/ai-context`, branch `master` |

LibreChat does NOT need the GitHub connector — the filesystem MCP is mounted and live. Goose reads via its developer extension. GitHub is a fallback only.

---

## 2. THE AUTHORITATIVE DOCUMENTS

All in the `ai-context` repo root unless noted:

| File | Purpose | When to read |
|---|---|---|
| `BUILD_STATE.md` | Live tracker — current phase, blockers, what's done, deferred items | **Every session, first** |
| `BACKUP_AI_MASTER_BUILD_PLAN.md` | Spine doc — full architecture, phases, exit tests, hard rules | When working a phase |
| `docs/GOTCHAS.md` | Permanent environment-specific facts (this machine only) | Before touching Docker, WSL, shell, MCP |
| `docs/MIGRATION_INVENTORY.md` | Remaining Claude Projects to migrate | During Phase 9 parallel-run |
| `README.md` | Repo layout and the household-vault rule | First-time orientation |
| `docs/MODEL_SELECTION_MATRIX.md` | Model-to-task mapping for build sequence steps | When recommending a model for the next step |

### Handoff docs (in `~/agent-workdir/`, not in git)

| File | Purpose |
|---|---|
| `GOOSE_HANDOFF_REPORT.md` | Full assessment of remaining work — what Goose does vs LibreChat, execution order, collaboration model |
| `GOOSE_TASK_PHASE_9A.md` | Ready-to-execute task file for Phase 9a (Tailscale + STT) — verified, with corrected config |
| `AGENT_BOOTSTRAP.md` | This file |

---

## 3. ENVIRONMENT FACTS

```
Machine:              Michael-PC, Windows 11 Home 26200, i5-12400, 15.8 GB RAM
Windows username:     micha  (not Michael — important for Windows paths)
WSL2:                 Ubuntu-24.04, VERSION 2, UNIX user = michael, home = /home/michael
Docker Desktop:       29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
git:                  core.autocrlf = false. Identity: michaelreynolds111-dev / michael.reynolds111@gmail.com
Disk:                 C: 464 GB / FullyEncrypted. D: FullyDecrypted (cannot be BitLockered).
.wslconfig:           memory=8GB, processors=6, swap=2GB

LibreChat v0.8.7:     ~/LibreChat — 6-container stack, frontend on host port 3080
Goose v41.0.0:        C:\Users\micha\AppData\Local\Programs\Goose\
Goose provider:       custom_deepinfra (base_url: https://api.deepinfra.com, base_path: v1/openai/chat/completions)
Goose skills:         7 skills at C:\Users\micha\.config\agents\skills\ — sync via sync_skills.ps1
gcloud CLI:           579.0.0 in WSL2, project librechat-504922
Tailscale:            installed on Windows host, not yet configured for LibreChat remote (Phase 9a)

Project files:        ~/  (WSL2 native, NEVER /mnt/c/)
Household vault:      ~/household-vault/  (NOT a git repo, never make it one)
Agent workdir:        ~/agent-workdir/  (LibreChat↔Goose handoff folder)
Compose overrides:    docker-compose.override.yml only — never touch the base compose file
```

### Shell context rule — every command must specify which shell:
- **WSL2:** `wsl -d Ubuntu-24.04 -- bash -lc "[command]"` (always target the distro explicitly — bare `wsl` may land in docker-desktop)
- **Windows PowerShell:** explicit `pwsh` or PowerShell prompt
- **Docker:** use service names (`docker compose exec api`), not container names

---

## 4. HARD RULES (non-negotiable)

### The Credential Rule — absolute, no exceptions
Passwords, PINs, MFA seeds, recovery codes, security answers, and private keys **never enter this system in any form.** Not in chat, not in RAG, not in memory, not in git, not in a skill. The system may hold a *pointer* to where a credential lives ("NRMA login is in Bitwarden, item name X") but never the value. If a build step appears to require storing a credential, the step is wrong — stop and redesign.

### Routing / privacy
- Clinical, family-law, household identity content → **DeepInfra direct or Anthropic direct only.** Never OpenRouter or any logging-enabled path.
- No hosted embeddings for clinical or household collections. **Local embeddings only** (mandatory, not fallback).
- Verified clean 9 Aug 2026: Clinical Work agent routing confirmed via DevTools — DeepInfra fetch only, no external hosts.

### Agent tool restrictions
- **Clinical Work agent:** zero tools, by design. Never add any.
- **Household Admin agent:** never add browser, web search, shell, code execution, or memory tools. Confirmed `tools: []` in MongoDB (9 Aug 2026).

### Git discipline
- `git config --global core.autocrlf false` before any clone (already set on this machine)
- No `git pull` needed after a push — all commits originate from the same WSL2 clone
- Gitleaks pre-commit hook is active and **blocking** — do not disable

### Infrastructure
- Two independent Docker Compose stacks: `librechat` and `torbox-system`. They stay independent.
- Goose config changes (`custom_deepinfra.json`) require full Goose quit + relaunch.
- `sudo` commands that prompt for a password must run in a live WSL2 terminal, not an automated shell (interactive prompts hang).
- Relative bind mounts in `docker-compose.override.yml` break on restart — use absolute WSL2 paths. Fixed 9 Aug 2026 (see GOTCHAS.md §5).
- MongoDB UID/GID warnings are cosmetic — do NOT set UID=1000 in .env (causes crash-loop, see GOTCHAS.md §3).

### What NOT to do
- Don't build anything on Roo Code (shut down 2026)
- Don't use `/mnt/c` or Windows paths for project files
- Don't touch the base compose file — override only
- Don't process logs or pastes >~2000 tokens — ask to trim first
- Don't use `tailscale funnel` — only `tailscale serve` (tailnet-private, not public internet)
- Don't make `~/household-vault/` a git repo — it never becomes one

---

## 5. CURRENT STATE (as of last BUILD_STATE read)

**Phases 0–8: ALL PASSED.** System is live.

**Phase 9 — Cutover: IN PROGRESS.**

| Next work item | Who | Status |
|---|---|---|
| **Phase 9a — Remote mobile access + STT** | Goose executes, LibreChat verifies | 👉 NEXT — task file ready in `agent-workdir/GOOSE_TASK_PHASE_9A.md` |
| Goose + LibreChat integration polish | Both | Queued behind 9a |
| Workspace consolidation (Session 10) | Goose | Queued — needs root path decision |
| Docker anomaly verify | Goose | Queued — 1 command |
| Tier-1 credential quarantine | Goose + human | Queued — needs H3 password manager decision |
| Legacy pipeline audit | Goose | Queued — blocks Cluster 6 |
| Cluster 6 Household DB agent build | Goose (vault) + LibreChat (agent) | Post-Session 10 |
| Claude Projects migration | LibreChat | Post-cutover, ongoing |

### Open decisions needed from Michael (blocking)
1. **H3 — Password manager:** Bitwarden or 1Password? (Unblocks Tier-1 quarantine + Cluster 6)
2. **ai-workspace root path:** `C:\Users\micha\ai-workspace\` as proposed, or different? (Unblocks workspace consolidation)
3. **Goose execution mode:** Scoped no-confirmation autonomous, or confirmation on every command?
4. **stash-go.sqlite backup:** Part of Session 10 or separate?
5. **Commit workflow:** Goose commits directly, or writes to `agent-workdir` and Michael commits?

---

## 6. THE GOOSE ↔ LIBRECHAT COLLABORATION MODEL

They do not share a conversation. They share **files**.

```
LibreChat (planner/verifier)          Goose (executor)
    │                                      │
    │  reads build docs via MCP            │  reads build docs via dev extension
    │  writes task instructions ──────────►│  reads task instructions
    │                                      │  executes (shell, file ops, Docker)
    │  reads results ◄─────────────────────│  writes results/report
    │  verifies against exit test           │
    │  updates BUILD_STATE.md               │  (or Goose updates it directly)
```

### Handoff protocol
1. **LibreChat plans** → writes `GOOSE_TASK_<name>.md` to `~/agent-workdir/`
2. **Goose executes** → writes `GOOSE_RESULT_<name>.md` to `~/agent-workdir/`
3. **LibreChat verifies** → reads result file, checks exit test, signs off or flags failures
4. **State update** → whoever is holding the session updates `BUILD_STATE.md` and commits via local git

### LibreChat's access constraints
- **Read-only** on `/app/ai-context/` — cannot commit directly
- **Read-write** on `/app/agent-workdir/` — scratch space for task files and result reviews
- For `BUILD_STATE.md` updates: write the update to `agent-workdir`, Michael or Goose commits it

---

## 7. MODEL RECOMMENDATION PRACTICE

At the end of **every response**, the Build Coordinator must recommend the
model Michael should switch **LibreChat** to for the next step that the
Build Coordinator itself will perform.

This is about the **LibreChat (Build Coordinator) model only** — NOT about
Goose. Goose is always pinned to DeepSeek V4 Flash and only executes
delegated shell/file/Docker work; it never uses the LibreChat model
selector. When the next step is a task being delegated to Goose, still
recommend the model the Build Coordinator should be on to **plan and
verify** that task (usually the default).

Recommendation line format:

    **Recommended model for next step (switch LibreChat to):** [model label] — [one-line rationale]

Preference is budget tier; escalate one rung at a time only when the task
type requires it. If the next step uses the current model, state
"(current — no switch)".

### Available models (from `librechat.yaml` — all via DeepInfra endpoint)

**Budget tier (default — use unless a reason below escalates):**

| Model | ID (`librechat.yaml`) | Cost/1M in/out | Best for |
|---|---|---|---|
| GPT-OSS 120B | `openai/gpt-oss-120b` | $0.037/$0.17 | Cheapest; bulk classification, extraction |
| Ling 3.0 Flash | `inclusionAI/Ling-3.0-flash` | $0.06/$0.18 | High-volume agentic loops |
| Nemotron 3.5 Lightning | `nvidia/NVIDIA-Nemotron-3.5-Lightning` | $0.08/$0.20 | Low-latency always-on agent |
| **DeepSeek V4 Flash 0731** | `deepseek-ai/DeepSeek-V4-Flash-0731` | $0.08/$0.18 | **Build Coordinator default** |
| DeepSeek V4 Flash | `deepseek-ai/DeepSeek-V4-Flash` | $0.09/$0.18 | Bulk ETL pipelines |
| Gemma 4 31B Turbo | `google/gemma-4-31B-it-turbo` | $0.09/$0.34 | Cheap multimodal vision |
| Qwen3.5 35B | `Qwen/Qwen3.5-35B-A3B` | $0.14/$1.00 | Everyday drafting, summaries |

**Value tier (escalate here when budget isn't enough):**

| Model | ID (`librechat.yaml`) | Cost/1M in/out | Best for |
|---|---|---|---|
| DeepSeek V3.2 | `deepseek-ai/DeepSeek-V3.2` | $0.26/$0.38 | General-purpose all-rounder |
| Gemini 3.1 Flash Lite | `google/gemini-3.1-flash-lite` | $0.25/$1.50 | 1M context, bulk doc ingestion |
| Qwen3.5 122B | `Qwen/Qwen3.5-122B-A10B` | $0.29/$2.40 | Complex analysis, long technical writing |
| **Qwen3 Coder 480B** | `Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo` | $0.30/$1.00 | **Best value coder** — code gen, review |
| MiniMax M3 | `MiniMaxAI/MiniMax-M3` | $0.28/$1.10 | Multimodal (text/image/video), 1M ctx |
| Kimi K2.5 | `moonshotai/Kimi-K2.5` | $0.45/$2.25 | General reasoning, vision |
| GLM 5.2 | `zai-org/GLM-5.2` | $0.75/$2.40 | Long-context reasoning, structured output |

**Flagship tier (reserve for strictly necessary cases only):**

| Model | ID (`librechat.yaml`) | Cost/1M in/out | Best for |
|---|---|---|---|
| DeepSeek V4 Pro 0813 | `deepseek-ai/DeepSeek-V4-Pro-0813` | $1.30/$2.60 | Near-frontier reasoning, deep analysis |
| Claude Sonnet 5 | `anthropic/claude-sonnet-5` | $2.00/$10.00 | **[SENSITIVE]** clinical/legal — required routing |
| Kimi K3 | `moonshotai/Kimi-K3` | $2.85/$14.25 | Long-horizon reasoning, big-context |
| Claude Opus 5 | `anthropic/claude-opus-5` | $5.00/$25.00 | **Highest cost** — final review only |

### Task-type → Model mapping

| Task type | Recommended model | Why |
|---|---|---|
| Routine build coordination | DeepSeek V4 Flash 0731 | $0.08/$0.18 — default; planning, session opening, state updates |
| Code generation / review | Qwen3 Coder 480B | $0.30/$1.00 — best value coder |
| Architecture / deep analysis | DeepSeek V4 Pro 0813 | $1.30/$2.60 — near-frontier reasoning, fraction of Claude cost |
| Safety / acceptance review | DeepSeek V4 Pro 0813 | $1.30/$2.60 — deep reasoning for leakage/gating checks |
| Bulk / pipeline / ETL | GPT-OSS 120B | $0.037/$0.17 — cheapest capable model |
| Long-context analysis | GLM 5.2 | $0.75/$2.40 — 1M context, multi-step reasoning |
| Clinical / household [SENSITIVE] | Claude Sonnet 5 | $2.00/$10.00 — **required routing** per §4 |
| Final critical review (rare) | Claude Opus 5 | $5.00/$25.00 — highest stakes only |

### Escalation ladder (cost-aware)

```
Default:   DeepSeek V4 Flash 0731       ($0.08/$0.18)
  ↓ reasoning needed
Reasoning: DeepSeek V4 Pro 0813          ($1.30/$2.60)
  ↓ code focus needed
Code:      Qwen3 Coder 480B              ($0.30/$1.00)
  ↓ SENSITIVE routing required
Clinical:  Claude Sonnet 5               ($2.00/$10.00)
  ↓ absolute highest stakes only
Critical:  Claude Opus 5                 ($5.00/$25.00)
```

### Rules
- Always recommend the cheapest model that can do the job well.
- Escalate one rung at a time — never skip to Claude Opus 5 unless every cheaper option has been considered and rejected with a stated reason.
- Clinical/household [SENSITIVE] content must always recommend Claude Sonnet 5 (required routing per §4).
- If the next step requires the same model as the current one, state "(current)" to confirm no switch is needed.
- Full matrix with all 20 models: see `docs/MODEL_SELECTION_MATRIX.md`.

---

*This file should be committed to the `ai-context` repo root. Once committed, any agent — LibreChat, Goose, or a future tool — gets told one thing: **"Read `AGENT_BOOTSTRAP.md` first, then follow its instructions."***
