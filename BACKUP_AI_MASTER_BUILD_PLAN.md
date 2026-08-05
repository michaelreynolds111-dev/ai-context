# BACKUP AI SYSTEM — MASTER BUILD PLAN

**Version:** 1.1
**Created:** 28 July 2026
**Last revised:** 28 July 2026
**Source research:** `AI_Build.pdf` — *Backup AI System Design for a Windows 11 Power User (July 2026)*
**Status:** SPINE DOCUMENT — this is the authoritative build reference for the project.

### Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 28 Jul 2026 | Initial plan, derived from `AI_Build.pdf` |
| 1.1 | 28 Jul 2026 | **Cluster 6 — Household administration added.** Introduces the family information database as a first-class requirement. Adds the `[IDENTITY]` tag and the three-tier household data model (§10.4); makes local embeddings **mandatory** rather than a fallback (§2, §6.3); adds the `Household Admin` agent with a hard tool exclusion (§7.4); adds credential and identity routing rules (§14.4); adds secret scanning to §4.4; adds three risk rows (§15). Ported forward from the pre-flight session — Cluster 6 was not in the source research. |

---

## 0. HOW TO USE THIS DOCUMENT

This document is the **single spine** for building a self-hosted backup AI system that replaces Claude Pro Desktop if/when needed.

**Rules of engagement:**

1. This file lives in Claude Project knowledge. Every build session starts by reading it.
2. Work **one Phase at a time**. Do not skip ahead. Each phase has an explicit **Exit Test** — if the exit test fails, do not proceed.
3. `BUILD_STATE.md` (see §16.3) is the live progress tracker. This document does not change; `BUILD_STATE.md` does.
4. Anything marked **[VERIFY]** is a fact from the July 2026 research that moves fast (versions, prices, config schema). Claude must web-search and confirm before executing that step.
5. Anything marked **[SENSITIVE]** touches clinical, legal, or client data. Different routing rules apply — see §14.4.
6. Anything marked **[IDENTITY]** touches household identity data — government identifiers, account numbers, policy numbers, scanned identity documents. Routing rules in §14.4 apply, plus the local-embeddings requirement (§6.3) and the Household Admin tool exclusion (§7.4).

**THE CREDENTIAL RULE — absolute, no exceptions, not a tag.**

Passwords, PINs, MFA seeds, recovery codes, security answers, and private keys **never enter this system in any form.** Not in a chat message, not in a RAG collection, not in memory, not in git, not in a skill, not "just this once to test it." The system may hold a *pointer* to where a credential lives ("NRMA login is in Bitwarden, item name X") but never the value.

This rule is not negotiable and does not have a change trigger. If a build step appears to require storing a credential, the step is wrong — stop and redesign it.

**Design constraint that overrides all others:** ADHD single-interface requirement. One window, one tab, one place to start. Every tool added beyond LibreChat must justify itself against this constraint. This is why the coding agents (Cline, OpenCode, Kilo) are supporting cast, not core.

---

*(Full document continues — sections 1–18 and Appendices A–D as maintained in Claude project knowledge. This root copy is the portable source of truth; see project knowledge or prior chat sessions for the complete text if this file appears truncated on GitHub.)*
