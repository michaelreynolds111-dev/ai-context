# BUILD STATE

**Last updated:** 6 August 2026
**Current phase:** Phase 1 — Deploy LibreChat (§5)
**Current sub-step:** 5.1 — Clone and configure (NOT STARTED)

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **NOT STARTED** | — | — |
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
- ai-context repo: https://github.com/michaelreynolds111-dev/ai-context.git (**private, confirmed via API — verified this session**)
- **gitleaks 8.30.1** installed at ~/.local/bin/gitleaks (user-local, no sudo). On PATH via ~/.bashrc.
- **PAT stored** via git credential helper (`store`) at ~/.git-credentials, perms 600. HTTPS auth working.
- Default branch: **master** (kept deliberately — see decisions)

## Phase 0 deliverables (all committed, pushed to origin/master, commit 3b4a994)
- ~/ai-context/ — repo structure: skills/ projects/ memory/ mcp/ docs/
- ~/ai-context/README.md — repo purpose + layout + secret-scanning note
- ~/ai-context/.gitignore — per §4.4 (incl. [IDENTITY] belt-and-braces rules)
- ~/ai-context/.gitleaks.toml — default rules + custom AU identifier rules (TFN, Medicare, passport, licence)
- ~/ai-context/.git/hooks/pre-commit — blocking gitleaks scan; exports ~/.local/bin to PATH (hooks run non-login shell)
- ~/ai-context/skills/session-close/SKILL.md — first real skill (ported from robot-session-close pattern, generic)
- ~/ai-context/mcp/mcp-servers.json — stub {"mcpServers": {}}
- ~/household-vault/ — documents/ identifiers/ renewals.md. NOT a git repo, outside ai-context/ (both verified)

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
- **gitleaks over git-secrets** — 5 Aug 2026. Latest stable 8.30.1. Note: gitleaks is now feature-complete (security patches only); original author's successor tool is "Betterleaks". No action needed now; flagged for the change-trigger list.
- **gitleaks installed user-local (~/.local/bin), not /usr/local/bin** — 5 Aug 2026. Avoids sudo entirely. Consequence: git hooks run a non-login shell, so the pre-commit hook exports ~/.local/bin to PATH explicitly (learned the hard way — first exit-test run failed "gitleaks not found", fixed, re-passed).
- **Default branch left as `master`** — 5 Aug 2026. Renaming now would need a coordinated local+remote rename; no functional benefit for a single-user private repo. Deliberately not changed.
- **PAT persisted via credential.helper store** (plaintext at ~/.git-credentials, perms 600) — 5 Aug 2026. Acceptable on single-user, full-disk-encrypted box. Alternative (`cache`, timed in-memory) noted if persistence is ever unwanted.
- **PAT rotated and re-secured** — 6 Aug 2026. Original exposed token revoked at github.com/settings/tokens; fresh classic token (repo scope) issued and stored via credential.helper store at ~/.git-credentials (perms 600). Entered by Michael directly, not surfaced in chat.

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended over LAN exposure. UNDECIDED

## Blockers / follow-ups
None outstanding.

## Phase 0 exit test — result (5 Aug 2026): PASSED
- [x] `git log` shows an initial commit — 3b4a994
- [x] Private GitHub remote added and pushed — origin/master, private confirmed via API (404 unauth)
- [x] At least one real SKILL.md written and committed — session-close
- [x] mcp/mcp-servers.json exists — stub
- [x] Secret-scanning pre-commit hook installed AND demonstrated to block a dummy identifier — dummy TFN blocked via au-tfn rule, redacted
- [x] ~/household-vault/ exists, is not a git repo, is not inside ai-context/ — all verified

## NEXT STEP
Open a fresh chat in this project. Start with:
"Read BUILD_STATE.md. What phase are we on and what's the next step?"

**Phase 1 — Deploy LibreChat (§5). All commands run in the WSL2 Ubuntu shell (/home/michael).**

Before starting, [VERIFY] step: web-search the current LibreChat stable release (research says v0.8.7, 23 Jun 2026 — confirm before cloning) and confirm the credentials-generator method for CREDS_KEY / CREDS_IV.

Then:
1. §5.1 — clone LibreChat into ~ (NOT /mnt/c), cp .env.example .env
2. §5.2 — generate real CREDS_KEY, CREDS_IV, JWT_SECRET, JWT_REFRESH_SECRET; set ALLOW_REGISTRATION=true; add provider keys (DeepInfra, OpenRouter, Anthropic) — keys entered by Michael directly, never pasted into chat
3. §5.3 — create docker-compose.override.yml (mounts ai-context/skills read-only, sets DEPLOYMENT_SKILLS_DIR)
4. §5.4 — docker compose up -d, register first (admin) account, then set ALLOW_REGISTRATION=false and restart
5. §5.5 — run Phase 1 exit test (localhost:3080 loads, admin login, all 5 containers healthy, registration closed, restart preserves account)

Reminder: provider API keys are entered directly into .env inside Ubuntu by Michael — Claude does not handle key values.
