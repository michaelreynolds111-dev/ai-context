# AGENT BOOTSTRAP — Backup AI System Build

**Purpose:** Single entry point for any agent (LibreChat or Goose) taking over work on the self-hosted Backup AI System build. Read this first, then follow its instructions.

**Created:** 10 August 2026
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

*This file should be committed to the `ai-context` repo root. Once committed, any agent — LibreChat, Goose, or a future tool — gets told one thing: **"Read `AGENT_BOOTSTRAP.md` first, then follow its instructions."**
