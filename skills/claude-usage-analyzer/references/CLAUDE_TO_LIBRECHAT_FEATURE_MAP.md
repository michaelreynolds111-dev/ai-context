# CLAUDE_TO_LIBRECHAT_FEATURE_MAP — Gap Analysis Reference

**Purpose:** Maps Claude.ai features (that may appear in the export data) to the current LibreChat/Goose build capabilities. Used by the claude-usage-analyzer skill to identify gaps.

**Last verified:** 15 August 2026 (against LibreChat v0.8.7, build docs in `ai-context/`)

---

## Feature Mapping Table

| Claude Feature | Signal in Export Data | LibreChat/Goose Equivalent | Status |
|---|---|---|---|
| **Artifacts (code)** | `artifacts` array, code type | LibreChat Artifacts (v0.8.7 supports) | ✅ Available |
| **Artifacts (SVG/HTML/React)** | `artifacts` array, svg/html/react type | LibreChat Artifacts | ✅ Available |
| **Projects** | `project` UUID on conversations | LibreChat RAG collections + `ai-context/projects/` | ✅ Available (configured) |
| **File uploads** | `attachments` or `files` on messages | LibreChat file upload + RAG | ✅ Available |
| **Web search** | Text patterns: "search the web", tool_use with search | Tavily MCP (LibreChat only) | ⚠️ Partial — LibreChat only, not Goose |
| **Long context (>30 msgs)** | Message count per conversation | DeepInfra endpoints (200K context) | ✅ Available |
| **Multi-turn planning** | >10 human messages per conversation | LibreChat multi-turn + agent skills | ✅ Available |
| **Custom instructions (Projects)** | Project association | LibreChat presets + `ai-context/projects/` | ✅ Available |
| **Model switching** | (Not in export — no model field) | LibreChat model switching | ✅ Available |
| **MCP tools** | tool_use blocks in content | LibreChat MCP + Goose MCP | ✅ Available (filesystem, Spotify) |
| **Memory/personalization** | (Not directly in export) | `ai-context/memory/` + LibreChat memory | ✅ Available (custom build) |
| **Code execution** | tool_use with code interpreter | LibreChat Code Interpreter | ⚠️ Check config |
| **Image analysis** | Image attachments | LibreChat vision models | ✅ Available (via DeepInfra) |
| **Scheduled tasks** | (Not in export) | Goose scheduled tasks / cron | ⚠️ Partial — needs setup |
| **Voice input** | (Not in export) | LibreChat voice input | ⚠️ Check config |
| **Conversation branching** | (Not in export) | LibreChat branching (regenerate) | ✅ Available |
| **Conversation search** | (Not in export) | LibreChat message search | ✅ Available |
| **Export data** | (This is the export) | LibreChat export | ✅ Available |
| **Agent skills** | (Not in export) | `ai-context/skills/` (8 skills) | ✅ Available (custom build) |
| **Thinking/extended reasoning** | (Not in export) | DeepInfra Claude models | ✅ Available |
| **Google Drive integration** | (Not in export) | Pending OAuth (`mcp-servers.json`) | ❌ Gap — pending |
| **Microsoft 365 integration** | (Not in export) | Pending OAuth (`mcp-servers.json`) | ❌ Gap — pending |
| **Browser/computer use** | (Not in export) | Not available | ❌ Gap |
| **Real-time collaboration** | (Not in export) | Not available | ❌ Gap (out of scope) |

---

## How to Use This Table

1. After running the analysis script, check which features the data shows were used.
2. Cross-reference each used feature against this table.
3. Features marked ⚠️ or ❌ are candidates for build improvements.
4. Features marked ✅ are already covered — no action needed.
5. For ⚠️ items, check the specific config (e.g. is Code Interpreter enabled in `librechat.yaml`?).
6. For ❌ items, decide if they're in scope for the build (some, like real-time collaboration, are not).

## Domain-to-Skill Mapping

The analysis script detects usage domains. Here's how each maps to existing skills:

| Usage Domain | Keywords in Data | Existing Skill | Gap? |
|---|---|---|---|
| Clinical/NDIS writing | SOAP, NDIS, referral, case note | `clinical-writing` | ✅ Covered |
| Family law drafting | FCFCoA, parenting, financial | `seddon-family-law-drafter` | ✅ Covered |
| Financial forensics | dissipation, asset pool, tracing | `seddon-financial-forensics` | ✅ Covered |
| Household admin | bill, appointment, reminder | `household-admin` | ✅ Covered |
| PowerShell/sysadmin | PowerShell, script, WSL, Docker | `powershell-sysadmin` | ✅ Covered |
| Workplace law research | Fair Work, award, employment | `workplace-law-research` | ✅ Covered |
| Build/dev work | agent, skill, MCP, LibreChat | `agent-builder`, `plan-executor` | ✅ Covered |
| General coding | Python, JavaScript, function | (No dedicated skill) | ⚠️ Could add |
| Research/web search | search, find, latest, news | Tavily MCP (LibreChat) | ⚠️ Goose lacks web search |
| Creative writing | story, poem, draft, write | (No dedicated skill) | ⚠️ Could add |
| Data analysis | CSV, analyze, chart, statistics | (No dedicated skill) | ⚠️ Could add |

---

*Re-verify this table against `docs/V0_8_7_CAPABILITIES.md` and `mcp/mcp-servers.json` if the build version changes.*
