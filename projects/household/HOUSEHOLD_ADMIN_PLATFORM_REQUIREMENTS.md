# Household Administration Platform — Software-Independent Requirements

**Classification:** [IDENTITY] · **Cluster:** 6 · **Status:** PLANNING
**Task:** Household 02 · **Date:** 23 August 2026
**Scope:** complete, software-independent functional / safety / continuity / recovery / operational
requirements for the Household Administration Platform. These requirements are deliberately
**platform-agnostic** — they must hold whether the implementation is Paperless-centred, custom-retrofit,
or a hybrid (see Options doc). They are DESIGN_REQUIREMENT statements unless marked otherwise. No
implementation implied; no platform selected.

---

## A. Evidence preservation

- A1. Immutable originals: preserve original acquired documents byte-identical (sha256 recorded); never
  destructively modify or overwrite an original by OCR/extraction/conversion.
- A2. Derivative lineage: every OCR text layer, conversion, thumbnail, or extracted derivative records
  its source original (source_sha256 / canonical_document_id) as a derived artefact, never severing the
  link.
- A3. Recoverability without AI/application: originals and their metadata must be recoverable/exportable
  via plain filesystem/standard formats without the AI chat/agent/RAG/application running.
- A4. Export: complete (documents + metadata + OCR) export to standard open formats; round-trip restore
  tested.
- A5. Checksum validation: periodic hash verification of the preserved set; automated alert on drift.
- A6. Physical-original location (where useful): optional serial/location field links a scan to any
  physical paper original and its archive position.
- A7. Retention / destruction approval: retention class + expiry per record; destruction requires an
  explicit approval event and is logged; no silent/unreviewed deletion.

## B. Acquisition and freshness

- B1. Intake sources: Google Gmail (messages + attachments), Google Calendar, Google Drive, local/
  manual/scanner, and future structured intake; each tracked per source.
- B2. Least privilege: acquisition uses scoped, non-elevated, rotation-capable credentials; token/config
  access restricted to Michael + system context (rclone.conf ACL already restricted; keep it that way).
- B3. Incremental checkpoints: per-source checkpoint persists; only new/changed items are fetched; safe
  re-run.
- B4. No upstream mutation: local layer never writes, edits, or deletes upstream Google content (rclone
  `copy`, never `sync`/`delete` from local; Apps Scripts never delete).
- B5. Stalled-source detection: per-remote success is logged explicitly; a silent no-run/no-output is
  surfaced as an alert (addresses U4 sarah-remote observability gap).
- B6. New/changed/renamed/deleted-at-source states: represent each explicitly in lifecycle; deleted-at-
  source is recorded as superseded/historical, not silently propagated.
- B7. Duplicate prevention: content-hash or canonical_id based de-duplication at intake; review queue for
  near-duplicates.
- B8. Expected-document detection: flag missing expected records (e.g., a monthly bill not yet arrived)
  against the renewals/recurring schedule.

## C. OCR and extraction

- C1. Local-only by default: OCR/extraction run locally (no hosted OCR of identity/clinical material);
  local embeddings remain mandatory for [IDENTITY] (§6.3 / §14.4 of master plan).
- C2. Native extraction first: prefer embedded text (PDF text layer, DOCX via mammoth) before OCR.
- C3. OCR candidates: route zero-text/low-text files to OCR; identify candidate sets (target the 132
  zero-text + 138 low-row PDFs first, then low-row DOCX/PPTX) via a separate local OCR worker, NOT in the
  live rag_api/api container.
- C4. Office/email conversion: DOCX/XLSX/PPTX/`.eml` (+ attachments) decode to searchable text/fields.
- C5. Table/layout needs: preserve tables/invoices layout for deterministic extraction where needed.
- C6. Confidence/quality signals: OCR/extraction outputs carry confidence/quality metadata; low-confidence
  goes to review, not silence.
- C7. Failure/review queue: failed extraction creates a review item (never a silent or partial-as-verified
  record).
- C8. No original overwrite: OCR writes NEW derivative text/artefacts; originals remain byte-identical
  (the legacy ocr_batch pipeline was destructive-in-place and must not be re-run that way).

## D. Document lifecycle

- D1. Inbox: an unprocessed/review inbox for newly acquired documents.
- D2. Correspondents: normalized correspondent/provider per document (insurer, bank, government agency,
  utility, school, etc.).
- D3. Document types: a managed taxonomy of document types (bill, statement, policy, certificate, lease,
  rego, renewal notice, letter, scan, email, etc.).
- D4. Tags: free + structured tags.
- D5. Custom fields: date fields (issue, effective, due, expiry), amounts, account references (as
  metadata, never Tier-1 values).
- D6. Subject/provenance: subject_scope + provenance (see doc 3) to separate CURRENT_HOUSEHOLD / estate /
  other-person / Seddon / archive / general-reference / unknown.
- D7. Dates: request/issue/effective/billing-period/due/expiry/review dates tracked per document.
- D8. Versions: version identity (current_version_id) with immutable version history.
- D9. Supersession: current/superseded linkage (supersedes_document_id); a superseded doc does not
  generate duplicate obligations/reminders.
- D10. Saved views: reusable filtered views (renewals due, unverified, per provider, etc.).
- D11. Workflows: simple state workflows (inbox -> review -> verified -> archived/superseded) with
  scheduled triggers where useful; prefer native over a bespoke orchestrator (native before n8n).
- D12. Physical archive reference: link to paper storage location/serial where kept.

## E. Retrieval

- E1. Exact/full-text: byte/full-text search over native + OCR text.
- E2. Metadata filtering: filter by document type, provider, subject_scope, date, version, retention.
- E3. Semantic retrieval: keep the existing pgvector semantic path (or its successor) for conceptual
  search where it adds value.
- E4. Latest/current selection: default to newest/current version; surface superseded explicitly.
- E5. Citations: every returned value cites its source document (filename + date).
- E6. Multi-document synthesis: grounded synthesis with per-fact source attribution.
- E7. Not-found: honest "not found" rather than inference/confabulation.
- E8. Subject isolation: CURRENT_HOUSEHOLD is the hard default; estate/other/Seddon require an explicit
  separate subject selector.
- E9. Minimum disclosure: return only the minimum evidence for the explicit request; no unsolicited
  cross-domain/inventory dumps.
- E10. Performance: bounded latency for normal retrieval.

## F. Verified household intelligence

- F1. Exact facts: verified facts source-ground to a document; stored with verification_state.
- F2. Source links: every fact carries source_file_id + calculation method.
- F3. Deterministic calculation: averages, totals, trends computed deterministically from verified values
  (no model estimation).
- F4. Verification state: DISCOVERED/QUARANTINED/EXTRACTED_CANDIDATE/VALIDATION_FAILED/AWAITING_REVIEW/
  VERIFIED/DISPUTED/SUPERSEDED/ARCHIVED (full machine in doc 3).
- F5. Conflicts: surface conflicting values for review, never auto-pick.
- F6. Stale facts: flag facts whose source is superseded or expired.
- F7. Price/obligation change detection: detect amount changes between versions/periods; prompt review.
- F8. Review queue: unverified/conflicted/stale-fact items surface to a review list.

## G. Obligations and reminders

- G1. Due-date / renewal-date / notice-deadline / review-date tracking per obligation.
- G2. Retention expiry + destruction approval.
- G3. Claims/refunds awaiting action (e.g., a paid-but-cancelled service) tracked.
- G4. Missing expected document detection (ties to B8).
- G5. Concise notifications: in-app first; email/push only after dates/ownership verified.

## H. Controlled production

- H1. Inspect template: read a blank/approved template and list its fields.
- H2. Map fields: map each field to a verified source fact.
- H3. Preview source/confidence: show value + source + confidence + calculation before any generation.
- H4. Explicit approval: require explicit Michael approval before creating output.
- H5. Create a new copy: output is a NEW file with a new name; original template + source docs untouched.
- H6. No autonomous submission: the system never submits forms, emails providers, or transacts.
- H7. Audit: record tools, sources, values, and approvals per generated document.

## I. Finance and Actual Budget (see also Actual Budget doc)

- I1. Account/category mapping (seeded by the existing Bank Statement Analysis/Spending Summary).
- I2. OFX/CSV import with predictable normalization shape.
- I3. Duplicate handling (dedup by transaction id + amount/date).
- I4. Transaction provenance: each transaction carries its source file (document source id).
- I5. Document obligation vs actual payment reconciliation as a separate linked process.
- I6. Unmatched bills vs transactions surfaced.
- I7. Transfers handled (not misclassified).
- I8. Budgeting and cash flow as Actual Budget capability (future).
- I9. No bank credential exposure; no agent write access to transaction data initially.

## J. Continuity

- J1. Provider and contact directory (names only; no credentials).
- J2. Responsibilities map (who holds what).
- J3. Document locations (vault, D:, lifecycle, index) described generically.
- J4. Renewal calendar (the up-to-date renewals.md / obligations view).
- J5. Bitwarden item-name pointers only — never secrets in runbooks.
- J6. Backup/recovery instructions tested (restore drill cadence).
- J7. First-day/week/month runbook for successors/household continuity.
- J8. Redacted printable pack (pointers, no sensitive values).
- J9. Successor access controls documented.

## K. Operations and complexity

- K1. Backups and restore drills: scheduled, tested (Mongo daily done; add pgvector + vault/offsite).
- K2. Health monitoring: container/service health (6 LibreChat containers healthy; monitor front door of
  any future worker).
- K3. Resource envelope: fit within the machine envelope (i5-12400, ~16 GB RAM, WSL2 8 GB / 6 procs);
  avoid open-ended heavy services (e.g., standalone embedding/budget/LanceDB without a retained worker).
- K4. Update cadence: track platform/image updates; pin what must stay reproducible.
- K5. Rollback: every change carries a tested rollback path (as done for /query_collection and MCP).
- K6. Export: full system export available.
- K7. No duplicate control planes: exactly one acquisition task, one index, one ledger, one secrets
  authority; retire legacy duplicates (daily_sync double-trigger resolved; LanceDB stop; briefings
  rationalize).
- K8. New-component rule: every new service must either retire custom complexity or provide a distinct
  capability (from the Brainstorm research — MICHAEL_DECISION/DESIGN_REQUIREMENT).

## Evidence ledger
- All A-K are DESIGN_REQUIREMENT unless noted (B2/C1 reference master-plan rules — VERIFIED_HISTORICAL_FACT;
  K8 references Brainstorm — MICHAEL_DECISION). No implementation performed.
