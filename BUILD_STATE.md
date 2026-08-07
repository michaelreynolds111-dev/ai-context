# BUILD STATE

**Last updated:** 8 August 2026
**Current phase:** Phase 3 — Agents + MCP (§7)
**Current sub-step:** Blocker resolved — MongoDB fresh init complete, login confirmed working. Ready to resume §7.3 MCP table (Spotify UI smoke test first, then next server).

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **PASSED** | All 5 checks green | 6 Aug 2026 |
| 2 — Providers | **PASSED (scope revised, v1.2)** | 6/8 checks green; 2 rescoped out — see below | 7 Aug 2026 |
| 3 — Agents + MCP | IN PROGRESS | — | started 8 Aug 2026 |
| 4 — Skills sync | NOT STARTED | — | — |
| 5 — Memory | NOT STARTED | — | — |
| 6 — Projects/RAG | NOT STARTED | — | — |
| 7 — Goose | NOT STARTED | — | — |
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
- **§7.3 first MCP server — Spotify — INSTALLED + OAuth-TESTED.** `@tbrgeek/spotify-mcp-server` via npx in api container. All 10 tools confirmed via log inspection. UI smoke test still pending.
- **MongoDB blocker — RESOLVED (8 Aug 2026).** Fresh data-node init. New admin account registered. ALLOW_REGISTRATION re-locked. Root cause of original incident: WiredTiger unclean shutdown (Aug 7 host sleep/wake event) left mongod.lock non-empty + storage.bson unreadable, causing crash-loop on next start. See GOTCHAS §4 (updated).
- **`docs/GOTCHAS.md` — CREATED and populated** (prior session). Updated this session with MongoDB resolution + UID/GID clarification.

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

## Documentation conventions
- **`BACKUP_AI_MASTER_BUILD_PLAN.md`** — spine, versioned (v1.2). Change via logged plan revision only.
- **`BUILD_STATE.md`** (this file) — live progress tracker. Read at session open; push at session close.
- **`docs/GOTCHAS.md`** — settled machine/stack facts. Read before touching a previously-fought area. Update at session close alongside BUILD_STATE.
- **`docs/PLAN_DEVIATIONS_2026-08-05.md`** — formal deviations from the plan with rationale.
- **GitHub Issues** — open/unresolved problems. Resolved lessons move to GOTCHAS.

**Session-open ritual:** read BUILD_STATE.md, skim GOTCHAS.md if touching a previously-fought area.
**Session-close ritual:** update BUILD_STATE + GOTCHAS, commit+push via local git in ~/ai-context, report SHA, remind Michael to `git pull`.

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

## Deviations from plan (previous sessions — 7 Aug 2026, 6 Aug 2026)
See prior BUILD_STATE entries (preserved in git history).

## Phase 0 exit test — PASSED (5 Aug 2026)
## Phase 1 exit test — PASSED (6 Aug 2026)
## Phase 2 exit test — PASSED, scope revised per v1.2 (7 Aug 2026)
(Full exit test detail preserved in git history / prior BUILD_STATE versions)

## NEXT STEP
**Resume Phase 3 — Agents + MCP (§7).** Blocker cleared.

1. **Spotify UI smoke test** — open LibreChat, use the Spotify agent, confirm the 10 tools work end-to-end in the UI (search, play, pause, current playback). Log-inspect after, don't trust agent self-report.
2. **Continue §7.3 MCP table** — next server(s) in lower-stakes-first order. Read BACKUP_AI_MASTER_BUILD_PLAN.md §7 before starting.
3. **§7.4 purpose-built agents** — Household Admin + Clinical Work, with hard tool exclusions built in from the start (never deferred).
4. **§7.6 exit test** — inspection-based verification of tool exclusions (not agent-reported).

All commands via Desktop Commander → `wsl -d Ubuntu-24.04` / UNC path. Read GOTCHAS.md §3/§4 before touching MongoDB or Docker again.
