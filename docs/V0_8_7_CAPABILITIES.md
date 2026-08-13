# LibreChat v0.8.7 Capabilities — Change Without Restart Reference

**Date:** 13 August 2026
**Status:** Staged — awaiting commit to `ai-context/docs/`
**Purpose:** Reference document for the Self-Improvement Protocol. Maps which
LibreChat v0.8.7 capabilities allow live changes (no restart) vs. which require
a container restart. Cited by `SELF_IMPROVEMENT_PROTOCOL.md` §4.

---

## 1. DYNAMIC CHANGES (NO RESTART)

These capabilities were introduced or confirmed in v0.8.7. Changes via these
mechanisms take effect immediately — no `docker compose restart api` needed.

### 1.1 Admin panel per-role/group config overrides

The admin panel (port 3000) supports per-role and per-group configuration
overrides. This means model selection, endpoint routing, and feature flags
can be changed for a specific role (e.g., ADMIN) or group without affecting
other users and without restarting the `api` container.

**What this enables for self-improvement:**
- Swap a model for the Research agent role without disrupting Clinical Work
- Test a new endpoint for one group before rolling it out system-wide
- Toggle a feature flag for a single role to A/B test behaviour

### 1.2 MCP allowlist changes via UI

MCP servers can be added to the allowlist via the admin panel UI without
restarting the `api` container. The MCP server becomes available to agents
immediately after UI registration.

**What this enables for self-improvement:**
- Register a new MCP server for a specific agent without downtime
- Test an MCP server against one agent before expanding access
- Retire an MCP server by removing it from the allowlist (no restart)

**Note:** The MCP server itself must be running and reachable at registration
time. The allowlist change is live; the server process is a separate concern.

### 1.3 Agent skill authoring via UI

Agents can author, edit, import, and sync skills via the admin panel / agent
UI. UI-registered skills are available immediately — no restart needed.

**What this enables for self-improvement:**
- Add a new skill to an agent without restart
- Revise a skill's instructions and have the change take effect immediately
- Import a skill from an external source and test it live

**Note:** Skills defined in `librechat.yaml` (if any) would require restart.
UI-registered skills do not. The distinction matters for the change path
(see `SELF_IMPROVEMENT_PROTOCOL.md` §4).

### 1.4 Agent instructions via API PATCH

Agent system prompts, routing rules, and tool lists can be updated via API
PATCH to the agent endpoint. Changes take effect immediately.

**What this enables for self-improvement:**
- Update an agent's system prompt to clarify behaviour (Level 1 change)
- Add a new step to an agent's workflow (Level 2 change)
- Adjust routing rules for an agent (Level 2 change — but see §3.2 invariant
  #2, #3, #4: tool-list changes to Clinical Work, Household Admin, or Paperwork
  are Level 4 / forbidden)

### 1.5 Agents and prompts in MongoDB

Agent definitions and prompts are stored in MongoDB, not in flat files parsed
at startup. Changes to MongoDB records are picked up live.

**What this enables for self-improvement:**
- Agent instruction changes persist across restarts (they are in the DB, not
  in a file that gets re-parsed)
- No need to edit `librechat.yaml` for agent-level changes

---

## 2. STAGED CHANGES (RESTART REQUIRED)

These changes require editing `librechat.yaml` and restarting the `api`
container (`docker compose restart api` or `docker compose up -d api`).

### 2.1 `librechat.yaml` changes

Any change to `librechat.yaml` requires a container restart. The file is
parsed at startup; live edits are not picked up.

**Affected config:**
- `endpoints:` block — endpoint definitions, model lists, provider config
- `memory:` block — `validKeys` for the memory system
- `mcpServers:` block — MCP server definitions (note: the *allowlist* can
  change via UI without restart, but adding a *new server definition* to the
  YAML requires restart)
- `speech:` block — STT configuration
- Any top-level config key

### 2.2 Restart procedure

```bash
# In WSL2, from the LibreChat directory:
cd ~/LibreChat
docker compose restart api

# Or, if the container needs recreation (e.g., after a bind-mount change):
docker compose up -d api
```

**GOTCHAS (see `docs/GOTCHAS.md`):**
- Never `docker compose down <service>` — Compose V2 ignores the service arg
  and tears down the entire project. Use `restart` or `up -d`.
- After a restart, `rag_api` may take ~20-30s to reload its model. Don't panic
  at a transient "RAG API not reachable" warning.
- If the container fails to start after restart (exit 127), use
  `docker compose up -d api` to recreate from the current override file.

---

## 3. DECISION MATRIX

| Change type | Mechanism | Restart? | Stage in |
|---|---|---|---|
| Agent system prompt | API PATCH | No | `staging-ai-context/` (for review) → apply via API |
| Agent routing rules | API PATCH | No | `staging-ai-context/` → apply via API |
| Agent tool list (non-forbidden agents) | API PATCH | No | `staging-ai-context/` → apply via API |
| Agent tool list (Clinical Work, Household Admin, Paperwork) | **FORBIDDEN** | N/A | N/A — Level 4 |
| New skill (UI-registered) | Admin panel UI | No | `staging-ai-context/skills/` → register via UI |
| Skill revision (UI-registered) | Admin panel UI | No | `staging-ai-context/skills/` → edit via UI |
| New MCP server (allowlist) | Admin panel UI | No | `staging-ai-context/mcp/` → register via UI |
| New MCP server (definition) | `librechat.yaml` | Yes | `staging-librechat/` → edit YAML → restart |
| Model swap (per-role/group) | Admin panel override | No | `staging-librechat/` (for review) → apply via UI |
| Model swap (global default) | `librechat.yaml` | Yes | `staging-librechat/` → edit YAML → restart |
| Endpoint change (per-role/group) | Admin panel override | No | `staging-librechat/` → apply via UI |
| Endpoint change (global) | `librechat.yaml` | Yes | `staging-librechat/` → edit YAML → restart |
| Memory `validKeys` | `librechat.yaml` | Yes | `staging-librechat/` → edit YAML → restart |
| STT config | `librechat.yaml` | Yes | `staging-librechat/` → edit YAML → restart |
| Feature flag (per-role/group) | Admin panel | No | `staging-librechat/` → apply via UI |
| Feature flag (global) | `librechat.yaml` | Yes | `staging-librechat/` → edit YAML → restart |
| Skill/doc/config file in `ai-context/` | Git commit | N/A | `staging-ai-context/` → git commit |

---

## 4. SOURCES

- LibreChat v0.8.7-rc1 changelog — admin panel per-role/group config overrides
- LibreChat v0.8.7 changelog — MCP allowlist without restart, agent skill authoring
- LibreChat MCP documentation — MCP server registration via UI
- LibreChat `librechat.yaml` documentation — restart-required config
- LibreChat admin panel documentation — per-role/group overrides
- LibreChat agent API documentation — agent endpoint PATCH
- LibreChat releases page — v0.8.7 release notes

---

*End of capability reference. Staged at
`agent-workdir/staging-ai-context/docs/V0_8_7_CAPABILITIES.md` — awaiting
commit to `ai-context/docs/`.*
