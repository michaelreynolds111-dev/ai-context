# BUILD STATE

**Last updated:** 6 August 2026
**Current phase:** Phase 2 — Providers (§6)
**Current sub-step:** Not yet started

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **PASSED** | All 5 checks green | 6 Aug 2026 |
| 2 — Providers | NOT STARTED | — | — |
| 3 — Agents + MCP | NOT STARTED | — | — |
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
- git: installed inside Ubuntu, core.autocrlf = false (confirmed)
- Disk: C: 464 GB / ~190 GB free / FullyEncrypted. D: FullyDecrypted (household data snapshot on C:)
- .wslconfig: memory=8GB, processors=6, swap=2GB — leave as-is through Phase 3
- GitHub: michaelreynolds111-dev, no SSH keys in Ubuntu -> use HTTPS + PAT
- ai-context repo: https://github.com/michaelreynolds111-dev/ai-context.git (private, confirmed via API)
- gitleaks 8.30.1 installed at ~/.local/bin/gitleaks (user-local, no sudo). On PATH via ~/.bashrc.
- PAT stored via git credential helper (`store`) at ~/.git-credentials, perms 600. HTTPS auth working.
- Default branch: **master** (kept deliberately — see decisions)
- **LibreChat v0.8.7** cloned to ~/LibreChat (WSL2 native fs, confirmed not /mnt/c)
- **Docker stack running:** 6 containers — LibreChat (api, port 3080), admin-panel (port 3000, internal), chat-mongodb, chat-meilisearch, vectordb, rag_api — all healthy
- **First admin account registered:** Michael Gareth Thompson Reynolds, login confirmed working, session survives container restart
- **ALLOW_REGISTRATION=false** confirmed via `/api/config` (`registrationEnabled:false`) — registration locked down post-setup

## Phase 0 deliverables (all committed, pushed to origin/master, commit 3b4a994)
- ~/ai-context/ — repo structure: skills/ projects/ memory/ mcp/ docs/
- ~/ai-context/README.md — repo purpose + layout + secret-scanning note
- ~/ai-context/.gitignore — per §4.4 (incl. [IDENTITY] belt-and-braces rules)
- ~/ai-context/.gitleaks.toml — default rules + custom AU identifier rules (TFN, Medicare, passport, licence)
- ~/ai-context/.git/hooks/pre-commit — blocking gitleaks scan; exports ~/.local/bin to PATH (hooks run non-login shell)
- ~/ai-context/skills/session-close/SKILL.md — first real skill (ported from robot-session-close pattern, generic)
- ~/ai-context/mcp/mcp-servers.json — stub {"mcpServers": {}}
- ~/household-vault/ — documents/ identifiers/ renewals.md. NOT a git repo, outside ai-context/ (both verified)

## Phase 1 deliverables (6 Aug 2026)
- ~/LibreChat/ — cloned from danny-avila/LibreChat, v0.8.7 (confirmed current stable via [VERIFY] web search)
- ~/LibreChat/.env — populated: CREDS_KEY (64 char hex), CREDS_IV (32 char hex), JWT_SECRET (64 char hex), JWT_REFRESH_SECRET (64 char hex), ADMIN_PANEL_SESSION_SECRET (64 char hex, added mid-session — see deviations), DEEPINFRA_API_KEY (real key, entered by Michael). ANTHROPIC_API_KEY and OPENROUTER_KEY left as placeholders — Michael does not hold those keys yet, deferred to Phase 2.
- ~/LibreChat/docker-compose.override.yml — mounts ~/ai-context/skills read-only to /app/skill (LibreChat's deployment-skills directory, confirmed via [VERIFY] — feature added in v0.8.6/PR #13523, DEPLOYMENT_SKILLS_DIR defaults to this path so no env var override was needed)
- Confirmed via container logs: `[deploymentSkills] Loaded 1 deployment skill(s) from /app/skill` — session-close skill from Phase 0 is live in LibreChat

## Files created/modified (prior session, 1 Aug)
- C:\HouseholdDataRaw\Data — verified snapshot of D:\Data (57,598 files / 28.3 GB)
- C:\HouseholdDataRaw\robocopy_log.txt — copy log

## Decisions made
- Ubuntu-24.04 LTS chosen (over 26.04) — 1 Aug 2026
- UNIX username: michael — 1 Aug 2026
- RAM upgrade deferred; .wslconfig stays 8 GB through Phase 3 — 1 Aug 2026
- D:\Data NOT deleted — live working dir of 7 scheduled tasks. Decommission at Session 10 — 1 Aug 2026
- Dump-and-index rejected for household data: known cleartext Tier-1 files in tree. Blocking quarantine = step 0 of §10.4.2 — 1 Aug 2026
- Legacy pipeline (.lancedb, profile.db, gateway) will be audited/decommissioned, never migrated — 1 Aug 2026
- GitHub auth: HTTPS + personal access token (no SSH keys in Ubuntu) — 1 Aug 2026
- ai-context repo name: ai-context — 1 Aug 2026
- gitleaks over git-secrets — 5 Aug 2026. Latest stable 8.30.1. Successor tool "Betterleaks" flagged for change-trigger list, no action needed now.
- gitleaks installed user-local (~/.local/bin), not /usr/local/bin — 5 Aug 2026. Avoids sudo. Pre-commit hook exports ~/.local/bin to PATH explicitly.
- Default branch left as `master` — 5 Aug 2026. No functional benefit to renaming for a single-user private repo.
- PAT persisted via credential.helper store (plaintext at ~/.git-credentials, perms 600) — 5 Aug 2026. Acceptable on single-user, full-disk-encrypted box.
- PAT rotated and re-secured — 6 Aug 2026. Original exposed token revoked; fresh classic token (repo scope) stored via credential.helper store.
- **DeepInfra key added, Anthropic/OpenRouter deferred** — 6 Aug 2026. Michael only held a DeepInfra key at deploy time. `.env` left with placeholder/commented entries for the other two; Phase 2 (§6, provider wiring) will need real Anthropic and OpenRouter keys before it can be exit-tested.
- **Local openssl over web-based credentials generator** — 6 Aug 2026. LibreChat docs offer a web tool at librechat.ai/toolkit/creds_generator; chose local `openssl rand -hex` instead to avoid sending secret material to any third-party page, even a first-party one.
- **`open-webui` container removed** — 6 Aug 2026. Was a leftover from the July 2026 evaluation phase (Open WebUI vs LibreChat vs LobeChat). Occupied port 3000, conflicting with LibreChat's admin-panel. Consistent with the already-locked decision to use LibreChat; stopped mid-session, fully removed at session close.

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended over LAN exposure. UNDECIDED

## Blockers / follow-ups
- Anthropic and OpenRouter API keys still needed before Phase 2 (provider wiring) can be fully exit-tested. DeepInfra key is in place.
- `librechat.yaml` does not yet exist (confirmed via startup log: `ENOENT ... /app/librechat.yaml`). This is expected — it's a Phase 2 deliverable, not a Phase 1 gap.

## Deviations from plan (this session)
1. **`.env` line-1 corruption during manual edit.** A stray `f` character appeared before the leading `#` on line 1 of `.env` (likely a terminal input race during nano editing), which caused `docker compose up -d` to fail with a YAML/env parse error. Fixed with `sed -i '1s/^f#/#/' .env`. No data loss — only a comment line was affected. Flagging in case corrupted comment lines recur during manual `.env` edits in later phases.
2. **`ADMIN_PANEL_SESSION_SECRET` not covered by original §5.2 credential list.** The build plan's original 5.2 instructions listed CREDS_KEY/CREDS_IV/JWT_SECRET/JWT_REFRESH_SECRET only. The admin-panel container (new since v0.8.5) additionally requires `ADMIN_PANEL_SESSION_SECRET` (min 32 chars) or it crash-loops with `SESSION_SECRET must be set to at least 32 characters (got 0)`. Generated and set the same way (openssl rand -hex 32) as an in-session fix. Recommend updating the master build plan's §5.2 checklist to include this for future rebuilds.
3. **Port 3000 conflict with legacy `open-webui` container.** Left running from the pre-Phase-0 evaluation period, it held port 3000 which admin-panel also wants. Stopped then removed (see decisions).
4. **Verification method correction:** `docker exec LibreChat printenv <VAR>` is NOT a valid way to check LibreChat's effective config — the `api` service bind-mounts the whole `.env` file to `/app/.env` and the Node app reads it directly via its own dotenv loader, rather than receiving vars through Compose's `environment:` block (that pattern is only used for a handful of hardcoded vars, and `env_file:` in the base compose is actually attached to `rag_api`, not `api`). Use `curl http://localhost:3080/api/config` or `docker compose logs api` to verify LibreChat's actual runtime config instead.

## Phase 0 exit test — result (5 Aug 2026): PASSED
- [x] `git log` shows an initial commit — 3b4a994
- [x] Private GitHub remote added and pushed — origin/master, private confirmed via API (404 unauth)
- [x] At least one real SKILL.md written and committed — session-close
- [x] mcp/mcp-servers.json exists — stub
- [x] Secret-scanning pre-commit hook installed AND demonstrated to block a dummy identifier — dummy TFN blocked via au-tfn rule, redacted
- [x] ~/household-vault/ exists, is not a git repo, is not inside ai-context/ — all verified

## Phase 1 exit test — result (6 Aug 2026): PASSED
- [x] localhost:3080 loads — confirmed, LibreChat chat UI renders
- [x] Admin login works — registered and logged in as Michael Gareth Thompson Reynolds
- [x] All 6 containers healthy — LibreChat (api), admin-panel, chat-mongodb, chat-meilisearch, vectordb, rag_api all `Up`/`healthy` (admin-panel required the SESSION_SECRET fix above to stop crash-looping)
- [x] Registration closed — confirmed via `curl http://localhost:3080/api/config` showing `"registrationEnabled":false`
- [x] Restart preserves account — session survived `docker compose up -d --force-recreate api`; navigating to localhost:3080 after restart lands directly in the logged-in chat UI, no re-login required

## NEXT STEP
Open a fresh chat in this project. Start with:
"Read BUILD_STATE.md. What phase are we on and what's the next step?"

**Phase 2 — Providers (§6). All commands run in the WSL2 Ubuntu shell (/home/michael/LibreChat) unless noted.**

Before starting, this phase needs real Anthropic and OpenRouter API keys — Michael to have these ready (entered directly into `.env`, never via chat).

Expected shape of the phase (confirm against the spine doc, not memory — read BACKUP_AI_MASTER_BUILD_PLAN.md §6 fresh):
1. Create `librechat.yaml` (does not currently exist — confirmed via startup log) — DeepInfra as custom OpenAI-compatible endpoint, OpenRouter as custom endpoint, Anthropic direct via native endpoint
2. Mount `librechat.yaml` into the container via docker-compose.override.yml (additive to the existing skills mount, not replacing it)
3. Restart and confirm all three providers appear in the model selector
4. Run Phase 2 exit test (exact criteria TBD — check §6 of the spine doc)

Reminder: DeepInfra key already in `.env` and confirmed working length (32 chars). Anthropic/OpenRouter keys still needed from Michael before this phase can complete.
