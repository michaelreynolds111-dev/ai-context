# EXIT TEST: deep-research-v2 — Deep Research agent (brief-consuming)

**Date:** 27 August 2026
**Built by:** agent-builder (Build Coordinator)
**Agent type:** B + D (skill + MCP server [search_web, fetch_page] + LibreChat agent)
**Change level:** 2 (process redesign of the live `deep-research` skill)

## Trigger test
- [ ] Request: paste a brainstorm `# BRIEF` block -> the agent consumes Objective/Scope/Key questions without re-asking
- [ ] Request: "Research the current state of [topic]" -> plans queries before searching
- [ ] Actual: <record result>

## Intake/plan test (NEW behavior)
- [ ] When a `# BRIEF` is present, the Objective and Key questions are treated as authoritative (no re-scoping, no broad discovery pass)
- [ ] A search plan (one query per key question + stop condition + completeness bar) is formed before any `search_web` call
- [ ] "(unspecified)" fields are flagged and searched narrowly, not widened into exploratory queries
- [ ] Actual: <record result>

## Routing test
- [ ] `[general]`/`[legal]`/`[workplace]`/`[technical]` brief -> executes
- [ ] `[household-identity]`/`[clinical]`/`[family-law]` brief -> does NOT execute; points to the correct dedicated agent
- [ ] Protected-domain brief routes via DeepInfra/Anthropic direct, never OpenRouter
- [ ] Actual: <record result>

## Tools test
- [ ] Required tools available: `search_web`, `fetch_page`
- [ ] Forbidden tools excluded: filesystem, shell, code, RAG/file_search, memory writes, browser
- [ ] Actual: <record result>

## Completion-bar test (NEW behavior)
- [ ] Returns as soon as the Objective is answered and no "Does NOT count" near-miss is produced (no padding)
- [ ] If the bar can't be met, returns strongest verified partial + exact remaining gap, labelled incomplete
- [ ] Actual: <record result>

## Output format test
- [ ] Every factual claim has an inline source URL
- [ ] "no sources found" when nothing relevant returned (no padding)
- [ ] Currency/staleness flagged; conflicts presented
- [ ] Research-vs-advice distinction flagged for law/medicine/finance/tax
- [ ] Actual: <record result>

## Safety check
- [ ] No Level 4 invariant touched (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [ ] Does not modify the improver or agent-builder
- [ ] No credential/secret in any staged or committed file
- [ ] `fetch_page` is SSRF-bounded (private addresses rejected) — unchanged from live
- [ ] Live `deep-research` skill untouched; this is a staged proposal until signed off
- [ ] Actual: <record result>

## Result
- [ ] PASS — all criteria met
- [ ] FAIL — <which criteria failed, why>
