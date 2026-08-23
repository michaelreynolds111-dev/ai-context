# Household Retrieval / OCR Bake-Off Plan

**Classification:** [IDENTITY] · **Status:** PLANNING · **Task:** Household 02
**Date:** 23 August 2026
**Scope:** a deterministic retrieval/OCR bake-off comparing the current stack against Paperless
full-text/metadata on the same sample, to inform the architecture decision. This is a PLAN for a
separately-approved future task. **No bake-off executed here.**

---

## 0. Purpose
Objectively measure where the current pgvector-based retrieval and the (candidate) Paperless full-text /
metadata retrieval each succeed and fail on the household corpus, so the Options A/B/C decision (doc 4)
rests on measured results rather than assumptions. Uses the same copy-safe sample set from the proof-of-fit
plan (doc 5).

## 1. Systems compared
1. **Current pgvector** — household-search MCP -> /query_collection -> household pgvector (all-MiniLM-L6-v2,
   semantic, identity-filtered). Baseline today.
2. **Paperless full-text** — full-text search over the sample (native + OCR text).
3. **Paperless metadata filters** — correspondents / document types / tags / custom fields / dates.
4. **Combined retrieval** — metadata filter + full-text (and optionally + pgvector semantic where it adds
   value) — to assess a Paperless-centred hybrid retrieval.

## 2. Question set (40-60 deterministic questions)
Design ~40-60 questions with KNOWN correct answers, covering:
- correct source (which document/chunk);
- exact identifier accuracy (account/rego/policy/membership number where safely present in sample);
- provider/correspondent;
- date retrieval (issue/due/expiry);
- latest/current version selection;
- conceptual retrieval (a paraphrase that is not an exact match);
- scanned-document recovery (zero-text/OCR only);
- OCR field recovery (a field legible only after OCR);
- duplicate/version handling (which is current);
- subject isolation (current-household question must NOT return OTHER_PERSON/GENERAL fixtures);
- false positives;
- not-found (a deliberately absent item should return nothing, not a confabulation);
- source citation (can the answer name the source document);
- multi-document synthesis (a question needing 2+ documents);
- latency;
- repeatability (same question twice -> same result);
- operational/admin cost (index/maintenance effort to keep correct).

## 3. Measures / metrics
- Correct-source rate; exact-identifier accuracy; provider/correspondent accuracy; date accuracy;
  latest/current selection accuracy; conceptual retrieval recall; scanned-document recovery;
  OCR field recovery; duplicate/version correctness; subject-isolation (zero cross-scope leakage);
  false-positive count; not-found correctness; citation completeness; multi-document synthesis quality;
  latency (p50/p95/max); determinism/repeatability; operational/admin cost (time to ingest, index and
  maintain each system).

## 4. Method
- Same 100-200 decoded, copy-safe sample in all systems.
- Blind/identical question battery applied to each system; results recorded to a table.
- No live data, no production mutation; all runs copy-safe and isolated; teardown + rollback after.

## 5. Outcome labels (decision inputs — NOT a selection)
```text
ADOPT_PAPERLESS_HYBRID   Paperless full-text/metadata measurably beats/ties current pgvector on the
                         required measures AND subject isolation AND provenance preservation; recommend
                         adopting a Paperless-centred hybrid (then stage migration per Slice 8 parity).
RETAIN_CUSTOM_RETROFIT   Current pgvector + custom retrofit is equal-or-better on the required measures
                         and/or Paperless fails a gate; recommend Option B.
EXTEND_PARALLEL_TRIAL    Results are close or a measure is inconclusive; extend the parallel trial
                         (wider sample / more questions) before deciding; no adoption.
NO_DECISION_BLOCKED      A blocker prevents a valid comparison; stop and report.
```
These labels feed Michael's/Build-Coordinator's architecture decision (doc 4). No label is an automatic
adoption.

## 6. Evidence ledger
- DESIGN_REQUIREMENT / ARCHITECTURE_HYPOTHESIS. No bake-off executed in this task (scope lock). Question/
  measure types reflect CONFIRMED_LIVE_FACT capabilities (current pgvector semantic retrieval, native OCR
  gap, duplication/version needs, subject-isolation requirement).
