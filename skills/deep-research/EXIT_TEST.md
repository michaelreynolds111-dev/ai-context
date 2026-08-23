# EXIT TEST: deep-research — Deep Research agent

**Date:** 23 August 2026
**Built by:** agent-builder (Build Coordinator)
**Agent type:** B + D (skill + MCP server + LibreChat agent)
**Change level:** 3 (scope)

## Trigger test
- [ ] Request: "Research the current state of [topic]" activates the Deep Research agent + skill
- [ ] Request: "Find out what the latest evidence says about [X]" activates it
- [ ] Actual: <record result>

## Routing test
- [ ] General-knowledge scope — no [SENSITIVE]/[IDENTITY] tag; routes via DeepInfra (any endpoint)
- [ ] Does NOT touch household/clinical/family-law agents or their routing
- [ ] Actual: <record result>

## Tools test
- [ ] Required tools available: `search_web`, `fetch_page`
- [ ] Forbidden tools excluded: `filesystem`, `shell`, `runCode`/code exec, `spotify`,
      `household-search`, `drive`, `github-buildstate`, `secondhand`, browser/web (the
      native "web search" — this agent uses SearXNG via MCP), memory writes
- [ ] Actual: <record result>

## Output format test
- [ ] Every factual claim has an inline source URL
- [ ] "no sources found" when nothing relevant returned (no padding)
- [ ] Currency/staleness flagged where relevant
- [ ] Research-vs-advice distinction flagged for law/medicine/finance/tax
- [ ] Actual: <record result>

## Safety check
- [ ] No Level 4 invariant touched (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [ ] No credential/secret in any staged or committed file
- [ ] `fetch_page` is SSRF-bounded (private addresses rejected)
- [ ] Actual: <record result>

## Result
- [ ] PASS — all criteria met
- [ ] FAIL — <which criteria failed, why>
