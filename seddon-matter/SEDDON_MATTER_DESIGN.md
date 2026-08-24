# Seddon Matter — Storage & Access Design

**Date:** 2026-08-15
**Status:** DRAFT — staged for review/promotion. Not yet committed.
**Author:** Plan Executor
**Purpose:** Resolve the family-identity correction (Azzopardi Reynolds vs Seddon) and define how Sam Seddon's legal documents are stored securely within the existing system while remaining readily accessible to the AI build for analysis.

---

## 1. Family identity correction (the facts)

- **Household:** Michael Reynolds + Sarah Azzopardi = the **Azzopardi Reynolds** family. This is the household that owns the Bitwarden vault, the household SCHEMA/INSTRUCTIONS, and the Household Admin agent.
- **Sam Seddon = Sarah's sister** = Michael's **sister-in-law**.
- The `seddon-source/` legal/forensic documents (asset pool, dissipation schedules, NAB bank statements, forensic reports, tax files, source-reference index) belong to **Sam Seddon's Federal Circuit and Family Court of Australia matter** (property settlement under FLA s.79, financial abuse / Kennon arguments).
- **Michael holds NO passwords and NO account access to any Seddon account.** He is a **custodian** of Sam's documents — he stores them securely and the AI build analyzes/drafts from them.
- The Seddon matter is **[SENSITIVE] third-party legal work**, a distinct workstream from the household's [IDENTITY] data and distinct from the household's own Tier-1 credentials.

## 2. What Michael has asked for

> "I need her legal documents to be readily accessed by the AI build for analysis, but to be stored as securely as possible within the existing system."

Translation into build terms:
1. **Readily accessible by the AI build for analysis** — the seddon-family-law-drafter and seddon-financial-forensics skills (and any drafting/analysis work) must be able to read the Seddon source documents.
2. **Stored as securely as possible within the existing system** — the documents themselves must not sit in plaintext anywhere a credential-bearing file would, and must inherit the system's [SENSITIVE] protections (local-only routing, DeepInfra/Anthropic direct only, never OpenRouter).

## 3. Current state (what already exists)

- `/app/seddon-source/` is **already mounted** in LibreChat's filesystem MCP allowlist (`librechat.yaml` → filesystem server args include `/app/seddon-source`). The AI build can already read these documents.
- The two `seddon-*` skills already route [SENSITIVE] via DeepInfra/Anthropic direct only.
- The documents are **separate from `ai-context/`** (they are not in the git repo, not committed).
- The household vault (`~/household-vault/`) is [IDENTITY] and does NOT hold Seddon legal documents — correct separation already.

## 4. Key design decision — how the Seddon docs are stored

**Decision:** The Seddon source documents are **[SENSITIVE] third-party legal Tier-3 documents** — for analysis/drafting by the AI build — **not** Tier-1 credentials and **not** household [IDENTITY] data. They do NOT go into the household vault and do NOT involve the household Bitwarden vault. They live in a **dedicated, separately-scoped, secure source directory** that the AI build reads for analysis.

**Why this is the correct framing:**
- They authenticate nothing (no logins) → not Tier-1.
- They are not the household's own identity data → not [IDENTITY]/household vault.
- They are legal case documents for drafting/analysis → [SENSITIVE] Tier-3, exactly what the seddon-* skills are for.
- Michael holds documents, not access → no credentials to enter anywhere.

**Concrete placement:**
- Keep `/app/seddon-source/` as the canonical read-only source tree that the AI build's filesystem MCP reads (already wired in `librechat.yaml`).
- It is **not** in `ai-context/` git repo (no commit risk), **not** in `household-vault/` (no [IDENTITY] co-mingling), and **not** referenced by any Bitwarden collection.
- **Encryption at rest:** the source directory sits on the encrypted `C:` drive (host is FullyEncrypted) — it already inherits the machine's disk encryption. For "as securely as possible," the source copy lives on encrypted `C:` and the accepted exposure model mirrors the household staging tree (encrypted disk, local-only routing).

**Note on "as securely as possible within the existing system":** the existing system trusts encrypted-C: at-rest + local-only routing (never OpenRouter) + no git commit of the source. That is the ceiling the build supports for [SENSITIVE] documents. If Michael wants stronger (e.g. a dedicated VeraCrypt volume for the Seddon source), that is a separate enhancement beyond the current build — flag it, but the current design already satisfies "readily accessible for analysis + stored securely within the existing system."

## 5. What this corrects in the build docs (staged edits)

### 5.1 `MICHAEL_MANUAL_BITWARDEN_GUI_CHECKLIST.md` (Step B) — org belongs to the household, no Seddon collection
- ❌ Old: org named "Seddon Household"; "Legal Case Shared" collection.
- ✅ New: org named for the **Azzopardi Reynolds household**; collections are household-scope only. **No Seddon collection** — Michael holds no Seddon logins, so there is nothing to share for the legal matter. The legal documents are stored as documents (Step 4 of this design), not as credentials.

### 5.2 `goose-recipe-bitwarden-security-audit.yaml` — the generated checklist text
- The manual-checklist text it emits should carry the corrected Step B (household org, no Seddon collection). Verify and edit the recipe's output template accordingly.

### 5.3 `seddon-family-law-drafter` SKILL.md — clarify third-party custodian framing
- The skill is correct that it drafts for **Samantha Seddon's** FCFCoA proceedings. Add an explicit note that Michael is drafting/analyzing **on her behalf from documents she provides**, holds **no account access** to any Seddon account, and works from the `seddon-source/` documents only. No credential/account access framing.

### 5.4 `seddon-financial-forensics` SKILL.md — same clarification
- Same custodian/documents-only note: figures come from the `seddon-source/` source documents (PocketSmith CSV, bank statements, tax returns, payslips). No account access.

### 5.5 `docs/MIGRATION_INVENTORY.md` — resolve the "Investigate Chris Bank Accounts" open question
- Row status: **STAYING PUT / not a household credential.** The "Chris Bank Accounts" (Chris Seddon) material is part of Sam's financial-forensics matter (account #5192/#8940 NAB statements in `seddon-source/`), **[SENSITIVE] third-party legal**, not the household's personal system credential data. The open question "should it be migrated into this personal system at all?" is answered: it stays within the **Seddon source scope** (`seddon-source/`), analyzed by the seddon-* skills, and is NOT a Tier-1 quarantine target and NOT an item for the household vault or the household Bitwarden. No values, no credentials.

### 5.6 Household `SCHEMA.md` / `INSTRUCTIONS.md` — no change needed
- Already correctly describe the Azzopardi Reynolds household fields/behaviour. The Seddon matter is deliberately out of household scope. No Seddon logins or legal-document references belong in the household vault.

## 6. Routing & security (unchanged, confirmed)

- Seddon content is [SENSITIVE] → route only via **DeepInfra direct or Anthropic direct**. Never OpenRouter, never a logging-enabled path. Confirmed in both seddon skills.
- Local embeddings only for [SENSITIVE]/[IDENTITY] at index time (`rag_api` runs `sentence-transformers` in-container). Any Seddon document indexed into a RAG collection must use local embeddings — before that happens, confirm no outbound traffic at index time (same rule as household index).
- Documents are not committed to git. `seddon-source/` is not in `ai-context/`.

## 7. Decisions recorded

1. **No dedicated Seddon RAG collection — RESOLVED (2026-08-15, Michael decision).** Analysis reads the `seddon-source/` documents **directly** via the filesystem MCP + the two `seddon-*` skills. No question-answering RAG collection is built for the Seddon matter. This keeps it simple: the source stays read-only, and the drafting/forensics skills read files directly. If QA-against-source ever becomes a real need, it would be a separate future build item (scoped `seddon` collection, **local embeddings**, tool-excluded agent) — not built now.
2. **Encryption at rest beyond encrypted-C:** open enhancement only. If Michael wants a VeraCrypt volume for the Seddon source specifically, that is a future hardening item. The existing encrypted-C + local-routing model already meets "readily accessible + stored securely within the existing system." No action now.

## 8. Summary of staged edits (all in `staging-ai-context/seddon-matter/`)

| File | Change | Channel |
|---|---|---|
| `MICHAEL_MANUAL_BITWARDEN_GUI_CHECKLIST.md` | Step B org renamed to household; remove "Legal Case Shared" collection | staged here → promote |
| `goose-recipe-bitwarden-security-audit.yaml` | corrected manual-checklist Step B text | flagged; recipe lives in agent-workdir/recipes (Goose/editable), verify there |
| `seddon-family-law-drafter/SKILL.md` | add custodian/documents-only note | staged here → promote |
| `seddon-financial-forensics/SKILL.md` | add custodian/documents-only note | staged here → promote |
| `docs/MIGRATION_INVENTORY.md` | resolve Chris-Bank-Accounts open question (STAYING PUT in Seddon scope) | staged here → promote |

**Promotion path:** these staged files are reviewed by Michael, then committed/promoted into `ai-context/` by Goose or Michael (git commit + push). LibreChat cannot write directly to `ai-context/`.
