# Cluster 6 Household Administration Platform — Build Path

**Date:** 23 August 2026  
**Primary goal:** turn the existing household RAG corpus into a practical household administration platform for document explanation, exact cost questions, renewals, and controlled form preparation—without discarding the completed LibreChat, pgvector, file-record, identity, safety, or Goose handoff work.

## 1. North-star outcome

Michael should be able to ask questions such as:

- “Explain the nature of my Maxxia novated lease.”
- “What am I paying for electricity per month?”
- “Which insurance or registration items expire in the next 90 days?”
- “Find the latest document about this provider.”
- “Prepare this administrative form using verified household records.”

The system must answer from evidence, cite its sources, use exact calculations where needed, distinguish verified facts from inferred candidates, and require Michael’s approval before generating or changing administrative records.

## 2. Preserve-first architecture

### Existing assets to retain unchanged

The current build is not a failed direction. It becomes the document intelligence foundation:

- `~/household-vault/` remains the source archive.
- The existing `household` pgvector collection remains the semantic index.
- The existing 1,935 LibreChat MongoDB file records remain the document registry.
- The existing 27,803 embedding rows remain in place.
- Existing local `sentence-transformers/all-MiniLM-L6-v2` embeddings remain the index/query model.
- Existing Michael-aligned RAG identity metadata remains the authorization boundary.
- Existing manifests, checkpoints, exclusions, failure logs, and rollback artifacts remain the audit trail.
- LibreChat remains the user interface and agent host.
- Goose remains the controlled implementation executor.
- The existing household project instructions and `household-admin` skill remain the behavioural policy source.

### Target architecture

```text
LibreChat Household Admin
        |
        +-- Household document search tool
        |       -> existing RAG API
        |       -> existing household pgvector collection
        |       -> source-labelled passages
        |
        +-- Household facts/ledger tool
        |       -> verified structured household database
        |       -> exact calculations, dates, totals, trends
        |
        +-- Household workflow tool
                -> controlled extraction and form preparation
                -> preview and approval
                -> new output file only
```

This is an additive architecture. No completed data layer is replaced until a successor has passed an explicit parity test.

## 3. Non-negotiable boundaries

- Do not re-index the 1,935 working documents unless an embedding-model migration is separately approved.
- Do not migrate away from pgvector merely to use a community template.
- Do not attach 1,935 file IDs to one LibreChat agent.
- Do not expose arbitrary SQL, MongoDB, pgvector, shell, filesystem, or Docker tools to Household Admin.
- Do not allow OpenRouter routing for household-sensitive content.
- Keep agent memory disabled.
- Do not put secrets, credential values, vectors, raw exception payloads, or full database records into logs.
- Do not overwrite original household documents or blank templates.
- Do not submit forms or contact providers automatically.
- Any write-capable workflow must require an explicit preview and approval step.
- Each implementation phase must preserve a tested rollback path.

## 4. Delivery strategy

Build in vertical slices that create useful functionality early while protecting the current system.

### Slice 1 — Whole-corpus document search

**User value:** explain contracts, locate documents, answer source-grounded questions over the whole 1,935-file corpus.

**Implementation:** extend the existing RAG API with a fixed-scope, read-only collection query route that reuses the already-loaded embedding model; expose it through one narrow internal MCP tool.

**Model-facing tool:**

```text
search_household_documents
```

**Initial input:**

```json
{
  "query": "plain-language household search",
  "max_results": 5
}
```

**Server-side constraints:**

- collection fixed to `household`;
- identity derived internally from the authenticated LibreChat user;
- caller cannot supply collection, identity, SQL, paths, or endpoint details;
- `max_results` defaults to 5 and is capped at 10;
- read-only;
- no content-bearing logs;
- bounded, sanitized errors;
- no external network exposure.

**Output:** bounded excerpts, generated file ID, safe source label, relevance, and available freshness metadata.

**Exit test:** at least 40 deterministic searches across all current extensions and all known corpus groupings; 100% authorized retrieval, zero unrelated sources, zero former/unrelated-scope access, no vector/data changes.

### Slice 2 — Household Admin agent

**User value:** one safe conversational interface for household questions.

**Configuration:**

- DeepInfra direct model route approved by the project state;
- canonical household instructions plus `household-admin` skill constraints;
- exactly one tool: `search_household_documents`;
- zero file attachments;
- memory disabled;
- no browser, web, code, shell, filesystem, database, Actions, or unrelated MCP tools.

**Behaviour tests:**

- explains a selected non-sensitive agreement using sources;
- finds a known document;
- asks for clarification on an ambiguous cost question;
- says “not found” when evidence is absent;
- refuses credential requests;
- does not use outside knowledge for household facts;
- cites source labels;
- cannot call an unapproved tool.

### Slice 3 — Metadata enrichment without re-embedding

**User value:** better filtering, chronology, latest-document selection, provider grouping, and duplicate/version handling.

Create a separate structured metadata registry keyed by the existing generated `file_id`. Do not rewrite vectors initially.

Suggested fields:

```text
file_id
safe_source_label
document_type
household_domain
provider
subject
effective_date
billing_period_start
billing_period_end
due_date
expiry_date
supersedes_file_id
source_status
extraction_status
verification_status
verified_at
```

Start with deterministic metadata from paths/manifests, then add content-derived candidates through a reviewed extraction workflow.

**Exit test:** every enriched record maps to exactly one existing file ID; no source file or embedding changes; date/provider filters return expected records; ambiguous extractions remain unverified.

### Slice 4 — Verified household ledger

**User value:** exact answers to cost, due-date, renewal, and trend questions.

Build a structured ledger separate from the semantic index. Use PostgreSQL unless a measured workload justifies another database. Reusing the existing database platform minimizes operational drift; ClickHouse is optional later for higher-volume analytics, not required for household scale.

Initial domains:

1. utilities;
2. vehicle and novated lease;
3. insurance;
4. registrations and licences;
5. subscriptions and recurring services;
6. household renewals.

Example utility schema:

```text
record_id
provider
service_type
billing_period_start
billing_period_end
billing_days
amount_due
usage_quantity
usage_unit
supply_charge
usage_charge
credits
payment_amount
payment_frequency
source_file_id
extraction_confidence
verification_status
```

Example lease schema:

```text
record_id
provider
vehicle_reference
agreement_start
agreement_end
pay_cycle
packaged_deduction
finance_component
running_cost_component
residual_amount
review_date
source_file_id
verification_status
```

**Tool:**

```text
query_household_ledger
```

This must expose predefined analytical intents rather than arbitrary SQL.

Examples:

```text
monthly_average
period_total
latest_amount
cost_trend
upcoming_expiries
lease_summary
```

**Exit test:** exact totals reconcile against a hand-checked sample; duplicate/amended bills are not double-counted; every returned value carries source IDs and calculation method.

### Slice 5 — Automated ingestion and review queue

**User value:** new bills and agreements become searchable and analytically useful with minimal manual work.

A workflow engine such as n8n can orchestrate:

```text
new document
-> classify
-> extract candidate fields
-> validate schema
-> detect duplicate/version
-> add to review queue
-> Michael approves/corrects
-> write verified ledger record
-> index document if eligible
-> update renewal schedule
```

Do not make n8n the source of truth. It coordinates work; verified records remain in the household registry/ledger.

**Exit test:** process a small set of synthetic or low-risk documents; failed extraction creates a review item, not a silent record; no automatic destructive action.

### Slice 6 — Renewals and reminders

**User value:** proactive household administration.

Capabilities:

- upcoming renewal list;
- due-soon and overdue items;
- missing-current-document detection;
- price-change review prompts;
- reminder creation after approval.

Start with in-app reports. Add notifications only after dates and ownership are verified.

**Exit test:** known test renewals trigger at the correct windows; stale/superseded documents do not create duplicate reminders.

### Slice 7 — Controlled administrative form preparation

**User value:** prepare forms using verified records.

Workflow:

```text
blank template
-> identify fields
-> map fields to verified facts
-> show value + source + confidence
-> require Michael approval
-> create a new draft
-> preserve original
```

Tools should be narrow:

```text
inspect_administrative_template
prepare_administrative_draft
```

Generation must occur in a dedicated document service or controlled Goose workflow—not through unrestricted agent filesystem/code access.

Rules:

- no automatic submission;
- no silent identifier insertion;
- unresolved fields remain blank or flagged;
- derived values show calculation method;
- generated files use new names;
- audit record lists sources and approvals.

**Exit test:** complete a synthetic or non-sensitive template end-to-end and compare every populated field with its approved source.

### Slice 8 — Optional Paperless-ngx document-management layer

Paperless-ngx is valuable if Michael wants richer document lifecycle features such as correspondents, tags, document types, inbox processing, OCR review, page preview, and controlled downloads.

It should be considered after Slices 1-4, not installed immediately. The present vault, pgvector corpus, and MongoDB registry already provide working storage and search foundations.

Adoption decision gate:

- identify a concrete lifecycle problem the current vault cannot solve;
- prove import preserves source provenance and file IDs;
- run in parallel;
- do not delete the current vault or index;
- require parity for search, metadata, backup, and access control.

## 5. Today’s build plan

### Batch A — Restore the missing collection-query primitive

Create one Goose task that:

1. forks or stages the exact deployed RAG API source/version;
2. adds only `POST /query_collection` using the existing in-process embedding object;
3. fixes collection to `household`;
4. derives identity from JWT only;
5. caps results and sanitizes errors/logging;
6. adds unit, authorization, integrity, and regression tests;
7. builds a pinned canary image;
8. tests against a scratch/copy-safe path;
9. recreates only `rag_api` after all gates pass;
10. verifies the original `/query`, `/ids`, `/embed`, and delete contracts remain unchanged;
11. verifies all household and testcollection counts/digests remain unchanged;
12. preserves image/config rollback.

Stop if the route requires a schema migration, re-embedding, or broad server refactor.

### Batch B — Add the one-tool MCP adapter

After Batch A passes, create one Goose task that:

1. builds a tiny pinned stdio or internal-only MCP adapter;
2. exposes only `search_household_documents`;
3. calls the internal `/query_collection` route;
4. rejects identity/collection overrides and unknown fields;
5. enforces result and timeout limits;
6. registers it agent-only in LibreChat;
7. recreates only the API container if required;
8. runs positive and negative tests;
9. proves unrelated MCP servers and routes unchanged;
10. writes rollback and manual agent instructions.

### Batch C — Create and verify Household Admin

Michael performs the single UI Save action. Goose then verifies live structure and runs the bounded behaviour suite.

### Batch D — First useful structured vertical slice

Implement **electricity costs first** because it exercises document retrieval, extraction, verification, calculations, dates, and trends.

Deliverables:

- utility ledger schema;
- extraction candidate workflow;
- manual review view/file;
- deterministic monthly-cost calculation;
- `query_household_ledger` tool with electricity intents;
- source-linked answers.

Target question:

> “What am I paying for electricity per month?”

The answer must distinguish latest bill, scheduled payment, and calculated average, asking a clarification where needed.

### Batch E — Maxxia lease vertical slice

Add verified lease fields and test:

> “Explain the nature of my Maxxia novated lease.”

The answer should combine semantic retrieval with structured lease facts, identify gaps, and cite the agreement/statement sources. It must not characterize the answer as professional financial advice.

### Batch F — Form-preparation pilot

Use one low-risk administrative template. Implement inspect -> map -> preview -> approval -> generate-new-copy. No submission.

## 6. Build-drift controls

Every Goose task must include:

- one clear objective;
- authoritative input list;
- explicit files/services permitted to change;
- baseline counts and checksums;
- pre-change rollback;
- canary before batch;
- stop conditions;
- post-change parity checks;
- one result file;
- no BUILD_STATE update inside implementation tasks;
- session close only after Build Coordinator verifies the result.

Maintain an architecture decision record for every non-trivial platform addition:

```text
problem
options considered
decision
assets preserved
new operational burden
security boundary
rollback
exit test
```

## 7. What not to do today

- Do not install Paperless-ngx, ClickHouse, Qdrant, and n8n all at once.
- Do not migrate the working pgvector corpus into another vector database.
- Do not rebuild embeddings merely to add metadata.
- Do not expose generic database MCP tools to Household Admin.
- Do not give the agent write-capable document tools before retrieval and ledger reads pass.
- Do not create the Household Admin agent until its collection-wide search tool is live.
- Do not begin form autofill before verified structured facts exist.

## 8. Completion definition for the main goal

The household administration platform reaches its first production-ready milestone when Michael can:

1. ask a whole-corpus document question and receive a sourced answer;
2. ask an exact electricity-cost question and receive a verified calculation with contributing sources;
3. ask for a lease explanation and receive a grounded synthesis;
4. list upcoming verified renewals;
5. prepare one administrative form through preview and approval;
6. confirm no source file was overwritten and no action was submitted automatically;
7. review a complete audit trail of tools, sources, calculations, and approvals.

## 9. Immediate next action

Create and execute:

`GOOSE_TASK_CLUSTER6_RAG_QUERY_COLLECTION_ROUTE.md`

Single objective:

> Add and live-verify one fixed-scope, read-only `/query_collection` route in the deployed RAG API using the existing loaded embedding model, with complete regression and rollback protection and no data migration, re-embedding, MCP registration, or agent creation.

After it passes, create the separate MCP-adapter task.
