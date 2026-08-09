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
- **Docker stacks on host:** two independent Compose stacks — `librechat` (6 project containers + 1 GitHub-MCP container `objective_ganguly` = 7 total) and pre-existing `torbox-system` (7 containers, unrelated to AI build). **Anomaly to verify at Session 10 start:** the `admin-panel` container displays as `clickhouse` in Docker Desktop — does not match the expected LibreChat admin panel image. Confirm the image/tag against `docker inspect` before touching.

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
