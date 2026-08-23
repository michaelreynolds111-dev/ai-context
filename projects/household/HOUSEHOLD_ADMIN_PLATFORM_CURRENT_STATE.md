# Household Administration Platform — Current State

**Classification:** [IDENTITY] · **Cluster:** 6 (household administration) · **Status:** PLANNING
**Task:** Household 02 · **Date:** 23 August 2026
**Scope:** canonical synthesis of the accepted current-system evidence ONLY. No platform installed,
trialled, selected, or mutated. Evidence classes: CONFIRMED_LIVE_FACT / VERIFIED_HISTORICAL_FACT /
MICHAEL_DECISION / DESIGN_REQUIREMENT / ARCHITECTURE_HYPOTHESIS / OPEN_DECISION / UNRESOLVED_UNKNOWN /
SUPERSEDED_ASSUMPTION. No hypothesis is presented as a live fact.

---

## 1. Purpose

This document records the authoritative current state of the household system as the input to the
Household Administration Platform planning foundation. It reconciles the accepted archaeology, prior
verified results, and the live metadata re-verified during Household 02. It is a snapshot used to derive
requirements (Requirements doc) and compare architecture options (Options doc) — it is not a decision
record and not an implementation mandate.

## 2. Active acquisition (CONFIRMED_LIVE_FACT)

- Google Apps Scripts export to Google Drive:
  - `gmail_forward_sync.gs` (~03:00 daily) — writes each message as a byte-identical `.eml` to Drive
    `Mail/messages/` and extracts attachments to `Mail/attachments/`, with per-run safety cap (~200
    threads), dedup by filename, checkpoint advance only on success. ACTIVE to 2026-08-23.
  - `calendar_sync.gs` (~04:00 daily) — re-exports rolling window (30 days past / 180 days future) to
    Drive `Calendar/` as `.ics`, marking deletions `_CANCELLED.ics`. ACTIVE to 2026-08-23.
- One-way rclone `copy` (never deletes local) pulls approved Drive/Calendar content daily to `D:\Data`
  via `rclone_sync.ps1`, now the sole acquisition task (`rclone Drive Sync`, enabled, 05:00). Local
  changes do not propagate upstream; source deletions do not delete the local retained mirror.
- `D:\Data` is the **active acquisition landing zone and retained source mirror** (`D:\Data\Michael\`
  Mail 24,356 .eml / Calendar / Drive mirror; `D:\Data\Sarah\` Calendar, Drive, Mail 9,913 .eml).
- Ops current: rclone log last run 2026-08-23 05:05; Michael gdrive path "nothing to transfer" (up to
  date). `ArchiveDailySync` disabled (Task 01 M1). `daily_sync.ps1` is acquisition-only (keep_convert +
  embed_batch steps removed — SUPERSEDED via legacy pipeline).

## 3. Current live retrieval stack (CONFIRMED_LIVE_FACT)

```text
LibreChat Household Admin agent
  -> search_household_documents  (household-search MCP, stdio, agent-only, chatMenu:false)
  -> POST /query_collection      (rag_api, pinned image, all-MiniLM-L6-v2)
  -> household pgvector collection (identity-filtered via JWT -> cmetadata.user_id)
```

- `household` pgvector: **27,803 rows / 1,935 file IDs**; `testcollection`: 1,374 rows (isolated).
- MongoDB `files`: 2,003 (household subset 1,935); agents 5; users 1 (one identity scope aligned to
  MICHAEL_LIBRECHAT_USER).
- `/query_collection` fixed-scope read-only; identity derived server-side from JWT; no caller-supplied
  collection/user/SQL/path; bounded results; sanitized logging. Pinned rag_api image retained; `/query`,
  `/query_multiple`, `/ids`, `/embed`, delete contracts preserved.
- `household-search` MCP exposes exactly one tool `search_household_documents` (query, max_results<=10);
  no resources/prompts/write tools; credential/protected-material queries rejected.
- Household Admin agent: 1, DeepInfra direct, memory disabled, file attachments 0; holds the canonical
  INSTRUCTIONS.md + household-admin skill (clarification-first, minimum disclosure, subject separation).
- LibreChat stack: 6 healthy containers (LibreChat, rag_api, chat-mongodb, vectordb, admin-panel,
  chat-meilisearch). RAG `/health` UP.
- household-vault: **17G / 6,077 docs**, curated preserve-first archive; identifiers/profile_facts.md;
  renewals.md (empty); NOT a git repo; additive copy of D: originals (estate lane separated).

## 4. Current gaps (VERIFIED_HISTORICAL_FACT + DESIGN_REQUIREMENT)

1. Daily acquisition is not connected to governed modern ingestion (no inbox/review pipeline to the index
   or ledger) — DESIGN_REQUIREMENT.
2. Current RAG extraction is native-text only (pdfjs/mammoth); ~10–15% of current-household docs lack OCR
   content; 132 zero-text unindexed files (105 PDF / 25 DOCX / 2 PPT); 879 indexed files with <=3 chunks;
   ~72% of indexed files lack page metadata (chunk-density estimate, not page-exact) — VERIFIED.
3. Legacy OCR (OCRmyPDF+Tesseract) was one-off and destructive-in-place (done 2026-06-24, 4,578 files);
   it is a reusable text asset but must not be re-run destructively — VERIFIED_HISTORICAL_FACT +
   REQUIREMENT (no original overwrite).
4. No canonical crosswalk spans source -> vault -> lifecycle record -> LibreChat file_id -> pgvector
   file_id -> version -> ledger — DESIGN_REQUIREMENT (doc 3).
5. No subject/provenance field separates CURRENT_HOUSEHOLD / estate / other-person / Seddon / archive /
   general-reference / unknown at query time — the highest-priority safety gap (min-disclosure evidence)
   — VERIFIED + DESIGN_REQUIREMENT (doc 3).
6. No current/superseded lifecycle model — DESIGN_REQUIREMENT.
7. No mature document inbox / review / version workflow — DESIGN_REQUIREMENT.
8. No verified household ledger (renewals.md empty; profile.db orphaned but mirrored) — DESIGN_REQUIREMENT.
9. No Actual Budget installation or transaction reconciliation (finance corpus OFX/CSV/XLSX present but
   not imported) — DESIGN_REQUIREMENT (doc 7).
10. No approved offsite/encrypted backup destination for vault originals / D: originals / local logical
    dumps (pgvector dump local-only) — DESIGN_REQUIREMENT (docs 2 continuity/operations).

## 5. Backup / recovery status (CONFIRMED_LIVE_FACT + VERIFIED_HISTORICAL_FACT)

- MongoDB: daily mongodump (15 kept), restore drill proven.
- pgvector: logical `pg_dump -Fc` created Task 01 (74,483,966 B, sha256 1e540f...); isolated restore
  drill PASSED (household 27,803 / testcollection 1,374 identical, drill DB dropped). Local-only.
- RAG images: pinned image + rollback config captured.
- vault / D:\Data / finance originals: NO offsite/cloud copy. Single-copy finance (OFX, Reynolds
  snapshots, lease docs) uniqueness risk recorded.
- No household continuity/runbook document exists yet — DESIGN_REQUIREMENT (doc 2 continuity).

## 6. Residual / legacy components (VERIFIED_HISTORICAL_FACT + SUPERSEDED_ASSUMPTION)

- Legacy LanceDB index (113,011 rows) stagnant/orphaned (Ollama not running); superseded by pgvector.
- archive_gateway.py / profile.db read path orphaned.
- Ollama: installed with a Startup shortcut and a 261.6 MB model, but NO service/process running —
  orphaned legacy embed runtime (not active, not to be started/queried).
- Legacy Gemini daily/weekly briefings still run (informational; overlap Household Admin purpose) —
  SUPERSEDED_ASSUMPTION re "no other reader"; to be retired/re-purposed under a separate decision.
- C: snapshot: partially refreshed mirror (Drive ~near-current to Aug 17; Mail current; Calendar stale
  to Aug 1) — SUPERSEDED "wholly stale snapshot" assumption; not authoritative.
- `ai-net` Docker network: created 2026-07-04, no labels, no containers attached — low-priority residue
  (UNRESOLVED_UNKNOWN, retained).
- `ai-context-removed/new-build-corpus-20260814`: stash-recommendation source corpus (18 files, 324K),
  not household — retained residue.
- `projects/Power App/`: Microsoft Power Automate Flow export (62 files, 560K, untracked) — separate,
  unrelated to household platform; preserved, not promoted.

## 7. Task 01 closure (CONFIRMED_LIVE_FACT, re-verified)

- M1: `ArchiveDailySync` disabled; `rclone Drive Sync` enabled and points directly to
  `D:\Data\rclone_sync.ps1`; `daily_sync.ps1` acquisition-only. PASS.
- M2: RcloneView RC daemon running; `127.0.0.1:5582` auth-required (operational). Credential rotated to
  Bitwarden per Michael; credential not read/printed. PASS.
- M3: Passwords.docx absent from pgvector (0) and MongoDB (0); Bitwarden preservation confirmed by
  Michael; final source quarantine remains a SEPARATE controlled action (not performed in Household 02
  per scope lock). PASS-with-explicit-deferral.
- pgvector logical backup + isolated-restore evidence present. PASS.

## 8. Unknowns most relevant to planning (see operational UNKNOWN_RESOLUTION.md)

- U4 (gdrive-sarah remote transfer): NO positive local log evidence of active transfer in ~3 weeks;
  Michael acquisition healthy; Sarah remote retention = LOW-confidence unknown; defines
  stalled-source/per-remote-success-logging requirement. UNRESOLVED_UNKNOWN (no Google contact).
- U12 (full set of out-of-scope indexed records): cannot be proven from current metadata — defined as an
  implementation/proof-of-fit requirement (subject_scope + hard filter). Precise limitation.
- U8 (`ai-net`) low priority; U2 stash corpus retained; U3 C: mirror partially-refreshed; U6 Ollama
  orphaned; U10 duplicate task resolved (M1); U11 Power App preserved.

## 9. Preserve-first foundation (VERIFIED_HISTORICAL_FACT + MICHAEL_DECISION)

Items retained unchanged as the document-intelligence foundation: household-vault; pgvector household +
testcollection; /query_collection + pinned image; household-search MCP + search_household_documents;
Household Admin agent + canonical instructions; MongoDB file-registry (1,935 household); one identity
scope; gmail/calendar Apps Scripts; rclone acquisition; Mongo backup + Docker Boot Orchestrator; cluster6
manifests/checkpoints/failure records/rollback. Verified all counts/digests unchanged this task.

## 10. Evidence ledger (this document)

- CONFIRMED_LIVE_FACT: all §2, §3, §5 (Mongo/pgvector/health), §7 (re-verified this task).
- VERIFIED_HISTORICAL_FACT: legacy pipeline, OCR history, backup map, §6 legacy components.
- MICHAEL_DECISION: Household Admin Platform is the approved target; Bitwarden sole secrets layer;
  Actual Budget future option; preserve-existing-work requirement.
- DESIGN_REQUIREMENT: all §4 gaps and §5 continuity/backup items.
- SUPERSEDED_ASSUMPTION: whole-corpus native file_search; no-MCP; LanceDB/Ollama active index; C: wholly
  stale; static corpus; stale model/provider expectations (see Superseded doc).
- UNRESOLVED_UNKNOWN: U4, U12 (precisely bounded), U8 (low), gdrive token freshness (out of scope).
