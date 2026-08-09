# Session 10 — ai-workspace Consolidation Plan

**Status:** Planned, not yet executed. Feeds into Session 10 (legacy pipeline decommission).
**Origin:** Designed in a separate planning chat (chat-history audit), reconciled here against BUILD_STATE.md Session 10 scope.
**Supersedes:** Nothing yet — this is additive to existing Session 10 scope (`D:\Data`, 7 scheduled tasks, credential quarantine, password manager, Sarah's access).

## Problem statement

Pre-LibreChat/Goose builds (some predating this project, some created alongside it via Desktop Commander in ad-hoc Claude Pro sessions) are scattered across `C:\` and `D:\` with no single scope. To let LibreChat's filesystem MCP and Goose's developer extension **monitor and fix** these systems, they need to be reachable through one bounded root — not a growing multi-path allowlist.

## Chosen model: `ai-workspace/` with NTFS junctions

Create one folder, e.g. `C:\Users\micha\ai-workspace\`, as the **only** path ever given to LibreChat's filesystem MCP and Goose's developer extension. In-place systems (Docker stacks, Task Scheduler-dependent scripts, native app data) are exposed *inside* `ai-workspace/` via NTFS junction points (`New-Item -ItemType Junction`), not moved. Standalone scripts and browser extensions with no path dependencies physically move in.

**Why junctions over alternatives:**
- **Git remotes per in-place dir** — rejected: still requires a multi-root MCP allowlist, defeats scope containment.
- **Physically moving everything** — rejected: breaks Task Scheduler jobs (hardcoded paths), breaks `docker-compose.yml` bind mounts (hardcoded paths), breaks `host.docker.internal` references.
- **Junctions** — nothing physically relocates, so Task Scheduler / Docker / native apps keep working unmodified, while the AI stack gets one bounded scope.

**Known trade-off:** junction-following behavior varies by MCP implementation (Node-based generally follow; some Python-based ones need a `--follow-symlinks`-equivalent flag). Expect to check this per-tool during execution, not assume it works everywhere.

## Full inventory (from chat-history audit, unverified against live disk — verify each before acting)

### Stay in place, exposed via junction

| Item | Real path | Why it must stay put |
|---|---|---|
| torbox-system stack | `C:\torbox-system\` | `docker-compose.yml` has hardcoded bind mounts (`C:\appdata\rdtclient`, `D:\Downloads\_staging`); container-to-container service name resolution |
| stash-torbox-bridge | `C:\torbox-system\stash-torbox-bridge\` | Subpath of above |
| Stash native app data | `C:\Users\micha\.stash\` (`stash-go.sqlite`, `config.yml`) | Native Windows install reads this path directly; **no backup exists yet — flag as open TODO, see below** |
| RDT Client config | `C:\appdata\rdtclient\rdtclient.db` | Docker bind mount source, hardcoded in compose |
| Downloads scanner | `D:\Downloads\_scanner\` (`scan.ps1`, `watcher.ps1`, `server.ps1`, `rules\media.yar`, `logs\`) | Two live Task Scheduler jobs (`MediaTorrentWatcher`, `MediaScannerServer`) reference this path directly |
| Resource watchdog | `D:\Data\resource_watchdog.ps1` + `resource_watchdog_log.txt` | Live Task Scheduler job references this path directly — **this is inside the Session 10 "7 live scheduled tasks" scope already; reconcile, don't duplicate work** |
| Stash backup target | `D:\Data\backups\stash\` | Runtime target for a still-unbuilt backup job |
| LibreChat | location TBD | **Goose to locate first** via `docker inspect librechat` → trace compose file. Add as a junction once found. |
| Claude Desktop MCP config | `C:\Users\micha\AppData\Roaming\Claude\claude_desktop_config.json` | Contains a live GitHub PAT — junction in read-only awareness, do not let Goose write here without explicit confirmation |

### Physically move into `ai-workspace/`

| Item | Real path | Destination |
|---|---|---|
| Sharon's Spotify export script | `C:\Users\micha\Desktop\spotify_export.py` | `ai-workspace\standalone-scripts\spotify\` |
| Spotify history aggregator | `...\Spotify Extended Streaming History\spotify_ranked_no_year.py` | same |
| Spotify history analyzer (older) | `...\Spotify Extended Streaming History\spotify_history_analyzer.py` | same |
| Memorial AV scripts | `C:\Users\micha\Desktop\Mum's Memorial\` (`.ps1` scripts only, not AV assets) | `ai-workspace\standalone-scripts\memorial\` |
| DeepInfra model fetcher | `D:\Data\Michael\Cherry Studio\update_deepinfra_models.ps1` | `ai-workspace\standalone-scripts\deepinfra-model-fetcher\` (Cherry Studio itself is uninstalled — script is now orphaned, still useful) |
| RYM Unrated extension | `C:\Users\micha\Desktop\rym-unrated-extension-DS FIX\` | `ai-workspace\browser-extensions\rym-unrated-ds-fix\` — **must re-load unpacked extension in Chrome from new path afterward** |
| Bendigo Smart Form Manager | Tampermonkey browser storage (not on disk) | Export `.user.js` from Tampermonkey dashboard → `ai-workspace\browser-extensions\bendigo-smart-form-manager\` |

### Config copies (not moved, copied for AI visibility)

| Item | Real path | Note |
|---|---|---|
| WSL memory config | `C:\Users\micha\.wslconfig` | Copy into `ai-workspace\configs\wsl\` |

### Explicitly out of scope / do not touch

- `T:\Torbox` — rclone virtual mount, not a real folder
- `C:\Users\micha\.claude-server-commander\` — active Desktop Commander MCP state
- Bitmagnet-Postgres Docker named volume — infra state, not a "build"
- Power Automate flows (Bendigo Health SharePoint) — cloud-only, not migratable to a repo

## Secrets audit — must be resolved before any commit

Do NOT commit verbatim. Build `.env.example` scaffolds instead; real values stay in git-ignored `.env` at their real (junctioned) paths.

- `stash-torbox-bridge\.env` — StashDB, TorBox, Prowlarr API keys
- `claude_desktop_config.json` — GitHub PAT for `michaelreynolds111-dev`, currently stored in plaintext
- LibreChat `.env` — DeepInfra keys (once located)

## Proposed `ai-workspace/` layout

```
C:\Users\micha\ai-workspace\
├── README.md                  # Master index
├── AGENTS.md                  # Instructions for Goose/LibreChat (see below)
├── SCOPE.md                   # In-scope / out-of-scope, and why
├── live-systems\              # ALL junctions — nothing physical
│   ├── torbox-system
│   ├── stash
│   ├── downloads-scanner
│   ├── watchdog                (scoped — only *.ps1 + log, not all of D:\Data)
│   ├── librechat                (pending Goose locating it)
│   └── claude-desktop-mcp
├── standalone-scripts\
│   ├── spotify\
│   ├── memorial\
│   └── deepinfra-model-fetcher\
├── browser-extensions\
│   ├── rym-unrated-ds-fix\
│   └── bendigo-smart-form-manager\
├── configs\
│   └── wsl\
└── docs\
    ├── stack-map.md            # How everything connects
    ├── secrets-inventory.md    # What's a secret, where the real file lives
    └── stash-backup-plan.md    # Resolves the still-open Stash backup TODO
```

## Execution brief for Goose (draft — refine at Session 10 start)

1. Confirm `ai-workspace/` root path with Michael before creating anything.
2. Locate LibreChat's real path via `docker inspect librechat` → trace bind mounts → find compose file directory.
3. Create `live-systems\` junctions one at a time, confirming each real path exists before junctioning (`Test-Path` first).
4. Physically move standalone scripts + browser extensions (git mv where already under version control; otherwise plain move).
5. For each junctioned/moved item, write a README covering: what it does, its real path, what depends on that real path (Task Scheduler job names, Docker service names), and what breaks if the real path changes.
6. Run secrets audit: for each `.env`/config file with live credentials, generate `.env.example` alongside it, confirm `.gitignore` excludes the real file from any repo `git init` inside `ai-workspace/`.
7. Update LibreChat's filesystem MCP config to a single allowed directory: `ai-workspace/`.
8. Update Goose's developer extension config to the same single root.
9. Update `claude_desktop_config.json` allowed-directory scoping to match (if applicable to that MCP server type).
10. Verification pass: confirm `MediaTorrentWatcher` and `MediaScannerServer` Task Scheduler jobs still fire, confirm `resource_watchdog` job still fires, confirm `docker compose ps` on torbox-system stack shows all containers healthy, confirm LibreChat still reachable at `localhost:3080`, confirm GitHub MCP still attaches in Claude Desktop.
11. Record exit test results and final junction/move map in `BUILD_STATE.md` per usual Session close ritual.

## Open items to resolve before Session 10 starts

- Reconcile this plan's `watchdog` junction with the existing Session 10 scope item "legacy pipeline decommission (`D:\Data`, 7 live scheduled tasks)" — likely the same underlying work, described from two angles. Don't duplicate.
- Confirm exact `ai-workspace/` root path with Michael (not yet decided).
- Confirm whether `stash-go.sqlite` backup (still an open TODO from earlier sessions — see MCP servers conversation, "Stash backup TODO is unresolved") should be built as part of this session or kept separate.
- LibreChat's real filesystem location is unknown — first Goose task, not assumed.
