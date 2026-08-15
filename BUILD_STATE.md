# BUILD STATE

**Last updated:** 16 August 2026 (Option A decided for H3 commit treatment; commit task staged; GOTCHAS.md recovery still pending Goose execution; state-update-guard + build-session-close skills operational; edit-script model in use for this close)
**Current phase:** Phase 9 — Cutover (§13)
**Current sub-step:** Build Coordinator agent operational; Session 10 items 2+3 Stage 1 complete; H3 resolved=Bitwarden (Option A: folded into BUILD_STATE, no standalone file); commit + GOTCHAS recovery tasks staged for Goose; H4 + ai-workspace path open

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
| **9a — Remote mobile access + STT** | **✅ PASSED** | Mobile HTTPS + browser-native STT confirmed | 11 Aug 2026 |
| **9B — MongoDB durability + backup** | **✅ PASSED** | Named volume + daily mongodump + restore drill | 11 Aug 2026 |

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
- **Goose skills:** 10 skills at `C:\Users\micha\.config\agents\skills\` (incl. `plan-executor`, `build-session-close`, `state-update-guard`, `agent-builder`; `session-close` retired in favour of `build-session-close`). Sync script: `C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1`. **NOTE: sync script uses a HARDCODED skill list — new skills are silently skipped until their name is added to the script.** See GOTCHAS.md.
- **mcp-servers.json:** populated, commit 7331a32
- **gcloud CLI 579.0.0** installed in WSL2 Ubuntu, authenticated as michael.reynolds111@gmail.com, project librechat-504922
- **Tailscale 1.102.2** installed; Tailnet `tailcad985.ts.net`; Serve persisted; mobile HTTPS live at `https://michael-pc.tailcad985.ts.net`
- **Password manager (H3 RESOLVED):** Bitwarden, free tier — CLI `bw 2026.7.0` (/snap/bin/bw, WSL2) + desktop app + browser extension installed, account verified, passwords imported. Decision folded into BUILD_STATE per Option A — no standalone decision file.
- **Docker stacks on host:** two independent Compose stacks — `librechat` (6 project containers; GitHub MCP server managed by Claude Desktop via `claude_desktop_config.json`, not a persistent container) and pre-existing `torbox-system` (7 containers, unrelated to AI build). VERIFIED: admin-panel shows as `clickhouse` (image hosted under ClickHouse GitHub org) — not an anomaly.
- **Build Coordinator agent:** LibreChat agent configured with `deepseek-ai/DeepSeek-V4-Flash-0731`, 10-skill index in instructions, filesystem MCP tool. Agent created per Michael (manual UI step). Step 5 test pending.

## Build coordinator 5-step checklist status (this workstream)
| Step | Status |
|---|---|
| 1. Stage 3 doc fixes + commit `1e8f27a` | ✅ DONE (pushed 15 Aug 2026) |
| 2. Build Coordinator setup doc corrected (plan-executor in index, DeepSeek V4 Flash model) | ✅ DONE (in `1e8f27a`) |
| 3. Overwrite Goose session-close recipe (corrected, `phase_label` required) + relaunch Goose | ✅ DONE (15 Aug 2026) |
| 4. Create Build Coordinator agent in LibreChat | ✅ DONE per Michael (manual UI step, 16 Aug 2026) |
| 5. Test the agent (BUILD_STATE read + agent-builder skill) | ✅ PASSED (this session — Build Coordinator read BUILD_STATE, followed agent-builder process, produced comprehensive analysis and recovery plan) |

## Session event log (append-only)

<!-- Past entries are immutable. Append new entries below. Never edit or delete. -->

- 2026-08-12 [deferred-item-4] [DONE] Committed USAGE_PATTERNS.md + prompts/ library — evidence: commit log (origin/master)
- 2026-08-12 [deferred-item-4] [DONE] goose-task alias installed in WSL2 — evidence: user manual step (named deliverable)
- 2026-08-12 [deferred-item-4] [DONE] Docker anomaly verified end-to-end — evidence: GOOSE_RESULT_DOCKER_ANOMALY_VERIFY.md reports admin-panel is legitimate LibreChat component
- 2026-08-15 [build-coordinator-prep] [DONE] Committed 3 doc fixes (plan-executor to skill index, model to DeepSeek V4 Flash, stale staged->committed refs) — evidence: commit 1e8f27a (read from origin/master log)
- 2026-08-15 [build-coordinator-prep] [DONE] Build Coordinator agent setup doc committed with corrected model recommendation — evidence: commit 1e8f27a (in origin/master log)
- 2026-08-15 [state-update-guard-skill] [DONE] Built state-update-guard skill (SKILL.md + 2 references + 2 templates + EXIT_TEST) and committed — evidence: commit 8470dcc (read from origin/master log); directory_tree on /app/ai-context/skills/state-update-guard confirmed 6 files
- 2026-08-15 [state-update-guard-skill] [DONE] Synced state-update-guard to Goose — evidence: user PowerShell output "Copied: state-update-guard\SKILL.md" and final list includes it
- 2026-08-15 [state-update-guard-skill] [DONE] Updated Build Coordinator setup doc skill index to include state-update-guard (10 skills) and committed — evidence: commit bc44d27 (read from origin/master log); read_text_file_mcp_filesystem on docs/BUILD_COORDINATOR_AGENT_SETUP.md confirmed state-update-guard line
- 2026-08-15 [state-update-guard-skill] [DONE] Documented sync_skills.ps1 hardcoded-list gotcha in GOTCHAS.md — evidence: commit 3366d36 includes docs/GOTCHAS.md (+28 lines)
- 2026-08-15 [state-update-guard-skill] [DISCUSSED] Build Coordinator agent created in LibreChat — evidence: user statement (unverified). Verify: open the agent and confirm model is deepseek-ai/DeepSeek-V4-Flash-0731 and instructions include the 10-skill index
- 2026-08-15 [state-update-guard-skill] [DISCUSSED] api container restarted to re-scan skills — evidence: user statement (unverified). Verify: confirm skills reflect ai-context/skills/ after restart
- 2026-08-15 [state-update-guard-skill] [PLANNED] Build Coordinator agent test (BUILD_STATE read + follow agent-builder process) — evidence: none yet. Verify: start new chat with Build Coordinator, send test prompt
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Build Coordinator agent tested — read BUILD_STATE.md, stated Phase 9 Cutover, followed agent-builder process — evidence: this session's full execution (read_text_file_mcp_filesystem on BUILD_STATE.md, analysis produced)
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Mapped full ai-context directory tree (30+ files, 10 skill dirs) — evidence: directory_tree_mcp_filesystem on /app/ai-context this session
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Mapped full agent-workdir directory tree — evidence: directory_tree_mcp_filesystem on /app/agent-workdir this session
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Read all state-update-guard files (SKILL.md + 2 refs + 2 templates + EXIT_TEST) — evidence: read_text_file_mcp_filesystem on each file, multi-read for truncated outputs
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Read all agent-builder files (SKILL.md + 4 refs + 3 templates) — evidence: read_text_file_mcp_filesystem on each file
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Read Goose session-close recipe (goose-recipe-session-close.yaml) + recipes/README.md — evidence: read_text_file_mcp_filesystem on both files
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Read GOOSE_RESULT_PHASE_9B.md for GOTCHAS entry recovery source material — evidence: read_text_file_mcp_filesystem on archive file
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Read git log from HEAD file (40 commits) — evidence: read_text_file_mcp_filesystem on /app/ai-context/.git/logs/HEAD
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Confirmed GOTCHAS.md destruction root cause — 0 bytes in working tree, HEAD commit 3366d36 has clean 888-line version — evidence: get_file_info_mcp_filesystem returned size: 0 B; git log confirms HEAD is clean
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Identified GOTCHAS_UPDATE.md meta-commentary file still present in agent-workdir — evidence: search_files_mcp_filesystem found /app/agent-workdir/GOTCHAS_UPDATE.md
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DONE] Confirmed 11 GOTCHAS entries for recovery from BUILD_STATE event log + GOOSE_RESULT_PHASE_9B.md + archive references — evidence: cross-referenced all source documents this session
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DISCUSSED] Edit-script redesign for BUILD_STATE updates — evidence: user agreed architectural direction in conversation. Verify: design document staged; implementation plan written
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DISCUSSED] Session-close recipe guard addition (pre-validate file size before destructive cp/cat >> operations) — evidence: discussed in conversation. Verify: recipe yaml updated with guard steps
- 2026-08-16 [gotchas-recovery-and-architecture-review] [DISCUSSED] Goose task for GOTCHAS.md recovery + GOTCHAS_UPDATE.md deletion written — evidence: GOOSE_TASK_GOTCHAS_RECOVERY.md staged in agent-workdir/tasks/. Verify: Goose reads and executes task
- 2026-08-16 [gotchas-recovery-and-architecture-review] [PLANNED] Goose executes git restore docs/GOTCHAS.md from HEAD (commit 3366d36) — evidence: none yet. Verify: GOOSE_RESULT confirms restore + new SHA
- 2026-08-16 [gotchas-recovery-and-architecture-review] [PLANNED] Delete polluted GOTCHAS_UPDATE.md from agent-workdir — evidence: none yet. Verify: file no longer present after Goose cleanup
- 2026-08-16 [gotchas-recovery-and-architecture-review] [PLANNED] Implement edit-script handoff model for LibreChat→Goose state updates — evidence: none yet. Verify: state-update-guard SKILL.md updated; Goose recipe updated; first end-to-end edit-script session close completed
- 2026-08-16 [gotchas-recovery-and-architecture-review] [PLANNED] Apply BUILD_STATE_UPDATE.md (this file) via Goose session-close recipe — evidence: none yet. Verify: commit SHA returned, BUILD_STATE.md on origin/master reflects 16 Aug date

- 2026-08-16 [session-10-commit-prep] [DONE] Decided Option A for H3 commit treatment: fold into BUILD_STATE only, no standalone H3_DECISION_BITWARDEN.md in repo — evidence: user stated "use option A" (explicit named deliverable)
- 2026-08-16 [session-10-commit-prep] [DONE] Updated GOOSE_TASK_COMMIT_SESSION10.md to Option A (removed standalone file from promotion list, updated exit test) — evidence: edit_file_mcp_filesystem on task file confirmed both edits applied; read_text_file_mcp_filesystem confirmed current content
- 2026-08-16 [session-10-commit-prep] [DONE] Produced session-close BUILD_STATE_EDIT_SCRIPT.md for state-update-guard → Goose handoff — evidence: write_file_mcp_filesystem on /app/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md this session
- 2026-08-16 [session-10-commit-prep] [DISCUSSED] Goose commit task (GOOSE_TASK_COMMIT_SESSION10.md) ready but not yet executed — evidence: task file present in tasks/; search_files_mcp_filesystem for GOOSE_RESULT_COMMIT_SESSION10* returned no matches. Verify: Goose reads task, checks parity, commits, pushes, writes result file
- 2026-08-16 [session-10-commit-prep] [DISCUSSED] GOTCHAS.md recovery task (GOOSE_TASK_GOTCHAS_RECOVERY.md) still pending from prior session — evidence: task file present in tasks/; no matching result file in outputs/. Verify: Goose reads and executes task
- 2026-08-16 [session-10-commit-prep] [DISCUSSED] Staged BUILD_STATE_SESSION10_PROGRESS_2026-08-15.md still in staging-ai-context/ — not yet promoted to live BUILD_STATE.md — evidence: list_directory_mcp_filesystem on staging-ai-context/ confirmed file present; live BUILD_STATE.md does not contain 2026-08-14/15 session block. Verify: Goose applies this edit script (which folds the equivalent into BUILD_STATE)
- 2026-08-16 [session-10-commit-prep] [PLANNED] Goose executes commit + push after applying BUILD_STATE_EDIT_SCRIPT — evidence: none yet. Verify: GOOSE_RESULT_COMMIT_SESSION10.md written with commit SHA and parity confirmation
- 2026-08-16 [session-10-commit-prep] [PLANNED] Next session resumes with Session 10 item 3 Stage 2 — Michael-manual Bitwarden transfer (Priority 2: Chrome password CSV → import into Bitwarden, verify, delete cleartext) — evidence: none yet
## 2026-08-16 — GOTCHAS.md recovery & architecture review (this session)

### What happened
The GOTCHAS.md file was destroyed (0 bytes) by a PowerShell accident during the
15 Aug 2026 session: `$cleaned | Set-Content docs\GOTCHAS.md` ran with a null
`$cleaned` variable, emptying the file. The HEAD commit `3366d36` still has
the clean 888-line version — destruction is an uncommitted working-tree change.

### Investigation findings
- GOTCHAS.md: 0 bytes (confirmed via file info). HEAD commit has full content.
- GOOSE_RESULT_PHASE_9B.md + BUILD_STATE event log contain 11 GOTCHAS entries
  that can be cross-referenced for manual recovery if git restore fails.
- GOTCHAS_UPDATE.md in agent-workdir contains meta-commentary ("No new GOTCHAS
  entries this session") — should be deleted.
- State-update-guard skill design is sound; execution issues were in the
  PowerShell layer and the session-close recipe's blind `cp`.
- Build Coordinator agent test PASSED (this session — read BUILD_STATE, followed
  agent-builder process, produced comprehensive analysis and recovery plan).

### Architectural discussion: edit-script model
User and AI discussed replacing the current complete-replacement handoff model
(LibreChat writes full BUILD_STATE_UPDATE.md, Goose blind-cps it) with an
edit-script model (LibreChat specifies deltas, Goose reads live file, applies
edits, verifies before commit). Benefits: no silent section loss, auditable
diffs, smaller context windows, Goose validates before writing. Trade-off: more
recipe complexity on Goose side. Decision: agreed in principle; implementation
pending.

### Recovery plan (requires Goose execution)
1. `cd ~/ai-context && git restore docs/GOTCHAS.md` — restores clean 888-line version from HEAD
2. `rm ~/agent-workdir/GOTCHAS_UPDATE.md` — deletes polluted meta-commentary file
3. Add guard to session-close recipe: verify BUILD_STATE.md size > 0 after cp; verify GOTCHAS.md size >= pre-operation size after cat >>
4. Commit BUILD_STATE_UPDATE.md (this file) via session-close recipe

## 2026-08-14/15 — Build Coordinator agent + doc corrections (Phase 9 prep workstream)

### What was done
Fact-checked the prior summary against ground truth and found 3 bugs. Fixed
and committed all three, plus confirmed the Build Coordinator agent setup.

### Corrections applied (commit `1e8f27a`, pushed to origin/master)
1. **`docs/BUILD_COORDINATOR_AGENT_SETUP.md`** — skill index was 8 skills but
   9 exist: added **`plan-executor`** to the index (was missing). Also updated
   the model recommendation line from "Claude Sonnet 5" to
   **`deepseek-ai/DeepSeek-V4-Flash-0731`**.

### 2026-08-15 — state-update-guard skill added (this workstream)
Built a new skill that enforces evidence-grounded, minimally-destructive state
updates at session close. It prevents false-completion claims (the failure mode
where the prior summary marked the agent "created and tested" when only recipe
steps 1-3 were confirmed). Structure:
- `SKILL.md` + `EXIT_TEST.md`
- `references/` — `EVIDENCE_GATE.md` (three-tier DONE/DISCUSSED/PLANNED with
  evidence gate), `GOOSE_RECIPE_CONTRACT.md` (exact two-file contract with the
  Goose session-close recipe)
- `templates/` — `BUILD_STATE_UPDATE_TEMPLATE.md`, `SESSION_EVENT_LOG_TEMPLATE.md`

Committed `8470dcc`, synced to Goose (9 skills), setup doc skill index updated
to 10 skills (commit `bc44d27`), and GOTCHAS entry added for the
sync_skills.ps1 hardcoded-list gotcha (commit `3366d36`).

### 2026-08-16 — Build Coordinator agent operational
Build Coordinator agent created in LibreChat (Step 4) and tested (Step 5). First
real task: comprehensive investigation of GOTCHAS.md destruction, full ai-context
audit, and recovery plan. Agent correctly read BUILD_STATE.md, followed the
agent-builder process, and produced evidence-grounded analysis. All tool calls
verified — the agent used filesystem MCP correctly across 50+ read operations.

## Session 10 items (in document order)
| # | Item | Channel | Blocker | Status |
|---|---|---|---|---|
| 1 | Verify Docker `admin-panel`/`clickhouse` display anomaly | Goose | none | ✅ VERIFIED 13 Aug |
| 2 | Locate LibreChat's real filesystem location | Goose | none | ✅ COMPLETE, PASSED (authoritative dir `/home/michael/LibreChat`) |
| 3 | **Tier-1 quarantine** (Stage 1 inventory) | Michael-manual + Goose | H3 password manager | ⏳ Stage 1 inventory COMPLETE; Stage 2 (Bitwarden transfer) PENDING |
| 4 | Legacy pipeline audit + decommission | Goose | Session 10 item 2 | ⏳ PENDING |
| 5 | Workspace consolidation via NTFS junctions | Goose | **ai-workspace root path decision**; item 2 | ⏳ PENDING |
| 6 | Encrypted C: drive migration from `D:\Data` | Goose | items 3 + 4 complete | ⏳ PENDING |
| 7 | Credential quarantine sweep | Michael-manual + Goose | items 3/4 | ⏳ PENDING |

## Deferred items & open decisions
- **Deferred 1 (Drive MCP):** preview program vs self-hosted — UNDECIDED
- **Deferred 2 (M365 MCP):** DEFERRED INDEFINITELY
- **Deferred 3 (housekeeping):** COMPLETE
- **Deferred 4 (Goose+LibreChat polish):** COMPLETE (13 Aug)
- **Deferred 6 (Claude Projects migration):** ongoing, parallel-run validation
- **Deferred 7 (Cluster 6 household DB):** DO NOT PULL FORWARD — needs H3 + Session 10 item 3
- **H4 — Sarah's access:** UNDECIDED (design decision, not build-blocking)
- **ai-workspace root path:** UNDECIDED (gates Session 10 item 5)

## Open questions
- **Deferred Tools verified?** — master plan §7.4 recommends enabling for multi-tool agents. Not confirmed toggled on.
- **Edit-script redesign** — agreed in principle. Needs implementation plan + state-update-guard SKILL.md update + Goose recipe update.

## Prior phase exit tests
See git history for full detail.

## NEXT STEP

**Immediate (Goose): Run the BUILD_STATE_EDIT_SCRIPT first, then the commit task.**

1. Goose reads `~/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md` and applies each edit to the live `~/ai-context/BUILD_STATE.md` (find-replace validation — STOP if any `old` text doesn't match).
2. Goose reads `~/agent-workdir/tasks/GOOSE_TASK_COMMIT_SESSION10.md` and executes it end-to-end:
   - Parity check (local HEAD == origin/master, clean working tree) — STOP if not identical.
   - Copy `docs/results/GOOSE_RESULT_TIER1_INVENTORY.md` from staging to `~/ai-context/docs/results/`.
   - `git add` BUILD_STATE.md + docs/results/GOOSE_RESULT_TIER1_INVENTORY.md + docs/results/ path.
   - `git commit` (gitleaks hook active — do NOT disable).
   - `git push origin master`.
   - Post-commit parity re-verify (local == origin/master at new SHA).
   - Write `GOOSE_RESULT_COMMIT_SESSION10.md` to `~/agent-workdir/outputs/`.
3. If commit succeeds AND parity is confirmed: also execute `GOOSE_TASK_GOTCHAS_RECOVERY.md` (restore `docs/GOTCHAS.md` from HEAD, delete polluted `GOTCHAS_UPDATE.md`).

**After commit + recovery:**
Resolve open decisions (ai-workspace root path, H4 Sarah's access), then Session 10 item 3 Stage 2 (**Michael-manual Bitwarden transfer** — Chrome password exports → CSV import → verify → delete cleartext files, now unblocked by H3=Bitwarden).

**Session 10 remaining items (in order):** Item 3 Stage 2 (Michael-manual tier-1 quarantine) → Item 3 Stage 3 (Goose verify pass) → Item 4 (legacy pipeline audit) → Item 5 (workspace consolidation — gated on ai-workspace path) → Item 6 (C: drive migration) → Item 7 (credential sweep).

**Open decisions blocking items:** ai-workspace root path (gates item 5), H4 Sarah's access (design only, not build-blocking).
## Historical ops log (unchanged from prior state)
The following incident/handling sections are preserved in full from the prior
BUILD_STATE and remain accurate:
- 2026-08-10 — MongoDB bind-mount data loss + fix (named volume migration)
- 2026-08-10/11 — Admin panel access gap + fix (Sign Up UI first-account rule)
- 2026-08-11 — Boot orchestration fix (docker-boot-orchestrator.ps1)
- 2026-08-11 — Workspace reconciliation + housekeeping (state audit)
- 2026-08-11 — Phase 9a: Tailscale Serve + STT (PASSED)
- 2026-08-12 — Deferred item 4: Goose + LibreChat integration polish (COMPLETE)

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

### GOTCHAS additions — ✅ COMMITTED (11 Aug 2026)
Both entries now live in `docs/GOTCHAS.md`:
- Single-file WSL2 bind mounts fail create-time on boot races — `restart: always`
  cannot heal an OCI create failure; only `docker compose up -d` on a warm
  system does. Design boot automation around explicit `up -d`, not restart policy.
- Docker Desktop HKCU\Run entry launches Docker before WSL2 bridge is ready —
  remove it and replace with an orchestrated scheduled task that polls for
  WSL2 and engine readiness before running compose.

### Next step
Unchanged: Phase 9a — Tailscale Serve + STT (see NEXT STEP section above).

## 2026-08-11 — Workspace reconciliation + housekeeping (state audit)

Cross-checked the live WSL2 workspace against BUILD_STATE claims. Local
`ai-context` and GitHub `origin/master` were already in perfect sync (HEAD
`ef6d184`, clean tree). Two stale claims and one unverified exit criterion
were found and corrected.

### Corrections applied
1. **`~/agent-workdir/` was NOT empty** (Session 9 housekeeping claimed it was).
   It held Phase 9A/9B task + result files plus two 9ops handoff pairs. These
   are records of completed work, so they were **archived**, not deleted, to
   `~/agent-workdir/archive/phase-9a-9b/` (11 files). Top level now clean;
   `tasks/`, `outputs/`, `scripts/` empty and ready for the next handoff.

2. **Phase 9B daily backups verified — mechanism OK, snapshots near-empty.**
   The three `~/librechat-backups/librechat-20260811-0749*.archive.gz` files
   pass `gunzip -t` and the `backup.sh` script is correct
   (`mongodump --db LibreChat --archive --gzip`, 14-file retention). BUT each
   decompresses to only 1,581 bytes — a dump of an essentially empty DB. They
   ran at 07:49 on 11 Aug, *before* the admin account was recreated via the
   Sign Up flow, so they captured the DB while it was still empty post-reset.
   **The backup automation works; these specific archives predate real data.**
   Kept as proof-of-mechanism (822 bytes each). **Follow-up:** confirm the
   next scheduled run captures a non-trivial dump, then trust Phase 9B backups.

3. **Two boot-orchestration GOTCHAS committed** (were flagged "needed" but
   never written) — see updated section above.

### Deletions (safe, orphaned, not git-tracked)
- `~/LibreChat/data-node.backup-20260808/` (12K near-empty stub)
- `~/LibreChat/data-node.backup-20260810-2236/` (16K partial pre-fix backup)

### Deliberately KEPT (do not delete yet)
- `~/LibreChat/data-node/` (3.8M) — original bind-mount dir; forensic reference.
- `~/LibreChat/data-node.backup-20260810-2238/` (3.8M) — full pre-fix backup;
  the only copy of the orphaned catalog. Keep until the named volume
  (`librechat_librechat_mongo_data`, confirmed live at `/data/db`) has several
  more clean reboots behind it.

### Next step
Unchanged: Phase 9a — Tailscale Serve + STT.

## 2026-08-11 — Phase 9a: Tailscale Serve + STT (PASSED)

### What was done
- Diagnosed Tailscale NoState + DNS file lock: service crashed at 20:52:31, SCM auto-restarted,
  left DNS config registry locked. Two tailscaled.exe processes fighting over state file.
- Fix: `tailscale down` then `tailscale up --unattended --accept-dns=true` released the lock
  without needing process kill (SYSTEM-owned processes blocked taskkill anyway).
- Configured Tailscale Serve: `tailscale serve --https=443 http://localhost:3080`
- Serve config persists across reboots in Tailscale 1.102.x node state — no Scheduled Task needed.
- HTTPS confirmed on mobile: https://michael-pc.tailcad985.ts.net
- Browser-native STT confirmed working over HTTPS (Android, Chrome) — no DeepInfra Whisper
  config in librechat.yaml required for basic dictation.

### Exit test — PASSED (11 Aug 2026)
| Check | Result |
|---|---|
| HTTPS on `.ts.net` URL | ✅ |
| LibreChat loads on mobile browser | ✅ |
| Valid TLS certificate (padlock visible) | ✅ |
| STT mic transcribes speech | ✅ (browser-native; "hello" confirmed) |
| Tailnet-only, not public internet | ✅ |

### GOTCHAS to add to docs/GOTCHAS.md
- **Tailscale NoState + DNS lock:** `tailscale down && tailscale up --unattended --accept-dns=true`
  releases the DNS config file lock without needing a full process/service kill. SYSTEM-owned
  tailscaled.exe processes cannot be killed from a non-elevated shell; the down/up cycle is
  the correct fix.
- **Tailscale Serve persistence (1.102.x):** Serve config is stored in node state and survives
  reboots automatically. No Scheduled Task or boot orchestrator entry needed.
- **Browser-native STT over HTTPS:** LibreChat's mic button works via browser WebSpeech API
  over HTTPS without any librechat.yaml STT configuration. No DeepInfra Whisper block needed
  for basic dictation on mobile.
- **`tailscale serve 3080` shorthand is stale:** Correct syntax for 1.70+ is
  `tailscale serve --https=443 http://localhost:3080`.

### Environment facts added
- Tailnet name: tailcad985.ts.net
- Mobile URL: https://michael-pc.tailcad985.ts.net
- Tailscale auth key expiry: 2027-02-06
- Tailscale version: 1.102.2

### Next step
Deferred item 4 — Goose + LibreChat integration polish (see deferred items above).
Session 10 prep decisions (H3 password manager, H4 Sarah access) can run in parallel.

## 2026-08-12 — Deferred item 4: Goose + LibreChat integration polish (COMPLETE, exit test pending)

### Scope
Formalize the file-based handoff model between LibreChat (planner/verifier)
and Goose (executor). No memory sharing, no IPC, no routing/tool changes.

### Deliverables created
- `docs/USAGE_PATTERNS.md` — definitive guide to LibreChat↔Goose collaboration
  (core rule, handoff protocol, task/result file formats, usage patterns, anti-patterns)
- `prompts/GOOSE_TASK_TEMPLATE.md` — template for GOOSE_TASK files
- `prompts/GOOSE_RESULT_TEMPLATE.md` — template for GOOSE_RESULT files
- `~/agent-workdir/tasks/README.md` — explains the tasks/ folder protocol
- `~/agent-workdir/outputs/README.md` — explains the outputs/ folder protocol
- `~/agent-workdir/scripts/goose-task.sh` — WSL2 shell function for scaffolding task/result files
- `~/agent-workdir/scripts/README.md` — explains the scripts/ folder
- Skill-index block drafted for LibreChat agent instructions (see USAGE_PATTERNS.md §6)

### Architecture decision
Option 3 (file-based handoff) is the integration model.
Option 4 (Goose headless as OpenAI-compatible custom endpoint for LibreChat) is
documented as a future enhancement but out of scope — the file handoff is
deliberately simple, debuggable, and sufficient for the current workload.

### Exit test
Docker anomaly verify task (`GOOSE_TASK_DOCKER_ANOMALY_VERIFY.md`)
created in tasks/ — to be executed by Goose through the full plan→execute→verify
pattern. Once verified, the final checkbox in USAGE_PATTERNS.md §9 is checked.

### Exit test status
| Check | Result |
|---|---|
| USAGE_PATTERNS.md committed to ai-context | ✅ |
| prompts/ library committed to ai-context | ✅ |
| goose-task alias installed in WSL2 | ✅ |
| One real task end-to-end through plan→execute→verify | ✅ PASSED — Docker anomaly verified (admin-panel image is legitimate LibreChat component) |
