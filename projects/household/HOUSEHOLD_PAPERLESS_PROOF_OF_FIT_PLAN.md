# Household Paperless-ngx — Copy-Safe Proof-of-Fit Plan

**Classification:** [IDENTITY] · **Status:** PLANNING · **Task:** Household 02
**Date:** 23 August 2026
**Scope:** a concrete, executable, **copy-safe** future plan for an isolated Paperless-ngx trial using
copies of approximately 100-200 approved documents. This is a PLAN for a separately-approved future
task. **Paperless is NOT installed or trialled here.** `copy-safe` means: everything uses copies; the
live vault/index/MCP/agent/source are never touched; full rollback is pre-captured.

---

## 0. Purpose
Determine, with objective evidence, whether a Paperless-ngx document-management layer adds genuine
lifecycle/OCR/review value over the current stack **for this household**, while rigorously proving it
preserves original provenance, file IDs, and canonical identity (doc 3). If it does not prove out, the
custom-retrofit (Option B) remains the fallback.

## 1. Sample requirements (100-200 decoded copies)
Assemble a representative COPY set drawn from approved, non-protected, current-household documents
(no credentials, no Seddon, no estate/deceased-family, no protected records):
- Native PDFs (text-layer present).
- Scanned/image-only PDFs (no text layer — OCR candidates).
- Images (JPEG/PNG/TIFF scans).
- DOCX / Office files.
- `.eml` and their attachments (email + attachment relationships).
- Utility bills; insurance documents; vehicle/rego; Maxxia/lease documents; government/correspondence;
  renewal/date documents.
- Deliberate duplicates; versions/amendments; zero-text and low-chunk (OCR-gap) samples.
- Synthetic **provenance-separation fixtures** (clearly-labelled synthetic rows in OTHER_PERSON and
  GENERAL_REFERENCE scopes) to test subject isolation on copies — never real estate/Seddon content.
- Each sample carries a known source_sha256 + canonical-ish identity + expected answers for bake-off.

## 2. Environment / isolation
- All copies live in an isolated scratch tree (e.g. `~/agent-workdir/household-proof-of-fit/`), NOT the
  vault or D: originals.
- Paperless runs as an isolated throwaway Docker container set (app + PostgreSQL + Redis + broker) with
  its own volume, no published host port (internal only), on the existing WSL2/Docker Desktop — removable.
- The live LibreChat stack, pgvector, MCP, Household Admin, vault, D:, and acquisition are **untouched**.
- Local-only processing (no cloud OCR of identity content).

## 3. Tests to execute (copy-safe)
1. **Byte-identical original preservation** — original file bytes/hash unchanged after ingestion.
2. **Archival + OCR derivatives** — derivatives created, originals intact (no overwrite).
3. **OCR text and field quality** — measured on scanned/zero-text samples (compare to known text).
4. **Email ingest** — `.eml` + attachment relationships preserved and retrievable.
5. **Duplicate / version behaviour** — near-dup and amended-bill handling; current vs superseded.
6. **Correspondents / document types / tags / custom fields** — how well they model our taxonomy.
7. **Subject scope** — can subject_scope be represented and used to isolate current-household vs
   other/general fixtures (no leakage across scopes).
8. **Current/superseded state** — model and filter.
9. **Inbox and review** — unprocessed/review workflow.
10. **Custom dates** — issue/due/expiry/review date fields.
11. **Workflows and scheduled triggers** — simple state workflows / scheduled OCR or retention triggers.
12. **Saved views** — reusable filtered views.
13. **API** — REST API for ingest/query/export; auth model.
14. **Export and restore** — full exporter round-trip.
15. **Filesystem recoverability** — can originals + metadata be recovered without Paperless running.
16. **Physical archive serial/location** — custom field linkage.
17. **CPU/RAM/disk/time/admin burden** — measured on i5-12400 (~16 GB RAM envelope).
18. **Local-only processing** — confirm no cloud/external OCR call for identity content.
19. **Teardown and rollback** — stop/remove the throwaway stack; originals + vault + live index verified
    unchanged; copies deleted.

## 4. Backup / isolation guarantees
- Pre-trial: capture baseline of vault, pgvector, MongoDB, D: originals, container list; record hashes.
- During trial: only copies and the isolated Paperless volume change.
- Post-trial teardown: remove throwaway containers/volume; re-verify baseline unchanged.
- Any drift beyond the intended set = immediate STOP + rollback (per stop conditions).

## 5. Exit decision thresholds
Objective thresholds (to be applied by Michael/Build-Coordinator after the trial):
```text
ADVANCE_TO_BAKEOFF   Paperless meets all core lifecycle/OCR/isolation gates AND provenance/file-id
                     preservation passes AND the measured OCR/lifecycle value is real over the current
                     stack; proceed to the retrieval/OCR bake-off (doc 6) for platform comparison.
EXTEND_PROOF_OF_FIT  Most gates pass but one or more open items need a second, wider, copy-safe run
                     (e.g. more scanned/OCR samples, workflow depth). Nothing is adopted.
REJECT_PAPERLESS     Paperless fails a load-bearing gate (provenance/file-id preservation, subject
                     isolation, original preservation, or resources); document why, keep Option B.
BLOCKED              A hard blocker (resource, package, isolation) prevents a valid trial; stop and
                     report; do not relax boundaries to proceed.
```
No adoption decision is made by the proof-of-fit itself; only the gate label is produced as evidence.

## 6. Production migration
**NOT AUTHORISED by this plan.** Even a PASS leads only to the bake-off; production migration (if ever)
is a separate, explicitly approved, staged task with parity requirements (Build-path Slice 8 gate:
do not delete vault or index; require search/metadata/backup/access parity).

## Evidence ledger
- All of the above is DESIGN_REQUIREMENT / ARCHITECTURE_HYPOTHESIS planning. No Paperless install, no
  copies created, no trial executed in this task (scope lock). Sample/tests reflect CONFIRMED_LIVE_FACT
  source types (utilities, insurance, Maxxia lease, government, renewal, duplicates, zero-text) and the
  documented OCR/provenance gaps.
