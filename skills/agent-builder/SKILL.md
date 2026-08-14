---
name: agent-builder
description: Use when the user wants to create a new agent or skill. Triggers on requests to "build an agent", "make a skill", "create an agent that...", "scaffold a new agent", "set up a new skill", "I need an agent for...", or any request to add new agent capability to the system. This skill scaffolds new agents/skills following the build's conventions, safety architecture, and staging workflow.
---

# Agent Builder

## When to use
- "Build an agent that..."
- "Make a skill for..."
- "Create an agent to handle..."
- "Scaffold a new skill"
- "I need an agent for [task]"
- "Set up a new agent/skill"
- Any request to add new agent capability to the system

## Hard rules
- **Never proceed on memory.** Read the build docs fresh every time: `BUILD_STATE.md`, `docs/GOTCHAS.md`, and the Self-Improvement Protocol (if committed). This is the same ritual as AGENT_BOOTSTRAP.md.
- **Never write directly to `ai-context/skills/`.** Stage everything to `staging-ai-context/skills/{name}/`. Promotion is a human/Goose action via git.
- **Never touch a Level 4 boundary.** Run the safety check (Step 3) on every request. If the request touches a Level 4 invariant, refuse, explain why, and suggest an alternative.
- **Never modify an existing skill.** This skill creates new agents only. Modifying existing skills is the `skill-improver`'s job.
- **Cite source docs, don't duplicate them.** When the new skill needs to reference the safety architecture, change paths, or collaboration model, point to the source docs — don't copy their content into the new skill.
- **Always define exit tests.** A new agent without checkable exit tests is not done.

## Process

### Step 1 — INTAKE
Understand what the user wants the new agent to do. Ask:
- Domain: what is the agent's purpose?
- Triggers: what phrases/requests should activate it?
- Tools needed: does it need MCP servers, shell access, web search, RAG?
- Sensitive/identity content: does it handle [SENSITIVE] or [IDENTITY] data?
- Model/endpoint: does it need a specific model or routing path?
- Infrastructure: does it need scheduled tasks, Docker, new MCP servers?

### Step 2 — CLASSIFY (agent type)
Determine which type of agent this is:
- **Type A:** Skill only — just a SKILL.md, no infra
- **Type B:** Skill + MCP server — needs a new MCP server registered
- **Type C:** Skill + model/endpoint — needs endpoint config in librechat.yaml
- **Type D:** Skill + LibreChat agent — needs an agent definition in MongoDB
- **Type E:** Skill + infrastructure — Goose sets up scheduled tasks, Docker, etc.

### Step 3 — SAFETY CHECK
Run the Level 4 boundary check. Refuse if the request:
- Needs tools that Clinical Work / Household Admin / Paperwork are excluded from
- Handles credentials (Tier 1 secrets never enter the system)
- Changes routing boundaries
- Modifies the skill-improver or this meta-agent
- Contradicts a GOTCHAS entry

If any Level 4 boundary is touched: refuse, explain which boundary and why, suggest an alternative within Level 1–3.

### Step 4 — SCAFFOLD
Generate the SKILL.md following conventions. Use `templates/SKILL_TEMPLATE.md` as the base. Fill in:
- Frontmatter (name, description with triggers)
- Sections (When to use, Hard rules, Standards, Process, Output format, Routing)
- Routing tags if [SENSITIVE] or [IDENTITY]
- Any references/scripts/assets/templates the new skill needs

See `references/SKILL_ANATOMY.md` for the full anatomy with examples from the 8 existing skills.

### Step 5 — STAGE
Write all files to `staging-ai-context/skills/{name}/`. Never write directly to `ai-context/skills/`.

### Step 6 — PLAN GOOSE TASK (if infra needed, Type B/C/E)
If the agent needs infrastructure, write a GOOSE_TASK file to `agent-workdir/tasks/`:
- MCP server setup → GOOSE_TASK with Docker/MCP setup steps
- Endpoint config → GOOSE_TASK with librechat.yaml edit + restart
- Infrastructure → GOOSE_TASK with the specific setup steps

Use `templates/GOOSE_TASK_AGENT_INFRA.md`. Check `docs/GOTCHAS.md` for relevant environment facts before writing the task. See `references/BUILD_FLOWS.md` for the full change-path and handoff details.

### Step 7 — DEFINE EXIT TESTS
Define how to verify the new agent works. Use `templates/EXIT_TEST_TEMPLATE.md`. Cover:
- Trigger test (does the right phrase activate it?)
- Routing test (does it route correctly for its classification?)
- Tools test (are the right tools available, wrong ones excluded?)
- Output format test (does it produce the expected structure?)

### Step 8 — HAND OFF
Present the full package for the user's review:
- The staged SKILL.md and any subdirectory files
- The GOOSE_TASK file (if any)
- The exit test definition
- The promotion path (commit → sync → register in LibreChat if needed)

## Staying current
The `references/CURRENT_METHODS.md` doc captures current best practices. It carries a date stamp. Check the date on each use; if the doc is more than 3 months old, run a web search for current agent-building best practices and offer to refresh the doc before proceeding.

## Output format
Present the handoff package as:
1. **Summary** — what the new agent does, its type (A–E), and change level (1–3)
2. **Files staged** — list of files written to `staging-ai-context/skills/{name}/`
3. **GOOSE_TASK** — the task file (if infra needed), with its path
4. **Exit tests** — the checkable conditions
5. **Promotion path** — the exact commands to commit, sync, and register
6. **Open questions** — anything that needs the user's decision

## Routing
Build tool — not [SENSITIVE] or [IDENTITY]. Can route via any available endpoint.
