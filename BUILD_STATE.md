# BUILD STATE

**Last updated:** 9 August 2026 (Phase 8 complete — Phases 0–8 done, Phase 9 in progress)
**Current phase:** Phase 9 — Cutover (§13)
**Current sub-step:** §13.2 — Work through deferred items in priority order (below). Claude Projects migration is last, as it is the largest and slowest-moving item.

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

### Deferred items — priority order

Work through these in the order listed. **Claude Projects migration is deliberately last** — it is the largest-scope, slowest-moving item, and migrating projects via LibreChat is itself the real-world validation of the whole system, so it benefits from a settled, fully-OAuth'd environment underneath it.

1. **Google Drive MCP OAuth** — ~30-45 min. Full steps in GOTCHAS.md §9. Needed for Research/Clinical agents to reach Drive-hosted documents.
2. **M365 MCP OAuth** — ~30-45 min. Full steps in GOTCHAS.md §9. Note the `MS365_MCP_TENANT_ID=consumers` requirement for personal MS accounts.
3. **Housekeeping cleanup (low priority, quick wins):**
   - `~/LibreChat/data-node.old-20260808` — remove via docker exec (leftover from the Aug 7-8 MongoDB reinit, see GOTCHAS §4)
   - `ADHD Treatment Plan.md` — currently in an unscoped RAG collection, needs reindexing to the correct scoped collection
   - `~/agent-workdir/goose_exit_test.md` and `min_wage_research.md` — Phase 7/8 test artefacts, safe to delete once no longer needed for reference
4. **Claude Projects migration (last, largest item)** — migrate remaining Claude Pro Projects into LibreChat's Projects/RAG feature (pattern already proven in Phase 6). This is the parallel-run validation period: as each project migrates, confirm retrieval quality matches or beats Claude Pro before considering that project's migration complete. No fixed deadline — proceed at a sustainable pace.

### Session 10 (separate, planned session — book when ready)
- Encrypted C: drive data migration from `D:\Data`
- Legacy pipeline decommission (`D:\Data`, 7 live scheduled tasks)
- Credential quarantine for any discovered cleartext files
- H3: Password manager decision (Bitwarden recommended, currently undecided)
- H4: Sarah's access setup decision (shared-machine approach recommended over LAN exposure)

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended. UNDECIDED
- Why can't D: be BitLockered? Worth pinning before Session 10.

## Prior phase exit tests
See git history for full detail.

## NEXT STEP
**Phase 9 — Cutover, deferred items, in priority order:**
1. Google Drive MCP OAuth (GOTCHAS §9)
2. M365 MCP OAuth (GOTCHAS §9)
3. Housekeeping cleanup (data-node.old, RAG reindex, test artefacts)
4. Claude Projects migration (last — largest scope, ongoing parallel-run validation)

Session 10 (separate): C: drive migration, legacy pipeline decommission, password manager + Sarah's access decisions.
