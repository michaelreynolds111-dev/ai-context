# Systems

## Machine: Michael-PC
- Windows 11 Home 26200
- CPU: i5-12400
- RAM: 15.8 GB (single stick: Crucial CT16G4DFRA32A.C16FT, DDR4-3200, Channel A DIMM 0 — upgrade deferred)
- C: 464 GB, FullyEncrypted (BitLocker/Device Encryption ON)
- D: FullyDecrypted — cannot be BitLockered (reason not yet captured). Live working dir of 7 scheduled tasks. Do not delete until Session 10 decommission.
- E: FullyDecrypted

## WSL2
- Distro: Ubuntu-24.04 (always target explicitly: `wsl -d Ubuntu-24.04 -- bash -lc "..."`)
- Default distro confirmed set to Ubuntu-24.04
- UNIX user: michael, home: /home/michael
- .wslconfig: memory=8GB, processors=6, swap=2GB — leave as-is through Phase 3+
- All project files live in WSL2 native fs (`~/`), NEVER /mnt/c/ or Windows paths

## Docker
- Docker Desktop 29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
- LibreChat stack at ~/LibreChat/ — 6 containers:
  - LibreChat (api, port 3080)
  - admin-panel (port 3000, internal)
  - chat-mongodb
  - chat-meilisearch
  - vectordb
  - rag_api
- All containers healthy as of 8 Aug 2026

## Key paths
- ~/LibreChat/ — LibreChat v0.8.7 clone
- ~/LibreChat/librechat.yaml — provider + MCP + model config
- ~/LibreChat/docker-compose.override.yml — all customisations
- ~/LibreChat/.env — secrets and config (never in git)
- ~/LibreChat/data-node/ — MongoDB data (fresh init 8 Aug 2026)
- ~/ai-context/ — git repo, source of truth
- ~/agent-workdir/ — agent read-write scratch space
- ~/household-vault/ — [IDENTITY] data, NOT a git repo, never becomes one

## Git / GitHub
- Repo: michaelreynolds111-dev/ai-context (private, master branch)
- Auth: HTTPS + PAT via git credential helper (store), ~/.git-credentials, perms 600
- gitleaks 8.30.1 at ~/.local/bin/gitleaks, pre-commit hook active with Australian identifier rules
- Push via local git always — GitHub MCP connector unreliable across long sessions

## Scheduled tasks on D:\Data (7 live, do not touch until Session 10)
- ArchiveDailySync, DailyDashboard, FamilyBriefing, rclone Drive Sync, rclone VFS Cache Clean, Resource Watchdog, TorBox Mount

## Inference
- Primary: DeepInfra (HIPAA/ISO27001/GDPR, zero-retention)
- Ceiling tier: anthropic/claude-sonnet-5 via DeepInfra
- OpenRouter: scaffolded/commented out (backlog, v1.2)
- Anthropic direct: optional, not currently wired
- Tavily: native LibreChat integration, TAVILY_API_KEY in .env, 1000 free credits/month
