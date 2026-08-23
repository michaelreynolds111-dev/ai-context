# Household Document Authority, Identity, Subject, and Verification Model

**Classification:** [IDENTITY] · **Cluster:** 6 · **Status:** PLANNING
**Task:** Household 02 · **Date:** 23 August 2026
**Scope:** defines the canonical authority roles for each layer, the cross-system document identity
model, the subject/access model, and the auditable verification state machine. These are DESIGN
proposals for review — not yet adopted in data. No implementation performed.

---

## Part 1 — Canonical authority policy proposal

### 1.1 `D:\Data` — active acquisition landing zone + retained source mirror
- Role: **evidence + staging + archive mix**. It is the live origin of acquired upstream Google content
  (Mail/Calendar/Drive) and the retained local mirror.
- Never writes upstream: rclone `copy` semantics (one-way pull) are load-bearing; local/system never
  mutates Google.
- Source deletions are NOT propagated to local (no `sync --delete`); a remote deletion is represented in
  lifecycle as historical/superseded, never silently deleted locally (copy-accumulation is intentional).
- Locally-originated files (scans, manual adds) are retained but MUST be tagged source_origin=local so
  they are not mistaken for Google-synced evidence.

### 1.2 `~/household-vault/` — curated preserve-first archive during transition
- Role: **permanent immutable evidence archive AND migration-safety copy** — both. It is the curated,
  identity-scoped set of preserved originals (6,077 docs / 17G) plus profile facts, reference, and the
  renewals ledger seed. NOT a git repo; NEVER become one. Additive, read-mostly, separate from the live
  index.

### 1.3 Future document lifecycle layer (platform undetermined — do NOT assume Paperless yet)
- Possible authority for: the canonical document record, metadata, review state, versioning,
  current/superseded status, OCR/text derivatives, retention, and workflow — for the operational
  documents it manages. It does NOT alone own the household domain; it cooperates via canonical identity.
- Proof-of-fit (doc 5) decides whether this layer is Paperless or a custom retrofit.

### 1.4 pgvector — derived semantic index
- Role: **derived semantic index**, not the primary evidence store and not the exact-facts database. It
  supports whole-corpus conceptual retrieval. It must NOT silently include out-of-scope classes (subject
  filter required).

### 1.5 LibreChat MongoDB — application registry
- Role: **application registry** (file records, agents, conversations). It is not the canonical household
  domain model. Its `file_id`/`file` records are wiring, not the source of truth for household facts.

### 1.6 Verified household ledger — authority for document-derived facts
- Role: **authority for verified document-derived facts, obligations, calculations, and state
  transitions**. Every value is source-linked (source_file_id), confidence/verification-state labelled,
  and deterministic. (Not implemented yet — DESIGN.)

### 1.7 Actual Budget — authority for transactions/budgets (future)
- Role: **eventual authority for imported/recorded transactions, budgets, categories, accounts, and
  actual-payment history** — NOT document facts. Reconciliation to the ledger is a separate linked
  process (doc 7). Not installed/imposed.

### 1.8 Bitwarden — sole secrets/credential authority
- Role: **sole secrets/password/credential authority** (Tier-1). Never in the vault/index/chat/git.
  Vault/system only holds pointers ("login stored in Bitwarden as item X").

---

## Part 2 — Canonical document identity and crosswalk

### 2.1 Canonical identity fields
```text
canonical_document_id      stable, opaque, immutable across rename/move
source_system              e.g. GOOGLE_GMAIL, GOOGLE_DRIVE, GOOGLE_CALENDAR, LOCAL_SCAN, MANUAL
source_account_alias       gdrive / gdrive-sarah / local
source_native_id           upstream native id (Gmail message id / Drive file id / .eml name) where present
source_relative_path       path in the source/D: tree at acquisition
source_sha256              immutable hash of the original bytes
original_acquired_at       when the original was acquired locally
original_observed_modified_at   last observed source mtime at acquisition
evidence_archive_location  vault + D: path of the preserved original
lifecycle_system_id        id in the chosen lifecycle layer (future)
librechat_file_id          MongoDB/household file record id (wiring)
pgvector_file_id           pgvector custom_id / metadata file_id (index wiring)
current_version_id         id of the current/active version
supersedes_document_id     id this document supersedes (null if none)
subject_scope              CURRENT_HOUSEHOLD|MICHAEL|SARAH|ESTATE_OR_DECEASED_FAMILY|
                           OTHER_PERSON_OR_FAMILY_ARCHIVE|SEDDON_OR_SEPARATE_LEGAL_MATTER|
                           GENERAL_REFERENCE|UNKNOWN_REVIEW_REQUIRED
document_domain            utility|insurance|vehicle|property|health|education|finance|government|
                           legal|renewal|reference|other
document_type              bill|statement|policy|certificate|lease|rego|renewal_notice|letter|scan|email|...
correspondent_or_provider  normalized name
lifecycle_state            DISCOVERED|QUARANTINED|EXTRACTED_CANDIDATE|VALIDATION_FAILED|AWAITING_REVIEW|
                           VERIFIED|DISPUTED|SUPERSEDED|ARCHIVED
verification_state         (see Part 4)
extraction_status          NOT_EXTRACTED|EXTRACTED_CANDIDATE|EXTRACTION_REVIEW|EXTRACTION_FAILED
ocr_status                 NATIVE_OK|OCR_APPLIED|OCR_CANDIDATE|OCR_FAILED|NOT_NEEDED
safety_class               TIER1_SECRET|TIER2_IDENTIFIER|TIER3_DOCUMENT|GENERAL
retention_class            e.g. KEEP_PERMANENT|KEEP_7Y|KEEP_2Y|POINTER_ONLY|DESTROY_APPROVAL
```

### 2.2 Identity rules
- **Stable across rename/move**: `canonical_document_id` is immutable/opaque; source_relative_path may
  change; lookups use the canonical id, not the path.
- **Duplicates**: detect by source_sha256 + (native id / content) at intake; one canonical record can
  reference one or more physical copies; a duplicate is linked, not re-created.
- **New versions / amended bills**: a new version is a NEW canonical_document_id with
  supersedes_document_id pointing to the superseded one; current_version_id tracks the active one. Never
  overwrite an existing version.
- **Source deletion**: original may remain locally (copy semantics); lifecycle_state reflects
  historical/superseded; a remote deletion is recorded, not propagated as local delete.
- **OCR derivative lineage**: every OCR/text derivative carries the source_sha256 of its original
  (derived, never the original replacement).
- **Immutable source hash**: source_sha256 of the original bytes is the identity anchor for the original.
- **Generated documents**: system-generated outputs get their own canonical id, source_system=GENERATED,
  and link their input source ids.
- **Email plus attachment relationships**: an email (sender + subject + date) and its attachment(s) are
  linked via a message-group id; each is a retrievable document.
- **One document concerning multiple people**: subject_scope can be multi-valued (array); subject search
  is by scope, not by person-name-only.
- **One file containing multiple logical records**: one file may map to multiple canonical_document_id
  records (e.g., a combined bill with electricity + gas); each record references the same source file.
- **Current vs historical authority**: only records with lifecycle_state in
  VERIFIED/current version and subject_scope=current household serve as authoritative answers by default;
  historical/superseded/other-subject require explicit selection.

---

## Part 3 — Subject and access model

### 3.1 Subject scopes
```text
CURRENT_HOUSEHOLD
MICHAEL
SARAH
ESTATE_OR_DECEASED_FAMILY
OTHER_PERSON_OR_FAMILY_ARCHIVE
SEDDON_OR_SEPARATE_LEGAL_MATTER
GENERAL_REFERENCE
UNKNOWN_REVIEW_REQUIRED
```
- Subject scope is **authorization-neutral metadata** — it describes WHAT a document is about, distinct
  from WHO may see it (Part 3.2).

### 3.2 Access (authorization) — defined separately from subject
- **Michael's current access**: full administrative access to all scopes (sole LibreChat user today;
  one identity scope).
- **Future Sarah access**: OPEN_DECISION (H4). Two viable shapes to decide later: (a) a read-only modern
  household scope under an explicit grant, or (b) a separate successor scope. Not decided here.
- **Successor/continuity access**: runbooks grant access surfaced via continuity docs (pointers only),
  subject to explicit grant.
- **Default Household Admin scope**: **CURRENT_HOUSEHOLD only**. The agent/household-search returns
  current-household records by default and must NOT auto-include estate/family/archive/unknown.
- **Explicit separate search requirement**: estate/family/archive/other-person/Seddon are reachable only
  through a deliberate, separately-authorized subject selector — never by default and never bundled into
  a current-household overview.
- **No automatic inclusion of unknown records**: UNKNOWN_REVIEW_REQUIRED records are excluded from default
  responses; they surface only to a review queue for classification, not as retrieval content.
- **Minimum necessary disclosure**: retrieval returns only the minimum evidence for the explicit request;
  no unsolicited cross-scope/cross-domain inventories (mirrors the canonical INSTRUCTIONS.md/SKILL.md
  guardrails).
- **Generated-form multi-person risks**: a form pulling values must restrict to the form's target
  subject/person and never blend another person's identifiers; unresolved fields stay blank/flagged.
- **Audit**: log subject_scope, actor, and access decision for every cross-scope or form-generation
  action; no secret/raw values in logs.

---

## Part 4 — Verification state machine

No simple Boolean `verified` flag. A state + transition audit.

### States
```text
DISCOVERED            record seen/acquired, not yet processed
QUARANTINED           set aside pending review (credential-shaped, out-of-scope, anomaly)
EXTRACTED_CANDIDATE   automated extraction produced a candidate value/mapping
VALIDATION_FAILED     candidate failed validation (cannot be trusted)
AWAITING_REVIEW       candidate/conflict/stale item awaiting a human decision
VERIFIED              confirmed against a source document with confidence + approval
DISPUTED              conflicting evidence; unresolved until review
SUPERSEDED            replaced by a newer version (still retained, not authoritative)
ARCHIVED              finalised/retained for historical/continuity, not live* (*retention may differ)
```

### Transition record (required for every transition)
```text
actor/service         who or what changed the state
timestamp             when
source document/version  which canonical_document_id + version
previous state        prior verification_state
new state             new verification_state
value (if any)        the verified value and its unit (metadata, not Tier-1)
confidence            confidence/quality signal (e.g. HIGH/MED/LOW or numeric)
reason                why the transition happened
approval event        approval id/actor where applicable (e.g. Michael approval for VERIFIED of an
                      exact cost; destruction approval for ARCHIVED+dropping)
rollback/correction   how to revert and the correction history (immutable append log)
```

### Usage
- VERIFIED is the only state that answers exact-fact / deterministic questions by default.
- An EXTRACTED_CANDIDATE is offered only with an explicit "candidate" caveat and source, never as a fact.
- Automated promotions (DISCOVERED -> EXTRACTED_CANDIDATE) are logged; human-approved transitions
  (-> VERIFIED) require an approval event for high-stakes/lifecycle changes.
- The audit trail is append-only and exportable.

## Evidence ledger
- Parts 1-4 are DESIGN_REQUIREMENT proposals. Part 1 maps to current real layers (CONFIRMED_LIVE_FACT for
  existence) with proposed authoritative roles (DESIGN). Part 3.2 H4 is OPEN_DECISION. Subject-scope
  multi-value and cross-scope handling are DESIGN. No data changed.
