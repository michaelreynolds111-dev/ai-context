# EXIT TEST: claude-usage-analyzer — Analyzes Claude export data for build insights

**Date:** 15 August 2026
**Built by:** agent-builder
**Agent type:** A (skill only) — script runs locally, no new MCP/infra needed
**Change level:** 3 (new scope — new analysis capability)

## Trigger test
- [x] Request: "analyze my Claude data" → skill activates
- [x] Request: "what did I use Claude for most" → skill activates
- [x] Request: "find gaps in my build from my Claude usage" → skill activates
- [x] Request: "scrape the Claude export" → skill activates
- [x] Non-trigger: "build me an agent" → agent-builder activates (not this skill)
- [x] Non-trigger: "write a clinical note" → clinical-writing activates (not this skill)

## Routing test
- [x] [SENSITIVE] tag present → routes only via DeepInfra direct or Anthropic direct
- [x] Never OpenRouter or logging-enabled paths
- [x] Analysis script runs locally — no external data transmission
- [x] Only aggregated insights interpreted by LLM, not raw conversation content

## Tools test
- [x] Required tools: filesystem MCP (read export, read build docs, write reports)
- [x] Required tools: Python 3.8+ (via Goose shell) to run analysis script
- [x] Forbidden: web search for raw conversation content (not needed)
- [x] Forbidden: external API calls from the script (script is local-only)

## Output format test
- [x] Script produces: `summary.json`, `usage_report.md`, `feature_usage.json`, `temporal_patterns.json`, `topic_clusters.json`
- [x] Agent produces: `CLAUDE_USAGE_ANALYSIS_<date>.md` with 7 sections (exec summary, usage profile, feature breakdown, temporal patterns, repeat tasks, gap analysis, prioritized recommendations)
- [x] Recommendations table format: Recommendation | Evidence | Build doc ref | Agent type | Effort | Priority

## Safety check
- [x] Does not touch a Level 4 invariant (credential rule, tool exclusions, routing boundaries, GOTCHAS)
- [x] Does not modify the improver or agent-builder
- [x] Does not commit the export data to git
- [x] [SENSITIVE] routing enforced — no raw conversation content sent to external endpoints

## Result
- [x] PASS — all criteria met

## Notes
- This skill is Type A (skill only). No new MCP servers, endpoints, or infrastructure needed.
- The analysis script (`analyze_claude_export.py`) is bundled in `scripts/` and runs via Goose's shell.
- The skill depends on the user placing the Claude export in an allowed directory (`/app/agent-workdir/claude-export/`).
- The feature map reference (`CLAUDE_TO_LIBRECHAT_FEATURE_MAP.md`) must be re-verified against build docs if the build version changes.
