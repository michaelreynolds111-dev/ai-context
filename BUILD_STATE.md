# BUILD STATE

**Last updated:** 9 August 2026 (Session 9 — Phase 9a detail expanded)
**Current phase:** Phase 9 — Cutover (§13)
**Current sub-step:** §9a — Remote mobile access + STT. Next after that: Claude Projects migration (item 4).

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
| 6 — Projects/RAG | **PASSED** | Pattern proven, scope decision made | 8 Aug 2026 |
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

## Phase 8 exit test — PASSED (9 Aug 2026)

### Cluster results
| Cluster | Result | Notes |
|---|---|---|
| 1 — Sysadmin (Goose) | ✅ PASSED | Removed stray hello-world container + image autonomously; Stash stack untouched |
| 2 — Clinical (LibreChat) | ✅ PASSED | Submission-quality progress note; no tool calls; routing confirmed via network tab (DeepInfra fetch only, no external hosts) |
| 3 — Agentic MCP (LibreChat) | ✅ PASSED | Tavily + filesystem MCP both fired; min_wage_research.md confirmed on disk with full junior/apprentice rate table |
| 4 — Research (LibreChat) | ✅ PASSED | Accurate s.524 FWA analysis; Qantas TWU [2022] FCAFC 71 correctly cited and characterised |
| 5 — Persistent context (LibreChat) | ✅ PASSED | Cross-session memory working; project recalled correctly after one-time seed |
| 6 — Household Admin (LibreChat) | ✅ PASSED | No tool calls fired; hard exclusions confirmed |

### Security audit — PASSED
- `git log -p` grep: all matches are placeholders (`changeme`), `<REDACTED>` markers, env var references, or documentation text. No real credential values in history.
- MongoDB agent inspection: `Clinical Work` and `Household Admin` both confirmed `tools: []` — hard exclusions intact.
- Memory collection: empty at DB level (v0.8.7 stores memory in agent internal state, not a top-level collection). No sensitive data exposed.

### Notes
- Cluster 5 required a one-time memory seed (project context had never been mentioned in a LibreChat conversation before). Expected and acceptable — from here forward memory carries it automatically.
- Cluster 2 routing confirmed 9 Aug 2026 via DevTools network tab: only call was `DeepInfra` fetch, 200, 189ms. No calls to OpenAI, OpenRouter, or any other external host. Routing verified clean.

## Phase 9 — Cutover (in progress)

System is live. LibreChat at `localhost:3080` + Goose are now the primary AI interface, replacing Claude Pro Desktop for daily use.

### Deferred items — final status after Session 9

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

4. **Claude Projects migration** — ⏳ AFTER Phase 9a
   - Pattern proven in Phase 6. Migrate remaining Claude Pro Projects into LibreChat Projects/RAG at a sustainable pace.
   - For each project: upload docs → confirm retrieval quality → mark migrated.
   - RAG data will move to C: drive in Session 10 — migration can begin now and carry over.

### Session 10 (separate, planned session — book when ready)
- Encrypted C: drive data migration from `D:\Data`
- Legacy pipeline decommission (`D:\Data`, 7 live scheduled tasks)
- Credential quarantine for any discovered cleartext files
- H3: Password manager decision (Bitwarden recommended, currently undecided)
- H4: Sarah's access setup decision (shared-machine approach recommended over LAN exposure, undecided)

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended. UNDECIDED
- Why can't D: be BitLockered? Worth pinning before Session 10.
- Drive MCP: apply to Google Developer Preview Program or pivot to self-hosted `@aaronsb/google-workspace-mcp`? UNDECIDED.

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

**After 9a completes:** Phase 9 Claude Projects migration (item 4) — no fixed deadline, parallel-run validation.

**Session 10 (book separately):** C: drive migration, legacy pipeline decommission, password manager + Sarah's access decisions.
