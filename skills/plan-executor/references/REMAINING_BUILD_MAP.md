# Remaining Build Plan — Channel & Blocker Map

**Source:** `BUILD_STATE.md` (read fresh — this is a derived working map, not the authoritative list)
**Purpose:** Reference for the plan-executor skill. Maps each remaining build item to:
- its execution channel (Goose / LibreChat-direct / Michael-manual)
- its blocking prerequisite(s)
- its exit test source

**Last derived:** 14 August 2026. **Always re-read BUILD_STATE.md fresh** — this map may go stale as items complete.

---

## SESSION 10 ITEMS (in document order)

| # | Item | Channel | Blocker | Exit test source |
|---|---|---|---|---|
| 1 | Verify Docker `admin-panel`/`clickhouse` display anomaly | Goose | none | BUILD_STATE environment facts; already **VERIFIED** 13 Aug — mark complete |
| 2 | Locate LibreChat's real filesystem location | Goose | none | first Goose task at Session 10 start; needed for workspace junction |
| 3 | **Tier-1 quarantine** (master plan §10.4.2 step 0) | Michael-manual + Goose | **H3 password manager decision** (hard blocker) | master plan §10.4.2 + security audit |
| 4 | Legacy pipeline audit + decommission | Goose | Session 10 item 2 (locate) | master plan §10.4.4; covers 7 scheduled tasks |
| 5 | Workspace consolidation via NTFS junctions | Goose | **ai-workspace root path decision** (hard blocker); item 2 (locate LibreChat) | SESSION_10_WORKSPACE_PLAN.md exit test |
| 6 | Encrypted C: drive migration from `D:\Data` | Goose | items 3 (quarantine) + 4 (audit) complete first | master plan |
| 7 | Credential quarantine sweep for cleartext files found in audit | Michael-manual + Goose | item 3/4 | security audit |

## DEFERRED ITEMS (outside Session 10, parallel/ongoing)

| Item | Channel | Blocker |
|---|---|---|
| 1 | Google Drive MCP OAuth | Michael decision (preview program vs self-hosted pivot) + potentially Goose | **Michael decision UNDECIDED** |
| 2 | M365 MCP OAuth | — | **DEFERRED INDEFINITELY** (work-managed account; do not reopen unless personal account or IT consent) |
| 3 | Housekeeping cleanup | — | **COMPLETE** |
| 4 | Goose + LibreChat integration polish | — | **COMPLETE (13 Aug)** |
| 5 | Workspace consolidation | Goose | Session 10 item (see above) |
| 6 | Claude Projects migration | LibreChat-direct + Michael | none — parallel-run, ongoing, no deadline. RAG data moves to C: in Session 10 |
| 7 | Cluster 6 — Household DB agent build | LibreChat-direct (scaffold) + Goose (RAG collection, vault) + Michael (quarantine first) | **H3** + Session 10 quarantine (item 3). DO NOT PULL FORWARD |

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

| Decision | Gates | Recommendation |
|---|---|---|
| H3 — Password manager | Session 10 item 3 (quarantine); Cluster 6 | Bitwarden (CLI support, family sharing, separate from Google) |
| H4 — Sarah's access | (not a hard block for build, but a design decision) | shared-machine access (Option A), not LAN exposure |
| ai-workspace root path | Session 10 item 5 (workspace consolidation) | e.g. `C:\Users\micha\ai-workspace\` (undecided) |
| Drive MCP: preview program vs self-hosted `@aaronsb/google-workspace-mcp` | Deferred item 1 | self-hosted (works with personal Gmail, no preview enrollment) |
| LibreChat real filesystem location | Session 10 item 2+5 | first Goose task at Session 10 start |

---

*End of working map. Re-derive from BUILD_STATE.md when any item completes.*
