# GOOSE TASK: <descriptive name>

## Context
<2-3 sentences: why this task exists, what phase it's part of>

## Objective
<One clear sentence: what "done" looks like>

## Prerequisites
- Read `BUILD_STATE.md` (current phase section)
- Check `docs/GOTCHAS.md` if touching Docker, WSL, shell, or MCP
- <Any env state that must be true before starting>

## Steps
1. <Step 1 — concrete, copy-pasteable>
2. <Step 2>
3. ...

## Success criteria (exit test)
- [ ] <Checkable condition 1>
- [ ] <Checkable condition 2>

## Constraints
- Follow hard rules in `AGENT_BOOTSTRAP.md` §4
- <Anything Goose must NOT do>

## Output
Write `GOOSE_RESULT_<name>.md` to `~/agent-workdir/outputs/` with:
- What was done (step-by-step summary)
- What succeeded / what failed
- Commands run and their output (trimmed if >2000 tokens)
- State of the system after execution
- Any follow-up needed
