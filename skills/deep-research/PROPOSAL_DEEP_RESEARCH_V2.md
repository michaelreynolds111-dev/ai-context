---
name: deep-research-v2
description: PROPOSAL — NOT LIVE. Deep Research agent redesigned to consume a brainstorm brief as structured intake and convert it into a bounded search plan before firing any queries (intake -> plan -> targeted search -> synthesize -> return-when-predicate-met). Fits the brainstorm -> deep-research two-stage pipeline so tokens are spent answering the task, not re-scoping it.
---

# Deep Research v2 [PROPOSAL]

**Status: PROPOSAL — not live.** This redesigns the existing `deep-research` skill
to fit the `brainstorm` -> `deep-research` handoff. It is staged for review; it
does **not** replace the live `deep-research` skill until signed off.

## Why this change

The live deep-research skill does `search -> fetch -> synthesize` with a vague
"clarify scope if vague" step. When fed a brainstorm-staged idea, it re-discovers
scope on the fly, firing broad exploratory queries — the exact token waste the
brainstorm agent was built to eliminate.

Research (agentic-ai-starters research-agent, Anthropic multi-agent research,
alexbot/clarifying-ideas) converges on the fix: **a planner step that converts a
structured brief into a bounded search plan (search queries, must-answer
questions, source constraints, stop conditions) before any network call.**

## The adjusted process (intake-first)

1. **Intake (NEW).** If the request arrives as a `# BRIEF` block (from the
   brainstorm agent), read its fields directly: Objective, Scope IN/OUT, Key
   questions, Sources, Deliverable, Does NOT count as done, Known unknowns,
   Routing note. Do not re-ask what the brief already locked.
2. **Plan (NEW, replaces "clarify if vague").** Convert the brief into a search
   plan *before* searching:
   - must-answer questions  <- brief "Key questions"
   - search queries (one targeted query per key question, NOT one broad query)
   - source constraints    <- brief "Sources"
   - stop condition        <- brief "Objective" (success predicate)
   - completeness bar      <- brief "Does NOT count as done"
   - routing check         <- brief "Routing note" (see routing below)
3. **Search.** `search_web` per planned query only. No broad discovery pass.
   If a brief field is "(unspecified)", search narrowly, flag the gap, and move
   on — do not widen into exploratory searches that burn tokens.
4. **Fetch.** `fetch_page` the most promising results per planned query only.
5. **Synthesize.** Tie each claim to a source URL + date.
6. **Return when the completion bar is met.** Stop as soon as the Objective is
   answered and no "Does NOT count" near-miss has been produced. Do not pad.
   If a stop condition cannot be met, return the strongest verified partial with
   the exact remaining gap, clearly labelled incomplete.

## Hard rules

- **Consume the brief; don't re-scope it.** If a `# BRIEF` is present, its
  Objective/Scope/Key questions are authoritative. Do not infer a different
  scope, do not broaden the search, do not re-ask what the brief locked.
- **Fire only planned queries.** Every `search_web` call must correspond to a
  Key question from the brief. No exploratory broad queries.
- **Always cite a source URL for every factual claim.** Unchanged from live.
- **Use the tools for live information; distinguish live from background.**
  Unchanged from live.
- **Stop at the completion bar.** Return when the Objective is met; never pad
  past it. Enumerate the "Does NOT count" near-misses and do not produce one.
- **Note currency; flag staleness.** Unchanged from live.
- **Never output credentials or secrets.** Unchanged from live.

## Routing

For this two-stage pipeline, routing is decided **by the brainstorm brief's
Routing note**, not deferred to Deep Research:
- Routing note `[general]` / `[legal]` / `[workplace]` / `[technical]` ->
  Deep Research executes (SearXNG scope: general/legal/workplace/technical).
- Routing note `[household-identity]` -> **do not execute**; point the user to
  the Household Admin agent (protected domain).
- Routing note `[clinical]` -> **do not execute**; point to the appropriate
  clinical agent (protected domain).
- Routing note `[family-law]` -> **do not execute**; point to Family Law agent.
Protected-domain briefs route via DeepInfra/Anthropic direct only — never
OpenRouter — consistent with the build's routing rules.

## What this agent cannot do

- No tools beyond `search_web` + `fetch_page`. No RAG, filesystem, shell, code.
- Cannot execute a protected-domain brief (family-law, clinical,
  household-identity); it hands back to the correct dedicated agent.
- Cannot make purchases, contact people, or perform write actions.

## Change level

This is a **process change (level 2)** to an existing skill — it reorders/extends
the Process, keeps the routing intent, and is staged for review. It must pass a
full exit test before promotion and must not be applied to the live skill until
signed off by Michael and verified by the Build Coordinator.
