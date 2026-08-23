# Household Administration Platform — Architecture Options

**Classification:** [IDENTITY] · **Cluster:** 6 · **Status:** PLANNING
**Task:** Household 02 · **Date:** 23 August 2026
**Scope:** objective comparison of the three architecture options. **NO option is selected here.** The
only recommendation is the next evidence-gathering decision gate. No install/trial.

---

## Option A — Paperless-centred hybrid

Candidate layers:
```text
D:\Data acquisition
  -> Paperless ingestion/OCR/lifecycle (DMS: inbox, correspondents, tags, types, versions, OCR review)
  -> canonical document crosswalk (doc 3 identity spine)
  -> pgvector semantic retrieval where it adds value
  -> verified PostgreSQL household ledger
  -> Actual Budget later
  -> LibreChat bounded tools
```

Assessment:
- **Requirements coverage**: Strong for lifecycle/OCR/inbox/metadata/version/API/recovery (A/B/C/D/G);
  Moderate-to-Weak for exact-facts ledger (F/H still need a separate verified ledger and controlled
  production).
- **Custom code required**: Moderate (crosswalk adapter to sync/preserve pgvector + MCP + ledger; import
  provenance mapping).
- **Operational complexity**: Moderate-to-High (a second container stack alongside LibreChat: app + Redis
  + DB + OCR worker; resource envelope must be respected i5-12400 ~16GB RAM).
- **Migration risk**: Moderate — the corpus is already OCR-enriched, so Paperless's OCR novelty is lower;
  MUST prove import preserves source provenance + file IDs + canonical identity (proof-of-fit doc 5).
- **Provenance & access model**: Strong potential (correspondents/types/tags + custom subject fields)
  IF subject_scope is explicitly configured and a hard CURRENT_HOUSEHOLD default enforced.
- **OCR quality/lifecycle**: Strong (integrated OCRmyPDF+Tesseract, inbox, review queue; matches the
  requirement C).
- **Original preservation**: Strong (non-destructive, byte-identical original retention if configured).
- **Export/recovery**: Strong (REST API + built-in exporter; filesystem recoverability).
- **API/integration quality**: Strong.
- **Performance**: Good at household scale.
- **Update burden**: Moderate (release cadence to track; pin versions; DB migrations).
- **Community maturity**: High.
- **Windows/WSL/Docker fit**: Moderate (WSL Docker ok; watch RAM/disk).
- **Actual Budget coexistence**: Independent; good (separate layer; reconcile via crosswalk doc 7).
- **Preserves current pgvector/MCP investment**: Moderate (retained but needs a re-key/adapter; may become
  secondary to Paperless full-text).
- **Failure/exit strategy**: Good (isolated proof-of-fit; current stack untouched until parity).

## Option B — Current-stack custom retrofit

Candidate layers:
```text
D:\Data acquisition
  -> custom canonical registry / OCR worker / review / version pipeline (built on the existing stack)
  -> household-vault (preserved)
  -> pgvector (retained semantic index)
  -> verified PostgreSQL ledger
  -> Actual Budget later
  -> LibreChat bounded tools
```

Assessment:
- **Requirements coverage**: Strong for exact-facts/ledger/verified-intelligence (F) and controlled
  production (H) on PostgreSQL; Moderate for document lifecycle (D) — inbox/review/version/correspondents/
  tags must be built custom (no DMS).
- **Custom code required**: High (custom registry, OCR-on-ingestion worker, versioning, lifecycle fields,
  workflow — bespoke to build and maintain).
- **Operational complexity**: Moderate (no new platform, but more bespoke code to own).
- **Migration risk**: Low-to-Moderate (keeps current identity, MCP, pgvector — additive/salvage-forward).
- **Provenance & access model**: Strong (subject_scope additive to the existing identity filter; reuse
  /query_collection + MCP pattern).
- **OCR quality/lifecycle**: Weak-to-Moderate (must build; reuse legacy OCR asset, no managed OCR
  lifecycle/review inbox).
- **Original preservation**: Strong (vault/D: unchanged; derivative-only OCR).
- **Export/recovery**: Moderate (manual/export code to write).
- **API/integration quality**: Moderate (no DMS API; bespoke endpoints).
- **Performance**: Strong at household scale.
- **Update burden**: Low-to-Moderate (fewer third-party components; you own the code).
- **Community maturity**: N/A (in-house).
- **Windows/WSL/Docker fit**: Strong (no new platform to fit; LibreChat stack already proven).
- **Actual Budget coexistence**: Strong (same PostgreSQL family; separate schema).
- **Preserves current pgvector/MCP investment**: Strong (all retained; additive).
- **Failure/exit strategy**: Good (additive; current stack is the fallback at all times).

## Option C — Parallel transitional hybrid

Candidate approach:
```text
current RAG/MCP remains production (unchanged)
+ isolated Paperless proof-of-fit (copies, doc 5)
+ same-sample retrieval/OCR bake-off (doc 6)
-> architecture decision (evidenced)
-> staged migration OR custom retrofit
```

Assessment:
- **Requirements coverage**: Strong overall (keeps current production + evaluates a Paperless path +
  measures against it before committing).
- **Custom code required**: Low initially (proof-of-fit copies + bake-off harness) rising to Moderate
  after decision.
- **Operational complexity**: Moderate (two evaluation tracks, time-boxed, isolated).
- **Migration risk**: Low (nothing replaced until decision; current stack stays production).
- **Provenance & access model**: Maintained (no change until decision; then add subject_scope regardless
  of choice).
- **OCR quality/lifecycle**: **Proven-by-trial** — exactly what the OCR bake-off measures.
- **Original preservation**: Strong (all trials use copies; originals untouched).
- **Export/recovery**: Strong (current + Paperless exporter both exercised).
- **API/integration quality**: Measured (bake-off metrics).
- **Performance**: Measured (latency tables).
- **Update burden**: Low during trial.
- **Community maturity**: N/A during trial (Paperless assessed, not adopted).
- **Windows/WSL/Docker fit**: Moderate (temporary isolated Paperless container; removable).
- **Actual Budget coexistence**: Independent.
- **Preserves pgvector/MCP investment**: Strong (retained throughout; decision determines whether it
  stays core or is complemented).
- **Failure/exit strategy**: Strong (evidence-gated, full rollback; both outcomes supported).

---

## Recommended next evidence-gathering decision gate (NOT a selection)

**Run the copy-safe Paperless proof-of-fit plan (doc 5) and the retrieval/OCR bake-off (doc 6) in
parallel against the current stack on the same 100-200 decoded sample, then re-evaluate A vs B with
measured results.**

Rationale:
- Produces the lifecycle/OCR evidence needed to justify Option A (Paperless) only if it genuinely beats
  the current stack on the required measures.
- Preserves the Option B (custom-retrofit) fallback and the current RAG/MCP investment throughout.
- De-risks the decision: no adoption, no migration, and no bespoke build commitment until the bake-off
  numbers are in.

Stopping rule: the decision gate is evidence-gathering only. No platform is selected, installed, or
trialled by this plan document; the proof-of-fit and bake-off are separately approved future tasks
(immediate next action: Michael reviews/approves the plans in docs 5 and 6).

## Final platform selected
**NO** — explicitly none selected in this task.

## Evidence ledger
- Option descriptions and scores are ARCHITECTURE_HYPOTHESIS/DESIGN based on accepted archaeology +
  Brainstorm research (MICHAEL_DECISION). No measured bake-off data exists yet (that is the point of the
  next gate). "Strong/Moderate/Weak" are planning judgements, not measured results.
