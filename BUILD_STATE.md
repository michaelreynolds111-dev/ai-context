# BUILD STATE

**Last updated:** 9 August 2026 (Session 9 — Phase 9 deferred items partially complete)
**Current phase:** Phase 9 — Cutover (§13)
**Current sub-step:** §13.2 — Deferred items. Drive MCP parked (preview program gate). M365 deferred (work IT policy). Next: housekeeping cleanup.

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

## Environment facts (confirmed)
- Machine: Michael-PC, Windows 11 Home 26200, i5-12400, 15.8 GB RAM
- Windows username: **micha** (not Michael — important for Windows paths)
- WSL2: Ubuntu-24.04, VERSION 2, UNIX user = michael, home = /home/michael
- Docker Desktop 29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
- git: core.autocrlf = false. Identity: michaelreynolds111-dev / michael.reynolds111@gmail.com
- Disk: C: 464 GB / FullyEncrypted. D: FullyDecrypted. D: cannot be BitLockered (confirmed).
- .wslconfig: memory=8GB, processors=6, swap=2GB
- **LibreChat v0.8.7** at ~/LibreChat — 6-container stack healthy
- **Goose v41.0.0** at `C:\Users\micha\AppData\Local\Programs\Goose\`
- **Goose provider:** custom_deepinfra — `base_url: https://api.deepinfra.com`, `base_path: v1/openai/chat/completions`. 10 models.
- **Goose skills:** 7 skills at `C:\Users\micha\.config\agents\skills\`. Sync script: `C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1`
- **mcp-servers.json:** populated, commit 7331a32
- **gcloud CLI 579.0.0** installed in WSL2 Ubuntu, authenticated as michael.reynolds111@gmail.com, project librechat-504922

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

### Deferred items — status after Session 9

1. **Google Drive MCP OAuth** — ⚠️ PARKED
   - gcloud CLI 579.0.0 installed in WSL2; drive.googleapis.com + drivemcp.googleapis.com enabled on project librechat-504922.
   - librechat.yaml `drive` mcpServer block added (corrected against current LibreChat docs — GOTCHAS §9 original entry was stale; new entry is the source of truth).
   - OAuth flow completed successfully; tokens stored; 8 Drive tools discovered by LibreChat.
   - **Blocker:** Google Workspace MCP servers require enrollment in the Developer Preview Program (`https://developers.google.com/workspace/preview`). Tool calls return permission denied for non-enrolled accounts. Program requires company name/website — not suitable for personal accounts without workaround.
   - **Options when ready to revisit:** (a) apply to preview program anyway, or (b) pivot to self-hosted `@aaronsb/google-workspace-mcp` which works with personal Gmail + standard Drive API without preview enrollment.
   - Chrome popup blocker gotcha documented: `http://localhost:3080` must be added to Chrome's allowed popups list for OAuth flows to work (Settings → Privacy → Pop-ups and redirects → Allowed).

2. **M365 MCP OAuth** — ⏭️ DEFERRED INDEFINITELY
   - Only available Microsoft account is work-managed. Work IT policy likely blocks external OAuth app connections. Not safe to attempt without IT approval.
   - Revisit only if a personal Microsoft account becomes available or IT consent is obtained.

3. **Housekeeping cleanup** — 👉 NEXT
   - `~/LibreChat/data-node.old-20260808` — remove (leftover from Aug 7-8 MongoDB reinit, GOTCHAS §4)
   - `ADHD Treatment Plan.md` — in unscoped RAG collection, needs reindexing to correct scoped collection
   - `~/agent-workdir/goose_exit_test.md` and `min_wage_research.md` — Phase 7/8 test artefacts, safe to delete

4. **Claude Projects migration** — LAST. No fixed deadline. Parallel-run validation period.

### Session 10 (separate, planned session — book when ready)
- Encrypted C: drive data migration from `D:\Data`
- Legacy pipeline decommission (`D:\Data`, 7 live scheduled tasks)
- Credential quarantine for any discovered cleartext files
- H3: Password manager decision (Bitwarden recommended, currently undecided)
- H4: Sarah's access setup decision (shared-machine approach recommended over LAN exposure)
- **Workspace consolidation** — new item, planned in a chat-history audit session (9 Aug 2026): consolidate scattered pre-project builds (torbox-system, Stash, downloads scanner, resource watchdog, standalone scripts, browser extensions) under a single `ai-workspace/` root using NTFS junctions, so LibreChat's filesystem MCP and Goose's developer extension can be scoped to one directory instead of a growing multi-path allowlist. Full inventory, rationale, and execution brief in **`SESSION_10_WORKSPACE_PLAN.md`**. This overlaps with the "legacy pipeline decommission" item above (the resource watchdog junction covers the same `D:\Data` scheduled-task scope) — reconcile into one work item at Session 10 start, don't duplicate.

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended. UNDECIDED
- Why can't D: be BitLockered? Worth pinning before Session 10.
- Drive MCP: apply to Google Developer Preview Program (company field awkward for personal use) or pivot to self-hosted `@aaronsb/google-workspace-mcp`? UNDECIDED.
- **ai-workspace root path** — not yet decided with Michael. Resolve at Session 10 start (see SESSION_10_WORKSPACE_PLAN.md).
- **LibreChat's real filesystem location** — needed for the workspace plan's junction step; not yet located. First Goose task at Session 10 start.

## Prior phase exit tests
See git history for full detail.

## NEXT STEP
**Phase 9 — Cutover, deferred items:**
- Items 1 (Drive) and 2 (M365) parked/deferred — see status above.
- **Item 3: Housekeeping cleanup** (next active work):
  1. Remove `~/LibreChat/data-node.old-20260808`
  2. Reindex `ADHD Treatment Plan.md` to correct scoped RAG collection
  3. Delete `~/agent-workdir/goose_exit_test.md` and `min_wage_research.md`
- Item 4: Claude Projects migration (last — largest scope, ongoing parallel-run validation)

Session 10 (separate): C: drive migration, legacy pipeline decommission, password manager + Sarah's access decisions, **and workspace consolidation (see SESSION_10_WORKSPACE_PLAN.md)**.
