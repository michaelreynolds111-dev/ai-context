# EXIT TEST: <skill-name> — <short description>

**Date:** <timestamp>
**Built by:** agent-builder
**Agent type:** A (skill only) | B (+MCP) | C (+model/endpoint) | D (+LibreChat agent) | E (+infra)
**Change level:** 1 (wording) | 2 (process) | 3 (scope)

## Trigger test
- [ ] Request: "<test phrase that should trigger the skill>"
- [ ] Expected: the skill activates
- [ ] Actual: <record result>

## Routing test
- [ ] If [SENSITIVE]/[IDENTITY]: routes only via <allowed paths>
- [ ] If no classification: routes via any endpoint
- [ ] Actual: <record result>

## Tools test
- [ ] Required tools available: <list>
- [ ] Forbidden tools excluded: <list>
- [ ] Actual: <record result>

## Output format test
- [ ] Produces: <expected output structure>
- [ ] Actual: <record result>

## Safety check
- [ ] Does not touch a Level 4 invariant (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [ ] Does not modify the improver or agent-builder
- [ ] Actual: <record result>

## Result
- [ ] PASS — all criteria met
- [ ] FAIL — <which criteria failed, why>
