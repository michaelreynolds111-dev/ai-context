# BUILD STATE

**Last updated:** 7 August 2026
**Current phase:** Phase 3 — Agents + MCP (§7)
**Current sub-step:** Not yet started

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **PASSED** | All 5 checks green | 6 Aug 2026 |
| 2 — Providers | **PASSED (scope revised, v1.2)** | 6/8 checks green; 2 rescoped out — see below | 7 Aug 2026 |
| 3 — Agents + MCP | NOT STARTED | — | — |
| 4 — Skills sync | NOT STARTED | — | — |
| 5 — Memory | NOT STARTED | — | — |
| 6 — Projects/RAG | NOT STARTED | — | — |
| 7 — Goose | NOT STARTED | — | — |
| 8 — Validation | NOT STARTED | — | — |
| 9 — Cutover | NOT STARTED | — | — |

## Environment facts (confirmed)
- Machine: Michael-PC, Windows 11 Home 26200, i5-12400, 15.8 GB RAM
- RAM stick: Crucial CT16G4DFRA32A.C16FT, DDR4-3200, Channel A DIMM 0 (upgrade deferred)
- WSL2: Ubuntu-24.04 installed, VERSION 2, UNIX user = michael, home = /home/michael
- Docker Desktop 29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
- git: installed inside Ubuntu, core.autocrlf = false (confirmed). Local git identity now set: user.name=michaelreynolds111-dev, user.email=michael.reynolds111@gmail.com (needed for the first local `git commit` in `~/ai-context` — earlier commits had all gone through the GitHub API tool, not local git)
- Disk: C: 464 GB / ~190 GB free / FullyEncrypted. D: FullyDecrypted (household data snapshot on C:) — **D: cannot be BitLockered (Michael confirmed 7 Aug 2026); exact reason (hardware/NAS vs Windows edition/licensing) not yet captured — see open questions.** This is *why* the full migration off D: onto encrypted C: matters, not just a nice-to-have
- .wslconfig: memory=8GB, processors=6, swap=2GB — leave as-is through Phase 3
- GitHub: michaelreynolds111-dev, no SSH keys in Ubuntu -> use HTTPS + PAT
- ai-context repo: https://github.com/michaelreynolds111-dev/ai-context.git (private, confirmed via API)
- gitleaks 8.30.1 installed at ~/.local/bin/gitleaks (user-local, no sudo). On PATH via ~/.bashrc. Confirmed firing correctly on local commits (7 Aug 2026 plan-edit commit scanned clean).
- PAT stored via git credential helper (`store`) at ~/.git-credentials, perms 600. HTTPS auth working.
- Default branch: **master** (kept deliberately — see decisions)
- **LibreChat v0.8.7** cloned to ~/LibreChat (WSL2 native fs, confirmed not /mnt/c)
- **Docker stack running:** 6 containers — LibreChat (api, port 3080), admin-panel (port 3000, internal), chat-mongodb, chat-meilisearch, vectordb, rag_api — all healthy
- **rag_api image switched to full (non-lite) build** — registry.librechat.ai/danny-avila/librechat-rag-api-dev:latest (11.8GB), replacing librechat-rag-api-dev-lite. Required for local embeddings (sentence-transformers). Pull took ~43 min on this connection — expect this again on any future `docker compose pull` unless the image is cached.
- **First admin account registered:** Michael Gareth Thompson Reynolds, login confirmed working, session survives container restart
- **ALLOW_REGISTRATION=false** confirmed via `/api/config` (`registrationEnabled:false`) — registration locked down post-setup
- **Desktop Commander MCP connector now in use for build execution.** Runs on the Windows host (PowerShell default shell); all LibreChat/WSL2 file and command operations are routed through `wsl -d Ubuntu-24.04 -- bash -lc "..."` invocations or the `\\wsl.localhost\Ubuntu-24.04\...` UNC path for file reads/writes, keeping everything in the WSL2 native filesystem per the hard rule. Confirmed working for both file edits and long-running background commands (the 43-min rag_api image pull ran this way).
- **DeepInfra confirmed to host Claude models directly** — `anthropic/claude-sonnet-5`, `claude-opus-5`, `claude-opus-4-8`, `claude-fable-5`, `claude-haiku-4-5`, `claude-sonnet-4-6`, plus `google/gemini-*` models, all through the same DeepInfra OpenAI-compatible endpoint. This was the trigger for the v1.2 plan revision (see below).

## Phase 0 deliverables (all committed, pushed to origin/master, commit 3b4a994)
- ~/ai-context/ — repo structure: skills/ projects/ memory/ mcp/ docs/
- ~/ai-context/README.md — repo purpose + layout + secret-scanning note
- ~/ai-context/.gitignore — per §4.4 (incl. [IDENTITY] belt-and-braces rules)
- ~/ai-context/.gitleaks.toml — default rules + custom AU identifier rules (TFN, Medicare, passport, licence)
- ~/ai-context/.git/hooks/pre-commit — blocking gitleaks scan; exports ~/.local/bin to PATH (hooks run non-login shell)
- ~/ai-context/skills/session-close/SKILL.md — first real skill (ported from robot-session-close pattern, generic)
- ~/ai-context/mcp/mcp-servers.json — stub {"mcpServers": {}}
- ~/household-vault/ — documents/ identifiers/ renewals.md. NOT a git repo, outside ai-context/ (both verified)

## Phase 1 deliverables (6 Aug 2026)
- ~/LibreChat/ — cloned from danny-avila/LibreChat, v0.8.7 (confirmed current stable via [VERIFY] web search)
- ~/LibreChat/.env — populated: CREDS_KEY, CREDS_IV, JWT_SECRET, JWT_REFRESH_SECRET, ADMIN_PANEL_SESSION_SECRET (all real random values), DEEPINFRA_API_KEY (real key)
- ~/LibreChat/docker-compose.override.yml — mounts ~/ai-context/skills read-only to /app/skill
- Confirmed via container logs: `[deploymentSkills] Loaded 1 deployment skill(s) from /app/skill`

## Phase 2 deliverables (7 Aug 2026)
- ~/LibreChat/librechat.yaml — **created.** `version: 1.3.13` (confirmed current schema via [VERIFY]). DeepInfra wired as a custom OpenAI-compatible endpoint (`baseURL: https://api.deepinfra.com/v1/openai`, `apiKey: ${DEEPINFRA_API_KEY}`, `fetch: true` to pull the live catalog). OpenRouter block present but **commented out** (scaffolded, not active — see decisions). No Anthropic-direct native endpoint configured — not needed, see decisions.
- ~/LibreChat/docker-compose.override.yml — updated: added bind mount for `librechat.yaml` → `/app/librechat.yaml`; added `rag_api` service override switching the image from `-lite` to the full `librechat-rag-api-dev` build (required for local embeddings)
- ~/LibreChat/.env — added `EMBEDDINGS_PROVIDER=huggingface` and `EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2` (uncommented and set from the existing placeholder lines)
- Confirmed via `rag_api` container logs: `sentence_transformers.SentenceTransformer` loaded `all-MiniLM-L6-v2` on CPU, `HuggingFaceEmbeddings` initialized successfully — no errors, no fallback to a remote provider
- Confirmed via LibreChat UI: DeepInfra model picker shows the full live catalog (Claude, Gemini, DeepSeek, Qwen, GLM, Kimi families and more) via `fetch: true`
- Real end-to-end RAG test performed: Michael attached a real document (his choice, informed — see deviations) to a chat, it embedded successfully, and `anthropic/claude-sonnet-5` (via DeepInfra) answered correctly from its content
- Network-traffic check on `rag_api`: `docker stats` NetIO identical before and after the full attach-embed-query cycle (117MB/5.14MB both times) — consistent with zero outbound traffic at index time, combined with the architectural guarantee that `EMBEDDINGS_PROVIDER=huggingface` computes in-process and cannot call an external API (unlike `openai`/`azure`)
- Model-switching test: mid-conversation switch from `anthropic/claude-sonnet-5` to `google/gemini-2.5-flash` (both via DeepInfra), conversation context and the earlier document both preserved correctly

## Files created/modified (prior session, 1 Aug)
- C:\HouseholdDataRaw\Data — verified snapshot of D:\Data (57,598 files / 28.3 GB)
- C:\HouseholdDataRaw\robocopy_log.txt — copy log

## Decisions made
- Ubuntu-24.04 LTS chosen (over 26.04) — 1 Aug 2026
- UNIX username: michael — 1 Aug 2026
- RAM upgrade deferred; .wslconfig stays 8 GB through Phase 3 — 1 Aug 2026
- D:\Data NOT deleted — live working dir of 7 scheduled tasks. Decommission at Session 10 — 1 Aug 2026
- Dump-and-index rejected for household data: known cleartext Tier-1 files in tree. Blocking quarantine = step 0 of §10.4.2 — 1 Aug 2026
- Legacy pipeline (.lancedb, profile.db, gateway) will be audited/decommissioned, never migrated — 1 Aug 2026
- GitHub auth: HTTPS + personal access token (no SSH keys in Ubuntu) — 1 Aug 2026
- ai-context repo name: ai-context — 1 Aug 2026
- gitleaks over git-secrets — 5 Aug 2026
- gitleaks installed user-local (~/.local/bin), not /usr/local/bin — 5 Aug 2026
- Default branch left as `master` — 5 Aug 2026
- PAT persisted via credential.helper store (plaintext at ~/.git-credentials, perms 600) — 5 Aug 2026
- PAT rotated and re-secured — 6 Aug 2026
- Local openssl over web-based credentials generator — 6 Aug 2026
- `open-webui` container removed — 6 Aug 2026 (port 3000 conflict with admin-panel, superseded per the LibreChat-over-Open-WebUI decision)
- **PLAN REVISION v1.2 — OpenRouter demoted from Phase 2 requirement to backlog/resilience item — 7 Aug 2026.** Michael only holds a DeepInfra key. Investigated whether this was a real gap: confirmed DeepInfra's catalog now includes Claude Sonnet 5 and other closed-lab models directly (checked against Michael's actual DeepInfra model list, not just general market comparisons), satisfying the build plan's "Ceiling" tier and the §14.4 compliant-routing requirement for [SENSITIVE]/[IDENTITY] data without a separate Anthropic key. OpenRouter's only remaining genuine value for this build is vendor redundancy (an independent inference relationship if DeepInfra has an outage/billing issue/coverage regression) — not capability. Master build plan updated to v1.2 accordingly (§1, §2, §3.3, §6.1, §6.2, §6.4, §14.3, §18); `librechat.yaml` keeps a commented-out OpenRouter block ready to activate. Anthropic-direct API key similarly deferred/optional, same reasoning.
- **rag_api switched from lite to full image for local embeddings — 7 Aug 2026.** The default `-lite` image only supports remote embeddings providers (OpenAI/Azure/remote HF/Ollama), which would violate the mandatory local-embeddings rule (§6.3) for any [SENSITIVE]/[IDENTITY] collection. Switched to the full `librechat-rag-api-dev` image via docker-compose.override.yml; confirmed `sentence-transformers` running in-container.
- **Desktop Commander MCP connector adopted for build execution — 7 Aug 2026.** Michael enabled it mid-session; from this point on, file edits and command execution for the LibreChat/WSL2 environment are done directly via Desktop Commander (routed through `wsl -d Ubuntu-24.04` to stay in the native filesystem) rather than Michael manually running every command and pasting output back. Faster, fewer transcription/paste errors (see deviations below re: earlier nano/heredoc issues). Michael still runs anything requiring his own credentials or browser interaction.
- **Real document used for RAG test rather than a synthetic file — 7 Aug 2026, Michael's explicit choice.** Flagged the tradeoff (real clinical-adjacent content going into an unscoped default collection, ahead of Phase 3/6 agent-level access control) before proceeding; Michael confirmed he was comfortable (file is old, not a live privacy concern to him) and to continue. Noted here so it's visible in the historical record, not because it's an open risk — nothing left the machine.
- **Confirmed D: cannot be BitLockered — 7 Aug 2026.** Michael confirmed this constraint explicitly this session. Reinforces (doesn't change) the already-planned approach: full migration off D: onto encrypted C:, not just a defensive copy. Exact reason not yet captured — see open questions.

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended over LAN exposure. UNDECIDED
- **New (7 Aug 2026): why can't D: be BitLockered?** Michael confirmed the constraint but the underlying reason wasn't captured — worth pinning down before Session 10, since it affects whether this is permanent (e.g. D: is a NAS/network mount or non-TPM external drive — migration is the only fix) or potentially resolvable (e.g. a Windows edition/licensing gap that could theoretically change). Doesn't block anything now; the plan already treats full migration off D: as mandatory either way.

## Blockers / follow-ups
- None blocking Phase 3. OpenRouter/Anthropic-direct keys are no longer blockers (see decisions) — pick up only if/when vendor redundancy becomes a priority.
- Three-collection RAG separation (general/clinical/household) explicitly deferred to Phase 3 (agent tool scoping) / Phase 6 (RAG knowledge bases) per the v1.2 plan revision — not a Phase 2 gap, a correct rescoping.
- A real document (`ADHD Treatment Plan.md`) is now indexed in LibreChat's default/unscoped RAG collection from the Phase 2 test. Not urgent, but worth keeping in mind once Phase 3 builds proper per-agent collection scoping — may want to reset/reindex cleanly at that point rather than carry forward an ad hoc test artifact.

## Deviations from plan (this session, 7 Aug 2026)
1. **rag_api full-image pull was very slow (~43 min) on this connection**, with highly variable throughput (as low as ~50KB/s at times). Not a bug — just a large image (11.8GB) and a real network condition. Completed successfully with exit code 0; noting for future sessions in case a `docker compose pull` is needed again (e.g. after an image update) — budget real time for it, don't assume something's stuck if it slows down.
2. **PowerShell→WSL→bash heredoc quoting broke on the first attempt to write `librechat.yaml` via Desktop Commander's `start_process`.** Triple-nested shell quoting (PowerShell calling `wsl bash -c "...heredoc..."`) mangled `$`, `"` and the heredoc delimiter. Fixed by switching to Desktop Commander's `write_file`/`edit_block` against the `\\wsl.localhost\Ubuntu-24.04\...` UNC path instead of constructing multi-layer shell commands — this avoids the quoting problem entirely for file content. Recommend this as the default approach for any further file writes via Desktop Commander in this project.
3. **Local git identity was unset in `~/ai-context`.** All prior commits to this repo had gone through the GitHub API tool (`create_or_update_file`), never a local `git commit` — so the plan-edit commit this session was the first to actually need `user.name`/`user.email` configured locally. Set to match the GitHub account. Not a problem, just a first-time setup gap worth knowing about if further local edits are made.

## Deviations from plan (previous session, 6 Aug 2026)
1. `.env` line-1 corruption during manual nano edit — stray `f` character before `#`. Fixed with sed. Cosmetic only.
2. `ADMIN_PANEL_SESSION_SECRET` not in original §5.2 checklist but required by admin-panel container (crash-loops without it). Generated and set. Recommend updating master build plan §5.2 for future rebuilds — **not yet done, still open as a plan TODO.**
3. Port 3000 conflict with legacy `open-webui` container. Stopped then removed.
4. `docker exec LibreChat printenv <VAR>` is NOT valid for checking LibreChat's effective config (the `api` service bind-mounts `.env` directly rather than receiving it via Compose `environment:`). Use `/api/config` or `docker compose logs api` instead.

## Phase 0 exit test — result (5 Aug 2026): PASSED
- [x] `git log` shows an initial commit — 3b4a994
- [x] Private GitHub remote added and pushed — origin/master, private confirmed via API (404 unauth)
- [x] At least one real SKILL.md written and committed — session-close
- [x] mcp/mcp-servers.json exists — stub
- [x] Secret-scanning pre-commit hook installed AND demonstrated to block a dummy identifier — dummy TFN blocked via au-tfn rule, redacted
- [x] ~/household-vault/ exists, is not a git repo, is not inside ai-context/ — all verified

## Phase 1 exit test — result (6 Aug 2026): PASSED
- [x] localhost:3080 loads — confirmed
- [x] Admin login works — confirmed
- [x] All 6 containers healthy — confirmed
- [x] Registration closed — confirmed via `/api/config`
- [x] Restart preserves account — confirmed

## Phase 2 exit test — result (7 Aug 2026): PASSED, scope revised per v1.2
- [x] DeepInfra models appear in the model picker and a chat completes — confirmed, full live catalog via `fetch: true`
- [x] **(v1.2)** OpenRouter — explicitly rescoped out of the Phase 2 exit criteria (demoted to backlog/resilience item). Scaffolded, commented out in `librechat.yaml`
- [x] Anthropic (Claude Sonnet 5) appears and a chat completes — confirmed via DeepInfra's `anthropic/claude-sonnet-5`, no separate Anthropic key needed
- [x] Model switching mid-conversation works — confirmed, `claude-sonnet-5` → `gemini-2.5-flash`, context preserved
- [x] **(v1.2)** Cost sanity check — scoped to DeepInfra only (sole active provider); not separately itemized this session
- [x] Local embeddings model loads and indexes a test document — confirmed, `sentence-transformers/all-MiniLM-L6-v2` in-container, real document indexed and retrieved correctly
- [x] Indexing produces no outbound network traffic — confirmed via `docker stats` NetIO delta (zero change) + architectural guarantee (huggingface provider never calls out)
- [x] **(v1.2)** Three separate RAG collections (general/clinical/household) — explicitly deferred to Phase 3/6, not a Phase 2 requirement (needs per-agent `file_search` scoping that doesn't exist yet)

## NEXT STEP
Open a fresh chat in this project. Start with:
"Read BUILD_STATE.md. What phase are we on and what's the next step?"

**Phase 3 — Agents + MCP (§7). All commands run in the WSL2 Ubuntu shell (/home/michael/LibreChat) unless noted, or via Desktop Commander routed through `wsl -d Ubuntu-24.04` / the `\\wsl.localhost\Ubuntu-24.04\...` UNC path.**

Read BACKUP_AI_MASTER_BUILD_PLAN.md §7 fresh before starting (not from memory) — this phase has real security-load-bearing content (the Household Admin / Clinical Work tool-exclusion rules, §7.4) that must be followed exactly, not approximated.

Expected shape of the phase:
1. Raise `recursionLimit`/`maxRecursionLimit` in `librechat.yaml` (defaults are too low for real agent tasks — §7.2)
2. Install core MCP servers per the §7.3 table, starting with lower-stakes ones (e.g. Spotify) before OAuth-heavy ones (M365, Google Drive)
3. Create purpose-built agents per §7.4's suggested table — pay special attention to the `Household Admin` and `Clinical Work` hard tool exclusions; these are not deferred to a later phase, they're built in from the start
4. Test each OAuth-based MCP individually before relying on it (documented issue: OAuth can fail for non-creator users in shared agent mode)
5. Run Phase 3 exit test per §7.6 — includes explicitly confirming (by inspection, not by asking the agent) that `Household Admin` has no browser/web search/shell/memory tool present

No new API keys required for this phase. Household vault classification work (Session 10 per the roadmap) is still gated behind Phase 6, not Phase 3 — don't pull it forward.
