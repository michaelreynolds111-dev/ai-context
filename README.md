# ai-context

Portable source of truth for the self-hosted backup AI build. Git-backed
markdown; no vendor lock-in at the memory/context level.

## Layout

- `skills/` -- portable SKILL.md capabilities (name + description frontmatter
  only, per the core Agent Skills spec -- no agent-specific frontmatter)
- `projects/` -- per-project instructions + knowledge (the Claude Projects
  equivalent)
- `memory/` -- human-readable long-term memory (preferences, people,
  systems, decisions)
- `mcp/` -- canonical MCP server list (`mcp-servers.json`), referenced by
  every client
- `docs/` -- source research and supporting docs

## What is deliberately NOT here

`~/household-vault/` lives outside this repo, is not a git repository, and
never becomes one. It holds [IDENTITY] material -- see
`BACKUP_AI_MASTER_BUILD_PLAN.md` section 10.4 for the tier model.

## Secret scanning

A gitleaks pre-commit hook is active (`.gitleaks.toml`, custom rules for AU
identifiers). It is a blocking control, not advisory. Do not disable it.

