# CURRENT_METHODS — Agent-Building Best Practices (2026)

**Date stamp:** 14 August 2026
**Staleness rule:** If this doc is more than 3 months old, run a web search for
"AI agent building best practices [current year]" and offer to refresh this
doc before proceeding.
**Purpose:** Capture current (2026) best practices from the field for building
agents, and their implications for this build.

---

## 1. HARNESS/SCAFFOLDING > MODEL UPGRADES

LangChain's Deep Agents team achieved significant gains on Terminal-Bench 2.0
using the **same underlying model** — only the harness changed. The scaffolding
around the model (context assembly, tool-output formatting, retry management)
produced better results than a model upgrade would.

**Implication for this build:** The SKILL.md structure, routing tags, hard
rules, and exit tests ARE the harness. Get them right and a weaker model
performs well; get them wrong and a stronger model underperforms. This is why
the `agent-builder` follows the conventions of the 8 existing skills so
closely — the conventions are the proven harness.

---

## 2. SEPARATION OF ROLES

The agent that proposes a change is not the agent that applies it, and neither
is the agent that evaluates whether the change helped. This avoids the
conflict of interest when an agent improves itself.

**Implication:** the agent-builder (proposes/scaffolds) ≠ Goose
(applies/executes) ≠ LibreChat (evaluates/verifies). This is already the
build's collaboration model — the agent-builder inherits it.

---

## 3. START SIMPLE, ADD COMPLEXITY ONLY WHEN THE SIMPLE LOOP WORKS

Do not add planning layers, parallel execution, or multi-agent orchestration
until the simple loop works reliably. Complexity in harnesses compounds — a
subtle bug in a simple harness is easy to find; the same bug inside a planning
layer inside a multi-agent system is not.

**Implication:** new agents should start as a single SKILL.md with clear rules.
Add references/, scripts/, templates/ only when the skill outgrows a single
file. The agent-builder itself demonstrates this — its SKILL.md is lean and
points to references/templates rather than carrying everything inline.

---

## 4. LAYERED GUARDRAILS

Production patterns combine input validation, output filtering, tool-risk
ratings, and human-intervention triggers.

**Implication:** the agent-builder's safety check (Step 3) is the input
validation layer. The hard rules in each new skill's SKILL.md are the output
filtering layer. The exit tests are the human-intervention trigger. The
4-level change classification is the tool-risk rating.

---

## 5. PERSISTENT NOTE-TAKING FOR CROSS-SESSION LEARNING

The Confucius Code Agent (Meta/Harvard, Feb 2026) uses persistent notes for
cross-session learning.

**Implication:** the build already has this — BUILD_STATE.md, GOTCHAS.md, and
the task/result file protocol are the persistent notes. The agent-builder
reads them fresh each time rather than carrying its own cache.

---

## 6. GOOSE IS MCP-NATIVE

Goose (donated to the Linux Foundation's Agentic AI Foundation, April 2026)
treats every capability as an MCP server.

**Implication:** when the agent-builder plans a Type B agent (skill + MCP), it
should design the MCP server to be Goose-compatible, not just
LibreChat-compatible.

---

## 7. SKILLS ARE THE UNIT OF AGENT CAPABILITY

Modern agent frameworks (Claude Skills, LibreChat Agent Skills, Goose skills)
treat a "skill" as a versioned, reviewable bundle — a SKILL.md plus optional
references, scripts, assets, and templates. Skills are model-invoked based on
their description/triggers, have ACLs and scoping, and can be imported/synced.

**Implication:** the agent-builder scaffolds skills — the standard unit of
agent capability in this ecosystem. A new capability = a new skill bundle.

---

*End of current methods. Re-search and refresh if older than 3 months.*
