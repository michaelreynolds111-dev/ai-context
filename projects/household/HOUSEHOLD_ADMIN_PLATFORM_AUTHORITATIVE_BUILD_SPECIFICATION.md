# Household Administration Platform — Authoritative Build Specification and LibreChat Implementation Guide

**Document status:** Authoritative implementation handoff  
**Date:** 24 August 2026  
**Intended consumer:** LibreChat/Household Admin, Goose AI, implementation agents, and human reviewers  
**Architecture direction:** `ADOPT_PAPERLESS_HYBRID`  
**Production deployment status:** **NOT AUTHORISED BY THIS DOCUMENT ALONE**

---

## 1. Purpose

This document is the single comprehensive implementation guide for completing the Household Administration Platform. It records the decisions already made, the evidence supporting them, the role of every major component, the required data flows, the safety and privacy boundaries, the indexing and retrieval strategy, the Gmail and attachment acquisition design, the staged implementation sequence, and the criteria that must be satisfied before any production cutover.

The platform must be built as a **preserve-first, provenance-aware, hybrid document and retrieval system**. It must not be treated as a generic “chat with a folder” project.

The target architecture is:

```text
Google/Gmail/Drive acquisition
              ↓
       retained source landing
              ↓
      governed copy + provenance
              ↓
 Paperless-ngx document subsystem
 ├── preserved originals
 ├── OCR/archive derivatives
 ├── metadata and lifecycle
 ├── review queues
 ├── current/superseded versions
 └── exact/full-text retrieval
              ↓
 canonical identity + indexing bridge
              ├───────────────┐
              ↓               ↓
      pgvector semantic    verified household ledger
      retrieval index      (later bounded slices)
              └───────┬───────┘
                      ↓
              bounded retrieval adapter
                      ↓
          household-search MCP / Household Admin
                      ↓
        grounded answers with citations and limits

Future, separate authority:
Actual Budget → transactions, categories, budgets and payments
```

---

## 2. Executive architecture decision

### 2.1 Approved direction

The working architecture direction is:

```text
ADOPT_PAPERLESS_HYBRID
```

This means:

- **Paperless-ngx** becomes the operational document-management substrate.
- **pgvector** remains the derived semantic retrieval index.
- A **bounded adapter** enforces subject scope, current-version rules, retrieval ordering, not-found thresholds, OCR quality gates, canonical identity and minimum disclosure.
- **Household Admin** remains the conversational interface.
- A future **verified household ledger** stores reviewed facts and obligations rather than raw model guesses.
- **Actual Budget** remains a later specialist authority for transactions and budgeting.

### 2.2 Why this direction was selected

Paperless-ngx has already demonstrated, in an isolated proof-of-fit environment:

- preservation of original files;
- non-destructive OCR/archive derivatives;
- document metadata and lifecycle management;
- tags, custom fields and saved views;
- subject-scope and current/superseded modelling through controlled configuration;
- email and attachment relationships;
- authenticated API access;
- exact and full-text retrieval;
- successful export;
- clean destruction and recreation;
- successful import;
- full restoration of the tested documents, metadata, relationships and views;
- zero measured original-checksum mismatches;
- zero measured metadata mismatches;
- zero manual data repairs in the clean restore drill.

The current pgvector/RAG/MCP investment remains valuable for semantic retrieval and must not be discarded.

The two attempted formal retrieval bake-offs became unnecessarily complex because they tried to compare unequal corpora and over-engineered metrics. Their defective or incomplete metrics are not decision evidence. Their safe qualitative observations are still useful:

- exact identifiers and document lifecycle are Paperless strengths;
- conceptual and paraphrased retrieval are pgvector strengths;
- pgvector alone does not understand authority, subject scope or supersession;
- zero-text and poor-scan records cannot be trusted merely because a nearest-neighbour result exists;
- exact and semantic retrieval are complementary.

### 2.3 What this decision does not mean

`ADOPT_PAPERLESS_HYBRID` does **not** mean:

- immediately migrating the household corpus;
- giving Household Admin direct Paperless API access;
- deleting the current semantic index;
- abandoning the retained source landing area;
- treating Paperless as the verified household ledger;
- using Paperless as a transaction or budgeting system;
- ingesting every mailbox or file without classification;
- allowing an LLM to control security filters;
- trusting all OCR output;
- retiring legacy components without archive-first rollback evidence.

---

## 3. Current system that must be preserved

The implementation must begin from the current, functioning AI system rather than rebuilding from scratch.

### 3.1 Existing semantic retrieval foundation

The current household semantic retrieval path contains approximately:

```text
1,935 household file IDs
27,803 household embedding rows
1,935 matching file records
```

The production vector database also contains a separate test collection. The previously verified overall pgvector row count was 29,177.

The existing route is conceptually:

```text
household-vault / indexed source corpus
              ↓
           pgvector
              ↓
      POST /query_collection
              ↓
      household-search MCP
              ↓
        Household Admin
```

This path must remain operational throughout staged implementation.

### 3.2 Existing acquisition foundation

The active acquisition side currently lands Google-derived data into a retained source area, principally under `D:\Data`.

The implementation must preserve:

- one-way, non-destructive acquisition;
- Google/Gmail/Drive source authority;
- current scheduled acquisition health;
- source timestamps where practical;
- source-file preservation;
- no upstream mutation;
- the distinction between source landing, operational document management and derived indexes.

### 3.3 Systems that remain separate

The following are not replaced by Paperless:

- Google/Gmail/Drive acquisition;
- the retained source landing/mirror;
- pgvector semantic retrieval;
- `/query_collection`;
- household-search MCP;
- Household Admin;
- verified facts and deterministic calculations;
- expected-document monitoring;
- acquisition-health monitoring;
- controlled form generation;
- Actual Budget;
- Bitwarden.

---

## 4. Authority model

Every store must have one clear authority role.

### 4.1 Source authority

Google, Gmail, Drive, scans and other external providers remain the source authorities for received material.

The local source landing is the retained acquisition copy.

Neither Paperless nor pgvector may silently rewrite the upstream source.

### 4.2 Document authority

Paperless is the operational authority for:

- the preserved document original used by the platform;
- OCR/archive derivative references;
- document metadata;
- review state;
- subject scope;
- current/superseded state;
- document type;
- correspondent;
- lifecycle state;
- exact/full-text search;
- document export and recovery.

### 4.3 Semantic retrieval authority

pgvector is a **derived and rebuildable index**, not a documentary authority.

If pgvector is lost, it must be possible to recreate it from eligible Paperless records and their approved extracted text.

### 4.4 Verified-fact authority

A later verified household ledger is authoritative for reviewed structured facts such as:

- bill issue date;
- due date;
- billing period;
- amount;
- renewal date;
- provider;
- policy or account reference;
- obligation status;
- provenance;
- conflicts;
- verification status;
- deterministic calculations.

The ledger must not be populated as “verified” solely from unreviewed OCR or LLM output.

### 4.5 Transaction and budget authority

Actual Budget will later be authoritative for:

- accounts;
- transactions;
- categories;
- budgets;
- payment status;
- actual cash movement.

Document-derived bills and statements can later be reconciled to Actual Budget, but Paperless must not become the transaction ledger.

### 4.6 Credential authority

Bitwarden remains authoritative for secrets and credentials.

Passwords, tokens, recovery codes and decryption secrets must never be stored in:

- Paperless metadata;
- extracted text intended for indexing;
- pgvector;
- task reports;
- Git repositories;
- LibreChat prompts;
- source filenames.

---

## 5. Canonical identity model

Paperless IDs, vector chunk IDs and file paths are wiring identifiers only. They must not be treated as the stable logical identity of a household document.

### 5.1 Required identifiers

The production design must formalise:

```text
canonical_document_id
  Stable identity of the logical document family.

document_version_id
  Immutable identity of one acquired version.

source_artifact_id
  Identity of the acquired source file/message/attachment instance.

paperless_document_id
  Paperless wiring identifier.

derivative_id
  Identity of an OCR/archive/thumbnail/extracted derivative.
```

### 5.2 Required relationships

```text
canonical_document_id.current_version_id
    → document_version_id

document_version_id.supersedes_version_id
    → prior document_version_id

source_artifact_id
    → document_version_id

paperless_document_id
    → document_version_id

derivative_id
    → source_artifact_id + paperless_document_id
```

### 5.3 Identity invariants

- A Paperless restore or re-key must not change canonical identity.
- A re-embedding must not change document-version identity.
- A new source version must receive a new `document_version_id`.
- A better scan must not silently overwrite the poor scan’s evidence history.
- Every vector chunk must point back to canonical and version identity.
- Every generated citation must resolve to a preserved Paperless document and source artifact.

---

## 6. Subject, consent and access model

Do not overload one field to represent ownership, source mailbox, household relevance and access authorisation.

### 6.1 Required concepts

```text
source_mailbox_scope
  Which authorised mailbox or source supplied the item.

document_subject
  The person/entity the document concerns.

household_relevance
  Whether the item is shared household administration.

subject_scope
  Controlled retrieval boundary.

access_authorisation
  Basis on which the platform may process the record.
```

### 6.2 Controlled subject-scope values

At minimum:

```text
CURRENT_HOUSEHOLD
OTHER_PERSON
GENERAL_REFERENCE
UNKNOWN_REVIEW_REQUIRED
```

### 6.3 Current-status values

The production model must avoid treating missing status as current.

Use explicit values such as:

```text
CURRENT
SUPERSEDED
HISTORICAL
UNVERSIONED_CURRENT
UNKNOWN_REVIEW_REQUIRED
```

`UNVERSIONED_CURRENT` is intended for legitimate single-version records that are current but do not belong to an established version family.

### 6.4 Mandatory default answer boundary

Before evidence can become answer-ready, the bounded adapter must enforce a server-side policy equivalent to:

```text
subject_scope == CURRENT_HOUSEHOLD
AND current_status IN (CURRENT, UNVERSIONED_CURRENT)
AND review_state permits answer use
```

The caller, Household Admin and the LLM must not be able to remove or override this boundary.

### 6.5 Sarah’s approved mailbox

Sarah has provided complete consent for household-administration access.

The platform must still preserve Sarah’s source identity and distinguish shared household records from private non-household records.

A document received through Sarah’s mailbox can be `CURRENT_HOUSEHOLD` when the document concerns shared household administration. A private record does not become household evidence merely because it was received in an authorised mailbox.

Use a source namespace such as:

```text
source_mailbox_scope = SARAH_AUTHORISED_HOUSEHOLD_SOURCE
```

Do not expose Sarah’s account identifier to the LLM unless necessary. Keep exact account identifiers in restricted configuration, not embedding content.

---

## 7. Gmail and attachment acquisition

Most of the useful bill data may be contained in Gmail attachments. The implementation must treat email processing as first-class, not ancillary.

### 7.1 Historical acquisition

Each authorised account should have a historical Gmail export/backfill.

Historical flow:

```text
account-holder-controlled Gmail export
              ↓
restricted staging
              ↓
message extraction
              ↓
attachment extraction
              ↓
classification and exclusions
              ↓
source landing
```

Do not ingest an entire historical mailbox blindly.

### 7.2 Ongoing acquisition

Michael’s account already uses an Apps Script that writes:

```text
Mail/messages
Mail/attachments
```

A Sarah-specific Apps Script has been prepared to write:

```text
MailSarah/messages
MailSarah/attachments
```

> Namespace note: flat, slash-free `MailSarah` (no nested `Mail/sarah/`) — eliminates the
> full-width-slash namespace defect from Apps Script's `getFoldersByName` treating the slash
> as a literal folder-name character.

The Sarah script:

- is deployed under Sarah’s Google account;
- checks the expected account context when Google exposes it;
- records `.eml` messages;
- extracts attachments;
- includes the Gmail message ID and attachment position in deterministic attachment filenames;
- writes the `.eml` last as the per-message completion marker;
- retains the checkpoint when any message fails;
- supports idempotent retry;
- advances the checkpoint only on an error-free run.

### 7.3 Local acquisition for Sarah

A separate Sarah-authorised rclone OAuth remote must copy only:

```text
MailSarah/
```

into a local destination such as:

```text
D:\Data\MailSarah\messages\
D:\Data\MailSarah\attachments\
```

Requirements:

- Sarah completes OAuth authorisation;
- no password sharing;
- one-way copy/sync with no upstream deletion;
- timestamps preserved where practical;
- source identity retained;
- counts and failures logged;
- remote immediately revocable;
- no unrelated Drive content acquired.

### 7.4 Message and attachment relationship model

For every message:

```text
email message
├── message body
├── attachment 1
├── attachment 2
└── attachment n
```

Store:

```text
message_group_id
parent_email_case_id
attachment_case_ids
source_message_id
source_mailbox_scope
```

The email body provides context and provenance. The bill/statement attachment generally carries greater evidentiary authority.

### 7.5 Portal-only email

If an email says “your bill is ready” but carries no attachment:

- preserve the email;
- classify it as a portal notice;
- do not invent the bill details;
- register an expected/missing underlying document;
- route to an approved portal retrieval or manual-review workflow later.

### 7.6 Exclusions

The ingestion system must detect and exclude or quarantine:

- passwords and credential exports;
- one-time codes;
- password resets;
- recovery codes;
- login/security alerts where not needed;
- legal matters outside authorised household scope;
- clinical records;
- identity documents requiring heightened handling;
- estate/deceased-family material;
- other-person records;
- encrypted records requiring a separate approved workflow;
- uncertain records.

---

## 8. Governed ingestion into Paperless

### 8.1 Source-to-copy workflow

The production ingestion bridge must never mount the live source tree into Paperless as a writable consumption source.

For every candidate:

```text
1. discover source candidate
2. classify source scope
3. apply prohibited-content rules
4. compute source hash read-only
5. create governed copy with opaque identity
6. verify source hash == copy hash
7. submit governed copy to Paperless
8. verify Paperless stored original == governed copy
9. store provenance and crosswalk
10. leave source unchanged
```

### 8.2 Ingestion states

Use explicit states such as:

```text
DISCOVERED
CLASSIFICATION_REQUIRED
EXCLUDED
APPROVED_FOR_COPY
COPIED_HASH_VERIFIED
SUBMITTED_TO_PAPERLESS
INGESTED
OCR_REVIEW_REQUIRED
METADATA_REVIEW_REQUIRED
APPROVED_FOR_INDEXING
INDEXED
FAILED_VISIBLE
```

### 8.3 Idempotency

Idempotency keys should include:

```text
source_artifact_id
source checksum
source message ID where applicable
attachment position where applicable
```

Retries must not silently create duplicate document families.

### 8.4 Failure policy

- Failures must be visible.
- A bad message/file must not block all future acquisition indefinitely.
- A failed source must not be skipped permanently by an advanced checkpoint.
- One retry is permitted only for demonstrated transient infrastructure errors.
- Parsing/OCR/classification failures must enter review queues.

---

## 9. Paperless metadata model

### 9.1 Required custom fields

At minimum:

```text
subject_scope
current_status
lifecycle_state
canonical_document_id
document_version_id
supersedes_version_id
source_artifact_id
derivative_id
message_group_id
parent_email_case_id
attachment_case_ids
source_mailbox_scope
household_relevance
review_state
ocr_quality_state
```

### 9.2 Lifecycle states

```text
INBOX
AWAITING_CLASSIFICATION
AWAITING_OCR_REVIEW
AWAITING_METADATA_REVIEW
VERIFIED_METADATA
APPROVED_FOR_INDEXING
SUPERSEDED
ARCHIVED
EXCLUDED
```

### 9.3 OCR quality states

```text
NATIVE_TEXT_USABLE
OCR_USABLE
OCR_LOW_FIDELITY_REVIEW_REQUIRED
ZERO_TEXT
RESCAN_REQUIRED
ALTERNATE_EXTRACTION_REQUIRED
UNSUPPORTED_FORMAT
```

### 9.4 Saved views

Required operational views:

```text
Inbox
Awaiting classification
Awaiting OCR review
Awaiting metadata review
Current household — answer ready
Superseded
Other person
General reference
Unknown review required
Failed ingestion
Expected but missing documents
```

### 9.5 Default answer-ready view

Conceptually:

```text
subject_scope = CURRENT_HOUSEHOLD
AND current_status IN (CURRENT, UNVERSIONED_CURRENT)
AND review_state IN (VERIFIED_METADATA, APPROVED_FOR_INDEXING)
AND ocr_quality_state IN (NATIVE_TEXT_USABLE, OCR_USABLE)
```

This is enforced by the adapter, not merely by a UI view.

---

## 10. OCR and extraction design

### 10.1 Native text first

For PDFs, Office files and email bodies:

1. attempt native text extraction;
2. preserve structure where practical;
3. avoid OCR when a reliable native text layer exists;
4. use OCR for image-only or failed-native cases.

### 10.2 Non-destructive OCR

The original must never be overwritten.

```text
original source copy
├── preserved unchanged
└── OCR/archive derivative
```

### 10.3 Poor-scan finding

A real low-quality image-only test scan produced a preserved derivative but garbled OCR text.

Therefore:

- successful OCR execution is not proof of usable extraction;
- low-quality OCR must be review-required;
- poor OCR must not become verified facts;
- a better source scan or manual review may be required.

### 10.4 Tables

For bills/statements with tables:

- retain the original layout in Paperless;
- preserve extracted raw text;
- attempt deterministic row/column extraction separately;
- do not infer a label/value relationship solely from OCR order;
- require review when columns are ambiguous;
- use the verified ledger for approved structured facts.

### 10.5 Email and Office

- Email messages and attachments are separate linked records.
- Office conversions must preserve the original Office file.
- Conversion output is a derivative.
- Real-mailbox and broad real-Office diversity were not proven in the prior trial and require staged operational observation.

---

## 11. Semantic indexing bridge

### 11.1 Eligibility

The indexer must query Paperless only for records meeting explicit eligibility rules.

Suggested default:

```text
subject_scope = CURRENT_HOUSEHOLD
AND current_status IN (CURRENT, UNVERSIONED_CURRENT)
AND review_state = APPROVED_FOR_INDEXING
AND ocr_quality_state IN (NATIVE_TEXT_USABLE, OCR_USABLE)
```

### 11.2 Chunk schema

Each semantic chunk must carry:

```text
chunk_id
canonical_document_id
document_version_id
source_artifact_id
paperless_document_id
derivative_id
chunk_number
chunk_text
subject_scope
current_status
review_state
ocr_quality_state
document_type
correspondent
document_date
source_checksum
derivative_checksum
embedding_model
embedding_model_version
chunking_policy_version
indexed_at
```

### 11.3 Chunking policy

Start conservatively:

```text
native prose:
  paragraph/sentence-aware chunks

policies and agreements:
  heading/section-aware chunks

emails:
  message body chunks; attachments indexed separately

tables:
  deterministic row/section representation where possible

poor OCR / zero text:
  not answer-ready; no trusted semantic indexing
```

Avoid embedding entire very large documents as single records.

### 11.4 Incremental updates

Before reindexing, compare:

```text
source checksum
derivative checksum
document_version_id
review state
current status
embedding model version
chunking policy version
```

If nothing relevant changed, do not re-embed.

If a document is superseded:

- keep it in Paperless;
- remove or exclude its chunks from the default semantic answer set;
- keep provenance and audit history.

### 11.5 Rebuildability

The semantic index must be completely rebuildable from eligible Paperless records.

The vector database must not be the only place where:

- chunk text;
- document identity;
- review state;
- source provenance;
- current/superseded state

can be determined.

---

## 12. Hybrid retrieval adapter

The adapter is the critical custom product. Household Admin must never call unrestricted Paperless or pgvector APIs directly.

### 12.1 Request validation

Validate:

```text
authenticated user
allowed operation
query length
result limit
subject boundary
current-version boundary
requested document class
minimum disclosure policy
```

The model cannot submit an arbitrary subject scope.

### 12.2 Retrieval order

```text
1. exact canonical/reference identifier match
2. exact authoritative metadata match
3. current Paperless full-text match
4. high-confidence pgvector semantic candidates
5. review-required evidence, flagged separately
```

### 12.3 Result filtering

Before answer generation:

```text
exclude OTHER_PERSON
exclude GENERAL_REFERENCE by default
exclude UNKNOWN_REVIEW_REQUIRED
exclude SUPERSEDED
exclude unapproved OCR
exclude unverified metadata when required
exclude duplicate canonical documents
```

### 12.4 Semantic not-found threshold

pgvector normally returns nearest neighbours even when none is genuinely relevant.

The adapter must implement:

- minimum relevance/distance threshold;
- document-class-aware threshold where justified;
- explicit `NOT_FOUND` response;
- no answer generation from weak neighbours;
- observability of threshold decisions.

### 12.5 Deduplication

Merge by:

```text
canonical_document_id
+ document_version_id
```

Avoid sending multiple chunks from the same document unless each adds distinct necessary evidence.

### 12.6 Evidence packet

Household Admin should receive only:

```text
canonical identity
safe title/label
document type
correspondent where permitted
document date
current/review/OCR status
minimum necessary excerpt
source citation
retrieval method
relevance or exact-match reason
```

Do not provide unrestricted full documents by default.

### 12.7 Answer contract

Household Admin must:

- answer only from supplied evidence;
- cite sources;
- distinguish sourced fact from inference;
- return honest not-found;
- identify review-required evidence;
- never present superseded material as current;
- avoid calculations unless deterministic structured data is supplied;
- disclose only the minimum information needed.

---

## 13. Verified household ledger

### 13.1 Purpose

The ledger stores reviewed facts derived from documents.

Example record:

```text
fact_id
fact_type
value
unit
period_start
period_end
due_date
canonical_document_id
document_version_id
source_location
extraction_method
verification_status
verified_by
verified_at
conflict_status
supersedes_fact_id
```

### 13.2 Verification states

```text
EXTRACTED_UNVERIFIED
REVIEW_REQUIRED
VERIFIED
CONFLICTED
SUPERSEDED
REJECTED
```

### 13.3 Deterministic calculations

Totals, averages, date differences and reconciliations should be computed from verified structured fields—not by asking an LLM to calculate from arbitrary OCR excerpts.

### 13.4 First vertical slice

The originally planned electricity/utility ledger remains a sensible first bounded vertical slice after the document and indexing bridge is implemented.

It should prove:

- acquisition from both authorised mailboxes;
- attachment extraction;
- document classification;
- OCR quality handling;
- verified amount/date extraction;
- missing expected bill detection;
- current-version handling;
- source citations;
- later payment reconciliation.

---

## 14. Expected-document monitoring

Search alone cannot reveal a document that was never acquired.

Create an expected-document register:

```text
provider
document_type
expected_frequency
expected_source_mailbox
normal_arrival_window
last_confirmed_document
next_expected_date
grace_period
missing_status
```

Required distinctions:

```text
NOT_EXPECTED
EXPECTED_NOT_YET_DUE
EXPECTED_AND_MISSING
ACQUISITION_SOURCE_UNHEALTHY
PORTAL_NOTICE_WITHOUT_DOCUMENT
DOCUMENT_RECEIVED_REVIEW_PENDING
```

The LLM must not infer missingness merely from an empty search result.

---

## 15. Backup, recovery and continuity

### 15.1 Paperless

Retain:

- supported Paperless exports;
- database backup;
- media/original files;
- configuration;
- pinned image digests;
- restore runbook;
- test evidence.

A clean restore was previously proven in isolation and must become a repeatable production runbook.

### 15.2 pgvector

Retain logical backups where helpful, but treat the semantic index as rebuildable.

The authoritative recovery path is:

```text
Paperless eligible records
+ canonical metadata
+ chunking policy
+ embedding model/version
→ rebuild pgvector
```

### 15.3 Source landing

Preserve source data independently of Paperless.

### 15.4 Recovery tests

Before production cutover, test:

- Paperless export/restore;
- canonical crosswalk restoration;
- index rebuild;
- adapter filter behaviour;
- missing-document register recovery;
- credential/token recreation;
- citations after restore.

---

## 16. Observability

Record metadata-safe operational events:

```text
source candidates discovered
files copied
hash matches/mismatches
Paperless ingestion successes/failures
OCR quality outcomes
review queues
indexing successes/failures
chunks added/removed
not-found decisions
superseded exclusions
cross-subject exclusions
expected-document misses
backup results
restore results
```

Never log:

- passwords;
- tokens;
- full private message bodies;
- raw document text unnecessarily;
- real values in general project reports;
- unrestricted source paths where opaque identities suffice.

---

## 17. Security requirements

### 17.1 Network exposure

- Bind test services to localhost only.
- Production services require explicit authenticated entry points.
- Never expose Paperless or pgvector directly to the public internet.

### 17.2 Secrets

- Keep OAuth tokens and API tokens in restricted secret storage.
- Regenerate instance tokens after restore as required.
- Do not commit `.env` files.
- Do not embed secrets.

### 17.3 Least privilege

- Acquisition credentials: read-only or non-destructive where available.
- Paperless adapter: read-only retrieval in the first stage.
- Indexer: read eligible Paperless records and write only to derived index.
- Household Admin: no direct database access.

### 17.4 Consent and revocation

Sarah’s consent is recorded for household administration, but Sarah must retain the ability to revoke the Sarah-specific Google OAuth access.

---

## 18. Selective retirement strategy

### 18.1 Retain

Retain:

- current Google acquisition;
- source landing;
- current semantic retrieval until replacement is proven;
- Household Admin;
- household-search MCP;
- current backups;
- canonical requirements;
- prior proof-of-fit evidence.

### 18.2 Avoid rebuilding

Do not custom-build parallel replacements for capabilities Paperless already provides adequately:

- document inbox;
- OCR queue;
- archive derivatives;
- thumbnails;
- correspondents/types/tags;
- lifecycle state;
- document review UI;
- duplicate document handling;
- document-management export/restore.

### 18.3 Retire later

Potential retirement candidates include:

- broken legacy Keep processing;
- old LanceDB/Ollama document-search paths;
- overlapping OCR scripts;
- duplicate document-status stores;
- obsolete thumbnail/archive tooling;
- redundant document-search components.

Retirement must be:

```text
inventory
→ confirm replacement
→ archive
→ verify rollback
→ disable
→ observe
→ delete only with separate approval
```

---

## 19. Implementation phases

### Phase 0 — Evidence and environment closure

Before implementation:

- safely close any partial Task 04 evaluation containers;
- keep defective metrics marked provisional;
- ensure Paperless test stack is stopped;
- ensure no disposable evaluation pgvector remains;
- verify production integrity;
- retain metadata-safe proof-of-fit evidence.

### Phase 1 — Production design only

Produce:

- canonical identity schema;
- Paperless metadata schema;
- ingestion state machine;
- Sarah and Michael source namespaces;
- adapter API contract;
- semantic chunk schema;
- OCR quality policy;
- rollback design;
- pilot selection.

No deployment.

### Phase 2 — Bounded read-only adapter prototype

Build an isolated adapter against the retained Paperless test environment.

Requirements:

- hard-coded server-side scope/current filters;
- exact metadata search;
- Paperless full-text search;
- pgvector semantic test path;
- exact-before-semantic merge;
- deduplication;
- not-found threshold;
- citations;
- no model-controlled filters.

### Phase 3 — Governed ingestion bridge pilot

Pilot one low-risk category, preferably ordinary vehicle/insurance or utility documents.

Use copies only.

Prove:

- source preservation;
- idempotency;
- metadata and review workflow;
- OCR quality gate;
- incremental indexing;
- rollback;
- no production regression.

### Phase 4 — Dual-mailbox acquisition

- deploy Sarah’s Apps Script;
- configure Sarah’s restricted rclone OAuth remote;
- process Michael and Sarah namespaces;
- preserve email/attachment links;
- establish historical backfills;
- test missing-document detection.

### Phase 5 — Parallel observation

Run old and new retrieval routes in parallel.

Do not require an elaborate research bake-off. Use practical acceptance tests:

- exact identifier;
- conceptual retrieval;
- current version;
- cross-subject exclusion;
- poor OCR review;
- not-found;
- source citation.

### Phase 6 — Controlled retrieval cutover

Only after pilot evidence:

- connect Household Admin to bounded hybrid adapter;
- retain fallback to existing household-search MCP;
- observe errors;
- do not remove old infrastructure yet.

### Phase 7 — Verified electricity/utility ledger

Build the first structured-fact vertical slice.

### Phase 8 — Actual Budget proof of fit

Install and evaluate Actual Budget separately after document/ledger foundations are stable.

### Phase 9 — Selective legacy retirement

Archive-first and reversible.

---

## 20. Acceptance criteria

### 20.1 Ingestion

```text
source modifications: 0
source/copy hash mismatches: 0
stored-original mismatches: 0
prohibited items ingested: 0
visible actionable failures: 100%
idempotent retry: PASS
```

### 20.2 Retrieval safety

```text
cross-subject leakage: 0
superseded-as-current answers: 0
poor-OCR evidence presented as verified: 0
model-controlled filter override: impossible
not-found invention: 0
source citations on sourced answers: >= 95%
```

### 20.3 Recovery

```text
restored original checksums: 100%
restored metadata: 100% for required fields
canonical crosswalk restored: 100%
index rebuild: PASS
adapter safety regression: PASS
```

### 20.4 Mail acquisition

```text
messages identifiable by source mailbox: 100%
attachments linked to messages: 100%
checkpoint does not skip failures: PASS
retry does not duplicate completed messages: PASS
Sarah OAuth revocable: PASS
upstream deletion/mutation: 0
```

### 20.5 Structured facts

```text
verified facts with source identity: 100%
unreviewed OCR auto-promoted to verified: 0
conflicts visible: 100%
deterministic calculations reproducible: 100%
```

---

## 21. Required implementation artefacts

LibreChat/Goose implementation tasks should produce, in order:

```text
1. ARCHITECTURE_DECISION_RECORD.md
2. CANONICAL_IDENTITY_SCHEMA.md
3. PAPERLESS_METADATA_SCHEMA.md
4. SOURCE_AND_MAILBOX_PROVENANCE_MODEL.md
5. GOVERNED_INGESTION_STATE_MACHINE.md
6. OCR_QUALITY_AND_REVIEW_POLICY.md
7. PAPERLESS_TO_PGVECTOR_INDEX_CONTRACT.md
8. HYBRID_RETRIEVAL_ADAPTER_API.md
9. SECURITY_AND_MINIMUM_DISCLOSURE_POLICY.md
10. BACKUP_RESTORE_AND_REBUILD_RUNBOOK.md
11. PILOT_IMPLEMENTATION_PLAN.md
12. PILOT_ACCEPTANCE_TESTS.md
13. CUTOVER_AND_ROLLBACK_PLAN.md
14. LEGACY_RETIREMENT_INVENTORY.md
```

No implementation task may silently rewrite this authority model.

---

## 22. LibreChat/Household Admin operating prompt

The future Household Admin agent should operate under a prompt equivalent to:

```text
You are the Household Administration assistant.

Use only evidence returned by authorised household tools.

Never request or override subject-scope, current-version, review-state or minimum-disclosure filters.

Prefer exact and authoritative metadata matches. Use semantic matches only when they meet the adapter’s relevance threshold.

Do not treat nearest-neighbour results as proof.

Do not treat poor OCR or review-required evidence as verified.

Do not use superseded documents as current evidence.

For every sourced factual answer:
- cite the canonical source;
- identify uncertainty or review state;
- use the minimum necessary disclosure;
- distinguish document evidence from a verified ledger fact.

If no eligible evidence is returned, say that the information was not found. Do not infer that a missing search result proves no document exists.

Do not calculate totals, averages or reconciliations unless a deterministic tool or verified structured facts are provided.

Do not expose credentials, tokens, unrestricted source paths, other-person records, legal/clinical records, or unknown-review records.
```

---

## 23. Implementation-agent instructions

Every Goose or coding-agent task derived from this document must have:

```text
single objective
explicit in-scope artefacts
explicit out-of-scope boundaries
fresh baseline
ordered steps
fixed safety gates
rollback before mutation
required reports
one stop condition
one immediate next action
```

Do not run broad exploratory tasks when a narrowly scoped design or implementation task will suffice.

Do not ask an agent to prove a decision already supported by sufficient evidence.

Use the largest sensible batch that fits within the context window while keeping one rollback domain.

---

## 24. Immediate next action

The next task is not another bake-off.

Create a tightly scoped **Paperless Hybrid Production Implementation Design** task whose sole objective is:

> Produce the exact schemas, adapter contract, ingestion state machine, security policy, pilot boundary, rollback plan and implementation task sequence for the first copy-safe production pilot—without deploying Paperless or migrating the full corpus.

That design task must use this document as the architecture authority.

---

## 25. Final non-negotiable principles

```text
Preserve originals.
Never mutate upstream sources.
One authority per concern.
Treat indexes as rebuildable.
Use explicit canonical identity.
Filter before retrieval reaches the model.
Exact evidence outranks semantic similarity.
Nearest does not mean relevant.
Poor OCR is review-required.
Missing search results do not prove missing documents.
Cite every source-backed answer.
Calculate deterministically.
Acquire Sarah’s records only through authorised, revocable account-scoped access.
Retire old systems only after archive, rollback and parallel observation.
No production migration without a separately approved implementation task.
```
