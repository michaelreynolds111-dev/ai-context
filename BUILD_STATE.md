# BUILD STATE

**Last updated:** 9 August 2026 (Session 9 — Cluster 6 build workstream and operational hardening backlog surfaced; scaffolds committed for household project and build-session-close skill)
**Current phase:** Phase 9 — Cutover (§13)
**Current sub-step:** §9a — Remote mobile access + STT. Deferred items 4–7 queued behind it.

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **PASSED** | All 5 checks green | 6 Aug 2026 |
| 2 — Providers | **PASSED (scope revised, v1.2)** | 6/8 checks green; 2 rescoped out | 7 Aug 2026 |
| 3 — Agents + MCP | **PASSED** | All items complete | 8 Aug 2026 |
| 4 — Skills sync | **PASSED** | All 4 exit criteria met | 8 Aug 2026 |
| 5 — Memory | **PASSED** | Native memory cross-conversation verified | 8 Aug 2026 |
| 6 — Projects/RAG | **PASSED (pattern only — Cluster 6 build outstanding)** | Pattern proven on New Build; Cluster 6 household DB still to build post-Session 10 | 8 Aug 2026 |
| 7 — Goose | **PASSED** | All 4 exit criteria met | 8 Aug 2026 |
| 8 — Validation | **PASSED** | All 6 clusters passed, security audit clean | 9 Aug 2026 |
| 9 — Cutover | IN PROGRESS | System live; working through deferred items | ongoing |
| **9a — Remote mobile access + STT** | **👉 NEXT** | See §13a exit test in master plan | — |

## Environment facts (confirmed)
- Machine: Michael-PC, Windows 11 Home 26200, i5-12400, 15.8 GB RAM
- Windows username: **micha** (not Michael — important for Windows paths)
- WSL2: Ubuntu-24.04, VERSION 2, UNIX user = michael, home = /home/michael
- Docker Desktop 29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
- git: core.autocrlf = false. Identity: michaelreynolds111-dev / michael.reynolds111@gmail.com
- Disk: C: 464 GB / FullyEncrypted. D: FullyDecrypted. D: cannot be BitLockered (confirmed).
- .wslconfig: memory=8GB, processors=6, swap=2GB
- **LibreChat v0.8.7** at ~/LibreChat — 6-container stack healthy, frontend published on host port 3080
- **Goose v41.0.0** at `C:\Users\micha\AppData\Local\Programs\Goose\`
- **Goose provider:** custom_deepinfra — `base_url: https://api.deepinfra.com`, `base_path: v1/openai/chat/completions`. 10 models.
- **Goose skills:** 7 skills at `C:\Users\micha\.config\agents\skills\`. Sync script: `C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1`
- **mcp-servers.json:** populated, commit 7331a32
- **gcloud CLI 579.0.0** installed in WSL2 Ubuntu, authenticated as michael.reynolds111@gmail.com, project librechat-504922
- **Tailscale:** installed on Windows host (version TBC). Not yet configured for LibreChat remote access — Phase 9a.
- **Docker stacks on host:** two independent Compose stacks — `librechat` (6 project containers; GitHub MCP server managed by Claude Desktop via `claude_desktop_config.json`, not a persistent container) and pre-existing `torbox-system` (7 containers, unrelated to AI build). **Anomaly to verify at Session 10 start:** the `admin-panel` container displays as `clickhouse` in Docker Desktop — does not match the expected LibreChat admin panel image. Confirm the image/tag against `docker inspect` before touching.

## Phase 8 exit test — PASSED (9 Aug 2026)

### Cluster results
| Cluster | Result | Notes |
|---|---|---|
| 1 — Sysadmin (Goose) | ✅ PASSED | Removed stray hello-world container + image autonomously; Stash stack untouched |
| 2 — Clinical (LibreChat) | ✅ PASSED | Submission-quality progress note; no tool calls; routing confirmed via network tab (DeepInfra fetch only, no external hosts) |
| 3 — Agentic MCP (LibreChat) | ✅ PASSED | Tavily + filesystem MCP both fired; min_wage_research.md confirmed on disk with full junior/apprentice rate table |
| 4 — Research (LibreChat) | ✅ PASSED | Accurate s.524 FWA analysis; Qantas TWU [2022] FCAFC 71 correctly cited and characterised |
| 5 — Persistent context (LibreChat) | ✅ PASSED | Cross-session memory working; project recalled correctly after one-time seed |
| 6 — Household Admin (LibreChat) | ✅ PASSED (tool-exclusion test only) | No tool calls fired; hard exclusions confirmed. **Full Cluster 6 build (vault, RAG collection, real-task test) still outstanding — see Deferred item 7** |

### Security audit — PASSED
- `git log -p` grep: all matches are placeholders (`changeme`), `<REDACTED>` markers, env var references, or documentation text. No real credential values in history.
- MongoDB agent inspection: `Clinical Work` and `Household Admin` both confirmed `tools: []` — hard exclusions intact.
- Memory collection: empty at DB level (v0.8.7 stores memory in agent internal state, not a top-level collection). No sensitive data exposed.

### Notes
- Cluster 5 required a one-time memory seed (project context had never been mentioned in a LibreChat conversation before). Expected and acceptable — from here forward memory carries it automatically.
- Cluster 2 routing confirmed 9 Aug 2026 via DevTools network tab: only call was `DeepInfra` fetch, 200, 189ms. No calls to OpenAI, OpenRouter, or any other external host. Routing verified clean.

## Phase 9 — Cutover (in progress)

System is live. LibreChat at `localhost:3080` + Goose are now the primary AI interface, replacing Claude Pro Desktop for daily use.

### Deferred items — status after Session 9

1. **Google Drive MCP OAuth** — ⚠️ PARKED
   - gcloud CLI 579.0.0 installed in WSL2; drive.googleapis.com + drivemcp.googleapis.com enabled on project librechat-504922.
   - librechat.yaml `drive` mcpServer block added (corrected against live LibreChat docs 9 Aug 2026 — GOTCHAS §9 original entry was stale; yaml block is now the source of truth).
   - OAuth flow completed; tokens stored; 8 Drive tools discovered by LibreChat.
   - **Blocker:** Google Workspace MCP servers require enrollment in the Developer Preview Program (`https://developers.google.com/workspace/preview`). Tool calls return permission denied for non-enrolled accounts. Program requires company name/website — awkward for personal accounts.
   - **Options when ready to revisit:** (a) apply to preview program, or (b) pivot to self-hosted `@aaronsb/google-workspace-mcp` which works with personal Gmail + standard Drive API without preview enrollment.
   - **Chrome popup gotcha:** `http://localhost:3080` must be in Chrome's allowed popups list for OAuth flows (Settings → Privacy → Pop-ups and redirects → Allowed). Already done — note for future OAuth flows on this machine.

2. **M365 MCP OAuth** — ⏭️ DEFERRED INDEFINITELY
   - Only available Microsoft account is work-managed. Work IT policy likely blocks external OAuth app connections.
   - Revisit only if a personal Microsoft account becomes available or IT consent is obtained.

3. **Housekeeping cleanup** — ✅ COMPLETE (9 Aug 2026)
   - `~/LibreChat/data-node.old-20260808` removed (1.1 MB freed)
   - `~/agent-workdir/goose_exit_test.md`, `min_wage_research.md`, `test.txt` removed
   - `ADHD Treatment Plan.md` — already absent from RAG store (cleared during Aug 7-8 MongoDB reinit); no action needed
   - `~/agent-workdir/` is now empty

4. **Goose + LibreChat integration polish** — 🆕 NEW WORKSTREAM (queued behind 9a)
   - Both tools are production-ready individually. Making them work as a coherent pair is a small, discrete workstream — not required for cutover, but high leverage for daily use.
   - **Scope:**
     - Formalise `~/agent-workdir/tasks/` and `~/agent-workdir/outputs/` as handoff folders between LibreChat (planning) and Goose (execution). Document the convention in `GOTCHAS.md` or a new `USAGE_PATTERNS.md`.
     - Create `~/agent-workdir/prompts/` as a shared reusable prompt library, referenced by path from both tools.
     - Add a "skill index" line to each LibreChat agent's system prompt listing available skills (skills auto-load in Goose but not in LibreChat).
     - Add a WSL alias `goose-task <file>` that opens Goose in `~/agent-workdir` with a task file preloaded — removes handoff friction.
     - Write down the decision rule ("thinking → LibreChat, doing → Goose") somewhere visible; codify the hard boundary that clinical content never crosses into Goose.
   - **Exit test:** Run one real task end-to-end through the plan-in-LibreChat / execute-in-Goose pattern using the new folder convention. Confirm both surfaces read/write the shared workspace cleanly.
   - **Non-goals:** No memory sharing between the two. No LibreChat↔Goose IPC. No changes to routing rules or agent tool sets.
   - **Dependencies:** None. Can run in parallel with Session 10 or slot into the post-cutover parallel-run period.

5. **Workspace consolidation** — 📋 SESSION 10
   - Consolidate scattered pre-project builds (torbox-system, Stash, downloads scanner, resource watchdog, standalone scripts, browser extensions) under a single `ai-workspace/` root using NTFS junctions, so LibreChat's filesystem MCP and Goose's developer extension can be scoped to one directory instead of a growing multi-path allowlist.
   - Full inventory, rationale, and execution brief in **`SESSION_10_WORKSPACE_PLAN.md`**.
   - **Overlaps with legacy pipeline decommission** — reconcile into one work item at Session 10 start. The `D:\Data` legacy pipeline audit and the `ai-workspace/` junction plan touch overlapping directories.

6. **Claude Projects migration** — LAST-BUT-ONE. No fixed deadline. Parallel-run validation period.
   - Pattern proven in Phase 6. Migrate remaining Claude Pro Projects into LibreChat Projects/RAG at a sustainable pace.
   - For each project: upload docs → confirm retrieval quality → mark migrated in `docs/MIGRATION_INVENTORY.md`.
   - RAG data will move to C: drive in Session 10 — migration can begin now and carry over.

7. **Cluster 6 — Household DB agent build** — 🏗️ THE BIG ONE, POST-SESSION-10
   - The Household Admin agent's *tool exclusions* were verified at Phase 8, but its actual purpose (retrieve household identifiers from a scoped RAG collection) has not been built. This is the single largest piece of remaining build work.
   - **Hard dependency:** Session 10 Tier-1 quarantine (§10.4.2 step 0) must complete first. No indexing of the household staging tree happens before every known credential file is quarantined into the password manager.
   - **Scope (per master plan §10.4):**
     - Populate `~/household-vault/{documents,identifiers,renewals.md}` from the cleaned staging tree
     - Refine `projects/household/SCHEMA.md` (scaffolded now — needs field-set matched to actual household data at build time)
     - Refine `projects/household/INSTRUCTIONS.md` (scaffolded now — behaviour rules already encoded)
     - Create `household` RAG collection with **local embeddings** — verify no outbound traffic at index time
     - Wire the collection to the `Household Admin` agent (tools already `[]` — do not change)
     - Write `skills/household-admin/SKILL.md` — method only, no values
   - **Exit test:** master plan §10.4.5 in full — every item classified, zero Tier-1 in vault, agent cites source document, agent says "not found" instead of confabulating, real household form completed end-to-end faster than by hand, `git log -p` clean for identifier patterns.
   - **Do not pull forward.** Master plan §17 warning: "It is tempting to pull the household database forward — it is the most immediately useful thing in this plan and the most concrete. Resist that."

### Session 10 (separate, planned session — book when ready)

**Blocking pre-requisites (must be resolved before Session 10 begins):**
- H3: Password manager decision (Bitwarden recommended). Tier-1 quarantine (§10.4.2 step 0) cannot start without a destination.
- H4: Sarah's access setup decision (shared-machine approach recommended over LAN exposure).
- ai-workspace root path choice (see SESSION_10_WORKSPACE_PLAN.md).

**Session 10 work items (in order):**
1. Verify Docker `admin-panel`/`clickhouse` display anomaly (quick first task; see Environment facts).
2. Locate LibreChat's real filesystem location — first Goose task at session start (needed for workspace junction step).
3. **Tier-1 quarantine** per master plan §10.4.2 step 0 — **blocking, must complete before any indexing** of the household staging tree.
4. Legacy pipeline audit and decommission — port/redesign/retire each component per §10.4.4. Covers the seven live scheduled tasks and predecessor automation (`.lancedb`, `profile.db`, gateway component, password-email/PDF readers).
5. Workspace consolidation via NTFS junctions per SESSION_10_WORKSPACE_PLAN.md (reconcile with legacy pipeline scope above).
6. Encrypted C: drive data migration from `D:\Data` (only after each scheduled task is repointed or retired).
7. Credential quarantine sweep for any cleartext files discovered during audit.

### Operational hardening — backlog (surface, no fixed deadline)

Items promised by master plan §14 and §16 but not yet built. None are blockers for cutover; each is a durability improvement. Rank and schedule after Phase 9a.

- **Backup automation** (§14.1) — MongoDB scheduled dump; `.env`/`librechat.yaml`/`docker-compose.override.yml` encrypted backup; `~/household-vault/` encrypted backup to a destination separate from the repo remote; pgvector volume backup at [IDENTITY] classification (post-Cluster 6).
- **Restore drill** (§14.1) — twice-yearly test. Needs a calendar entry and a written procedure.
- **Agent-tool drift check** — scheduled MongoDB query that alerts if `Clinical Work` or `Household Admin` gains any tool. The Phase 8 audit confirmed intact-today; drift over time is silent unless watched.
- **Memory audit schedule** (§14.4 enforcement point 2) — monthly `mongodump` of the memory collection + grep for identifier patterns.
- **Post-commit gitleaks** — weekly `gitleaks detect --source .` over full history in `ai-context/`. Complements the pre-commit hook.
- **Stack health monitoring** — `docker compose ps` health check with Tailscale-sent notification on any container not `healthy`. Currently no visibility if MongoDB dies overnight.
- **STT canary** (post Phase 9a) — weekly canned-audio POST to the DeepInfra Whisper endpoint. Detects endpoint or model-ID drift before it matters in the field.
- **Cost monitor automation** (§14.3) — weekly DeepInfra spend + cached-input hit-rate report (email or Tailscale-served dashboard).
- **Update cadence** (§14.2) — monthly reminder to `git pull` LibreChat, read release notes, `docker compose pull && up -d`.
- **Log rotation** — LibreChat + Goose logs currently unbounded.
- **Missing skills** (§16.4, §16.5) — `session-open`, `verify-before-executing`, `config-file-writer`. Optional but referenced in master plan.
- **`USAGE_PATTERNS.md`** — documents the plan-in-LibreChat / execute-in-Goose decision rule and the shared-workspace convention. Created as part of Deferred item 4.

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10.
- H4: Sarah's access — Option A (shared machine) recommended. UNDECIDED.
- Why can't D: be BitLockered? Worth pinning before Session 10.
- Drive MCP: apply to Google Developer Preview Program or pivot to self-hosted `@aaronsb/google-workspace-mcp`? UNDECIDED.
- **ai-workspace root path** — not yet decided. Resolve at Session 10 start (see SESSION_10_WORKSPACE_PLAN.md).
- **LibreChat's real filesystem location** — needed for workspace plan junction step; not yet located. First Goose task at Session 10 start.
- **Music agent** — mentioned as one of five agents built at Phase 3. Confirm it's actually used or drop from agent list (unused agents are maintenance surface for no benefit).
- **Deferred Tools verified?** — master plan §7.4 recommends enabling for the multi-tool agents (Research, Desktop Ops). Not confirmed as actually toggled on. Materially affects the 128-tool ceiling.

## Prior phase exit tests
See git history for full detail.

## NEXT STEP
**Phase 9a — Remote mobile access + STT (do this first — highest daily-use impact):**
See §13a in BACKUP_AI_MASTER_BUILD_PLAN.md for full steps and exit test.

Quick reference sequence:
1. Check Tailscale version: `tailscale version` (Windows PowerShell or system tray)
2. Enable HTTPS certs in Tailscale admin console → DNS tab
3. Install Tailscale on phone, log in to same account, confirm device appears in tailnet
4. On Windows host (PowerShell): `tailscale serve 3080`
5. Note the `.ts.net` URL printed, open it on phone — confirm LibreChat loads over HTTPS
6. Make Serve persistent: create a Windows Scheduled Task (see §13a.4 in master plan for exact steps)
7. Add STT block to `librechat.yaml` (see §13a.5 in master plan)
8. Restart LibreChat API container: in WSL2 — `cd ~/LibreChat && docker compose restart api`
9. Test mic on phone at `.ts.net` URL
10. Record exit test result in BUILD_STATE.md

**After 9a completes:** Items 4–7 in the deferred list above:
- Item 4: Goose + LibreChat integration polish (small workstream, high leverage — can run in parallel with Session 10 or post-cutover)
- Item 5: Workspace consolidation (Session 10)
- Item 6: Claude Projects migration (last-but-one, ongoing, parallel-run validation)
- Item 7: **Cluster 6 Household DB agent build** (post-Session-10 — the largest remaining piece of build work; scaffolds now in `projects/household/`)

**Session 10 (book separately, after H3+H4 decisions):** Docker anomaly verify → LibreChat filesystem locate → Tier-1 quarantine → legacy pipeline audit → workspace consolidation → C: drive migration.

## 2026-08-10 — MongoDB bind-mount data loss + fix (unscheduled, Phase 9 ops)

### What happened
After a Windows restart, LibreChat login failed with "User Not Found" for all
accounts. Root cause: MongoDB's data directory (`chat-mongodb`) was a **bind
mount** (`./data-node:/data/db`) on the Ubuntu-24.04 WSL2 filesystem. On boot,
Docker Desktop started the mongo container before the cross-distro bind mount
was fully live. Mongo saw what looked like an empty directory and initialized
a fresh WiredTiger catalog — while the real data files remained on disk,
orphaned and un-cataloged. Log showed `"Startup from clean shutdown?": true`
(not a crash — a silent re-init).

Initially suspected a Goose Phase 9a session (`docker compose down api`,
which per Compose V2 behavior tears down the whole project when given a
service arg) as the cause. Ruled out by timeline: container `Created`
timestamp (2026-08-07T23:21:46Z) predates that session, and the old catalog
(`base write gen: 10269`) was actively checkpointing as late as this
morning — the reset occurred specifically during today's restart, not
during any Goose-run command.

### Decision: accept data loss, fix root cause
User (Michael) explicitly deprioritized the old chat history and reprioritized
preventing recurrence. No forensic WiredTiger salvage was attempted.

### Fix applied (live, interactive session)
1. Confirmed via `docker inspect` + `mongosh` queries that the `LibreChat` db
   was cataloged empty (0 users) while ~30 orphaned `.wt` files sat unreferenced
   on disk — proved catalog reset, not physical data loss.
2. Took a full `sudo cp -a` backup of the pre-fix `data-node/` directory
   (permission-denied on non-sudo copy; uid 999-owned files) before any change.
   Backup at `~/LibreChat/data-node.backup-20260810-2238/` (233M).
3. Migrated MongoDB from bind mount to a **named Docker volume**:
   - `~/LibreChat/docker-compose.yml` line ~60: changed
     `- ./data-node:/data/db` → `- librechat_mongo_data:/data/db`
     (single documented exception to override-only rule — Compose cannot
     cleanly override/replace a service-level bind mount from an override
     file without risking a duplicate `/data/db` mount; confirmed via
     Docker's own docs that override lists are appended, not replaced).
   - `~/LibreChat/docker-compose.override.yml`: added `librechat_mongo_data:`
     to the existing top-level `volumes:` key (alongside `spotify_mcp_credentials:`).
   - Verified via `docker compose config` render before applying — confirmed
     exactly one `/data/db` mount, `type: volume`, before running `up`.
4. Ran `docker compose up -d mongodb`, then `docker compose up -d` for the
   full stack. Named volume created: `librechat_librechat_mongo_data`.
5. Recreated the user account via `npm run create-user` (interactive, inside
   the `api` container) since `ALLOW_REGISTRATION=false` blocks the normal
   Sign Up flow. Login confirmed working.

### Files created/changed
- `~/LibreChat/docker-compose.yml` — mongodb volume line changed (backed up
  as `docker-compose.yml.bak-<timestamp>` before edit)
- `~/LibreChat/docker-compose.override.yml` — added `librechat_mongo_data`
  to top-level volumes
- `~/LibreChat/data-node.backup-20260810-2236/` and `-2238/` — pre-fix backups
  (kept, not git-tracked, not deleted)
- `~/LibreChat/data-node/` — original bind-mount directory, left in place as
  a reference/potential future forensic-recovery source, NOT deleted

### Known follow-up, not yet fixed
- `${UID}:${GID}` in `docker-compose.yml`'s mongodb service resolves to an
  empty string (`user: ':'` in rendered config) because `UID`/`GID` aren't
  set in `.env`. Pre-existing, unrelated to this incident, low priority —
  flag for a future session.
- `~/LibreChat/data-node.backup-20260808/` — an unrelated near-empty stub
  directory discovered during investigation, predates this incident,
  harmless, not cleaned up.

### Blockers
None currently. GitHub MCP connector was unavailable for the entirety of
this session (both read and write) — this update is being pushed via the
documented WSL2 local git fallback, not the connector.

### Next step
Hand `GOOSE_TASK_PHASE_9B_MONGO_DURABILITY.md` (already created, in
`~/agent-workdir/` or wherever Michael saved it) to Goose to build:
automated daily mongodump backups (Windows Task Scheduler → WSL2, 14-day
retention, local-only), a mongodb healthcheck + `depends_on condition:
service_healthy` on the api service, and a tested restore drill against a
scratch database. GOTCHAS.md additions for the named-volume requirement and
the `docker compose down <service>` footgun are included in that task file
(Task 5) and should be committed once Goose completes it.

## 2026-08-10/11 — Admin panel access gap (follow-up to Mongo fix)

### What happened
After the MongoDB durability fix, login worked (user recreated via
`npm run create-user`, role: ADMIN confirmed in DB), but the separate
Admin Panel service (port 3000) rejected the account: "You do not have
admin privileges." LibreChat API logs showed:
  [requireCapability] Forbidden: user ... missing capability 'access:admin'

### Root cause
Admin access is gated by a `access:admin` system grant record (in the
`systemgrants` collection), not just the `role: ADMIN` field on the user
document. That grant is normally created by a first-user bootstrap routine
(seedSystemGrants) that runs as part of the real Sign Up / registration
flow. `npm run create-user` is a lower-level CLI utility that inserts
directly into the `users` collection and does not trigger this seeding —
so the account had the right role but not the underlying capability.

### Fix
1. Temporarily set ALLOW_REGISTRATION=true in ~/LibreChat/.env
2. Recreated api container: docker compose up -d --force-recreate api
   (NOT `restart` — stale bind-mount error, same class as the documented
   restart-vs-up gotcha; `up -d --force-recreate` required)
3. Deleted the CLI-created account: npm run delete-user <email>
4. Registered fresh via the actual Sign Up UI at localhost:3080 — this is
   what triggers the first-user capability seed
5. Confirmed admin panel (localhost:3000) access works
6. Set ALLOW_REGISTRATION back to false, recreated api again

### Lesson
When an account needs to be recreated on a fresh/reset database, use the
Sign Up UI for the FIRST account, not `npm run create-user` — even though
create-user correctly sets role: ADMIN, it skips the system-grant seeding
that the admin panel actually checks. create-user remains fine for
additional, non-first accounts on an already-bootstrapped instance.

### Status
Phase 9B (MongoDB durability + backup hardening) is now fully closed:
named volume in place, health-gated startup verified working (mongodb
reported Healthy during today's api recreation), automated daily backups
scheduled and restore-drill-validated, admin access restored via the
correct path, GOTCHAS.md updated (commit 2afff83 + this session's addition
below).

## 2026-08-11 — Boot orchestration fix (unscheduled, Phase 9 ops)

### What happened
After every Windows reboot the `LibreChat` API container failed to start
(exit 127). Root cause: Docker Desktop was launching via an HKCU\Run registry
key before the WSL2 bind-mount bridge was fully initialised. Docker tried to
mount `librechat.yaml` (a single-file WSL2 bind mount) before the bridge was
live — the mount path didn't exist, container create failed, exit 127. The
`restart: always` policy cannot heal a create-time OCI failure — the container
never started, so the policy never engaged.

### Fix applied
1. Removed Docker Desktop from HKCU\Run (was the uncontrolled launcher).
2. Authored `C:\Users\micha\scripts\docker-boot-orchestrator.ps1` (v3) —
   a PowerShell orchestrator that:
   - Polls WSL2 readiness before touching Docker
   - Launches Docker Desktop via Start-Process
   - Polls Docker engine until it answers (caught a 39-second gap on real boot)
   - Runs `docker compose up -d` on librechat stack (idempotent heal)
   - Waits for chat-mongodb healthy, then starts torbox-system (staggered)
   - Logs every step to `C:\Users\micha\scripts\logs\docker-boot.log`
3. Registered "Docker Boot Orchestrator" Windows Scheduled Task:
   - Trigger: logon, user micha, 60s delay
   - Action: powershell.exe -NonInteractive -WindowStyle Hidden
     -ExecutionPolicy Bypass -File docker-boot-orchestrator.ps1
   - RunLevel: Highest

### Exit test — PASSED (2026-08-11)
Post-reboot log confirmed:
- WSL2 poll fired, engine poll waited 39s (race caught and handled)
- LibreChat container: Starting → Started
- All 13 containers up across both stacks
- docker-boot.log: === Boot orchestrator complete ===

### Files created
- `C:\Users\micha\scripts\docker-boot-orchestrator.ps1` — orchestrator script
- `C:\Users\micha\scripts\logs\docker-boot.log` — runtime log (appends each boot)

### GOTCHAS additions needed
- Single-file WSL2 bind mounts fail create-time on boot races — `restart: always`
  cannot heal an OCI create failure; only `docker compose up -d` on a warm
  system does. Design boot automation around explicit `up -d`, not restart policy.
- Docker Desktop HKCU\Run entry launches Docker before WSL2 bridge is ready —
  remove it and replace with an orchestrated scheduled task that polls for
  WSL2 and engine readiness before running compose.

### Next step
Unchanged: Phase 9a — Tailscale Serve + STT (see NEXT STEP section above).
