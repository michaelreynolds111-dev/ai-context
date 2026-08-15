# Safety Architecture — Extract from the Self-Improvement Protocol

**Source:** `docs/SELF_IMPROVEMENT_PROTOCOL.md` v2.0, §3 (committed at `ai-context/docs/`).
**Purpose:** The safety architecture the agent-builder inherits. This is an extract with citation — the canonical version lives in the protocol. Read it fresh from `ai-context/docs/SELF_IMPROVEMENT_PROTOCOL.md` rather than relying on this extract.
**Extracted:** 14 August 2026.

---

## 1. THE 4-LEVEL CHANGE CLASSIFICATION

Every proposed change is classified into one of four levels. The level
determines the change path and the safety constraints. This classification is
**structural** — Level 4 changes are not merely discouraged, they are
**forbidden by design**.

| Level | Description | Change path | Human checkpoint | Auto-revert |
|---|---|---|---|---|
| **Level 1 — Wording** | Rephrasing, clarification, tone adjustment within an existing instruction or skill | Dynamic (API PATCH or UI edit) | Required | Yes (eval suite) |
| **Level 2 — Process** | New step in a workflow, revised handoff format, new eval task | Dynamic or staged (depends on target) | Required | Yes (eval suite) |
| **Level 3 — Scope** | New skill, new MCP server, new model, new agent, expanded tool access | Staged (staging dir → validate → promote) | Required | Yes (eval suite) |
| **Level 4 — Forbidden** | Changes to safety rules, routing boundaries, tool exclusion lists, or the improver itself | **NOT PERMITTED** | N/A — never proposed | N/A |

**Building a new agent is a Level 3 change** (new skill/agent). It follows the
staged path: stage in `staging-ai-context/` → validate → promote via git.

---

## 2. NAMED HARD INVARIANTS (LEVEL 4 — NEVER TOUCH)

These are the structural boundaries the agent-builder must never propose
changes to. A new agent must never be designed to cross them:

1. **Credential Rule** — no credentials, tokens, or secrets in any
   `ai-context/` file, skill, agent instruction, or trace. The gitleaks
   pre-commit hook enforces this at commit time. A new agent must never be
   designed to store or output Tier 1 secrets (passwords, PINs, MFA seeds,
   recovery codes).

2. **Clinical Work tool exclusion** — the `Clinical Work` agent has
   `tools: []` (hard exclusion). Never propose adding tools to this agent.
   This keeps clinical output on DeepInfra/Anthropic direct ONLY.

3. **Household Admin tool exclusion** — the `Household Admin` agent has
   `tools: []` (hard exclusion). Never propose adding tools to this agent.
   Household identifiers are retrieved via scoped RAG only, never via tool
   calls.

4. **Paperwork agent routing** — the Paperwork agent routes to
   DeepInfra/Anthropic direct ONLY, with no tools. Classification [SENSITIVE].
   Never propose changing this routing or adding tools.

5. **GOTCHAS invariants** — every entry in `docs/GOTCHAS.md` is a hard-won
   environmental fact. The agent-builder must not propose changes that
   contradict a GOTCHAS entry when planning Goose tasks.

6. **Read-only safety boundary** — `/app/ai-context` and `/app/LibreChat`
   are read-only to LibreChat (via filesystem MCP). The agent-builder stages
   new skills to `agent-workdir/staging-ai-context/`; promotion is a
   human/Goose action via local git. Never write directly to production paths.

7. **Self-modification of the improver** — the agent-builder must not propose
   changes to itself or to the skill-improver. This is structural, not
   advisory.

---

## 3. HOW THE AGENT-BUILDER APPLIES THIS (STEP 3 — SAFETY CHECK)

At the safety-check step, run through the Level 4 list. If the proposed new
agent touches any Level 4 boundary, the agent-builder:
1. Refuses to scaffold it.
2. Explains which boundary is touched and why.
3. Suggests an alternative that stays within Level 1–3.

For Level 1–3 changes, proceed but flag the level in the handoff package so
the user knows the change path and checkpoint requirements.

**Concrete refusal triggers:**
- New agent needs tools that Clinical Work / Household Admin / Paperwork are
  excluded from → FORBIDDEN
- New agent handles credentials → Credential Rule applies (Tier 1 never in
  system)
- New agent changes routing boundaries → FORBIDDEN
- New agent modifies the improver or this meta-agent → FORBIDDEN
- New agent contradicts a GOTCHAS entry → FORBIDDEN

---

*End of extract. The canonical safety architecture lives in
`docs/SELF_IMPROVEMENT_PROTOCOL.md` §3 (committed at `ai-context/docs/`).
Re-read it fresh rather than relying on this extract.*
