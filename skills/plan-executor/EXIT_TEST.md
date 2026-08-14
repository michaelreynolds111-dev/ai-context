# EXIT TEST: plan-executor — Remaining-build-plan execution skill

**Date:** 14 August 2026
**Built by:** agent-builder (Build Coordinator)
**Agent type:** A (skill only) + D (attached to a LibreChat agent, dynamic, no restart)
**Change level:** 3 (scope — new skill)

## Trigger test
- [ ] Request: "Execute the next item in the build plan"
- [ ] Expected: the skill activates, reads BUILD_STATE fresh, states the current position, and proposes the next un-done item in document order
- [ ] Actual: <record result>

## Routing test
- [ ] Not [SENSITIVE] or [IDENTITY]: routes via any available endpoint
- [ ] Actual: <record result>

## Tools test
- [ ] Required tools available: filesystem MCP (read /app/ai-context, read-write /app/agent-workdir)
- [ ] Forbidden tools excluded: no shell, no Docker, no Task Scheduler (those are Goose's domain)
- [ ] Actual: <record result>

## Channel test (the key new behaviour)
- [ ] The three-channel model works: Goose task files written for infra, LibreChat-direct for planning/staging/verification, phone-friendly step-by-step manual instructions for Michael
- [ ] Does NOT duplicate what Goose can do with shell/Docker
- [ ] Actual: <record result>

## Output format test
- [ ] Produces: Position → Channel → What was done → Exit test → BUILD_STATE update → Next item
- [ ] Actual: <record result>

## Safety check
- [ ] Does not touch a Level 4 invariant (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [ ] Refuses Tier-1 handling; stages to staging-ai-context/; never writes to ai-context/ or LibreChat/
- [ ] Actual: <record result>

## Real-task test (the definitive exit test)
- [ ] A real remaining-build item (e.g. the first Session 10 step that is not blocked — verify Docker anomaly, or the next un-blocked deferred item) is executed end-to-end through the correct channel, verified against its exit test, and recorded in a BUILD_STATE update
- [ ] Actual: <record result>
