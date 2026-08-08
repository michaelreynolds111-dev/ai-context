# BUILD STATE

**Last updated:** 8 August 2026 (Phase 7 complete — Phases 0–7 done, Phase 8 next)
**Current phase:** Phase 8 — Validation (§12)
**Current sub-step:** §12 — Run real task from each cluster, score against Claude Pro.

## Phase status
| Phase | Status | Exit test | Date |
|---|---|---|---|
| Pre-flight | **PASSED** | All 4 checks green | 1 Aug 2026 |
| 0 — Source of truth repo | **PASSED** | All 6 checks green | 5 Aug 2026 |
| 1 — LibreChat deploy | **PASSED** | All 5 checks green | 6 Aug 2026 |
| 2 — Providers | **PASSED (scope revised, v1.2)** | 6/8 checks green; 2 rescoped out | 7 Aug 2026 |
| 3 — Agents + MCP | **PASSED** | All items complete | 8 Aug 2026 |
| 4 — Skills sync | **PASSED** | All 4 exit criteria met | 8 Aug 2026 |
| 5 — Memory | **PASSED** | Native memory cross-conversation verified | 8 Aug 2026 |
| 6 — Projects/RAG | **PASSED** | Pattern proven, scope decision made | 8 Aug 2026 |
| 7 — Goose | **PASSED** | All 4 exit criteria met — see below | 8 Aug 2026 |
| 8 — Validation | IN PROGRESS | — | next |
| 9 — Cutover | NOT STARTED | — | — |

## Environment facts (confirmed)
- Machine: Michael-PC, Windows 11 Home 26200, i5-12400, 15.8 GB RAM
- Windows username: **micha** (not Michael — important for Windows paths)
- WSL2: Ubuntu-24.04, VERSION 2, UNIX user = michael, home = /home/michael
- Docker Desktop 29.6.1, WSL2 backend, Ubuntu-24.04 integration ON
- git: core.autocrlf = false. Identity: michaelreynolds111-dev / michael.reynolds111@gmail.com
- Disk: C: 464 GB / FullyEncrypted. D: FullyDecrypted. D: cannot be BitLockered (confirmed).
- .wslconfig: memory=8GB, processors=6, swap=2GB
- **LibreChat v0.8.7** at ~/LibreChat — 6-container stack healthy
- **Goose v41.0.0** installed at `C:\Users\micha\AppData\Local\Programs\Goose\`
- **Goose config:** `C:\Users\micha\AppData\Roaming\Block\goose\config\`
- **Goose provider:** custom_deepinfra — `base_url: https://api.deepinfra.com`, `base_path: v1/openai/chat/completions`, engine: openai. 10 models configured.
- **Goose skills:** 7 skills at `C:\Users\micha\.config\agents\skills\` (copied from WSL ai-context/skills/)
- **Goose skills sync script:** `C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1` — run after any skill edit in WSL
- **Goose extensions active:** developer (shell+files), filesystem-mcp, mcp-tavily-search, skills, summon, analyze, todo, apps, extensionmanager — 9 extensions, 32 tools
- **Filesystem MCP (Goose):** scoped to WSL ai-context + agent-workdir via UNC paths. Cannot write directly to UNC paths — uses developer shell (`wsl` copy) as workaround. This is expected and acceptable.
- **mcp-servers.json:** populated with filesystem + spotify entries, commit 7331a32

## Phase 7 exit test — PASSED (8 Aug 2026)
- §11.1 Goose installed natively on Windows — ✓ v41.0.0
- §11.2 Configured: same DeepInfra key, same skills folder, same mcp-servers.json — ✓
- §11.5 Multi-step Docker/WSL task completed autonomously — ✓
  - Task: 4-step chain: check Docker containers → check WSL2 disk → write file to agent-workdir → read back and confirm
  - Goose hit a real constraint (filesystem-mcp cannot write UNC paths directly), self-corrected using `wsl` copy via developer shell, confirmed file on disk — no human intervention required
  - This proves capability LibreChat agents cannot replicate: unbounded shell loop with self-correction
- §11.5 Skills loading — ✓ all 8 skills confirmed in Goose UI (7 ported + 1 built-in goose-doc-guide)
- §11.5 Confirmation prompts — ✓ Goose desktop operates with default confirmation behaviour

## Phase 7 deliverables (8 Aug 2026)
- Goose v41.0.0 installed: `C:\Users\micha\AppData\Local\Programs\Goose\`
- Provider config: `C:\Users\micha\AppData\Roaming\Block\goose\config\custom_providers\custom_deepinfra.json`
- Goose config: `C:\Users\micha\AppData\Roaming\Block\goose\config\config.yaml` (extensions: filesystem-mcp, mcp-tavily-search wired)
- Skills dir: `C:\Users\micha\.config\agents\skills\` — 7 skills
- Skills sync script: `C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1`
- mcp-servers.json populated: `~/ai-context/mcp/mcp-servers.json` (commit 7331a32)
- Exit test artefact: `~/agent-workdir/goose_exit_test.md` (confirmed present on disk)

## Decisions made (this session, 8 Aug 2026)
- **Goose custom provider: `base_path` must be the full completions path** — `v1/openai/chat/completions`, not a prefix. Goose's OpenAI engine appends nothing further when `base_path` is set — it replaces the default suffix entirely. `base_url` is the bare host only. Setting `base_path` to empty string `""` or `null` causes Goose to auto-append `/v1/chat/completions` to `base_url`, duplicating any path already in the URL.
- **Goose skills use `~/.config/agents/skills/` on Windows** — not a `config.yaml` path key. Windows junction points (mklink /J) cannot cross the WSL UNC boundary ("Local volumes required"). Copy approach used instead; sync script maintained.
- **Goose `developer` extension is the primary WSL/Docker tool** — filesystem-mcp is useful for Windows-side file ops but cannot write to UNC paths. Goose self-corrects via shell when needed. This is the correct division of labour.
- **Filesystem-mcp in Goose uses UNC paths** — `\\wsl.localhost\Ubuntu-24.04\home\michael\ai-context` and `...agent-workdir`. These are readable but not writable by the MCP server process directly.
- **Tavily in Goose wired as `mcp-tavily-search` stdio extension** — key stored in envs block in config.yaml. Separate from LibreChat's native Tavily integration (which uses .env). Both can coexist.

## Deviations from plan (this session, 8 Aug 2026)
1. **Goose v41 installed (plan referenced v1.44.x from GitHub releases)** — same codebase, different versioning scheme in the Windows desktop installer. No functional impact.
2. **Skills cannot be symlinked to WSL** — Windows junctions require local volumes. Copy + sync script used instead of a live symlink. Acceptable trade-off: sync script is one command, and skills don't change frequently.
3. **Filesystem-mcp cannot write UNC paths** — Goose's developer shell used as fallback for WSL writes. Documented in GOTCHAS §10.
4. **Goose base_path/base_url debugging** — took 3 iterations to find the correct split. Root cause: Goose's OpenAI engine behaviour when `base_path` is set vs null vs empty string is not clearly documented. Confirmed fix: `base_url=https://api.deepinfra.com`, `base_path=v1/openai/chat/completions`. Added to GOTCHAS §10.

## Prior phase exit tests
See git history for full detail. Summary:
- Phase 0 PASSED 5 Aug 2026 | Phase 1 PASSED 6 Aug 2026 | Phase 2 PASSED 7 Aug 2026
- Phases 3–6 all PASSED 8 Aug 2026

## Open questions
- H3: Password manager — Google PM currently; Bitwarden recommended. UNDECIDED — hard dependency for Session 10
- H4: Sarah's access — Option A (shared machine) recommended. UNDECIDED
- Why can't D: be BitLockered? Worth pinning before Session 10.

## Blockers / follow-ups
- Google Drive MCP OAuth — deferred from Phase 3, still pending human-gated step (GOTCHAS §9)
- M365 MCP OAuth — deferred from Phase 3, still pending (GOTCHAS §9)
- `ADHD Treatment Plan.md` in unscoped RAG collection — low priority cleanup
- `~/LibreChat/data-node.old-20260808` (1.1MB) — low priority, remove via docker exec
- Goose exit test artefact `~/agent-workdir/goose_exit_test.md` — can be deleted, kept for record

## NEXT STEP
**Phase 8 — Validation (§12).**

Run one real task per cluster and score against what Claude Pro would have produced:
- Cluster 1 (sysadmin): Diagnose/fix a real Docker/WSL issue in Goose
- Cluster 2 (clinical): Draft a real professional document — correct model tier + routing
- Cluster 3 (agentic MCP): Multi-tool task spanning Drive + M365
- Cluster 4 (research): Real workplace-law research question with citations
- Cluster 5 (persistent context): Fresh chat — confirm skills/memory/project context apply
- Cluster 6 (household admin): Complete a real household form end-to-end, timed

Then run the Phase 8 security audit (memory dump, git log -p grep, agent tool list inspection).
Any FAIL blocks cutover for that cluster.
