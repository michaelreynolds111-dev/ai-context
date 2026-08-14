# GOOSE_TASK: <descriptive_name>

Write this file to `agent-workdir/tasks/GOOSE_TASK_<NAME>.md` and have Goose
execute it. Base it on `prompts/GOOSE_TASK_TEMPLATE.md` or the `goose-task`
alias. Follow `docs/USAGE_PATTERNS.md` §4 for the handoff protocol.

> **Channel rule for the plan-executor:** use a GOOSE_TASK **only** when the
> item needs shell, Docker, WSL file operations, Task Scheduler, or other
> infrastructure that only Goose can do. Do NOT use it for anything the
> plan-executor agent (or Michael) can do directly. Never duplicate Goose.

## Context
<2-3 sentences: why this task exists, what build item it covers (cite the
BUILD_STATE.md deferred/Session-10/backlog item), which bottleneck it clears>

## Objective
<One clear sentence: what "done" looks like>

## Prerequisites
- Read `BUILD_STATE.md` — state the current phase/sub-step.
- Check `docs/GOTCHAS.md` if touching Docker, WSL, shell, or MCP.
- <Any env state that must be true before starting — e.g. which decisions are
  already made (H3/H4/ai-workspace path), which earlier items are done>

## Steps
1. <Step 1 — concrete, copy-pasteable>
2. <Step 2>
3. <Step 3>

## Success criteria (exit test)
- [ ] <Checkable condition 1> — from the item's exit test in BUILD_STATE /
      master plan / SESSION_10_WORKSPACE_PLAN.md
- [ ] <Checkable condition 2>
- [ ] <Checkable condition 3>
- [ ] <No containers/live systems were disrupted that shouldn't be>

## Constraints
- Follow hard rules in `AGENT_BOOTSTRAP.md` §4.
- **Never touch a Level 4 boundary** (credential rule, clinical/household/
  paperwork tool exclusions, routing boundaries, GOTCHAS invariants).
- **Never store or output Tier-1 secrets.** Credential quarantine is a
  Michael-manual step with guidance — Goose must not copy secret values into
  any file/trace.
- <GOTCHAS-specific constraints for this environment — WSL2 distro targeting,
  quoting layers, Docker boot races, no `docker compose down <service>`,
  single-file bind-mount fragility, etc.>
- Do NOT touch `Clinical Work` / `Household Admin` / `Paperwork` agent tool
  configs.

## Output
Write `GOOSE_RESULT_<name>.md` to `~/agent-workdir/outputs/` with:
- What was done (step-by-step summary)
- What succeeded / what failed
- Commands run and their output (trimmed if >2000 tokens)
- State of the system after execution
- Any follow-up needed

After verification, the plan-executor moves this task/result pair to
`agent-workdir/archive/` and drafts a `BUILD_STATE.md` update block.
