# Decisions

## Architecture
- LibreChat v0.8.7 as the hub (not Open WebUI / LobeChat / Cherry Studio) — 8 Aug 2026
- Goose as capability ceiling, not Crush (Apache-2.0 vs FSL-1.1-MIT) — decided pre-build
- DeepInfra primary inference; OpenRouter backlog/resilience only (v1.2, 7 Aug 2026)
- Git-backed markdown as source of truth — not any app's internal DB
- Do NOT build on Roo Code — shut down Apr 2026
- Local embeddings mandatory for [SENSITIVE]/[IDENTITY] content — never a hosted endpoint at index time
- Credentials never enter this system in any form — password manager only

## Build decisions (session by session)
- Ubuntu-24.04 LTS chosen (over 26.04) — 1 Aug 2026
- WSL2 default distro set to Ubuntu-24.04 — 1 Aug 2026
- RAM upgrade deferred; .wslconfig stays 8GB through Phase 3+ — 1 Aug 2026
- D:\Data NOT deleted — live working dir of 7 tasks; decommission at Session 10 — 1 Aug 2026
- GitHub auth: HTTPS + PAT — 1 Aug 2026
- gitleaks over git-secrets, installed user-local — 5 Aug 2026
- Default branch: master — 5 Aug 2026
- OpenRouter demoted to backlog; DeepInfra covers full model tier — 7 Aug 2026
- rag_api switched to full image (local embeddings) — 7 Aug 2026
- Desktop Commander adopted for build execution in Claude Desktop — 7 Aug 2026
- MongoDB fresh init over WiredTiger recovery (lost data = test only) — 8 Aug 2026
- UID=1000 in .env NOT the fix for MongoDB UID/GID warnings (causes crash-loop) — 8 Aug 2026
- Desktop Commander NOT wired into LibreChat (shell can't be safely scoped without per-call confirmations) — 8 Aug 2026
- Filesystem MCP: @modelcontextprotocol/server-filesystem, scoped to ai-context/ (ro) + agent-workdir/ (rw) — 8 Aug 2026
- Tavily native integration over MCP server (simpler, covers §7.3 + §7.5) — 8 Aug 2026
- Google Drive + M365 OAuth deferred (human-gated, 30-45min each, steps in GOTCHAS §9) — 8 Aug 2026
- OpenMemory deferred (requires OpenAI key for extraction LLM by default; §14.4 violation) — 8 Aug 2026
- Model picker: endpointsMenu: false + modelSpecs with 18 models in 5 tiers, fetch: false — 8 Aug 2026

## Open decisions
- H3: Password manager — Google PM current; Bitwarden recommended. UNDECIDED (hard dependency for Session 10)
- H4: Sarah's household access — Option A (shared machine) recommended. UNDECIDED
- Why can't D: be BitLockered? — Worth pinning before Session 10
- OpenMemory LLM provider swap — needs investigation before Phase 5 OpenMemory step
