# EXIT TEST: brainstorm — Brainstorm / task-shaping agent

**Date:** 27 August 2026
**Built by:** agent-builder (Build Coordinator)
**Agent type:** A + D (skill only, no infra; optional LibreChat agent with `tools: []`)
**Change level:** 1 (wording) / scoped

## Trigger test
- [ ] Request: "I have a rough idea for building an app that tracks [X]" activates the brainstorm skill
- [ ] Request: "Help me shape this idea so I can hand it to the deep research agent" activates it
- [ ] Request: "Barely-articulated thought + 'research this for me'" activates it
- [ ] Actual: <record result>

## Routing test
- [ ] Non-sensitive idea → routes via DeepInfra, no OpenRouter
- [ ] Idea touching clinical/family-law/household-identity → Routing note flags the domain; routes via DeepInfra/Anthropic direct only
- [ ] Actual: <record result>

## Tools test
- [ ] Required tools available: **none**. Skill must run with `tools: []`.
- [ ] Forbidden tools excluded: web search, fetch_page, RAG/file_search, filesystem, shell, code exec, memory writes
- [ ] Actual: <record result>

## Output format test
- [ ] Produces a structured brief with (at least most of): Objective, Scope (IN/OUT), Key questions, Sources, Deliverable, Does NOT count as done, Known unknowns
- [ ] Brief length ~200–400 words (ultra-low token)
- [ ] Does NOT add filler / rephrase user's idea back at them
- [ ] Marks unresolved fields as "(unspecified)" instead of inventing them
- [ ] Actual: <record result>

## Token-usage test (the user's explicit requirement)
- [ ] No web/RAG/tool calls fired (zero tool tokens)
- [ ] Output bounded to the brief only (no extra reasoning dumps)
- [ ] Actual: <record result>

## Safety check
- [ ] No Level 4 invariant touched (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [ ] Does not modify the improver or agent-builder
- [ ] No credential/secret in any staged or committed file
- [ ] Actual: <record result>

## Result
- [ ] PASS — all criteria met
- [ ] FAIL — <which criteria failed, why>
