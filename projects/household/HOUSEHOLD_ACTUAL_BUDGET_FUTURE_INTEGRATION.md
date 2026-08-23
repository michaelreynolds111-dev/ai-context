# Household Actual Budget — Future Integration Boundary

**Classification:** [IDENTITY] · **Status:** PLANNING · **Task:** Household 02
**Date:** 23 August 2026
**Scope:** defines the future Actual Budget layer as a canonical planning boundary: Actual Budget is the
authority for transactions/budgets/payments; the verified household ledger is the authority for
document-derived facts/obligations; reconciliation is a separate linked process. **Actual Budget is NOT
installed or imposed here** — this is planning for a future, separately-approved step.

---

## 1. Authority boundary (see also doc 3)
- **Actual Budget (future)**: authority for imported/recorded **transactions**, budgets, categories,
  accounts, and **actual-payment history**.
- **Verified household ledger**: authority for **document-derived obligations/facts** (bills, due dates,
  amounts owed per a document, renewals, calculations).
- **Reconciliation**: a **separate linked process** that matches "document says X is due" against "Actual
  Budget says X was actually paid", producing variance / unmatched items. Neither side owns the other.

## 2. Available seed inputs (CONFIRMED_LIVE_FACT — exists in corpus, not yet imported)
- **OFX bank exports** (Actual Budget-import friendly): `Archive/2024-07-01.ofx`, `Archive/2024-07-01 (1).ofx`,
  `Court Finance Analysis/Account 8940 Complete CSV.ofx`.
- **Bank CSV**: `2026-01-01.csv`, `2026-01-01-2up.csv`, Account 8940 CSV (path generalized).
- **XLSX financials**: Reynolds_FullSnapshot, Reynolds_Finances, Bank Statement Analysis and Spending
  Summary (category-mapping seed).
- **Direct-debit/recurring-payment documents** in Mail attachments (recurring-payment signals).
- **Ledger-like XLSX** (Money / payments / schedule).
- Court/family-law finance (NAB, Seddon matter) is routed to the Seddon lane, NOT household Actual Budget.

## 3. Import model
- OFX/CSV/XLSX normalized into a predictable import shape (dedup by transaction id + amount/date + account).
- Account/category mapping seeded from the Spending Summary; configurable, reviewable.
- Every imported transaction keeps **document source id / provenance** (source_file_id) so
  document<->transaction reconciliation is possible.

## 4. Reconciliation model (document-ledger vs transaction)
- **Billed-vs-paid**: match document obligation (ledger) to actual payment (Actual Budget) by amount,
  date-window, provider/account.
- **Unmatched bill** (document exists, no matching transaction) -> review item.
- **Unmatched transaction** (payment exists, no matching document) -> review item.
- **Duplicate payment** detection (two transactions for one bill).
- **Payment-date and amount variance** between billed and paid.
- **Transfers** identified and excluded from spending/income mis-classification.
- **Recurring transaction detection** to feed expected-document/renewal logic.
- Reconciliation is read-only at first; corrections require explicit approval.

## 5. Prerequisites / hold points (must be met before any install)
1. Provenance/subject boundary designed (doc 3) so finance is scoped to the correct household classes
   (Seddon/estate excluded from household Actual Budget).
2. Reconciliation model agreed (this doc).
3. Import shape + account/category mapping defined.
4. No bank credential exposure; no agent write access initially.
5. Backup/export/recovery for Actual Budget data defined.
6. Architecture decision (doc 4) does not preclude it — Actual Budget is independent of Paperless vs
   retrofit.

## 6. Read-only conversational access (first phase)
- Household Admin may answer transaction/budget questions read-only from Actual Budget (or a bounded
  adapter) — no bank API credentials, no autonomous changes during proof-of-fit.
- Later phases could add reporting; autonomous write is NOT in scope.

## 7. Adoption prerequisites
- Actual Budget is adopted only after: (a) the provenance boundary is in place, (b) the import/reconciliation
  model is validated on synthetic/small real data, (c) backup/restore for its store is defined, and (d) a
  separate explicit approval. Not satisfied today.

## 8. Proof-of-fit timing
Actual Budget is a **later** platform slice (after document retrieval + ledger fundamentals). Its
proof-of-fit is independent of, and should follow, the Paperless/retrieval decision so finance sits on the
chosen foundation. No staged sequencing mandated here beyond "later".

## Evidence ledger
- Seed inputs: CONFIRMED_LIVE_FACT (path/count verified in archaeology; generalized in this doc).
- Authority/reconciliation/prereqs: DESIGN_REQUIREMENT / OPEN_DECISION (to be confirmed with Michael and
  Actual Budget proof-of-fit). No Actual Budget install.
