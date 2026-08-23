# Household — Superseded Assumptions Register

**Classification:** [IDENTITY] · **Status:** PLANNING / REFERENCE · **Task:** Household 02
**Date:** 23 August 2026
**Scope:** register planning assumptions that are now superseded, WITHOUT rewriting or deleting any
historical evidence (BUILD_STATE event log, archaeology reports, prior results remain immutable). Each
entry states the superseded assumption, why it changed, and the current canonical replacement.

---

## Register

### S1 — Native LibreChat file search as the whole-corpus design
- Superseded assumption: Conceived/written that the Household Admin agent would use native LibreChat
  `file_search` scoped to a whole `household` collection (see early INSTRUCTIONS/SCHEMA wording and the
  original master-plan x§10.4 phrasing).
- Why superseded: LibreChat v0.8.7 file search requires explicit per-file IDs and has no
  collection-wide binding; the 10-file UI limit must not be bypassed by storing 1,935 IDs in one agent
  (Cluster 6 architecture investigation). A dedicated read-only collection-wide query route + MCP tool is
  the approved path.
- Current replacement: `POST /query_collection` (rag_api) + `household-search` MCP
  `search_household_documents` -> Household Admin agent (live). See HOUSEHOLD_ADMIN_PLATFORM_CURRENT_STATE.md.

### S2 — "No MCP needed for Cluster 6"
- Superseded assumption: x§7.4 note "Cluster 6 needs no new MCP server."
- Why superseded: The live `household-search` MCP (one tool, agent-only, stdio, /query_collection-backed)
  was added and verified to satisfy whole-corpus retrieval safely. The spirit of the rule (no broad/
  dangerous MCP surface) is preserved — it is one narrow read-only tool, NOT a general tool.
- Current replacement: household-search MCP (exactly one model-facing tool). Doc 1.

### S3 — LanceDB/Ollama as the active household index
- Superseded assumption: The legacy pipeline (LanceDB `archive.lance`, nomic-embed-text via Ollama) was
  the index of record.
- Why superseded: pgvector `household` is the live index (27,803 rows / 1,935 IDs); LanceDB (113,011 rows)
  is stagnant/orphaned (Ollama not running); superseded by the live RAG/MCP platform.
- Current replacement: pgvector household + /query_collection. LanceDB to be retired under a separate
  decision post-parity. Doc 1 / Options doc.

### S4 — C: snapshot described as wholly stale (or wholly current) one-time quarantine
- Superseded assumption: C:\HouseholdDataRaw\Data was labeled a "stale one-time quarantine snapshot" (or,
  at the opposite extreme, a live mirror).
- Why superseded: Recency metadata shows it is a **partially refreshed mirror** — Drive ~near-current (to
  Aug 17), Mail current (to Aug 23), Calendar stale (to Aug 1). Neither wholly stale nor wholly current.
- Current replacement: treat C: as a partial mirror / gap-fill candidate, NOT authoritative, NOT the live
  origin (D: is authoritative). Doc 1 §6 + UNKNOWN_RESOLUTION (U3).

### S5 — Static corpus assumptions
- Superseded assumption: the household corpus was treated as a static, one-time snapshot
  (several early planning texts).
- Why superseded: Confirmed ACTIVE Google acquisition continues daily (Gmail .eml to 2026-08-23, Calendar
  .ics to 2026-08-23, rclone daily). The platform must handle continuous new intake, not a fixed set.
- Current replacement: active acquisition + governed ingestion requirement (Requirements doc B).

### S6 — Old model/provider expectations
- Superseded assumption: expectations that the Household Admin agent would run on `anthropic/claude-sonnet-5`
  via some routing, or that OpenRouter/multi-route was acceptable for [IDENTITY].
- Why superseded: Live agent is on DeepInfra direct `deepseek-ai/DeepSeek-V4-Flash-0731`; OpenRouter is
  explicitly disallowed for household-sensitive content; local embeddings mandatory.
- Current replacement: DeepInfra direct (or Anthropic direct) only for [IDENTITY]; local embeddings.
  Doc 1.

### S7 — Exact counts / "next-step" text that is now stale
- Superseded: any earlier "next step" stating the immediate action was agent creation or a different slice
  before the /query_collection route + MCP + agent existed.
- Why superseded: The Batch A (query route), Batch B (MCP), Batch C (agent) build-path completed. The
  current immediate next action is Household 02 planning review + (if approved) Paperless proof-of-fit /
  bake-off; NOT a platform install.
- Current replacement: see BUILD_STATE Header (Household Admin Platform roadmap; /query_collection next at
  the time) and this task's recommended next action. Cluster 6 delays/misreads (e.g. "embeddings 0")
  corrected by later verified results.

### S8 — "No established offsite backup needed yet"
- Superseded assumption (implicit early on) that a local-only copy sufficed.
- Why superseded: vault/D: originals and single-copy finance exports are vulnerable with no offsite copy;
  an approved encrypted offsite destination is now a requirement.
- Current replacement: Requirements doc A7/K1; backup map; UNIQUE_DATA_BACKUP_REQUIREMENTS. No transfer
  until a destination is approved (preserve-only).

## How this register is maintained
- Entries are append-only; historical docs are never edited.
- When a new assumption is superseded, append an S<n> entry pointing to its current replacement rather than
  modifying older entries.
