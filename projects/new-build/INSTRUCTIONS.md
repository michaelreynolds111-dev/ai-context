# New Build — Stash / TorBox Media Discovery & Recommendation System

## What this project is

A self-hosted adult media discovery and acquisition stack for personal use,
running on Michael-PC (Bendigo, Australia). Built around:

- **Stash** — local scene library manager (native Windows, port 9999)
- **TorBox** — cloud debrid/download backend, mounted via **rclone** as `T:\`
- **Prowlarr** — indexer aggregation (port 9696)
- **stash-torbox-bridge** — custom Python/FastAPI service (Docker, port 8770)
  handling ML-based recommendations, download dispatch, and loop-closing

Stash scans `T:\` directly — there is no local download or copy-to-staging
step. Full stack lives at `C:\torbox-system\` on the Windows host (NOT inside
WSL2 — this is a native Windows service stack with some Docker containers).

## Working style for this project

- Take initiative. Proceed autonomously on diagnosis and non-destructive
  fixes. Only pause for confirmation before destructive or irreversible
  actions (deleting data, running `metadataClean`, dropping DB tables, etc.)
- Root-cause and architectural diagnosis before proposing fixes — not
  incremental patching.
- If a proposed solution looks over-engineered relative to the actual need,
  say so and simplify.

## Critical operational rules — do not violate these

1. **Mount-before-Stash ordering is non-negotiable.** Starting Stash before
   `T:\` is mounted has caused database corruption before. Always confirm
   `T:\` is readable (`Test-Path T:\`) before starting or restarting Stash.
2. **`metadataClean` is destructive when the mount is down.** Running Stash's
   `metadataClean` GraphQL mutation while `T:\` is unmounted deletes all scene
   entries. This has happened once already and required a full DB restore.
   Never run it without first confirming the mount is live.
3. **Docker Desktop corrupts `config.json`.** It repeatedly rewrites
   `C:\Users\micha\.docker\config.json`, adding `"credsStore": "desktop"`,
   which breaks builds. Remove only that key (preserve everything else)
   before every `docker compose build`.
4. **The real Stash database** lives at `C:\Users\micha\.stash\stash-go.sqlite`
   — NOT under `D:\Stash\`. Backups are at `D:\Backups\Stash\` in dated
   subfolders, written nightly.
5. **Recommendation DB writes** must always take a WAL-safe sqlite3 backup API
   snapshot first. Reads should open with
   `sqlite3.connect(f"file:{DB}?mode=ro", uri=True)` to avoid WAL conflicts
   with the running container.
6. **Native Windows services have no watchdog.** The rclone `T:\` mount is
   only triggered by a LogonTrigger scheduled task — if the rclone process
   dies mid-session, the mount stays down until next logon with no
   auto-recovery. Same applies to the native Stash process. (This is a known
   gap — see On the horizon below.)

## System facts

- Stash library: schema 85/85, ~751 scenes at last check (deliberately
  cleaned of megapack pollution).
- Recommendation engine: SQLite at `data/recommendations.db` (WAL mode).
  Tier-2 ML model trained on ~2,700+ feedback decisions. Passive skips are
  weighted at ~0.3 (ambiguous signal), NOT treated as hard negatives
  (confidence=1.0) — treating them as rejections degrades model quality.
- Retrain acceptance gate uses a temporal holdout comparison
  (`ACCEPTANCE_TOLERANCE=0.02`) and correctly rejects degraded candidates —
  confirmed reliable.
- Pack/megapack pollution degrades the library — quality-first download
  ordering (highest bitrate/resolution first) and robust pack detection
  matter for library integrity.

## Tools and command patterns

- **Desktop Commander** is the primary tool for all file/process operations
  on this Windows host. Reliable pattern: write PowerShell scripts to file
  via `write_file`, then execute with
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <path>`. Inline
  `-Command` strings mangle `$var`, `$_`, and nested quotes — avoid them.
- **Docker commands** should be wrapped in
  `Start-Job { docker ... } | Wait-Job -Timeout 25` with explicit
  `Stop-Job`/`Remove-Job` cleanup to prevent indefinite hangs. Use a process
  timeout ≥90,000ms for anything involving Docker jobs or HTTP calls;
  StashDB refresh operations need ~620,000ms.
- **Docker build sequence:** remove `credsStore` from `config.json` →
  `docker compose build stash-torbox-bridge` →
  `docker compose up -d stash-torbox-bridge`. For a syntax check without a
  full rebuild: `docker cp` the file into the container at `/tmp/check_X.py`,
  then `docker exec ... python -m py_compile`.
- **Stash GraphQL API:** `http://localhost:9999/graphql`. Send JSON bodies
  via `curl.exe -d "@file.json"` or `Invoke-WebRequest`. Avoid
  `Invoke-RestMethod` — it auto-deserializes and fails on GraphQL
  introspection responses containing fields named `type`.
- **PowerShell gotchas:** `ConvertFrom-Json` fails on GraphQL introspection
  responses with fields named `type` — use raw `.Content` text instead. The
  `$i:` pattern inside strings parses as a drive reference — use `${i}:`.
- **Stash Tagger config:** Query Mode = "Filename"; blacklist regex
  `(?<=\w)\.(?=\w)` converts dotted filenames to spaced words before
  querying StashDB. `tagOperation` must be `"merge"` to avoid a
  switch-statement crash.
- **Prowlarr search:** uses `clean_title()` and `search_with_fallback()` with
  progressive query loosening. Date-anchored queries
  (`Studio YY.MM.DD Performer`) are prioritized — this matches how adult
  releases are actually named on indexers.
- **Silent scheduled tasks:** `D:\Data\watchdog_silent.vbs` launches
  PowerShell with window style 0 (fully invisible); Task Scheduler action is
  `wscript.exe "D:\Data\watchdog_silent.vbs"`.

## Key file locations (native Windows paths)

- `C:\torbox-system\` — full stack root
- `C:\torbox-system\docker-compose.yml` — see `knowledge/docker-compose.yml`
  (password redacted; real file has the value)
- `C:\torbox-system\stash-torbox-bridge\` — the FastAPI bridge app, source
  mirrored in `knowledge/source/`
- `C:\torbox-system\stash-torbox-bridge\STASH_IDENTIFICATION_RUNBOOK.md` —
  full identification workflow, mirrored in `knowledge/`
- `C:\Users\micha\.stash\stash-go.sqlite` — the real Stash database
- `D:\Backups\Stash\` — nightly Stash backups, dated subfolders
- `C:\Users\micha\.docker\config.json` — gets corrupted by Docker Desktop,
  see rule 3 above

## What's deliberately NOT in this project's knowledge

- `.env` (real API keys/secrets) — NEVER pulled in. `.env.example` (template
  only) is included instead.
- The large pile of one-off `check-*.ps1`, `_check_*.ps1`, `_test_*.ps1`
  scripts in `C:\torbox-system\` and `stash-torbox-bridge\` — these are
  throwaway diagnostic scratch files from past debugging sessions, not
  durable knowledge. If a specific one becomes relevant, read it directly
  from disk at the time rather than pre-loading it here.

## On the horizon (as of last update)

- Watchdog/auto-recovery mechanism for the rclone mount and Stash service,
  to remove the manual recovery dependency on logon triggers.
- Completing phash generation across the full library (see runbook), then a
  second Identify pass.
- Continued ML model improvement as more watch-signal feedback accumulates.
- Auto Tag configuration for content that will never match StashDB.
- StashDB API key rotation was outstanding as of last update (a key was
  exposed in a prior Claude session and needed regenerating at stashdb.org)
  — confirm current status before assuming this is still open.
