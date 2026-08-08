# BUILD STATE

**Last updated:** 8 August 2026 (final — Phases 0–6 complete, Phase 7 next)
**Current phase:** Phase 7 — Goose (§11)
**Current sub-step:** §11.1 — Install Goose natively on Windows.

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **PASSED** | All 5 checks green | 6 Aug 2026 |
| 2 — Providers | **PASSED (scope revised, v1.2)** | 6/8 checks green; 2 rescoped out — see below | 7 Aug 2026 |
| 3 — Agents + MCP | **PASSED** | All items complete — see below | 8 Aug 2026 |
| 4 — Skills sync | **PASSED** | All 4 exit criteria met | 8 Aug 2026 |
| 5 — Memory | **PASSED** | Native memory cross-conversation verified | 8 Aug 2026 |
| 6 — Projects/RAG | **PASSED** | Pattern proven, scope decision made | 8 Aug 2026 |
| 7 — Goose | IN PROGRESS | — | next |
| 8 — Validation | NOT STARTED | — | — |
| 9 — Cutover | NOT STARTED | — | — |

## Environment facts (confirmed)
- Machine: Michael-PC, Windows 11 Home 26200, i5-12400, 15.8 GB RAM
- RAM stick: Crucial CT16G4DFRA32A.C16FT, DDR4-3200, Channel A DIMM 0 (upgrade deferred)
- WSL2: Ubuntu-24.04 installed, VERSION 2, UNIX user = michael, home = /home/michael
- Docker Desktop 29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
- git: installed inside Ubuntu, core.autocrlf = false (confirmed). Local git identity set: user.name=michaelreynolds111-dev, user.email=michael.reynolds111@gmail.com
- Disk: C: 464 GB / ~190 GB free / FullyEncrypted. D: FullyDecrypted (household data snapshot on C:) — **D: cannot be BitLockered (Michael confirmed 7 Aug 2026); exact reason not yet captured — see open questions.**
- .wslconfig: memory=8GB, processors=6, swap=2GB — leave as-is through Phase 3
- GitHub: michaelreynolds111-dev, no SSH keys in Ubuntu -> use HTTPS + PAT
- ai-context repo: https://github.com/michaelreynolds111-dev/ai-context.git (private, confirmed via API)
- gitleaks 8.30.1 installed at ~/.local/bin/gitleaks (user-local, no sudo). On PATH via ~/.bashrc.
- PAT stored via git credential helper (`store`) at ~/.git-credentials, perms 600. HTTPS auth working.
- Default branch: **master** (kept deliberately — see decisions)
- **LibreChat v0.8.7** cloned to ~/LibreChat (WSL2 native fs, confirmed not /mnt/c)
- **Docker stack running:** 6 containers — LibreChat (api, port 3080), admin-panel (port 3000, internal), chat-mongodb, chat-meilisearch, vectordb, rag_api — all healthy (confirmed 8 Aug 2026 post-recovery)
- **rag_api image switched to full (non-lite) build** — registry.librechat.ai/danny-avila/librechat-rag-api-dev:latest (11.8GB)
- **Admin account re-registered** (8 Aug 2026) after MongoDB fresh init. Login confirmed working, ALLOW_REGISTRATION=false re-locked via /api/config.
- **ALLOW_REGISTRATION=false** confirmed via `/api/config` (`registrationEnabled:false`) — registration locked down.
- **Desktop Commander MCP connector in use for build execution.** All LibreChat/WSL2 ops routed through `wsl -d Ubuntu-24.04 -- bash -lc "..."` or `\\wsl.localhost\Ubuntu-24.04\...` UNC path.
- **DeepInfra confirmed to host Claude models directly** — `anthropic/claude-sonnet-5`, `claude-opus-5`, `claude-opus-4-8`, `claude-fable-5`, `claude-haiku-4-5`, `claude-sonnet-4-6`, plus `google/gemini-*` models.
- **MongoDB data dir:** `~/LibreChat/data-node/` — fresh init as of 8 Aug 2026. Old corrupt dir preserved at `~/LibreChat/data-node.old-20260808` (uid 999, requires `docker exec` to delete — low priority, 1.1MB).


## Phase 0 deliverables (all committed, pushed to origin/master, commit 3b4a994)
- ~/ai-context/ — repo structure: skills/ projects/ memory/ mcp/ docs/
- ~/ai-context/README.md, .gitignore, .gitleaks.toml, pre-commit hook, session-close SKILL.md, mcp-servers.json stub
- ~/household-vault/ — documents/ identifiers/ renewals.md. NOT a git repo, outside ai-context/

## Phase 1 deliverables (6 Aug 2026)
- ~/LibreChat/ — cloned v0.8.7, .env populated, docker-compose.override.yml created
- 6-container stack confirmed healthy, admin login working, registration locked

## Phase 2 deliverables (7 Aug 2026)
- ~/LibreChat/librechat.yaml — v1.3.13 schema, DeepInfra wired, OpenRouter commented-out scaffold
- docker-compose.override.yml — librechat.yaml bind mount + rag_api full image override
- .env — EMBEDDINGS_PROVIDER=huggingface, EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
- End-to-end RAG verified: local embeddings, zero outbound traffic, model switching confirmed

## Phase 3 progress (8 Aug 2026) — IN PROGRESS
- **§7.2 recursion limits — DONE.** `recursionLimit: 75` / `maxRecursionLimit: 150` confirmed in librechat.yaml.
- **§7.4 purpose-built agents — ALL BUILT (8 Aug 2026).**
  | Agent | Model | Tools | §7.6 verified |
  |---|---|---|---|
  | Desktop Ops | DeepSeek-V4-Pro | 15 filesystem tools | ✓ DB-inspected |
  | Research | DeepSeek-V4-Pro | 15 filesystem + web_search | ✓ DB-inspected |
  | Clinical Work | claude-sonnet-5 | 0 — empty by design | ✓ DB-inspected |
  | Household Admin | DeepSeek-V4-Pro | 0 — empty by design | ✓ DB-inspected |
  | Music | (existing) | 10 Spotify tools | ✓ from earlier |
- **§7.5 native web search — DONE** (via Tavily native integration, verified above).
- **§7.6 exit test — PASSED (8 Aug 2026).** Tool exclusions verified by direct MongoDB inspection (`db.agents.find()`), not agent self-report. Clinical Work and Household Admin both confirmed `tools: []` in DB. Desktop Ops and Research tool lists match expected config exactly. `test.txt` confirmed on WSL2 disk at `~/agent-workdir/` via bind mount.
- **Remaining in Phase 3:** Google Drive MCP + M365 MCP OAuth flows (human-gated). These don't block Phase 3 exit — agents are built, tools will attach when OAuth is complete.
- **§7.3 MCP table — Spotify ✓, Filesystem ✓, Tavily/web search ✓ (8 Aug 2026).**
  - Spotify: installed, token-lifecycle bug fixed (`SPOTIFY_EXPIRES_AT=1`), UI smoke test PASSED.
  - Filesystem MCP (`@modelcontextprotocol/server-filesystem` v2026.7.10): wired with hard directory scoping. `/app/ai-context` (ro) + `/app/agent-workdir` (rw) mounted via override. `household-vault/` and `LibreChat/` not mounted — physical exclusion. 15 tools confirmed.
  - Tavily native: `TAVILY_API_KEY` in `.env`, web search confirmed with real citations. Covers §7.3 + §7.5 in one step.
  - `~/agent-workdir/` created as agent scratch space.
- **Desktop Commander not wired into LibreChat (8 Aug 2026):** `allowedDirectories` only restricts file ops, not terminal commands. Without per-call confirmations (which LibreChat agents don't show), shell access can't be safely scoped. Official filesystem-only server used instead. Desktop Commander stays in Claude Desktop for supervised build work only.

## Decisions made
- Ubuntu-24.04 LTS chosen (over 26.04) — 1 Aug 2026
- UNIX username: michael — 1 Aug 2026
- RAM upgrade deferred; .wslconfig stays 8 GB through Phase 3 — 1 Aug 2026
- D:\Data NOT deleted — live working dir of 7 scheduled tasks. Decommission at Session 10 — 1 Aug 2026
- Dump-and-index rejected for household data — 1 Aug 2026
- Legacy pipeline will be audited/decommissioned, never migrated — 1 Aug 2026
- GitHub auth: HTTPS + PAT — 1 Aug 2026
- gitleaks over git-secrets, installed user-local — 5 Aug 2026
- Default branch: master — 5 Aug 2026
- PAT via credential.helper store (~/.git-credentials, perms 600) — 5 Aug 2026
- PAT rotated and re-secured — 6 Aug 2026
- `open-webui` container removed (port conflict) — 6 Aug 2026
- **PLAN REVISION v1.2** — OpenRouter demoted to backlog/resilience — 7 Aug 2026
- rag_api switched to full image for local embeddings — 7 Aug 2026
- Desktop Commander adopted for build execution — 7 Aug 2026
- Real document used for RAG test (Michael's explicit choice) — 7 Aug 2026
- D: cannot be BitLockered confirmed — 7 Aug 2026
- **MongoDB fresh init chosen over WiredTiger recovery** — 8 Aug 2026. Lost data was early-phase test content only; no household/clinical data was ever in the DB. Pragmatic call.
- **UID/GID in .env NOT the correct fix** — 8 Aug 2026. Setting UID=1000 in .env causes MongoDB to run as uid 1000, which can't read its own uid-999 data files. The UID/GID warnings from docker compose are cosmetic noise; MongoDB runs correctly as uid 999 (its internal default) when the Compose `user:` directive resolves to blank. The real prevention is clean shutdown handling (see GOTCHAS §4 updated).
- **MCP agent design pattern (established with Spotify, applies to all Cluster-3 MCP agents)** — 8 Aug 2026. Scope each MCP agent NARROW: one service per agent for now (don't pre-merge Drive/M365/Spotify into one general agent — decide consolidation later). Use a reliable tool-calling model (sonnet-5) for the first smoke test to eliminate "did it even call the tool" as a variable, then downgrade to a cheap model for daily use. No skills, no file context, minimal system prompt for simple tool-call agents. Subagents/Handoffs/Chain OFF (beta, don't build on them). This does NOT relax the hard tool-exclusion rules for Household Admin / Clinical Work agents — those still get built with exclusions from the start.
- **Spotify token-lifecycle: force refresh-on-boot** — 8 Aug 2026. Env-var-mode static access tokens are a trap in `@tbrgeek/spotify-mcp-server` (fakes expiry, never refreshes). `SPOTIFY_EXPIRES_AT=1` forces a real refresh from the durable refresh token on every start. General principle for any static-token MCP server: prefer forcing refresh over pasting a "fresh" access token. See GOTCHAS §6.
- **Filesystem MCP: use `@modelcontextprotocol/server-filesystem`, not Desktop Commander** — 8 Aug 2026. Desktop Commander's `allowedDirectories` doesn't restrict terminal commands, only file ops. Without per-call confirmation prompts (which LibreChat agents don't show), shell access can't be safely scoped. Official Anthropic filesystem-only server used instead — no shell at all, directory scoping is the actual boundary. Desktop Commander stays in Claude Desktop for supervised build work only.
- **Filesystem scope: `ai-context/` (ro) + `agent-workdir/` (rw), household-vault/ and LibreChat/ excluded** — 8 Aug 2026. Physical exclusion via not mounting those dirs into the container — not a config rule that could be misconfigured.
- **Tavily native integration over MCP server** — 8 Aug 2026. LibreChat has built-in Tavily support via `TAVILY_API_KEY` in `.env`, cleaner than wiring a separate MCP server. Covers §7.3 Tavily entry and §7.5 web search in one step.

## Documentation conventions
- **`BACKUP_AI_MASTER_BUILD_PLAN.md`** — spine, versioned (v1.2). Change via logged plan revision only.
- **`BUILD_STATE.md`** (this file) — live progress tracker. Read at session open; push at session close.
- **`docs/GOTCHAS.md`** — settled machine/stack facts. Read before touching a previously-fought area. Update at session close alongside BUILD_STATE.
- **`docs/PLAN_DEVIATIONS_2026-08-05.md`** — formal deviations from the plan with rationale.
- **GitHub Issues** — open/unresolved problems. Resolved lessons move to GOTCHAS.

**Session-open ritual:** read BUILD_STATE.md, skim GOTCHAS.md if touching a previously-fought area.
**Session-close ritual:** update BUILD_STATE + GOTCHAS, commit+push via local git in ~/ai-context, report SHA. (No `git pull` needed — all commits come from this same clone, so it's always current after a push. Only pull if you've edited files directly on GitHub via the web UI.)

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended. UNDECIDED
- **New (7 Aug 2026): why can't D: be BitLockered?** Doesn't block anything now; worth pinning before Session 10.

## Blockers / follow-ups
- ~~MongoDB data loss / login broken~~ — **RESOLVED 8 Aug 2026** (see Phase 3 progress above)
- Three-collection RAG separation deferred to Phase 3 (agent tool scoping) / Phase 6 — correct rescoping, not a gap.
- `ADHD Treatment Plan.md` indexed in default/unscoped RAG collection from Phase 2 test. May want to reset/reindex cleanly once Phase 3 builds per-agent collection scoping.
- Manual cleanup: `~/LibreChat/data-node.old-20260808` (1.1MB, uid 999 owned). Remove via: `docker exec chat-mongodb rm -rf /data/../data-node.old-20260808` — low priority.

## Deviations from plan (this session, 8 Aug 2026)
1. **MongoDB blocker resolved via fresh init** (described above). Decision logged in Decisions.
2. **UID=1000 in .env attempted and immediately reverted** — caused MongoDB crash-loop (can't read uid-999 data files). Lesson: the UID/GID warnings are cosmetic; don't try to fix them by setting michael's uid — MongoDB needs to run as its own internal uid 999. Added to GOTCHAS §3 and §4.
3. **`docker compose exec` service name vs container name** — compose uses service name `mongodb`; `docker exec` uses container name `chat-mongodb`. These are different and not interchangeable. Used `docker exec chat-mongodb` + `docker cp` for all container operations this session.
4. **GitHub MCP connector unavailable at session start** — required toggling on in the Claude UI before it appeared in tool_search. Once available it worked fine. Reinforces GOTCHAS §5: treat it as available for reads at session start only; don't depend on it surviving a long session.
5. **Spotify 401 debug — corrected a prior session's wrong root cause.** The Aug 7 session's note that the package "re-derives a fresh access token on every container start" was disproven by reading the source. It only refreshes when it believes the token is expired, and in env-var mode it fakes expiry to start+1h. Fixed with `SPOTIFY_EXPIRES_AT=1`. GOTCHAS §6 corrected. Lesson reinforced: verify package behaviour against source, don't carry forward an unverified assumption.

## Deviations from plan (previous sessions — 7 Aug 2026, 6 Aug 2026)
See prior BUILD_STATE entries (preserved in git history).

## Phase 0 exit test — PASSED (5 Aug 2026)
## Phase 1 exit test — PASSED (6 Aug 2026)
## Phase 2 exit test — PASSED, scope revised per v1.2 (7 Aug 2026)
(Full exit test detail preserved in git history / prior BUILD_STATE versions)

## Phase 3 exit test — PASSED (8 Aug 2026)
- §7.1 agent capabilities — ✓
- §7.2 recursion limits (75/150) — ✓
- §7.3 Spotify MCP — ✓ (token bug fixed, UI smoke test passed)
- §7.3 Filesystem MCP — ✓ (15 tools, directory-scoped, bind-mounted)
- §7.3 Tavily/web search — ✓ (native integration, citations verified)
- §7.3 Google Drive MCP — ⏳ deferred (30-45min human-gated OAuth, steps in GOTCHAS §9)
- §7.3 M365 MCP — ⏳ deferred (30-45min human-gated OAuth, steps in GOTCHAS §9)
- §7.4 all 5 agents built — ✓
- §7.5 native web search — ✓
- §7.6 exit test (tool exclusions DB-inspected) — ✓ PASS
- Household Admin tool exclusion verified by MongoDB inspection — ✓
- Research/General agents cannot reach clinical/household collections — ✓ (collections not yet built, correct by absence)

## Phase 4 exit test — PASSED (8 Aug 2026)
- §8.1 volume mount (`/app/skill`) confirmed working from Phase 1 — ✓
- §8.4 all 7 skills appear in LibreChat catalog after container restart — ✓
- `/s` manual invocation available via Skills toolbar — ✓
- Skills correctly absent until container restart (GOTCHAS §8 updated) — ✓
- Model picker cleaned up: `endpointsMenu: false` hides unused providers; 18 models in 5 tiers via `modelSpecs`; `fetch: false` keeps list curated — ✓
- Model list sourced from live DeepInfra API output (deepinfra_models.md, 8 Aug 2026) — ✓

## Phase 5 exit test — PASSED (8 Aug 2026)
- LibreChat native memory configured at top-level in librechat.yaml — ✓
- `validKeys` allow-list set (preferences, tone, systems, people, working_style) — ✓
- Memory agent pointed at DeepInfra Work-tier (no OpenAI dependency) — ✓
- `agent.enabled: true` explicitly set (required in v0.8.7, now opt-in) — ✓
- `messageWindowSize: 10` (conservative) — ✓
- Memory stored in conversation 1 recalled correctly in conversation 2 — ✓ VERIFIED
- `~/ai-context/memory/` markdown files seeded: preferences.md, systems.md, people.md, decisions.md — ✓
- OpenMemory MCP deferred: default setup requires OpenAI for extraction LLM (§14.4 violation). Revisit once DeepInfra routing for extraction is confirmed viable.

## Phase 6 exit test — PASSED (8 Aug 2026)
- RAG + agent + INSTRUCTIONS.md pattern proven on New Build (Stash) project — ✓
- `projects/new-build/` committed with 17 knowledge files (README, runbook, TODO, docker-compose redacted, env.example, 12 Python source files) — ✓ commit bf95d2e
- `Stash Ops` agent built in LibreChat UI (knowledge-only, High tier model) — ✓
- gitleaks false positive documented and allowlisted in `.gitleaksignore` — ✓
- `docs/MIGRATION_INVENTORY.md` updated: all remaining 13 projects marked DEFERRED to post-cutover — ✓
- **Scope decision:** remaining project migrations deferred until after Phase 9 cutover. They will be done *using* LibreChat (not Claude Desktop), which is itself the real-world validation that the system works. See MIGRATION_INVENTORY.md.

## NEXT STEP
**Phase 7 — Goose (§11).**

Install Goose (Block) natively on Windows. Configure it to point at the same DeepInfra key, same ai-context/skills/ folder, and same mcp-servers.json. Prove it can complete a multi-step Docker/WSL task that a LibreChat agent cannot (recursion limit or shell-loop requirement).

The Stash stack live-access upgrade (giving Goose scoped write access to C:\torbox-system\stash-torbox-bridge\) is the natural first real task once Goose is running -- it validates Cluster 1 (sysadmin/infra) and proves the secret-separation boundary holds.
