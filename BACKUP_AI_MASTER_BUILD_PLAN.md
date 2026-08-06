# BACKUP AI SYSTEM — MASTER BUILD PLAN

**Version:** 1.2
**Created:** 28 July 2026
**Last revised:** 7 August 2026
**Source research:** `AI_Build.pdf` — *Backup AI System Design for a Windows 11 Power User (July 2026)*
**Status:** SPINE DOCUMENT — this is the authoritative build reference for the project.

### Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 28 Jul 2026 | Initial plan, derived from `AI_Build.pdf` |
| 1.1 | 28 Jul 2026 | **Cluster 6 — Household administration added.** Introduces the family information database as a first-class requirement. Adds the `[IDENTITY]` tag and the three-tier household data model (§10.4); makes local embeddings **mandatory** rather than a fallback (§2, §6.3); adds the `Household Admin` agent with a hard tool exclusion (§7.4); adds credential and identity routing rules (§14.4); adds secret scanning to §4.4; adds three risk rows (§15). Ported forward from the pre-flight session — Cluster 6 was not in the source research. |
| 1.2 | 7 Aug 2026 | **OpenRouter demoted from Phase 2 requirement to backlog/resilience item.** During Phase 2, confirmed DeepInfra's catalog now hosts Claude Sonnet 5 and other closed-lab models directly (verified 6 Aug 2026), closing the capability gap OpenRouter was originally meant to cover. OpenRouter's remaining value is vendor redundancy — a second, independent inference relationship — not capability. `librechat.yaml` keeps a scaffolded, commented-out OpenRouter block ready to activate; the Anthropic-direct endpoint is likewise no longer required for the Ceiling tier since DeepInfra covers it. Updated: §1.1, §1.2, §2, §3.3, §6.1, §6.2, §6.4, §14.3, §18. |

---

## 0. HOW TO USE THIS DOCUMENT

This document is the **single spine** for building a self-hosted backup AI system that replaces Claude Pro Desktop if/when needed.

**Rules of engagement:**

1. This file lives in Claude Project knowledge. Every build session starts by reading it.
2. Work **one Phase at a time**. Do not skip ahead. Each phase has an explicit **Exit Test** — if the exit test fails, do not proceed.
3. `BUILD_STATE.md` (see §16.3) is the live progress tracker. This document does not change; `BUILD_STATE.md` does.
4. Anything marked **[VERIFY]** is a fact from the July 2026 research that moves fast (versions, prices, config schema). Claude must web-search and confirm before executing that step.
5. Anything marked **[SENSITIVE]** touches clinical, legal, or client data. Different routing rules apply — see §14.4.
6. Anything marked **[IDENTITY]** touches household identity data — government identifiers, account numbers, policy numbers, scanned identity documents. Routing rules in §14.4 apply, plus the local-embeddings requirement (§6.3) and the Household Admin tool exclusion (§7.4).

**THE CREDENTIAL RULE — absolute, no exceptions, not a tag.**

Passwords, PINs, MFA seeds, recovery codes, security answers, and private keys **never enter this system in any form.** Not in a chat message, not in a RAG collection, not in memory, not in git, not in a skill, not "just this once to test it." The system may hold a *pointer* to where a credential lives ("NRMA login is in Bitwarden, item name X") but never the value.

This rule is not negotiable and does not have a change trigger. If a build step appears to require storing a credential, the step is wrong — stop and redesign it.

**Design constraint that overrides all others:** ADHD single-interface requirement. One window, one tab, one place to start. Every tool added beyond LibreChat must justify itself against this constraint. This is why the coding agents (Cline, OpenCode, Kilo) are supporting cast, not core.

---

## 1. SYSTEM OVERVIEW

### 1.1 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  WINDOWS 11 HOST                                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  WSL2 (Ubuntu) — native filesystem ~/  NOT /mnt/c       │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  DOCKER DESKTOP                                  │  │  │
│  │  │                                                  │  │  │
│  │  │  ┌────────────┐  ┌──────────┐  ┌──────────────┐  │  │  │
│  │  │  │ LibreChat  │  │ MongoDB  │  │ Meilisearch  │  │  │  │
│  │  │  │  :3080     │  │          │  │              │  │  │  │
│  │  │  └─────┬──────┘  └──────────┘  └──────────────┘  │  │  │
│  │  │        │                                         │  │  │
│  │  │  ┌─────┴──────┐  ┌──────────┐  ┌──────────────┐  │  │  │
│  │  │  │  RAG API   │  │ pgvector │  │ OpenMemory   │  │  │  │
│  │  │  │            │  │          │  │  MCP (Mem0)  │  │  │  │
│  │  │  └─────┬──────┘  └──────────┘  └──────────────┘  │  │  │
│  │  │        │                                         │  │  │
│  │  │  ┌─────┴────────────┐                            │  │  │
│  │  │  │ LOCAL EMBEDDINGS │ ← never leaves the box     │  │  │
│  │  │  │  (mandatory)     │   [SENSITIVE] + [IDENTITY] │  │  │
│  │  │  └──────────────────┘                            │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  ~/ai-context/   ← GIT REPO = SINGLE SOURCE OF TRUTH   │  │
│  │     skills/  projects/  memory/  mcp/                  │  │
│  │     (NO household identity data — see §4.4)            │  │
│  │                                                        │  │
│  │  ~/household-vault/  ← [IDENTITY] NOT IN GIT           │  │
│  │     documents/  identifiers/  → RAG collection only    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐   ┌──────────────────────────────────┐     │
│  │ Goose (CLI + │   │ Cherry Studio (WARM SPARE ONLY)  │     │
│  │ desktop app) │   │ demoted after cutover            │     │
│  │ CAPABILITY   │   └──────────────────────────────────┘     │
│  │ CEILING      │                                            │
│  └──────────────┘                                            │
└──────────────────────────────────────────────────────────────┘
              │                          │
              ▼                          ▼
      ┌───────────────┐          ┌──────────────────┐
      │  DEEPINFRA    │          │   OPENROUTER     │
      │  (PRIMARY —   │          │  (BACKLOG v1.2 — │
      │  HIPAA / ISO  │          │  redundancy only,│
      │  covers full  │          │  scaffolded but  │
      │  model tier)  │          │  not wired)      │
      └───────────────┘          └──────────────────┘
              │
              ▼  [SENSITIVE] clinical/legal + [IDENTITY] household only
      ┌───────────────┐
      │ ANTHROPIC API │  (direct — optional, v1.2: DeepInfra's
      └───────────────┘   anthropic/claude-sonnet-5 already covers
                           the Ceiling tier compliantly)


      ╔══════════════════════════════════════════════════╗
      ║  PASSWORD MANAGER — DELIBERATELY OUTSIDE          ║
      ║  Tier 1 credentials live here and only here.      ║
      ║  The AI system stores pointers, never values.     ║
      ║  No MCP bridge that returns secrets into context. ║
      ╚══════════════════════════════════════════════════╝
```

### 1.2 Component roles

| Component | Role | Replaces (Claude Pro) |
|---|---|---|
| **LibreChat v0.8.7** | Daily driver. Chat + agents + MCP + web search + RAG + skills + memory in one tab | Claude Pro Desktop (the whole app) |
| **`ai-context/` git repo** | Single source of truth for skills, projects, memory, MCP config | Claude Projects + Skills |
| **DeepInfra** | Primary BYO inference backend | Anthropic subscription |
| **OpenRouter** | **(v1.2) Backlog — vendor redundancy only, not currently wired.** DeepInfra hosts Claude Sonnet 5 and covers the full model tier directly | — |
| **Anthropic API direct** | **(v1.2) Optional.** DeepInfra's `anthropic/claude-sonnet-5` already satisfies the Ceiling tier compliantly; keep as a documented fallback | — |
| **OpenMemory MCP** | Portable cross-tool long-term memory | Claude memories |
| **Goose (Block)** | Capability ceiling — unbounded autonomous sysadmin/coding loops | Claude Code |
| **Cherry Studio** | Warm spare, demoted | (current partial backup) |
| **Local embeddings model** | In-container embeddings so [SENSITIVE] and [IDENTITY] content is never sent to a third-party embeddings endpoint at index time | — (new in v1.1) |
| **Password manager (external)** | Holds every Tier-1 credential. **Outside this system by design.** The AI holds pointers to it, never values | — (new in v1.1) |

### 1.3 The six usage clusters this must serve

Clusters 1–5 come from the source research. **Cluster 6 was added in v1.1** and did not exist in `AI_Build.pdf` — it carries its own routing constraints and is the only cluster with a hard tool exclusion.

| # | Cluster | Primary tool | Secondary |
|---|---|---|---|
| 1 | Sysadmin/infra (Docker, WSL2, PowerShell, media stack) | **Goose** | LibreChat + desktop-commander MCP |
| 2 | Mental-health case-manager work automation **[SENSITIVE]** | **LibreChat** + M365 MCP + clinical SKILL.md set | Anthropic direct for highest-stakes |
| 3 | Broad agentic MCP tool use (Drive, M365, Spotify, browser, files) | **LibreChat** | — |
| 4 | Web research with citations (workplace law, domain research) | **LibreChat** native web search | Tavily/Brave MCP |
| 5 | Persistent context (skills, KBs, long-term memory) | **git-backed markdown** | OpenMemory MCP + skillSync + RAG |
| 6 | Household administration — family information database, form-filling, renewals, "where is the document / what is the number" **[IDENTITY]** | **LibreChat** `Household Admin` agent + scoped RAG collection | git-backed markdown for non-identity reference |

**Cluster 6 in one line:** answer *"what is the number, where is the document, when is it due, who do I call"* fast enough that household admin stops being a task you avoid — without ever holding a credential.

---

## 2. LOCKED DESIGN DECISIONS

These were settled by the research. Do not relitigate them mid-build.

| Decision | Rationale | Change trigger |
|---|---|---|
| LibreChat is the hub, not Open WebUI / LobeChat / Cherry Studio | Deepest MCP integration of the self-hosted UIs (per Metabase Cloud's July 2026 evaluation); ClickHouse-backed since 4 Nov 2025 so commercially de-risked; 33,900+ stars | Cherry Studio's CherryClaw agent matures into a robust unattended harness → re-test |
| Goose is the capability ceiling, not Crush | Apache-2.0 (Crush is FSL-1.1-MIT, not OSI-approved); 51.3k stars, 500+ contributors; Linux Foundation Agentic AI Foundation governance since 7 Apr 2026 | Goose governance/licence changes |
| DeepInfra primary; **OpenRouter demoted to backlog (v1.2)** | Lowest per-token on open models; HIPAA/SOC2/ISO 27001/GDPR + zero-retention; DeepInfra's catalog now includes Claude Sonnet 5 and other closed-lab models directly (confirmed 6 Aug 2026), closing the capability gap OpenRouter was meant to cover. Its remaining value is vendor redundancy — an independent inference relationship if DeepInfra has an outage, billing issue, or catalog regression — not capability | DeepInfra has a sustained outage, billing problem, or drops model coverage you rely on → re-wire the already-scaffolded OpenRouter block in `librechat.yaml` |
| Git-backed markdown is the source of truth, not any app's internal DB | Portability across LibreChat / Goose / Crush / future tools; human-readable; diffable | Never — this is the insurance policy |
| **Do NOT build on Roo Code** | Shut down 21 Apr 2026, repo archived 15 May 2026; team pivoted to Roomote (~$899/mo per parallel instance) | — |
| Two tools maximum (LibreChat + Goose) | ADHD single-interface constraint | LibreChat's Agent Chain/Subagents exit beta **and** MCP OAuth issues close → drop Goose |
| **Local embeddings are mandatory, not a fallback** (v1.1) | Indexing is not inference. Every [SENSITIVE] and [IDENTITY] document gets chunked and sent to whatever embeddings endpoint is configured — a third-party endpoint would see clinical notes and identity documents in plaintext at index time, regardless of how careful the chat-model routing is. Decided in Phase 2, not deferred | Never for [SENSITIVE]/[IDENTITY]. General-purpose collections may use a hosted endpoint if throughput demands it |
| **Credentials never enter the system** (v1.1) | pgvector is a search index, not a secret store: no per-document ACL, plaintext alongside the embedding, retrievable by any agent holding `file_search` on that collection. Mem0 auto-extraction compounds it | **None.** This is the one decision in this document with no change trigger |
| **Household Admin agent gets no browser and no shell** (v1.1) | An agent that can both read identity documents and fetch untrusted web content is the Operation Pale Fire exfiltration path (§11.4) with better loot | Never while the agent retains [IDENTITY] retrieval |

---

## 3. PRE-FLIGHT CHECKLIST

Complete **all** of these before Phase 0. Nothing downstream works without them.

### 3.1 Machine

- [ ] Windows 11, virtualisation enabled in BIOS
- [ ] WSL2 installed and set as default (`wsl --set-default-version 2`)
- [ ] Ubuntu distro installed under WSL2
- [ ] Docker Desktop installed, **WSL2 backend enabled**, integration switched on for the Ubuntu distro
- [ ] ≥ 16 GB RAM (LibreChat + Mongo + Meilisearch + pgvector + OpenMemory is not light)
- [ ] ≥ 40 GB free disk on the WSL2 virtual disk
- [ ] Git installed **inside WSL2** (not just Windows Git)

### 3.2 Critical WSL2 configuration

- [ ] `git config --global core.autocrlf false` — **set this BEFORE any cloning.** CRLF line endings break shell scripts inside Linux containers.
- [ ] All project files live in the **WSL2 native filesystem** (`~/`), **never** `/mnt/c/` or a Windows path. Cross-filesystem mounts cause the documented MongoDB volume-permission errors (LibreChat GitHub Discussion #2053) and are ~10x slower.

### 3.3 Accounts and keys

- [ ] DeepInfra account + API key
- [ ] OpenRouter account + API key — **(v1.2) demoted to optional/backlog.** DeepInfra's catalog covers the full model tier including Claude Sonnet 5; only pursue this if/when vendor redundancy against DeepInfra becomes a priority (§2, §18). **[VERIFY]** current BYOK terms if/when revisited — sources conflict: one reports 5.5% credit fee and "first 1M requests/month free, then 5%", another reports a $25,000/month list-price threshold.
- [ ] Anthropic API key — **(v1.2) optional.** DeepInfra's `anthropic/claude-sonnet-5` already covers the highest-stakes writing tier; get this key later if a direct Anthropic relationship becomes worth having
- [ ] Private GitHub repo created for `ai-context` (private — it will hold clinical/legal skills)
- [ ] Tavily or Brave Search API key (for research MCP, Cluster 4)
- [ ] Microsoft 365 account credentials ready for OAuth
- [ ] Google account ready for Drive OAuth
- [ ] Spotify developer app (if porting the Spotify connector)

**Cluster 6 prerequisites (v1.1)** — none of these are API keys; they are decisions to have made before Phase 6:

- [ ] **A password manager chosen and in use** for Tier-1 credentials. This is a hard dependency, not a nice-to-have: without somewhere legitimate for credentials to live, pressure builds to put them somewhere illegitimate
- [ ] The existing family-information project located and its current form identified (folder / Notion / Airtable / custom DB) — determines import vs rebuild
- [ ] **What "scrape" currently means** written down explicitly: reading email, parsing statements, or logging into portals. If it involves stored portal logins, that component collides with the credential rule and needs redesign before it is ported
- [ ] No new API key is required for local embeddings — the model runs in-container
- [ ] **Household data snapshot off unencrypted `D:` — DONE and VERIFIED (1 Aug 2026):** robocopy `D:\Data` → `C:\HouseholdDataRaw\Data`, 57,598 files / 28.3 GB, per-file verification passed (one live log file re-copied). **`D:\Data` is NOT deleted and must not be** — it is the live working directory of seven scheduled tasks discovered during verification: `ArchiveDailySync`, `DailyDashboard`, `FamilyBriefing`, `rclone Drive Sync`, `rclone VFS Cache Clean`, `Resource Watchdog`, `TorBox Mount`. Some are household-pipeline (sync, briefing, dashboard), some are media-stack (TorBox, rclone cache, watchdog). Scripts likely hardcode `D:\Data` internally, so repointing is a migration, not a task-property edit. **Decommission plan:** audit each task at the Session 10 legacy-pipeline audit (household-pipeline tasks) or as Cluster 1 work (media-stack tasks) → repoint or retire → only then delete `D:\Data`. Until then: the C: snapshot is the protected archive; new data written to D: remains on unencrypted storage — acceptable, bounded exposure

### 3.4 Exit test for Phase Pre-flight

```bash
wsl -l -v                    # Ubuntu shows VERSION 2
docker run hello-world       # succeeds from inside WSL2 shell
git config --global core.autocrlf   # returns "false"
pwd                          # inside WSL2, returns /home/<user>, not /mnt/c/...
```

---

## 4. PHASE 0 — SOURCE OF TRUTH REPO

**Goal:** the portable layer exists before any app does. If every app in this plan disappeared tomorrow, this repo is what survives.

### 4.1 Create the structure

```bash
cd ~
mkdir -p ai-context/{skills,projects,memory,mcp,docs}
cd ai-context
git init
```

### 4.2 Canonical layout

```
~/ai-context/
├── README.md                  # what this is, how each tool consumes it
├── BUILD_STATE.md             # live build progress tracker
├── skills/                    # portable SKILL.md capabilities
│   ├── clinical-writing/SKILL.md
│   ├── workplace-law-research/SKILL.md
│   ├── powershell-sysadmin/SKILL.md
│   ├── seddon-financial-forensics/SKILL.md      [SENSITIVE]
│   ├── seddon-family-law-drafter/SKILL.md       [SENSITIVE]
│   ├── household-admin/SKILL.md                 (method only — no data)
│   └── session-close/SKILL.md
├── projects/                  # per-project knowledge (the "Projects" equivalent)
│   ├── <project-name>/
│   │   ├── INSTRUCTIONS.md    # what would be Claude Project Instructions
│   │   └── knowledge/         # files fed to LibreChat RAG
│   └── household/                               [IDENTITY]
│       ├── INSTRUCTIONS.md    # IN GIT — agent behaviour, safe to commit
│       ├── SCHEMA.md          # IN GIT — what fields exist, NOT their values
│       └── (no knowledge/ dir — see ~/household-vault below)
├── memory/                    # human-readable long-term memory
│   ├── preferences.md         # tone, formatting, working style
│   ├── people.md
│   ├── systems.md             # home lab / media stack / infra facts
│   └── decisions.md           # decision log
├── mcp/
│   ├── mcp-servers.json       # CANONICAL server list — all clients reference this
│   └── README.md              # per-client wiring notes
└── docs/
    └── AI_Build_research.md   # the source research, converted to markdown
```

**And, deliberately outside the repo (v1.1):**

```
~/household-vault/             ← [IDENTITY] — NEVER a git repo, never a subfolder of ai-context
├── documents/                 # scans: passports, licences, certificates, policies
├── identifiers/               # Tier-2 reference: Medicare, TFN, policy/account numbers
└── renewals.md                # dates, who-to-call, what-to-bring
```

The physical separation is the point. `ai-context/` is a git repo that gets pushed to GitHub; `household-vault/` is not a repo and has no remote. A structural boundary survives a tired evening in a way that a `.gitignore` entry does not. Back it up per §14.1 — encrypted, separately, never to the same destination as the repo.

### 4.3 SKILL.md template (stick to the core spec)

The Agent Skills / SKILL.md standard is supported by 16+ tools (Claude Code, Cursor, Codex, Goose, OpenCode, GitHub Copilot, LibreChat). **Use only `name` + `description` frontmatter plus a markdown body. Avoid agent-specific frontmatter** — that is what breaks portability.

```markdown
---
name: clinical-writing
description: Use when drafting or reviewing clinical documentation, case notes, referrals, or professional correspondence in a mental health case-management context. Triggers on requests to write, review, or restructure client-facing or clinical documents.
---

# Clinical Writing

## When to use
...

## Standards
...

## Process
1. ...

## Output format
...
```

### 4.4 `.gitignore`

```
.env
*.key
secrets/
**/knowledge/raw/

# [IDENTITY] — belt and braces; the vault lives outside the repo entirely
household-vault/
projects/household/knowledge/
*.identifiers.md
```

**[SENSITIVE]** Clinical and legal skills go in the **private** repo. Never mirror this repo publicly. Never commit real client data — skills describe *method*, knowledge folders hold *data*, and data-bearing folders should be evaluated individually for whether they belong in git at all.

### 4.4a Secret scanning — install before the first commit (v1.1)

`.gitignore` prevents the mistakes you anticipated. A scanner catches the ones you didn't — a TFN pasted into a skill body while debugging, a policy number in an example, a `.env` copied to `.env.backup`.

Install `gitleaks` (or `git-secrets`) as a pre-commit hook in `ai-context/` during Phase 0, before the repo has any history worth protecting. Add a custom rule set for Australian identifiers — TFN, Medicare, passport patterns — since the stock rules target cloud API keys and will not catch these.

**Why this is not optional:** git history is effectively permanent, and a push to GitHub is irreversible. Rotating a leaked API key takes a minute. You cannot rotate a Medicare number.

**Exit condition:** commit a file containing a dummy TFN-shaped string and confirm the hook blocks it. An untested hook is not a control.

### 4.5 Exit test

- [ ] `git log` shows an initial commit
- [ ] Private GitHub remote added and pushed
- [ ] At least one real `SKILL.md` written and committed
- [ ] `mcp/mcp-servers.json` exists (can be a stub `{"mcpServers": {}}`)
- [ ] **(v1.1)** Secret-scanning pre-commit hook installed **and demonstrated to block** a dummy identifier
- [ ] **(v1.1)** `~/household-vault/` exists, is **not** a git repo (`git status` inside it fails), and is not inside `ai-context/`

---

## 5. PHASE 1 — DEPLOY LIBRECHAT

**Goal:** LibreChat running at `http://localhost:3080` with an admin account.

**[VERIFY]** Latest stable at time of research: **v0.8.7 (23 June 2026)**. Check current release before cloning.

### 5.1 Clone and configure

```bash
cd ~
git clone https://github.com/danny-avila/LibreChat.git
cd LibreChat
cp .env.example .env
```

### 5.2 Minimum `.env` edits

```bash
# Generate real values for these — do not ship defaults
CREDS_KEY=<32-byte hex>
CREDS_IV=<16-byte hex>
JWT_SECRET=<random>
JWT_REFRESH_SECRET=<random>

# Registration — leave open long enough to create your admin account, then close
ALLOW_REGISTRATION=true

# Provider keys (Phase 2 wires them properly; put them here now)
DEEPINFRA_API_KEY=<key>
OPENROUTER_KEY=<key>
ANTHROPIC_API_KEY=<key>
```

**[VERIFY]** LibreChat ships a credentials generator in its docs — use it rather than hand-rolling `CREDS_KEY`/`CREDS_IV`, since lengths are strict.

### 5.3 Override file — do this now, not later

Create `docker-compose.override.yml`. **All customisations go here** so `git pull` on LibreChat never clobbers them.

```yaml
services:
  api:
    volumes:
      - ./librechat.yaml:/app/librechat.yaml
      - /home/<user>/ai-context/skills:/app/skills:ro
    environment:
      - DEPLOYMENT_SKILLS_DIR=/app/skills
```

### 5.4 Start

```bash
docker compose up -d
docker compose logs -f api
```

Visit `http://localhost:3080`. **Register the first account — it becomes admin. There are no default credentials.** Then set `ALLOW_REGISTRATION=false` and restart.

### 5.5 Exit test

- [ ] `http://localhost:3080` loads
- [ ] Admin account created and can log in
- [ ] `docker compose ps` shows api, mongodb, meilisearch, rag_api, vectordb all healthy
- [ ] Registration closed
- [ ] A restart (`docker compose down && docker compose up -d`) preserves the account

---

## 6. PHASE 2 — WIRE PROVIDERS

**Goal:** tiered model access through DeepInfra. **(v1.2)** OpenRouter is scaffolded but not wired (backlog item, see §2); Anthropic direct is optional since DeepInfra covers the Ceiling tier.

### 6.1 Model tiering strategy

| Tier | Use for | Models **[VERIFY exact DeepInfra model IDs]** |
|---|---|---|
| **Ceiling** | Highest-stakes clinical/legal writing **[SENSITIVE]** | **(v1.2)** Claude Sonnet 5 via **DeepInfra** (`anthropic/claude-sonnet-5`) — confirmed 6 Aug 2026 to satisfy this tier without a separate Anthropic key, and still compliant per §14.4 since DeepInfra direct is an allowed Tier-2/[SENSITIVE] route. Anthropic direct remains available as an optional alternative |
| **High** | Complex reasoning, research synthesis, hard debugging | GLM-5.2 (intelligence index 51, Artificial Analysis), DeepSeek V4 Pro |
| **Work** | Daily drafting, summarisation, agent loops | DeepSeek V4 Flash, MiniMax-M3, Qwen3.5 family |
| **Code** | Coding and sysadmin agent work | Kimi K2.7-Code, Kimi K2.6 |
| **Cheap** | Classification, extraction, bulk | gpt-oss-120B, small Qwen3.5 |

Reference price point from the research: DeepSeek V4 Pro at **$1.30/M input direct** vs $1.74–$2.10 elsewhere; cached input as low as **$0.10/M**. **[VERIFY]** — prices move.

### 6.2 `librechat.yaml` custom endpoints

Create `librechat.yaml` in the LibreChat root. **[VERIFY]** the exact schema against current LibreChat config docs before applying — this is a starting template, not gospel.

```yaml
version: 1.2.8

endpoints:
  custom:
    - name: "DeepInfra"
      apiKey: "${DEEPINFRA_API_KEY}"
      baseURL: "https://api.deepinfra.com/v1/openai"
      models:
        default: []          # populate with verified model IDs
        fetch: true          # let LibreChat pull the live model list
      titleConvo: true
      titleModel: "current_model"
      modelDisplayLabel: "DeepInfra"

    # --- OpenRouter: backlog (v1.2), not currently wired ---
    # Demoted from a Phase 2 requirement to a resilience item — DeepInfra's
    # catalog (confirmed 6 Aug 2026) already covers the full model tier,
    # including Claude Sonnet 5. Activate only if vendor redundancy against
    # DeepInfra becomes a priority (see §2, §18).
    # - name: "OpenRouter"
    #   apiKey: "${OPENROUTER_KEY}"
    #   baseURL: "https://openrouter.ai/api/v1"
    #   models:
    #     default: []
    #     fetch: true
    #   titleConvo: true
    #   modelDisplayLabel: "OpenRouter"
```

Anthropic is a **native** endpoint in LibreChat — enable it via `ANTHROPIC_API_KEY` in `.env` rather than as a custom endpoint. **(v1.2) Optional** — DeepInfra's `anthropic/claude-sonnet-5` already covers the Ceiling tier without this.

### 6.3 RAG embeddings — **local, mandatory** (revised in v1.1)

The RAG API needs an embeddings provider configured separately from chat models. **In v1.0 this section treated local embeddings as a fallback. As of v1.1 they are the decision, made here in Phase 2 rather than deferred to Phase 6.**

**The reasoning:** indexing is not inference. Careful chat-model routing (§14.4) governs what the *conversation* sees. It does not govern indexing. When a document enters a RAG collection it is chunked and every chunk is sent to the configured embeddings endpoint — so a hosted embeddings provider would receive clinical case notes and scanned identity documents in plaintext at index time, no matter how disciplined the chat routing is. With Cluster 6 in scope, that is the whole family's identity documents.

**[VERIFY]** before executing:
- Which embeddings providers the current `rag_api` supports, and the exact env var names
- That a local HuggingFace sentence-transformers model can be configured with no outbound calls at index time
- **Confirm empirically, do not assume:** index a test document, watch container network activity, and verify nothing leaves the box

**Sizing note.** A local embeddings model adds roughly 1–2 GB resident to the stack. This is comfortable within the 8 GB `.wslconfig` allocation for normal use. Bulk-indexing the household vault is the heaviest single memory event in the build — do that after the RAM upgrade, and raise `.wslconfig` for the duration if needed.

**Collection separation is part of the config, not a Phase 6 detail.** Three distinct RAG collections from the outset:

| Collection | Contents | Attached to |
|---|---|---|
| `general` | Technical docs, research, non-sensitive reference | Research, General agents |
| `clinical` **[SENSITIVE]** | Case-management material | Clinical Work agent only |
| `household` **[IDENTITY]** | Vault documents and identifiers | Household Admin agent only |

There is no per-document access control *inside* a collection. Separation between collections is therefore the only real boundary — get it right at creation, because merging is easy and unmerging is not.

### 6.4 Exit test

- [ ] DeepInfra models appear in the model picker and a chat completes
- [ ] **(v1.2)** OpenRouter — demoted to backlog, **not a Phase 2 exit criterion**. Scaffolded in `librechat.yaml`, reactivate per §2/§18 if needed later
- [ ] Anthropic (Claude Sonnet 5) appears and a chat completes — **(v1.2)** satisfied via DeepInfra's `anthropic/claude-sonnet-5`; no separate Anthropic key required for Phase 2
- [ ] Model switching mid-conversation works
- [ ] **(v1.2)** Cost sanity check scoped to DeepInfra only, since it is the sole active provider
- [ ] **(v1.1)** Local embeddings model loads and indexes a test document
- [ ] **(v1.1)** Indexing produces **no outbound network traffic** — verified by observation, not assumed
- [ ] **(v1.1)** Three separate RAG collections exist: `general`, `clinical`, `household` — **(v1.2) deferred to Phase 3/6**, since collection separation requires per-agent knowledge scoping (`file_search`) that doesn't exist until agents are built

---

## 7. PHASE 3 — AGENTS + MCP

**Goal:** autonomous agents with scoped tools. This is Clusters 2, 3 and 4.

### 7.1 Enable agent capabilities

LibreChat's default agent capability list is:
`["deferred_tools", "execute_code", "file_search", "web_search", "artifacts", "subagents", "actions", ...]`

**Treat `subagents` and Agent Chain as experimental.** Both are beta. Programmatic Tool Calling requires a self-hosted Code Interpreter with a Tool Call Server component — do not attempt it in the initial build.

### 7.2 Raise the recursion limit — critical

The agent loop is **bounded at a documented default of 25 steps**. A "step" is defined in the docs as either an AI API request or a round of tool usage, where one round of tool usage is usually 3 steps (API Request → Tool Usage → Follow-up API Request). **So 25 steps ≈ 8 tool calls.** When the limit is hit it raises `GraphRecursionError` (LangGraph-based) rather than continuing.

Set both:
- `recursionLimit` — the working value
- `maxRecursionLimit` — the ceiling that caps what the UI is allowed to set

Suggested starting values: `recursionLimit: 75`, `maxRecursionLimit: 150`. Tune upward if tasks stop early; if a task *still* dies on `GraphRecursionError`, that is the documented trigger to move the task to Goose (Phase 6).

### 7.3 Core MCP servers to install

Configure in `librechat.yaml` under `mcpServers`, **or** use the newer UI-based MCP flows that avoid config-file edits and restarts. Keep `~/ai-context/mcp/mcp-servers.json` as the canonical list regardless — MCP configs are portable and belong in version control.

| Server | Cluster | Notes |
|---|---|---|
| **Playwright MCP** (Microsoft, official) | 3, 4 | Browser automation on Windows (PowerShell + WSL). Its filesystem-backed output mode is ~4x more token-efficient when the agent has filesystem access — enable it. |
| **Filesystem / desktop-commander MCP** | 1, 3 | Desktop file access. Scope it to a working directory. |
| **Microsoft 365 MCP** | 2, 3 | OAuth — see the warning below |
| **Google Drive MCP** | 3 | OAuth — see the warning below |
| **Spotify MCP** | 3 | Low stakes, good first OAuth test |
| **Tavily or Brave Search MCP** | 4 | Deeper research beyond native web search |
| **OpenMemory MCP** | 5 | Added in Phase 5. **Not** attached to Household Admin (§9.1) |

**Cluster 6 needs no new MCP server (v1.1)** — it is a RAG collection plus a scoped agent, nothing more. This is deliberate. Every MCP server added to the Household Admin agent is a potential outbound channel, and the cluster's requirements are met entirely by `file_search` against a local collection.

### 7.4 Two hard constraints

**⚠ The 128-tool ceiling.** Metabase Cloud's July 2026 writeup documents blowing past the model's tool-array limit when adding the Linear MCP, forcing them to selectively disable tools. **Do not run "every tool, all the time."** Instead:
- Create **purpose-built agents per cluster**, each with a scoped tool subset
- Use **Deferred Tools** so tools load on demand rather than all being present in every request

Suggested agents:
| Agent | Tools | Explicitly denied |
|---|---|---|
| `Clinical Work` **[SENSITIVE]** | M365, file_search (`clinical` collection), memory, clinical SKILL.md set | Browser, shell |
| `Research` | web_search, Tavily/Brave, Playwright, artifacts | file_search on `clinical` or `household` |
| `Desktop Ops` | filesystem/desktop-commander, execute_code | file_search on `clinical` or `household` |
| `Household Admin` **[IDENTITY]** (v1.1) | file_search (`household` collection **only**), artifacts, `household-admin` skill | **Browser, web_search, Playwright, shell, execute_code, memory, OpenMemory** |
| `General` | small default set | file_search on `clinical` or `household` |

**⚠ The Household Admin exclusion list is load-bearing, not conservative defaults.**

The forbidden combination is *retrieval of identity data* + *any channel that reaches an attacker*. An agent that can read your passport scan and also fetch a web page can be instructed by that page's content to summarise what it just retrieved into a URL. This is exactly the Operation Pale Fire class of attack described in §11.4, with better loot than a dev environment.

Note that `Research` and `Household Admin` are deliberately *disjoint* — this is the one place where the two-tools-maximum principle (§2) yields to a security boundary. If a task genuinely needs both ("find the renewal cost online and compare to my policy"), do it as two turns in two agents, moving the answer by hand. The friction is the control.

Web search and browser tools are also denied on `Clinical Work` for the same reason; v1.0 already had this right and v1.1 makes the rationale explicit.

**⚠ MCP OAuth in shared agent mode.** Open GitHub issues (#9213, #13428, #13401) confirm MCP OAuth in agent mode was still being hardened through mid-2026 — a shared agent's OAuth-based MCP tools could fail to authenticate for users other than the creator, because each request needs to carry the user's own identity and permissions, not the admin's. **Test every OAuth-based MCP (M365, Google) individually before relying on it for high-stakes work.**

### 7.5 Native web search

Enable LibreChat's native web search with inline citations, backed by a reasoning-tier model. This is Cluster 4 and it works fully in-window — no second tool needed.

### 7.6 Exit test

- [ ] An agent completes a 10+ tool-call task without `GraphRecursionError`
- [ ] Each OAuth MCP (M365, Google, Spotify) authenticates and returns real data
- [ ] Playwright MCP navigates a page and extracts content
- [ ] Filesystem MCP reads/writes only inside its scoped directory
- [ ] Web search returns answers with working inline citations
- [ ] Total tool count per agent is well under 128
- [ ] **(v1.1)** `Household Admin` agent has **no** browser, web search, shell, or memory tool present in its tool list — confirmed by inspection, not intent
- [ ] **(v1.1)** Ask `Household Admin` to fetch a URL. It should be unable to. A refusal is not a pass — the tool must be absent
- [ ] **(v1.1)** `Research` and `General` agents cannot retrieve from the `household` or `clinical` collections

---

## 8. PHASE 4 — SKILLS SYNC

**Goal:** `~/ai-context/skills/` loads automatically into LibreChat. This is the Claude Skills equivalent.

### 8.1 Two loading mechanisms

| Mechanism | How | Use for |
|---|---|---|
| **skillSync** | `skillSync.github` in `librechat.yaml`, pointed at the private repo's `skills/` path | Live-syncing skills you actively edit |
| **`DEPLOYMENT_SKILLS_DIR`** | Env var pointing at a bundled read-only directory (already mounted in §5.3) | Stable skills you don't want editable from the UI |

Start with the volume-mount + `DEPLOYMENT_SKILLS_DIR` approach from §5.3 (simpler, no GitHub token needed for a private repo), then add `skillSync.github` once the repo layout is stable.

### 8.2 Invocation modes

Skills in LibreChat (v0.8.6+) can be:
- invoked **manually** with `/s`
- **auto-discovered** via the skill catalog
- **always-applied**

Map these to your Claude Project skills: the ones that should fire automatically (like a session-close routine) become always-applied or auto-discovered; specialist ones stay manual.

In v0.8.7, agents with skills can author new skills on the fly — useful, but review anything auto-authored before committing it to the repo.

### 8.3 Skills to port from current Claude usage

| Current Claude skill | Port priority | Notes |
|---|---|---|
| `seddon-financial-forensics` **[SENSITIVE]** | High | Method only in git; the CSV data stays out of the repo and goes into a scoped RAG collection |
| `seddon-family-law-drafter` **[SENSITIVE]** | High | Court formatting requirements are pure method — highly portable |
| `robot-session-close` | High | Rename to a generic `session-close`; the handover-doc pattern is the backbone of multi-session work |
| Clinical writing / professional writing | High | Cluster 2 |
| `household-admin` **(new, v1.1)** | High | Cluster 6. Write fresh — no Claude original. Encodes the three-tier model (§10.4), the credential rule, form-filling method, and the "state the source document for every figure" requirement. **Method only — never a value** |
| Workplace law research | Medium | Cluster 4 |
| PowerShell / sysadmin | Medium | Cluster 1 — also loaded by Goose |
| Document skills (docx/pptx/xlsx/pdf) | Medium | LibreChat's Code Interpreter can run the same libraries; the skill bodies port directly |

### 8.4 Exit test

- [ ] A skill in `~/ai-context/skills/` appears in the LibreChat skill catalog without a restart (or after one documented restart)
- [ ] `/s` manual invocation works
- [ ] An always-applied skill demonstrably changes output
- [ ] Editing the markdown file in the repo changes behaviour in LibreChat

---

## 9. PHASE 5 — PORTABLE MEMORY

**Goal:** long-term memory that is not locked inside one app. This is the Claude memories equivalent.

### 9.1 Two layers — run both

**Layer A: LibreChat native per-user Memory.** Configure the `memory` block in `librechat.yaml` with:
- `validKeys` — constrain what can be stored (prevents memory sprawl)
- `personalize` — user-toggleable
- `messageWindowSize` — how much conversation is considered for extraction

Note the known limitation: LibreChat memory is **per person, not global**. For a single-user deployment this is fine.

**⚠ Memory is an exfiltration surface for Cluster 6 (v1.1).**

Both native memory and Mem0 *automatically extract* what looks salient from conversation. Mention a Medicare number once while filling a form and it may be silently persisted, then resurface weeks later in an unrelated chat — possibly one held by an agent that *does* have browser access. The user never sees the write happen.

Mandatory controls:
- **Memory and OpenMemory are disabled on the `Household Admin` agent.** No exceptions. Cluster 6's value is retrieval from a curated vault, which needs no memory layer at all
- Use `validKeys` as an allow-list, not a block-list — constrain native memory to `preferences`, `tone`, `systems`, `people` and nothing else. Anything not enumerated cannot be stored
- Set `messageWindowSize` conservatively; a large extraction window increases the odds of catching an identifier in passing
- **Audit it in Phase 8:** dump the memory store and read it. Not "check the config" — read what is actually in there

**Layer B: OpenMemory MCP** — local-first, Mem0-powered, runs via one `docker-compose`. Exposes `add_memories` and `search_memory` over MCP to **any** MCP-compatible client. This is the layer that makes memory portable to Goose and anything that comes next.

**Layer C (optional but recommended): plain-markdown memory.** `~/ai-context/memory/*.md` — human-readable, git-diffable, and the ultimate fallback. A markdown/Obsidian-vault memory MCP can surface it. If OpenMemory ever breaks, this still works.

### 9.2 Seed the memory from current Claude usage

Export and write into `~/ai-context/memory/`:
- **`preferences.md`** — the context-management protocol currently in Claude user preferences (input truncation, modular task execution, token-aware responses, no repetition), writing tone, formatting defaults
- **`systems.md`** — home lab facts, media stack, Docker/WSL setup, hostnames, quirks
- **`people.md`**, **`decisions.md`** — as needed

### 9.3 Exit test

- [ ] OpenMemory container running via `docker-compose`
- [ ] LibreChat connected to OpenMemory over MCP
- [ ] `add_memories` writes and `search_memory` retrieves across two separate conversations
- [ ] Native LibreChat memory also stores a preference and applies it in a new chat
- [ ] `~/ai-context/memory/preferences.md` committed
- [ ] **(v1.1)** `validKeys` configured as an allow-list and a write outside it is rejected
- [ ] **(v1.1)** `Household Admin` has no memory tool present
- [ ] **(v1.1)** Memory store dumped and read end to end — contains no identifiers

---

## 10. PHASE 6 — PROJECTS / RAG KNOWLEDGE BASES

**Goal:** the Claude Projects equivalent.

**Formula:** LibreChat RAG file collections **+** a git-backed `projects/` folder of markdown **=** Projects.

### 10.1 Per-project pattern

```
~/ai-context/projects/<project>/
├── INSTRUCTIONS.md     # becomes the agent's system prompt / always-applied skill
└── knowledge/          # uploaded into a LibreChat RAG file collection
```

For each project:
1. Write `INSTRUCTIONS.md` (port the text from the corresponding Claude Project Instructions)
2. Create a dedicated LibreChat **agent** for that project, with the scoped tool set
3. Upload `knowledge/` into a **file collection** attached to that agent
4. Attach the relevant skills

### 10.2 Projects to migrate

Inventory every current Claude Project. For each, capture: Project Instructions text, knowledge files, attached skills, typical model tier, and whether it is **[SENSITIVE]** or **[IDENTITY]**.

### 10.3 Exit test

- [ ] One project fully reconstructed (instructions + knowledge + skills + agent)
- [ ] RAG retrieval returns correct passages with citations from the knowledge files
- [ ] The reconstructed project produces output of comparable quality to the Claude original on a known task

---

### 10.4 **[IDENTITY]** The household database — Cluster 6 (new in v1.1)

The family information database is the largest single project in Phase 6 and the only one with its own security model. Build it **last** in this phase, after the pattern is proven on a low-stakes project. Do not learn the RAG workflow on your family's passports.

#### 10.4.1 The three tiers

Every item goes in exactly one tier. Classify *before* ingesting — this is the whole design.

| Tier | What | Examples | Where it lives |
|---|---|---|---|
| **1 — Secrets** | Anything that grants access | Passwords, PINs, MFA seeds, recovery codes, security answers, private keys | **Password manager only.** The system holds a pointer: *"NRMA login → Bitwarden, item 'NRMA'"*. Never the value |
| **2 — Identifiers** **[IDENTITY]** | Numbers that identify but do not authenticate | Medicare, TFN, passport, licence, policy, account, membership, NDIS, CRN | `~/household-vault/identifiers/` → `household` RAG collection. Local embeddings. Household Admin agent only |
| **3 — Documents & reference** | Everything else | Scans, certificates, form templates, renewal dates, who-to-call, warranty info, appliance models | Same vault and collection. Lower stakes but same routing — not worth a second pipeline |

**Tier 2 is where the value is.** It is what makes form-filling fast, and it is the tier that needs the care. Tier 3 needs nothing this plan doesn't already do for any project.

**The boundary between 1 and 2 is "does it authenticate?"** A Medicare number identifies you; it does not log in as you. A password logs in as you. When something sits ambiguously between the two — a credit card number, a security question answer — **treat it as Tier 1**. The cost of over-classifying is mild inconvenience. The cost of under-classifying is not recoverable.

#### 10.4.2 Build order

**Source (confirmed, updated 1 Aug 2026):** live system at `D:\Data`; a **verified point-in-time snapshot** (57,598 files / 28.3 GB, per-file byte check passed) sits at **`C:\HouseholdDataRaw\Data`** on encrypted C:. `D:\Data` remains the working directory of seven live scheduled tasks (see §3.3) and is **not deleted** until each task is repointed or retired. Session 10 works from a **fresh re-sync** of the snapshot taken at session start (one robocopy re-run), so quarantine and classification operate on current data, then the legacy tasks are audited and `D:\Data` is decommissioned.

**What the tree actually contains (observed during the copy — this is not the "messy folder of exports" H1 described):**

- Google Drive / Gmail (full `.eml` message exports) / Calendar / Keep / Amplenote dumps for both Michael and Sarah
- **A predecessor automation pipeline:** sync + OCR batch scripts, an existing `.lancedb` embeddings store, `profile.db`, a "gateway" component with a `.gateway_token` file, scheduled-task registration scripts, and utilities including `read_password_emails.py` and `find_pdf_passwords.py`
- **Known cleartext Tier-1 material at specific paths**, including: `Michael\Drive\Chrome Passwords.csv` and `.xlsx`, `goddarnhooplehead Drive Dump\Passwords.docx`, Keep notes titled "Recovery Codes", "Last.fm Login", "CogLab Login", "Ahpra login", and `archive\gateway_old\.gateway_token`
- [SENSITIVE] family-law and clinical material mixed through the same tree

**Consequences:**
- **Dump-and-index is dead as a first step.** Indexing anything before Tier-1 quarantine would embed live credentials into pgvector. Step 0 below is now mandatory and blocking
- **The old pipeline gets audited, not ported.** H2's "retrieval only" answer predates seeing the tree; components like the gateway and password-email readers must each be classified (port / redesign / retire) against §10.4.4 before anything is reused
- **The old `.lancedb` store and `profile.db` are themselves data-bearing artifacts** — an embeddings store is not anonymised (§14.1). They are decommissioned and securely deleted at Session 10, not carried forward

0. **Tier-1 quarantine (new, blocking).** Before any classification pass: move the known credential files listed above into the password manager, then delete them from staging — including any duplicates elsewhere in the tree (search by filename and by content pattern). Grep the tree for credential patterns to catch the ones not yet known. **Nothing is indexed while this step is incomplete**
1. **Classify before ingesting.** Walk the staging tree item by item and assign a tier. Expect further Tier-1 material beyond the known list — that is why step 0 is a quarantine, not a completion
2. **Extract remaining Tier 1 to the password manager.** Replace each with a pointer in the vault. This must be complete before anything is indexed
3. **Populate `~/household-vault/`** — documents, identifiers, renewals
4. **Write `projects/household/SCHEMA.md`** in git: what fields exist, not their values. *"Each vehicle has: rego, expiry, insurer, policy number, roadside membership."* This is portable, safe to commit, and is what makes the agent useful — it can tell you what it should know even when it can't find it
5. **Create the `household` RAG collection** with local embeddings; index the vault
6. **Create the `Household Admin` agent** per §7.4 — the exclusion list is the build step, not an afterthought
7. **Write `skills/household-admin/SKILL.md`** — method only, no values

#### 10.4.3 Behaviour rules for the agent

Put these in `INSTRUCTIONS.md`, and set them before first use:

- **Always cite the source document** for every identifier returned. An unattributed number is unverifiable, and RAG will occasionally return a superseded document with total confidence
- **Flag staleness.** Documents expire. If a retrieved document has a date, surface it and its expiry alongside the answer
- **Never output a Tier-1 value even if one is found.** If a credential has leaked into the vault, the agent should say so and refuse — that is a defect report, and the vault needs cleaning
- **Say "not found" rather than infer.** A confabulated policy number is worse than no answer, because it looks like an answer
- **Confirm before writing.** The agent reads the vault. Any change to a stored value is done by hand

#### 10.4.4 The "scrape" question — resolve before building

The existing project reportedly scrapes information. Before porting, establish which of these it means:

| If it does this | Then |
|---|---|
| Reads email / parses statements from files you already hold | Straightforward. Port it. Runs as a separate scheduled job that writes to the vault; **it is not a tool on the Household Admin agent** |
| Logs into portals with stored credentials | **Collides with the credential rule.** Do not port as-is. The stored logins move to the password manager and the automation is redesigned, or the component is retired |
| Something else | Write it down and design against the actual behaviour |

**Keep ingestion and retrieval as separate systems.** A scheduled job writes to the vault; the agent reads from it. Combining them would give the retrieval agent network access and undo §7.4.

#### 10.4.5 Exit test — Cluster 6

- [ ] Every item classified into a tier before any indexing occurred
- [ ] Zero Tier-1 values in `~/household-vault/` — verified by grep against known credential patterns
- [ ] `SCHEMA.md` committed to git; **no identifier values in it**
- [ ] `household` collection built with local embeddings, no outbound traffic at index time
- [ ] `Household Admin` retrieves a real identifier and **cites the source document**
- [ ] The agent correctly says "not found" for something genuinely absent instead of inventing it
- [ ] The agent surfaces an expiry date on a document that has one
- [ ] **Real-task test:** complete an actual outstanding household form end to end, timed. If it is not meaningfully faster than doing it by hand, the vault structure is wrong — not the model
- [ ] `git log -p` reviewed for the household path: no identifier has ever been committed

---

## 11. PHASE 7 — GOOSE (CAPABILITY CEILING)

**Goal:** unbounded autonomous loops for Cluster 1. Add this **only after** LibreChat is working — it is a deliberate second window and must be justified.

### 11.1 Install

Goose (Block) runs natively on Windows as a desktop app + CLI. Apache-2.0. Governed by the Linux Foundation's Agentic AI Foundation (repo moved to the org 7 April 2026). Supports 30+ providers and 70+ MCP extensions.

### 11.2 Configure

- Point it at the **same DeepInfra key**
- Point it at the **same `~/ai-context/skills/` folder** (Goose supports the SKILL.md standard)
- Load the **same `~/ai-context/mcp/mcp-servers.json`** server list

The whole point is that Goose and LibreChat share one brain — same skills, same memory, same tools, different execution harness.

### 11.3 Trigger rule — when to use Goose instead of LibreChat

Use Goose when **any** of these is true:
- A LibreChat agent task repeatedly stops on `GraphRecursionError` even after raising `recursionLimit`
- The task requires a long, self-correcting shell loop against Docker/WSL/PowerShell
- The task needs to install packages, edit files, run tests, and read results iteratively

Otherwise stay in LibreChat. Every unnecessary trip to a second window costs more than the capability gains.

### 11.4 ⚠ SECURITY — read before enabling autonomy

**Never enable fully-automatic no-confirmation mode outside a scoped working directory.** Block's own "Operation Pale Fire" red-team exercise (January 2026) compromised Goose via a poisoned recipe with malicious instructions hidden in invisible Unicode characters.

Mandatory controls:
- Scope Goose to a specific working directory
- Keep confirmation prompts on for anything outside it
- Never load third-party recipes/extensions without reading the raw source
- Same rule applies to Cherry Studio's no-confirmation mode

### 11.5 Exit test

- [ ] Goose completes a multi-step Docker/WSL task that LibreChat could not
- [ ] Goose loads the same SKILL.md files
- [ ] Goose reads/writes OpenMemory
- [ ] Confirmation prompts fire outside the scoped directory

---

## 12. PHASE 8 — VALIDATION

**Goal:** prove the system replaces Claude Pro before you depend on it. Do not skip this.

Run a **real task from each cluster** — not a toy prompt — and score against what Claude Pro would have produced.

| # | Cluster | Validation task | Pass criteria |
|---|---|---|---|
| 1 | Sysadmin/infra | Diagnose and fix a real Docker/WSL issue end-to-end | Completes autonomously in Goose; LibreChat handles a lighter version |
| 2 | Clinical work **[SENSITIVE]** | Draft a real professional document to standard | Accuracy and tone acceptable; correct model tier; correct routing |
| 3 | Agentic MCP | Multi-tool task spanning Drive + M365 + browser | All OAuth holds; no tool-limit errors |
| 4 | Research | A real workplace-law research question | Citations present, accurate, and clickable |
| 5 | Persistent context | Start a fresh chat and confirm skills/memory/project context all apply | Context applies without re-explaining |
| 6 | Household admin **[IDENTITY]** (v1.1) | Complete a real outstanding household form or renewal end to end, timed against doing it by hand | Faster than manual; every figure cited to a source document; no confabulated numbers; agent still has no browser |

**Additional Phase 8 security audit (v1.1)** — these are not cluster tests, they are checks on the controls themselves. Run them at the end, and treat any failure as a cutover blocker:

- [ ] Dump the memory store and read it end to end. No identifiers present
- [ ] `git log -p` across the whole repo history, grepped for credential and identifier patterns. Nothing found
- [ ] Inspect the live tool list of every agent. `Household Admin` has no browser, shell, or memory
- [ ] Confirm `~/household-vault/` is not a git repo and has no remote
- [ ] Confirm LibreChat is still bound to localhost only

**Scoring:** for each, record PASS / PARTIAL / FAIL in `BUILD_STATE.md` with a note. Any FAIL blocks cutover for that cluster — keep using Claude Pro for it until fixed.

---

## 13. PHASE 9 — CUTOVER

1. Run both systems in parallel for **at least two weeks**. No cutover on faith.
2. Log every time you reach for Claude Pro instead of LibreChat, and why. That log is the remaining gap list.
3. Close the gaps.
4. **Demote Cherry Studio** to warm spare — leave it installed and configured, stop using it daily.
5. Only then consider downgrading the Claude subscription.

**Do not delete anything.** The value of this build is that it is a *backup*. Keeping Claude Pro alongside it is not a failure state.

---

## 14. OPERATIONS

### 14.1 Backup

- `~/ai-context/` → private GitHub (push after every session)
- LibreChat Mongo volume → scheduled `docker exec` dump to a Windows-side folder that is itself backed up
- `.env`, `librechat.yaml`, `docker-compose.override.yml` → encrypted backup, **never** in git
- **(v1.1)** `~/household-vault/` **[IDENTITY]** → encrypted backup to a destination **separate from the repo remote**. Never GitHub, never an unencrypted cloud sync folder. A local encrypted archive plus one offsite encrypted copy
- **(v1.1)** The pgvector volume now contains embedded identity content. Treat its backup at the same classification as the vault itself — an embeddings store is not anonymised

**Test the restore, twice a year.** An untested backup of irreplaceable documents is a story you tell yourself. This matters more for Cluster 6 than anywhere else in the build: LibreChat can be rebuilt from this plan in an afternoon; your family's document archive cannot be rebuilt at all.

### 14.2 Updates

```bash
cd ~/LibreChat
git pull
docker compose down
docker compose pull
docker compose up -d
```
Customisations live in `docker-compose.override.yml` and `librechat.yaml`, so pulls are safe. **Read release notes first** — this stack moves fast.

### 14.3 Cost monitoring

- Weekly check on DeepInfra spend; watch cached-input hit rate
- **(v1.2)** OpenRouter is not currently wired (backlog item, §2) — no spend expected. If reactivated, confirm it's only hit for failover/redundancy, not silently absorbing daily traffic
- Anthropic direct should be a small, deliberate line item

### 14.4 **[SENSITIVE] Data routing rules — non-negotiable**

| Data type | Allowed | Forbidden |
|---|---|---|
| **Credentials — Tier 1** (v1.1)<br>Passwords, PINs, MFA seeds, recovery codes, security answers, private keys | **Nothing. No model, no endpoint, no collection, no memory store, no git repo.** Password manager only | **Everything.** Including DeepInfra direct, including Anthropic direct, including local models. This row has no allowed column by design |
| **Household identifiers — Tier 2** **[IDENTITY]** (v1.1)<br>Medicare, TFN, passport, licence, policy and account numbers | DeepInfra direct **or** Anthropic direct, **and** local embeddings at index time, **and** Household Admin agent only | **Never** OpenRouter. **Never** a hosted embeddings endpoint. **Never** an agent holding browser, web search, shell, or memory tools |
| **Household documents — Tier 3** (v1.1) | Same as Tier 2 | Same as Tier 2 |
| Mental-health case-management content | DeepInfra direct (HIPAA/SOC 2/ISO 27001/GDPR, zero-retention) **or** Anthropic direct, **and** local embeddings at index time | **Never** OpenRouter. **Never** any logging-enabled or routed path. **Never** a hosted embeddings endpoint |
| Family law matter content | Same as above | Same as above |
| General/technical | Anything | — |

Enforce this structurally, not by memory: give the Clinical Work and Household Admin agents access **only** to the DeepInfra and Anthropic endpoints.

**Three enforcement points, not one (v1.1).** v1.0 enforced routing at the chat endpoint. That is necessary but no longer sufficient:

1. **Endpoint restriction** — which providers the agent may call
2. **Embeddings locality** — what the *indexer* sees, which endpoint restriction does not govern (§6.3)
3. **Tool exclusion** — what channels exist for data to leave once retrieved (§7.4)

A gap in any one of the three defeats the other two.

### 14.5 Security posture

- No no-confirmation autonomy outside scoped directories (see §11.4)
- Registration closed on LibreChat
- **LibreChat is bound to localhost. This is now load-bearing (v1.1).** In v1.0 this was hygiene protecting a chat app. It now protects your family's identity documents. Exposing this beyond localhost — even on the LAN, even "just to reach it from the laptop" — requires a reverse proxy with real auth, and is a decision to make deliberately rather than in passing
- Private repo only for `ai-context`
- Treat MCP servers as untrusted code — read source before installing
- **(v1.1)** Secret-scanning pre-commit hook active on `ai-context` (§4.4a)
- **(v1.1)** No agent holds both [IDENTITY]/[SENSITIVE] retrieval and an outbound channel (§7.4)
- **(v1.1)** Every new MCP server is checked against §7.4 before being added to a scoped agent. **The tool ceiling in §7.4 is a security boundary, not a capability budget** — the failure mode is adding one convenient tool to the Household Admin agent eighteen months from now, having forgotten why the list was short
- **(v1.1)** Full-disk encryption on. The vault is protected by process controls while running and by BitLocker when the machine is off. Confirm it is actually enabled — Windows 11 Home does not always enable device encryption by default

---

## 15. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MCP OAuth fails in shared agent mode (#9213, #13428, #13401) | Medium | High for Cluster 2/3 | Test each OAuth MCP in isolation; single-user deployment reduces exposure |
| 128-tool ceiling hit | Medium | Medium | Per-agent tool scoping + Deferred Tools from day one |
| `GraphRecursionError` kills long tasks | High | Medium | Raise `recursionLimit`; escalate to Goose |
| 2026-07-28 MCP spec breaking changes (stateless transport, removed session IDs) | **High — this is today** | Medium | Expect a window where some servers/clients need updates; pin versions; don't upgrade mid-build |
| Subagents/Agent Chain instability (beta) | High | Low | Don't build on them |
| MongoDB volume permission errors | Medium | High | WSL2 native filesystem only; `core.autocrlf false` |
| Version/price drift from the July 2026 research | Certain | Low–Medium | Every **[VERIFY]** tag gets a live check |
| Poisoned MCP/recipe supply chain ("Operation Pale Fire") | Low | **Severe** | Scoped directories, confirmations on, read source |
| Sensitive data routed through a logging path | Low | **Severe** | Structural enforcement via agent endpoint restrictions (§14.4) |
| **(v1.1)** Credential leaks into a RAG collection or memory store | **Medium** — this is a human-process risk, not a technical one, and the pressure is highest when you are busy | **Severe** — pgvector has no ACL and no expiry; Mem0 extracts silently | Tier-1 extraction before ingestion (§10.4.2); memory disabled on Household Admin; `validKeys` allow-list; Phase 8 memory dump audit |
| **(v1.1)** Prompt injection exfiltrates identity data via a browser-enabled agent | Low **while §7.4 holds** | **Severe** | Hard tool exclusion, verified by inspection at Phase 3 and again at Phase 8. Reviewed every time a tool is added to any agent |
| **(v1.1)** Identity data accidentally committed and pushed | **Medium** | **Severe and irreversible** — you cannot rotate a Medicare number, and GitHub history is effectively permanent | Vault physically outside the repo; `.gitignore`; tested pre-commit scanner (§4.4a); `git log -p` audit at Phase 8 |
| **(v1.1)** Household DB becomes stale and is silently trusted | **High** — this is the most likely failure by a distance, and the least dramatic | Medium — a confidently-returned superseded policy number causes real-world harm | Mandatory source-document citation and expiry surfacing (§10.4.3); renewal dates in `renewals.md`; scheduled quarterly review |
| **(1 Aug 2026)** Known cleartext Tier-1 files in staging are indexed before quarantine, or the legacy pipeline (`.lancedb`, `profile.db`, gateway token) is carried forward unaudited | **Medium** — the files are known and named, but Session 10 is weeks away and staging is browsable in the meantime | **Severe** — live credentials embedded in pgvector, or a legacy component with stored auth quietly running alongside the new build | Blocking step 0 quarantine in §10.4.2; legacy pipeline audit (port/redesign/retire per component); old embeddings store and profile DB securely deleted, never migrated; staging tree treated as [IDENTITY]+[SENSITIVE] from now, not from Session 10 |

---

## 16. CLAUDE PROJECT SETUP — BUILD INSTRUCTIONS

This section configures **this Claude Project** so Claude can drive the build effectively across many sessions.

### 16.1 Project Instructions — copy this in verbatim

```
This project builds a self-hosted backup AI system on Windows 11 to replace
Claude Pro Desktop. The spine document is BACKUP_AI_MASTER_BUILD_PLAN.md in
project knowledge. BUILD_STATE.md is the live progress tracker.

AT THE START OF EVERY SESSION:
1. Read BUILD_STATE.md to determine the current phase and any blockers.
2. State which phase and sub-step we are working on before doing anything else.
3. Do not begin a new phase until the previous phase's Exit Test is recorded
   as passed in BUILD_STATE.md.

HOW TO WORK:
- One phase at a time. One sub-step at a time. Wait for confirmation before
  moving on unless I say "go ahead" or "continue through".
- Give exact, runnable commands. Specify whether each command runs in WSL2
  Ubuntu, Windows PowerShell, or a container shell. Never leave this ambiguous.
- Before any step tagged [VERIFY] in the spine, web-search to confirm the
  current version, price, or config schema. The research is from July 2026 and
  this stack moves fast. Do not execute a [VERIFY] step on memory alone.
- When I paste logs or errors, read only the relevant portion. If it exceeds
  ~2000 tokens, ask me to trim it or save it to a file rather than ingesting
  all of it.
- When something fails, debug systematically: reproduce, isolate, form one
  hypothesis, test it. Do not shotgun fixes.
- Config files (librechat.yaml, docker-compose.override.yml, .env) are
  artifacts. Produce them as complete files, not fragments, and tell me
  exactly where they go.

HARD RULES:
- All project files live in the WSL2 native filesystem (~/). Never /mnt/c or a
  Windows path. Flag it immediately if I drift.
- git config --global core.autocrlf false must be set before any clone.
- Never suggest routing clinical, family-law, or household identity content
  through OpenRouter or any logging-enabled path. DeepInfra direct or
  Anthropic direct only.
- NEVER ask me to paste a password, PIN, MFA seed, recovery code, security
  answer, or private key, and never design a step that stores one. If a step
  appears to need a credential, the step is wrong — stop and say so. The system
  holds pointers to the password manager, never values.
- Never suggest a hosted embeddings endpoint for clinical or household
  collections. Local embeddings only — indexing is not inference, and the
  indexer sees everything regardless of how chat routing is configured.
- Never suggest adding a browser, web search, shell, code execution, or memory
  tool to the Household Admin or Clinical Work agents. If a task seems to need
  one, split it across two agents by hand. The friction is the control.
- Never suggest enabling fully-automatic no-confirmation agent mode outside a
  scoped working directory.
- Household identity data lives in ~/household-vault/, which is NOT a git repo
  and never becomes one. Flag it immediately if I drift.
- Do not build anything on Roo Code. It shut down in 2026.
- All customisations go in docker-compose.override.yml, never in the base
  compose file.

AT THE END OF EVERY SESSION:
Produce a BUILD_STATE.md update: phase completed, exit test result, files
created or changed with paths, blockers, decisions made with rationale, and
the exact next step. I will paste this back into project knowledge.
```

### 16.2 Files to add to Project Knowledge

| File | Purpose | When |
|---|---|---|
| `BACKUP_AI_MASTER_BUILD_PLAN.md` | This document — the spine | Now |
| `AI_Build.pdf` | Original research (already present) | Already there |
| `BUILD_STATE.md` | Live progress tracker | Create at start of Phase 0, re-upload after each session |
| `librechat.yaml` (working copy) | Current config for reference | Once Phase 2 starts |
| `mcp-servers.json` | Canonical MCP list | Once Phase 3 starts |
| `CLUSTER_VALIDATION.md` | Phase 8 test results | Phase 8 |
| `HOUSEHOLD_CLASSIFICATION.md` **(v1.1)** | Appendix D worksheet, filled in — the tier assignment for every item **[IDENTITY]** | Before Phase 6. **Structure and field names only. No values — this file goes into project knowledge, which is not the vault** | 

### 16.3 `BUILD_STATE.md` template

```markdown
# BUILD STATE

**Last updated:** <date>
**Current phase:** Phase N — <name>
**Current sub-step:** <x.y>

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | NOT STARTED / IN PROGRESS / PASSED / BLOCKED | — | — |
| 0 — Source of truth repo | | | |
| 1 — LibreChat deploy | | | |
| 2 — Providers | | | |
| 3 — Agents + MCP | | | |
| 4 — Skills sync | | | |
| 5 — Memory | | | |
| 6 — Projects/RAG | | | |
| 7 — Goose | | | |
| 8 — Validation | | | |
| 9 — Cutover | | | |

## Environment facts
- WSL2 distro:
- Docker Desktop version:
- LibreChat version:
- Repo path:
- LibreChat path:

## Files created/modified this session
- path — what changed

## Decisions made
- decision — rationale — date

## Blockers
- description — what's been tried — what's next

## NEXT STEP
<exact next action>
```

### 16.4 Project skill to create: `build-session-close`

Mirrors the existing `robot-session-close` pattern. Create in the Claude Project so it fires automatically.

```markdown
---
name: build-session-close
description: End-of-session closing routine for the Backup AI System build. Trigger when a phase exit test passes, or when the user says "we're done", "what's next", "session wrap", "update the build state", "write me a handover", or any equivalent. Also trigger at the natural end of a build conversation. Do not wait to be asked.
---

# Build Session Close

Produce a complete BUILD_STATE.md replacement (not a diff) containing:

1. Updated date and current phase/sub-step
2. Updated phase status table
3. Any new environment facts discovered
4. Every file created or modified this session, with full paths
5. Decisions made, each with a one-line rationale
6. Blockers: what failed, what was tried, what to try next
7. The exact next step, specific enough to start cold

Then state in one line: what to paste into project knowledge and what to
commit to the ai-context repo.

Do not summarise the conversation. Produce the artifact.
```

### 16.5 Optional project skills

| Skill | Purpose |
|---|---|
| `verify-before-executing` | Forces a live web check on any **[VERIFY]** step before commands are given |
| `config-file-writer` | Standardises how `librechat.yaml` / compose / `.env` files are produced — always complete files, always with placement instructions |

### 16.6 Session protocol

**Opening a session:** "Read BUILD_STATE.md. What phase are we on and what's the next step?"

**During:** one sub-step at a time. Paste real errors, trimmed.

**Closing:** "Session wrap" → the `build-session-close` skill fires → paste the output into `BUILD_STATE.md` → upload to project knowledge → `git commit` in `ai-context`.

---

## 17. SEQUENCED ROADMAP

| When | Do | Outcome |
|---|---|---|
| **Session 1** | Pre-flight + Phase 0 | Repo exists, environment verified |
| **Session 2** | Phase 1 | LibreChat running at localhost:3080 |
| **Session 3** | Phase 2 | All three providers working, tiering set |
| **Sessions 4–5** | Phase 3 | Agents + core MCP servers, OAuth tested |
| **Session 6** | Phase 4 | Skills syncing from repo |
| **Session 7** | Phase 5 | Memory portable across tools |
| **Sessions 8–9** | Phase 6 — general projects | Projects reconstructed, RAG pattern proven on low-stakes material |
| **Sessions 10–11** **(v1.1, revised 1 Aug 2026)** | Phase 6 §10.4 — household DB | Cluster 6 live. Session 10 is **Tier-1 quarantine (step 0), legacy-pipeline audit, classification, and extraction — no building.** Session 11 indexes and builds the agent |
| **Week 2+** | Phase 7 | Goose added *only if* a real ceiling is hit |
| **Weeks 3–4** | Phases 8–9 | Validated, parallel-run, cutover |

**Minimum viable backup = Phases 0–3.** That alone replaces most of Claude Pro's day-to-day value in one window. Everything after that is depth.

**On sequencing Cluster 6 (v1.1).** It is tempting to pull the household database forward — it is the most immediately useful thing in this plan and the most concrete. Resist that. It depends on local embeddings (Phase 2), agent tool scoping (Phase 3), and a proven RAG workflow (Phase 6). Building it early means building it on unproven infrastructure with your family's documents as the test data.

Session 10 exists as a separate session on purpose: classification is unglamorous, it is the step most likely to get rushed, and it is the step where getting it wrong is unrecoverable. It gets its own session with nothing to build at the end of it.

---

## 18. CHANGE TRIGGERS — WHEN TO REVISIT THIS PLAN

- LibreChat's **Agent Chain and Subagents exit beta** *and* MCP OAuth issues fully close → you can likely drop Goose entirely and go single-tool
- **DeepInfra prices rise** above OpenRouter's routed rates for your top models → re-evaluate the primary/secondary split
- **(v1.2)** **DeepInfra has a sustained outage, billing issue, or drops model coverage you rely on** → re-wire the already-scaffolded (commented-out) OpenRouter block in `librechat.yaml` for vendor redundancy
- **Cherry Studio's CherryClaw agent** matures into a robust unattended harness → it becomes a legitimate single-app alternative worth re-testing
- **MCP spec churn** settles after the 2026-07-28 stateless transport change → re-verify all servers
- Any component **changes licence or governance** → re-evaluate
- **(v1.1)** **LibreChat gains per-document ACLs within a RAG collection** → the strict collection separation in §6.3 could relax. Until then, collection boundaries are the only real boundary
- **(v1.1)** **A maintained MCP server appears for your password manager** that returns *references* rather than secret values → could reduce Tier-1 friction. **[VERIFY]** carefully: any server that returns secrets into model context is disqualified regardless of how it is marketed
- **(v1.1)** **You start wanting the Household agent to browse** → do not add the tool. That impulse is the signal to revisit §7.4 deliberately, in writing, not to make a quick config change

---

## APPENDIX A — MIGRATION INVENTORY WORKSHEET

Fill this in before Phase 6. One row per item to port.

| Item | Type | Cluster | [SENSITIVE]? | [IDENTITY]? | Ported to | Status |
|---|---|---|---|---|---|---|
| | Project / Skill / Memory / Connector | 1–6 | Y/N | Y/N | LibreChat agent / skills/ / memory/ / MCP / household-vault | |

**Current Claude connectors to replicate as MCP servers:** Google Drive, Gmail, Google Calendar, Microsoft 365, Spotify, Desktop Commander, browser automation (Chrome → Playwright MCP), PowerShell.

---

## APPENDIX B — QUICK COMMAND REFERENCE

```bash
# --- WSL2 Ubuntu shell ---
cd ~/LibreChat
docker compose up -d                  # start
docker compose down                   # stop
docker compose logs -f api            # tail API logs
docker compose ps                     # health check
docker compose restart api            # reload after librechat.yaml change

# --- source of truth ---
cd ~/ai-context
git add -A && git commit -m "session: <phase>" && git push

# --- diagnostics ---
docker stats                          # resource usage
docker compose exec api sh            # shell into the API container
wsl --shutdown                        # from PowerShell — hard reset WSL2
```

---

## APPENDIX C — SOURCE RESEARCH SUMMARY

Retained so the reasoning survives even if this plan is edited.

- **LibreChat** — self-hosted open-source chat platform, 33,900+ GitHub stars (early 2026), acquired by ClickHouse 4 Nov 2025 (announced by Ryadh Dahimene and creator Danny Avila; named enterprise deployments include Shopify, Daimler Truck, Fetch, cBioPortal). Latest stable v0.8.7 (23 June 2026). Provides autonomous MCP agents with a real plan→act→observe loop, Skills (v0.8.6+), subagents and Agent Chain (both beta, up to 10 agents), native web search with citations, sandboxed Code Interpreter (8+ languages), file search/RAG, Artifacts, per-user Memory, and MCP over stdio/HTTP/SSE.
- **Known limits** — 128-tool ceiling (Metabase Cloud, July 2026: adding the Linear MCP blew past the model's tool-array limit); MCP OAuth gaps in shared agent mode; memory is per-person not global; agent loop bounded at 25 steps default. Metabase still chose LibreChat over Open WebUI and LobeChat, citing the deepest and most serious MCP integration of the three.
- **Goose (Block)** — Apache-2.0, 51.3k stars, 500+ contributors (The AI Agent Index, Q3 2026), Linux Foundation Agentic AI Foundation governance since 7 Apr 2026. Native Windows desktop + CLI, 30+ providers, 70+ MCP extensions. Fully autonomous: installs packages, edits files, executes shell commands, runs tests, reads results.
- **Crush (Charm)** — strong second: Go single binary, first-class Windows (PowerShell + WSL), MCP over stdio/HTTP/SSE, Agent Skills, mid-session model switching. Licensed FSL-1.1-MIT, not OSI-approved.
- **Coding-agent landscape 2026** — Roo Code shut down (announced 21 Apr 2026 by founder Matt Rubens, repo archived 15 May 2026 at ~24,200 stars / 3,300 forks / 3M downloads; team pivoted to Roomote at ~$899/mo per parallel instance). Roo's own recommendation for a model-agnostic open-source extension was Cline. Kilo Code is the other live successor (Roo fork on the OpenCode server engine). Cline: 57,900+ stars, 4M+ installs. OpenCode (SST): ~170k stars. All coding-first and IDE/terminal-bound — they fail the single-interface constraint.
- **Cherry Studio** — 48,900+ stars, v1.9.12 portable (1 July 2026), added the CherryClaw autonomous agent (merged March 2026) with autonomous mode, no-confirmation mode, scheduled tasks, channels, MCPWorld marketplace. Its most mature agentic path assumes Anthropic-protocol tool-calling models and nudges toward its own CherryIN provider. Newer and less battle-tested than LibreChat Agents or Goose.
- **DeepInfra** — $107M Series B on 4 May 2026 (co-led by 500 Global and Georges Harik); processes nearly five trillion tokens per week; revenue tripled since the start of 2026. Own US NVIDIA Blackwell B200 infrastructure. SOC 2 / ISO 27001 / HIPAA / GDPR certified, zero-retention. 190+ open-source models over OpenAI-compatible APIs.
- **OpenRouter** — per APIMart (2026), a 5.5% credit fee, and for BYOK "first 1M requests/month free, then 5% of what the call would have cost." A June 2026 source (usagepricing.com) instead reports a $25,000/month list-price threshold. **Conflicting — verify.**
- **MCP** — donated to the Agentic AI Foundation (Linux Foundation directed fund) on 9 Dec 2025; MCP lead maintainer David Soria Parra confirmed the donation. Co-founded by Anthropic, Block and OpenAI with support from Google, Microsoft, AWS, Cloudflare and Bloomberg. Anthropic cites more than 10,000 active public MCP servers; SDKs see ~97M monthly downloads. The 2026-07-28 spec release candidate makes MCP stateless (removes the session-ID header and the initialize handshake), simplifying self-hosting but introducing breaking changes.
- **Skills** — the Agent Skills / SKILL.md open standard is supported by 16+ tools. Stick to the core spec (name, description, markdown body); avoid agent-specific frontmatter.
- **Memory** — OpenMemory MCP: local-first, Mem0-powered, one docker-compose, exposes `add_memories` / `search_memory` over MCP to any client.
- **Security** — Block's "Operation Pale Fire" red-team exercise (January 2026) compromised Goose via a poisoned recipe with malicious instructions hidden in invisible Unicode characters.

**All version numbers and prices above are as of July 2026 and move fast.**

**Note on Cluster 6 (v1.1):** the household database is **not** in the source research. It was raised during the pre-flight session and is a requirement of the household, not a finding of the July 2026 market survey. Nothing in Appendix C speaks to it, and no vendor claim above should be read as validating it. Its design rests on general principles — separation of secrets from identifiers, local indexing, tool exclusion — rather than on any researched product capability.

---

## APPENDIX D — HOUSEHOLD DATA CLASSIFICATION WORKSHEET **[IDENTITY]** (v1.1)

Fill this in during Session 10, **before** anything is indexed. One row per item in the existing family database.

**This worksheet records structure, never values.** "Vehicle → rego number → Tier 2 → in vault" is a row. The rego number itself is not.

| Item / field | Tier (1/2/3) | Authenticates? | Current location | Destination | Expiry / review | Done |
|---|---|---|---|---|---|---|
| e.g. Medicare number | 2 | No | old DB | vault/identifiers | card expiry | ☐ |
| e.g. MyGov password | 1 | **Yes** | old DB | **password manager** | — | ☐ |
| e.g. Passport scan | 3 | No | Drive folder | vault/documents | 2031 | ☐ |
| | | | | | | ☐ |

### The classification question, in order

1. **Does it authenticate?** If yes → Tier 1, no further questions
2. **Could it be used with other information to authenticate?** If plausibly yes → Tier 1. Over-classify when unsure
3. **Does it identify a person or an account?** → Tier 2
4. **Otherwise** → Tier 3

### Completion criteria

- [ ] Every item in the existing database has a row
- [ ] Every Tier-1 item has been **moved** to the password manager and **removed** from its old location
- [ ] The old database's Tier-1 fields are confirmed empty, including any backups, exports, or sync copies of it
- [ ] Nothing in this worksheet contains an actual value

### Household-specific open questions — resolve before Phase 6

Carried forward from the pre-flight session. These are not blockers for Phases 0–5.

| # | Question | Why it matters | Status |
|---|---|---|---|
| H1 | What form does the existing family database take? (folder / Notion / Airtable / custom DB) | Determines import vs rebuild, and how hard Tier-1 extraction will be | **RESOLVED, then REVISED (1 Aug 2026)** — not just a folder of exports. The tree at `D:\Data` (now staged at `C:\HouseholdDataRaw\Data` on encrypted C:) contains a **predecessor automation pipeline** (sync/OCR scripts, a `.lancedb` embeddings store, `profile.db`, a gateway component with token, scheduled tasks) plus **known cleartext Tier-1 files** (Chrome password exports, `Passwords.docx`, "Recovery Codes" and login notes, `.gateway_token`). See §10.4.2 for the full inventory and the new blocking quarantine step. This is an import **and** a decommission, not a rebuild |
| H2 | What does "scrape" do concretely — read email, parse statements, or log into portals? | If it stores portal logins it collides with the credential rule and must be redesigned before porting (§10.4.4) | **PARTIALLY REOPENED (1 Aug 2026)** — answered as "retrieval and form-fill only," but the tree contains `read_password_emails.py`, `find_pdf_passwords.py`, and a gateway component with a stored token. Likely benign utilities from the old build, but each old-pipeline component must be individually audited against §10.4.4 (port / redesign / retire) at Session 10 before reuse. Nothing from the old pipeline is assumed safe |
| H3 | Which password manager? | Hard dependency. Tier-1 extraction cannot start without a destination | **OPEN** — currently Google Password Manager; recommended moving to Bitwarden or 1Password (CLI support, proper family sharing, separate from the Google account the vault's source documents live in). Awaiting decision |
| H4 | Who else in the household needs access, and how? | LibreChat memory is per-person and the deployment is single-user. A second user is a design change, not a setting | **OPEN** — Sarah needs access. Recommended: start with shared-machine access (Option A) rather than exposing LibreChat on the LAN (Option B), which would contradict §14.5. Awaiting decision |
| H5 | Is full-disk encryption actually enabled? | Windows 11 Home does not always enable it by default (§14.5) | **RESOLVED** — live check via `Get-BitLockerVolume`: `C:` FullyEncrypted/On (Device Encryption). `D:` and `E:` FullyDecrypted/Off. `ai-context/` and `household-vault/` will live on `C:` under WSL2, so the build itself is covered. The existing source folder at `D:\Data` (see H1) is not |

---

*End of spine document.*
