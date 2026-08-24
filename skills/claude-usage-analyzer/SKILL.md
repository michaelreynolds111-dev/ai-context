---
name: claude-usage-analyzer
description: Use when analyzing Claude.ai export data to understand usage patterns, identify which features were used most, surface features that could have been useful, and generate build-improvement recommendations for the LibreChat/Goose build. Triggers on requests to "analyze my Claude data", "what did I use Claude for", "scrape the Claude export", "compare Claude vs LibreChat", "find gaps in my build", "optimize my build from Claude usage", or any mention of the Claude data export / conversations.json.
---

# Claude Usage Analyzer

## When to use
- "Analyze my Claude export data"
- "What did I use Claude for most?"
- "Scrape the Claude export for insights"
- "Compare what I did in Claude vs what LibreChat can do"
- "Find gaps in my build based on my Claude usage"
- "Generate build suggestions from my Claude history"
- Any mention of `conversations.json` or the Claude data export

## Hard rules
- **Never proceed on memory.** Read the build docs fresh every time: `BUILD_STATE.md`, `docs/USAGE_PATTERNS.md`, and `docs/V0_8_7_CAPABILITIES.md` via filesystem MCP. This is the same ritual as AGENT_BOOTSTRAP.md.
- **Never upload the raw export to any external service.** The Claude export contains the user's full conversation history — [SENSITIVE] personal data. Analysis runs locally via the Python script; only aggregated/summarized insights leave the script.
- **Never send raw conversation content through OpenRouter or any logging-enabled path.** If using an LLM to interpret the aggregated analysis, route via DeepInfra direct or Anthropic direct only.
- **Always run the analysis script first, then interpret.** Do not eyeball the JSON. The script produces structured aggregates; the agent interprets those aggregates.
- **Always cite the source build doc** when proposing a gap or improvement. Every recommendation must trace back to either (a) a pattern in the data or (b) a capability in the build docs.
- **Never modify the build.** This skill analyzes and recommends. Implementation is the user's call, executed via Goose tasks or the agent-builder skill.

## Standards
- Language: Plain, analytical, direct. No hedging.
- Tense: Present tense for findings ("You use X most"), future tense for recommendations ("Add Y to enable Z").
- Length: Findings concise with counts/percentages; recommendations prioritized by impact.
- Format: Structured Markdown with tables for comparisons, bullet lists for recommendations.

## Process

### Step 1 — LOCATE & VALIDATE THE EXPORT
1. Confirm the Claude export is accessible. The user downloads it from claude.ai Settings → Privacy → Export Data; Anthropic emails a download link. The zip contains `conversations.json` (and possibly `projects.json`, `account.json`).
2. The export must be placed in an allowed directory: `/app/agent-workdir/claude-export/` (create it) or another path the filesystem MCP can reach.
3. If the export is a zip, ask the user (or write a Goose task) to unzip it into `/app/agent-workdir/claude-export/`.
4. Validate: confirm `conversations.json` exists and is valid JSON before proceeding.

### Step 2 — READ BUILD CONTEXT
Read these fresh via filesystem MCP (do not rely on memory):
- `BUILD_STATE.md` — current phase, what's built, what's deferred
- `docs/USAGE_PATTERNS.md` — how LibreChat and Goose collaborate
- `docs/V0_8_7_CAPABILITIES.md` — what the current build can do
- `mcp/mcp-servers.json` — which MCP servers are wired
- `skills/*/SKILL.md` — the existing skill inventory (what capabilities exist)

### Step 3 — RUN THE ANALYSIS SCRIPT
Run `scripts/analyze_claude_export.py` against the export. The script:
- Parses `conversations.json` (handles the standard Claude export schema)
- Extracts: conversation count, message counts, temporal patterns, artifact usage, project usage, tool/feature usage signals, topic clustering (keyword frequency), conversation length distribution, repeat-task detection
- Produces structured JSON + Markdown reports in the output directory
- Handles large files via streaming (does not load entire file into memory twice)

Usage:
```bash
python3 scripts/analyze_claude_export.py \
  --input /app/agent-workdir/claude-export/conversations.json \
  --output /app/agent-workdir/claude-export/analysis/
```

If the script is not yet present (first run), see `references/SCRIPT_DEPLOYMENT.md` for the Goose task to create it.

### Step 4 — INTERPRET THE AGGREGATES
Read the script's output reports. Identify:
1. **Top usage domains** — what did the user actually do most? (coding, writing, research, legal, clinical, household admin, etc.)
2. **Feature usage signals** — artifacts, projects, file uploads, web search, long context, multi-turn planning
3. **Temporal patterns** — when, how often, session length
4. **Repeat tasks** — things done many times that could be automated/skilled
5. **Gaps** — features used in Claude that LibreChat/Goose doesn't yet replicate

### Step 5 — MAP FINDINGS TO BUILD CAPABILITIES
Compare each finding against the current build (from Step 2):
- Does LibreChat/Goose already support this? (check `V0_8_7_CAPABILITIES.md` + skill inventory)
- Is it partially supported? (e.g. RAG exists but not configured for this domain)
- Is it missing entirely? (gap)
- Could an existing skill be extended? (recommendation for skill-improver)

### Step 6 — PRODUCE THE REPORT
Write the final report to `/app/agent-workdir/outputs/CLAUDE_USAGE_ANALYSIS_<date>.md` with:
1. **Executive summary** — top 5 findings
2. **Usage profile** — what the user did, with counts and percentages
3. **Feature usage breakdown** — which Claude features were used, how often
4. **Temporal patterns** — when and how the user works
5. **Repeat tasks & automation opportunities** — things done repeatedly
6. **Gap analysis** — Claude features used vs LibreChat/Goose capabilities (table)
7. **Prioritized recommendations** — ranked by impact, each with: what, why (citing data + build doc), how (which agent type / Goose task), effort level

## Output format
- **Analysis reports** (from script): `analysis/summary.json`, `analysis/usage_report.md`, `analysis/feature_usage.json`, `analysis/temporal_patterns.json`, `analysis/topic_clusters.json`
- **Final report** (from agent): `outputs/CLAUDE_USAGE_ANALYSIS_<date>.md` — structured Markdown with the 7 sections above
- **Recommendations table**: columns = Recommendation | Evidence (data) | Build doc ref | Agent type | Effort | Priority

## What this agent cannot do
- Cannot execute build changes — it analyzes and recommends only.
- Cannot access the Claude export if it's outside the allowed filesystem directories. The user must place it in an allowed path.
- Cannot send raw conversation content to external services — only aggregated insights.
- Cannot determine which Claude model was used per conversation — the export does not include this field.

## Routing [SENSITIVE]
This skill handles [SENSITIVE] content (the user's full Claude conversation history). Route only via DeepInfra direct or Anthropic direct. Never OpenRouter or any logging-enabled path. The analysis script runs locally; only aggregated, non-conversation-level insights are interpreted by the LLM.
