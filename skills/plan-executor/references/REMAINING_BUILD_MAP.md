# Remaining Build Plan — Channel & Blocker Map

**Source:** `BUILD_STATE.md` (read fresh — this is a derived working map, not the authoritative list)
**Purpose:** Reference for the plan-executor skill. Maps each remaining build item to:
- its execution channel (Goose / LibreChat-direct / Michael-manual)
- its blocking prerequisite(s)
- its exit test source

**Last derived:** 16 August 2026 (re-derived from BUILD_STATE.md after H3=Bitwarden decision, Build Coordinator test, GOTCHAS recovery, and edit-script model adoption)

---

## SESSION 10 ITEMS (in document order)

| # | Item | Channel | Blocker | Exit test source |
|---|---|---|---|---|
| 1 | Docker anomaly verify | — | **ALREADY DONE** (12 Aug 2026) | GOOSE_RESULT_DOCKER_ANOMALY_VERIFY.md; BUILD_STATE marks complete |
| 2 | GOTCHAS.md recovery | Goose | none (git restore from HEAD) | file size > 0; matches HEAD commit `3366d36` content |
| 3 | Commit + push outstanding work (edit-script applied) | Goose | items 1+2 complete | GOOSE_TASK_COMMIT_SESSION10.md; BUILD_STATE_EDIT_SCRIPT.md |
| 4 | **Tier-1 quarantine** (master plan §10.4.2 step 0) | Michael-manual + Goose | none — H3 resolved (Bitwarden, free tier) | master plan §10.4.2 + security audit |
| 5 | Legacy pipeline audit + decommission | Goose | none (no hard blocker) | master plan §10.4.4; covers 7 scheduled tasks |
| 6 | Workspace consolidation via NTFS junctions | Goose | **ai-workspace root path decision** (hard blocker) | SESSION_10_WORKSPACE_PLAN.md exit test |
| 7 | Encrypted C: drive migration from `D:\Data` | Goose | items 4 (quarantine) + 5 (audit) complete first | master plan |
| 8 | Credential quarantine sweep for cleartext files found in audit | Michael-manual + Goose | items 4/5 | security audit |

## DEFERRED ITEMS (outside Session 10, parallel/ongoing)

| Item | Channel | Blocker |
|---|---|---|
| 1 | Google Drive MCP OAuth | Michael decision (preview program vs self-hosted pivot) + potentially Goose | **Michael decision UNDECIDED** |
| 2 | M365 MCP OAuth | — | **DEFERRED INDEFINITELY** (work-managed account; do not reopen unless personal account or IT consent) |
| 3 | Housekeeping cleanup | — | **COMPLETE** |
| 4 | Goose + LibreChat integration polish | — | **COMPLETE (12 Aug 2026)** |
| 5 | Workspace consolidation | Goose | Session 10 item (see above) |
| 6 | Claude Projects migration | LibreChat-direct + Michael | none — parallel-run, ongoing, no deadline. RAG data moves to C: in Session 10 |
| 7 | Cluster 6 — Household DB agent build | LibreChat-direct (scaffold) + Goose (RAG collection, vault) + Michael (quarantine first) | Session 10 quarantine (item 4). DO NOT PULL FORWARD |

## OPERATIONAL HARDENING BACKLOG (in suggested order, none blocked)

| Item | Channel | Notes |
|---|---|---|
| Backup automation (§14.1) | Goose (+ Michael for .env encrypt key) | mongodump scheduled, .env/librechat.yaml encrypted backup, vault backup, pgvector volume |
| Restore drill (§14.1) | Goose + Michael (calendar entry) | needs written procedure |
| Agent-tool drift check | Goose (scheduled MongoDB query) | alerts if Clinical/Household gain any tool |
| Memory audit schedule (§14.4) | Goose | monthly mongodump + grep identifiers |
| Post-commit gitleaks | Goose | weekly `gitleaks detect --source .` |
| Stack health monitoring | Goose + Michael | docker compose ps + Tailscale notification |
| STT canary (post Phase 9a) | Goose | weekly canned-audio POST to Whisper endpoint |
| Cost monitor automation (§14.3) | Goose + Michael | weekly DeepInfra spend report |
| Update cadence (§14.2) | Michael-manual | monthly git pull + compose up -d |
| Log rotation | Goose | LibreChat + Goose logs unbounded |
| Missing skills (§16.4/§16.5) | LibreChat-direct (agent-builder) | session-open, verify-before-executing, config-file-writer |
| USAGE_PATTERNS.md reference | — | already created (Deferred item 4) |

## OPEN DECISIONS THAT GATE ITEMS (surface early, don't invent workarounds)

| Decision | Gates | Status |
|---|---|---|
| **H3 — Password manager** | Session 10 quarantine; Cluster 6 | **RESOLVED 15 Aug 2026: Bitwarden (free tier).** Account created, CLI 2026.7.0 installed, org "Azzopardi Reynolds" created, Sarah invited. Next: Priority 2 Chrome CSV import. |
| H4 — Sarah's access | (not a hard block for build, but a design decision) | UNDECIDED. Recommendation: shared-machine access (Option A), not LAN exposure. |
| ai-workspace root path | Session 10 item 6 (workspace consolidation) | UNDECIDED. Recommendation: `C:\Users\micha\ai-workspace\` |
| Drive MCP: preview program vs self-hosted `@aaronsb/google-workspace-mcp` | Deferred item 1 | UNDECIDED. Recommendation: self-hosted (works with personal Gmail, no preview enrollment). |

## RECENT SESSION OUTCOMES (16 Aug 2026) — ITEMS COMPLETED

| Item | Status | Key evidence |
|---|---|---|
| Build Coordinator agent test | ✅ PASSED | BUILD_STATE read + agent-builder process followed; session event log records full execution |
| GOTCHAS.md destruction diagnosed | Root cause confirmed | File was 0 bytes; HEAD commit `3366d36` has clean 888-line version; git restore is the fix |
| Edit-script model designed | Architecture agreed | Replaces blind `cp` BUILD_STATE replacement; state-update-guard produces edit-scripts; Goose applies + verifies |
| GOOSE_TASK_GOTCHAS_RECOVERY staged | Ready for Goose | Restores GOTCHAS.md from HEAD + deletes polluted GOTCHAS_UPDATE.md |
| GOOSE_TASK_COMMIT_SESSION10 staged | Ready for Goose | Commits BUILD_STATE_EDIT_SCRIPT + all staged files; pushes to origin/master |
| H3 decision (Option A) applied | Folded into BUILD_STATE | No standalone H3_DECISION_BITWARDEN.md; decision lives in BUILD_STATE only |

---

*End of working map. Re-derive from BUILD_STATE.md when any item completes.*
