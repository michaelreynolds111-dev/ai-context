# GOTCHAS.md

Permanent, citable facts about **this specific machine and stack** (Michael-PC),
discovered the hard way during the build. Read this before touching anything a
past session already fought with — Node/npm on Windows, PowerShell↔WSL↔Docker
command layering, Docker volume/UID behaviour, MCP server auth, or the GitHub
connector.

## What belongs here vs. elsewhere

- **GOTCHAS.md (this file):** settled facts about the environment. "X behaves
  this way on this machine, here's the workaround." Not a maybe, not a
  question.
- **`docs/PLAN_DEVIATIONS_2026-08-05.md`:** formally logged *deviations from
  the build plan itself* — where we intentionally did something different from
  what the plan said, with rationale. About the plan, not the machine.
- **`BUILD_STATE.md` "Deviations" sections:** per-session running log of what
  happened. Transient. Entries here graduate into GOTCHAS.md when they turn
  out to be a permanent environmental fact rather than a one-off.
- **GitHub Issues on this repo:** genuinely *open* questions and unresolved
  problems still being worked. Once resolved-and-permanent, the lesson moves
  here.

## How to maintain this file

- Add an entry whenever a session burns real time on an environment-specific
  surprise that a fresh session would otherwise re-discover from scratch.
- Each entry: **Symptom**, **Root cause** (if known — say so if not), **Fix/
  workaround**. Keep it concrete and copy-pasteable.
- Never put secrets, tokens, or full credential values in here (the gitleaks
  pre-commit hook will block them anyway, but don't rely on that).
- This file is pushed to GitHub like every other build doc. Update it as part
  of session close, alongside `BUILD_STATE.md`.

---

# 1. WSL2 / distro

## `wsl` (bare) launched the wrong distro (`docker-desktop`)

**Symptom:** Bare `wsl ...` commands ran against `docker-desktop` instead of
Ubuntu, so project files/git weren't found and commands behaved bizarrely.

**Root cause:** `docker-desktop` was the default WSL distro. Docker Desktop
registers its own WSL distros; one of them can end up as default.

**Fix:** `wsl --set-default Ubuntu-24.04` was run to fix the default. As a
belt-and-braces rule, **always target the distro explicitly**:
`wsl -d Ubuntu-24.04 -- bash -lc "..."`. If any command's output looks like
the wrong distro (no `ai-context` folder, git not found), stop and check
`wsl -l -v` before continuing.

---

## WSL2 shell PATH leaks Windows executables via interop

**Symptom:** Inside `wsl -d Ubuntu-24.04 -- bash -lc "npm --version"`, `npm`
resolved to the **Windows** npm (`C:\Users\micha\AppData\Roaming\npm`, version
11.16.0) and `node` wasn't found at all — because WSL's default PATH appends
the Windows PATH through interop, and there's no native Node installed in
Ubuntu.

**Root cause:** WSL↔Windows interop puts Windows `PATH` entries on the Linux
`PATH`. With no Ubuntu-native Node, `npm`/`npx` fall through to the Windows
binaries, which then can't cooperate with a Linux shell.

**Fix/workaround:** Don't rely on host Node from either side for project work.
The MCP servers that need Node run **inside the LibreChat `api` Docker
container** (stdio servers spawned via `npx`), where `node v24.16.0` /
`npx 11.13.0` are present and correct. Nothing project-related needs a
WSL2-native or Windows-native Node install.

# 2. Shell quoting / command layering

## PowerShell → WSL → bash heredoc quoting mangles content

**Symptom:** First attempt to write `librechat.yaml` via a multi-layer
`start_process` (PowerShell calling `wsl bash -c "...heredoc..."`) mangled
`$`, `"`, and the heredoc delimiter. Triple-nested quoting is unreliable.

**Root cause:** Each layer (PowerShell parser → WSL arg handling → bash) does
its own quote/escape processing; `$` and `"` get eaten before reaching the
intended target.

**Fix/workaround:** For **file content**, don't build multi-layer shell
commands at all — use Desktop Commander's `write_file` / `edit_block` against
the `\\wsl.localhost\Ubuntu-24.04\home\michael\...` UNC path. This is the
default for all project file writes.

## PowerShell → WSL → Docker exec adds a third layer

**Symptom:** Inline `node -e "..."` / `mongosh --eval "..."` passed through
`pwsh` → `wsl bash -lc "..."` → `docker compose exec ...` fail with
"Missing ')'"-type PowerShell parser errors, before the command even reaches
WSL.

**Fix/workaround:** Base64-encode the payload in PowerShell (no special chars
to mangle), decode + pipe on the far side:
```powershell
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))
wsl -d Ubuntu-24.04 -- bash -lc "echo $b64 | base64 -d | docker compose exec -T <svc> <interpreter>"
```
Confirmed working for `node` and `mongosh`. (Note: an earlier base64 attempt
"failed due to line-wrapping" per BUILD_STATE — that was a different transport;
the `echo $b64 | base64 -d | ...` pipe form works because the base64 is a
single unwrapped token on one line.)

## `sudo` silently hangs in the PowerShell.MCP console

**Symptom:** `sudo` in a WSL command invoked from the PowerShell console blocks
with no visible password prompt — the console just hangs.

**Fix/workaround:** Detect the hang with `pwsh:wait_for_completion`, recover
with `pwsh:cancel`. Avoid `sudo` entirely: install user-local binaries to
`~/.local/bin` and export PATH in `~/.bashrc` (this is how gitleaks was
installed).

# 3. Docker / containers

## `UID`/`GID` unset — cosmetic noise, do NOT "fix" by setting UID=1000

**Symptom:** Every `docker compose` command prints:
```
The "UID" variable is not set. Defaulting to a blank string.
The "GID" variable is not set. Defaulting to a blank string.
```

**Root cause:** The base `docker-compose.yml` uses `user: "${UID}:${GID}"` for
`mongodb` and `meilisearch`. When unset, Compose resolves `user: ":"` which
effectively means "use the container image's default user" — for MongoDB that
is uid **999** (its internal `mongodb` user). This is correct behaviour.

**IMPORTANT — do NOT set UID=1000 in .env:** Tried on 8 Aug 2026. Setting
`UID=1000` causes Compose to override MongoDB's user to uid 1000 (`michael`),
which then cannot read the data files owned by uid 999 → immediate crash-loop
(exit 14, fatal assertion on `storage.bson`). The warnings are cosmetic. Leave
UID/GID unset in .env. MongoDB runs fine as uid 999 with `user: ":"`.

**Actual prevention for data loss:** see §4 — the real risk is unclean
shutdown, not the UID/GID warnings.

## Never `docker compose down <service>` — service arg is ignored in Compose V2

**Symptom:** Running `docker compose down <service>` (e.g. `down api`) tears
down the ENTIRE project, not just the named service.

**Root cause:** In Compose V2, the `down` command ignores positional service
arguments. It shuts down all services and removes all containers/networks for
the project.

**Fix:** Use `docker compose stop <service>` to stop a single service, or
`docker compose up -d --force-recreate <service>` to recreate one. Never use
`down` with a service argument.

## `--force-recreate <service>` can recreate more than the named service

**Symptom:** `docker compose up -d --force-recreate api` also recreated
`rag_api`. That produced a transient (~15-20s) "RAG API is either not running
or not reachable at http://rag_api:8000" warning in the `api` logs.

**Root cause:** Not a real regression — a startup race. `rag_api` reloads its
local `sentence-transformers` model on CPU, which takes ~30s; `api`'s
readiness check ran before it finished.

**Fix/workaround:** Don't panic at that specific warning right after a
recreate. Give `rag_api` ~20-30s, then verify reachability for real. `curl` is
NOT installed in the `api` image — use node's built-in fetch instead:
```
docker compose exec api node -e "fetch('http://rag_api:8000/health').then(r=>console.log(r.status))"
```
(pass it via the base64 pipe from §2 to avoid quoting issues). A `200`
confirms healthy.

## `docker exec <api> printenv <VAR>` is NOT a valid config check

**Symptom:** Checking LibreChat's effective config via `printenv` in the
container shows nothing useful.

**Root cause:** The `api` service **bind-mounts `.env` directly** and reads it
in-process, rather than receiving variables through Compose's `environment:`
block. So `printenv` doesn't reflect what LibreChat actually loaded.

**Fix/workaround:** Verify config via `curl http://localhost:3080/api/config`
(from the host) or `docker compose logs api` (which echoes the parsed custom
config at startup).

## Containers exit 127 / don't auto-recover after a host sleep or Docker restart

**Symptom:** After a host sleep/wake or Docker Desktop restart, the `api`
container was found `Exited (127)` while the other 5 containers had
auto-restarted fine. Its last log line was a *clean* graceful SIGTERM
shutdown, not a crash.

**Root cause:** Not fully pinned down — most likely a bind-mount readiness
race right after the host event (exit 127 = "command not found", consistent
with mounts not yet available when the restart fired).

**Fix/workaround:** Just bring it back up: `docker compose up -d api`, then
confirm health via `/api/config`. Worth watching whether this recurs — if it
does, a `restart: unless-stopped` / dependency tweak may be warranted. **See
§4: a host event like this is also the suspected trigger for the MongoDB
reinitialization.**

## The full `rag_api` image is huge and slow to pull

**Symptom:** Pulling the full (non-lite) `librechat-rag-api-dev` image
(~11.8GB) took ~43 min, with throughput dipping as low as ~50KB/s.

**Fix/workaround:** Not a bug — real network + big image. Budget the time; a
slow-down doesn't mean it's stuck. Only re-pays this cost on a fresh
`docker compose pull` (e.g. after an image update); the image is cached
otherwise.

# 4. Data / MongoDB

## MongoDB reinitialized in place — login broke, users collection emptied (Aug 7-8)

**Symptom:** Login at localhost:3080 failed with "Unable to login with the
information provided." Container logs showed
`Passport Local Strategy - User Not Found` — i.e. the account doesn't exist,
not a wrong password. The `LibreChat.users` collection had **0 documents**.

**Investigation findings (confirmed, not guesses):**
- The mongodb data bind mount is correct:
  `/home/michael/LibreChat/data-node` → `/data/db` (verified via
  `docker inspect chat-mongodb`).
- Real WiredTiger data files (~1.1MB, dated Aug 6-7) are still physically on
  disk in `data-node/`, owned by uid `999`.
- MongoDB's own logs show **two separate `"MongoDB starting"` events**: one on
  **Aug 6 09:57 UTC** that created the real collections (`users`,
  `conversations`, `messages`, `sessions`, `transactions`, `files`), and a
  **second on Aug 7 10:01 UTC (~8pm Sydney)** that recreated only the base
  seed collections (roles, accessroles, agentcategories, systemgrants, etc.)
  — **with no `users` collection created in that second startup.**
- That second event was the evening of Aug 7, **before** the Aug 8 working
  session began — this was NOT caused by the Phase 3 / Spotify work.
- Other collections that survived: systemgrants(23), agentcategories(7),
  accessroles(17), roles(2). Everything user-generated is gone from the live
  DB.

**Root cause (resolved 8 Aug 2026):** The Aug 7 host sleep/wake event caused
Docker to restart the mongodb container. mongod detected a non-empty
`mongod.lock` (unclean shutdown) and attempted to read `storage.bson` to
recover — but `storage.bson` was unreadable in that state, causing a fatal
assertion (exit 14) and crash-loop. On the crash-loop restarts, MongoDB
reinitialized with only seed collections, losing the user-created collections.
The UID/GID warnings (§3) are **not** the cause — MongoDB was running as uid
999 throughout, which is correct. The crash-loop is what caused the data loss.

**Resolution (8 Aug 2026):**
1. Backed up corrupt `data-node/` via `docker exec` → `cp -a /data/db /data/db-backup` inside container.
2. Chose fresh init over WiredTiger recovery (lost data = only test content, no household/clinical data).
3. Moved old `data-node/` to `data-node.old-20260808`, created fresh empty `data-node/`.
4. Started MongoDB cleanly — `"Startup from clean shutdown?: true"` confirmed in logs.
5. Re-enabled ALLOW_REGISTRATION temporarily, created new admin account, re-locked registration.
6. Confirmed all 6 containers healthy + `registrationEnabled: false` via `/api/config`.

**How to prevent recurrence:** The underlying trigger is Docker restarting
mongodb after an unclean host event. Two mitigations:
- **Don't force-stop the host or Docker Desktop without first running
  `docker compose stop` in `~/LibreChat`** — this gives mongod a clean SIGTERM
  and lets it write a clean shutdown marker.
- **If the machine does sleep/crash unexpectedly**, check mongodb container
  status immediately on next boot with `docker compose ps`. If it's
  crash-looping (exit 14 in logs + "Lock file is not empty"), do NOT let it
  keep restarting — stop it immediately, back up `data-node/`, then decide
  recover-vs-fresh before bringing it back up.

**What was NOT lost:** all build progress. The plan, BUILD_STATE, config files,
skills live in git. Phase 1/2 exit tests remain validly passed.

## MongoDB must use a NAMED VOLUME, never a bind mount, on WSL2+Docker Desktop

**Symptom (Phase 9a, Aug 10 2026):** After a Windows restart, the MongoDB
catalog was silently reinitialized — all user-created collections (users,
conversations, messages, etc.) were gone, replaced with seed data only. The
MongoDB log still reported `"Startup from clean shutdown?: true"`.

**Root cause:** The `data-node/` directory was a bind mount on the Ubuntu-24.04
WSL2 filesystem. On Windows boot, Docker Desktop starts before the cross-distro
bind path is fully mounted, so MongoDB sees an empty directory and initializes
fresh — silently overwriting all data.

**Fix (Phase 9B, Aug 11 2026):** Migrated MongoDB data to a named volume
(`librechat_librechat_mongo_data`). Docker named volumes are managed by Docker
itself and are available before container startup, regardless of WSL2 mount
state.

**Verify:** `docker inspect chat-mongodb --format '{{json .Mounts}}' | python3 -m json.tool`
should show `/data/db` as `"Type": "volume"`, NOT `"Type": "bind"`.

## Daily mongodump backup via Windows Task Scheduler

**Backup script:** `~/librechat-backups/backup.sh` (WSL2 native, 700 perms,
not git-tracked). Retains last 14 dumps.

**Windows Task Scheduler job:** `LibreChat-Mongo-Backup` runs daily at 06:00
via `wsl -d Ubuntu-24.04 -- bash -lc '~/librechat-backups/backup.sh'`.

**Restore drill (documented in Phase 9B Task 4):** restore into throwaway db
to verify backups work without touching live data:
```bash
LATEST=$(ls -1t ~/librechat-backups/librechat-*.archive.gz | head -1)
docker exec -i chat-mongodb mongorestore --gzip --archive \
  --nsFrom 'LibreChat.*' --nsTo 'LibreChat_restoretest.*' < "$LATEST"
```
Then verify collection counts and `db.dropDatabase()` on the restoretest db.

---

# 5. GitHub connector

## GitHub MCP connector tools can drop out of the active tool set mid-session

**Symptom:** `github:get_file_contents` worked at session start, but after
many `tool_search` calls loading other tool namespaces during a long session,
all `github:*` tools returned "not found" — and `tool_search` could not
rediscover them (the `github` namespace isn't in tool_search's catalog).

**Fix/workaround — now the DEFAULT, not a fallback:** push via **local git**
through the WSL2 shell. `~/ai-context` is a real clone with HTTPS+PAT push
access (from Phase 0). Write files via Desktop Commander to the UNC path, then:
```
wsl -d Ubuntu-24.04 -- bash -lc "cd ~/ai-context && git add <files> && git commit -m '...' && git push"
```
The gitleaks pre-commit hook runs automatically on this path. Use the GitHub
connector (if available) only for a quick read at the very start of a session;
don't depend on it surviving a long working session.

---

# 6. MCP servers

## `@tbrgeek/spotify-mcp-server` README doesn't match its published CLI

**Symptom:** README documents `spotify-mcp-server auth` as an interactive
browser wizard. Running it just starts the MCP server in stdio mode
("authentication tools available") — the `auth` arg is silently ignored.

**Root cause:** `package.json` defines `"auth": "node dist/scripts/authenticate.js"`
as an **npm script** (run via `npm run auth` from inside the package dir), but
the `bin` entry only maps `spotify-mcp-server` → `dist/index.js`, which never
routes to that script.

**Fix/workaround:** Invoke the script directly, bypassing the broken CLI:
```powershell
node "<global npm root>\@tbrgeek\spotify-mcp-server\dist\scripts\authenticate.js"
```
Global npm root via `npm config get prefix`
(here: `C:\Users\micha\AppData\Roaming\npm\node_modules`). It prompts for
Client ID/Secret in the terminal and opens the browser for OAuth.

## Same package: env-var auth needs ALL FOUR tokens, or it silently degrades

**Symptom:** With only `SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET` +
`SPOTIFY_REFRESH_TOKEN` set, the server started but exposed only 3 setup tools
(`spotify_health_check`, `spotify_get_auth_status`,
`spotify_setup_instructions`) instead of the full 10-tool set — no error, just
silent fallthrough to "no credentials found."

**Root cause:** `dist/auth/token-manager.js` gates env-var auth on a single
`if (envClientId && envClientSecret && envAccessToken && envRefreshToken)` —
**all four** ANDed. Missing `SPOTIFY_ACCESS_TOKEN` fails the whole check.

**Fix:** Set all four in `.env` and reference all four in `librechat.yaml`'s
`mcpServers.spotify.env`. Confirmed: the full 10-tool set appears once
`SPOTIFY_ACCESS_TOKEN` is present.

## Same package: env-var mode fakes token expiry and never refreshes — MUST set `SPOTIFY_EXPIRES_AT=1`

**Symptom (8 Aug 2026):** All 10 tools loaded and `spotify_get_auth_status`
reported "authenticated", but every `spotify_search` (and any other real API
call) failed with `401 "Bad or expired token"`. Restarting the `api` container
did NOT fix it. Injecting a freshly-minted access token into `.env` and
restarting did NOT fix it either — same 401.

**Root cause (confirmed by reading `dist/auth/token-manager.js`, not guessed):**
In env-var mode the package trusts the static `SPOTIFY_ACCESS_TOKEN` string and
**fabricates its expiry**:
```js
const expiresAt = process.env.SPOTIFY_EXPIRES_AT
  ? parseInt(process.env.SPOTIFY_EXPIRES_AT)
  : Date.now() + 3600 * 1000;   // default: 1 HOUR FROM CONTAINER START
```
`ensureValid()` only calls the refresh endpoint when `isExpired()` is true, and
`isExpired()` checks against that fabricated `expiresAt`. So with
`SPOTIFY_EXPIRES_AT` unset, for the first hour after every container start the
package **believes the stale static token is valid and never refreshes it** —
it sends the dead token verbatim and gets 401. `spotify_get_auth_status` only
checks that credentials are *present* (`isConfigured()`), not that they work,
so it always says "authenticated" — which is what sends you chasing a
re-auth/credentials red herring. Restarting doesn't help because it just
re-reads the same stale static token and re-fakes another hour of validity.

**This corrects an earlier note in this section** which claimed the package
"re-derives a fresh access token on each container start." It does NOT, in
env-var mode, unless it thinks the token is expired. That earlier assumption
was wrong.

**Fix (verified end-to-end, 8 Aug 2026):** Add a permanently-past expiry so the
token manager always refreshes on boot from the (durable, valid) refresh token:
```
# in ~/LibreChat/.env
SPOTIFY_EXPIRES_AT=1
```
and pass it through in `librechat.yaml`:
```yaml
    env:
      SPOTIFY_CLIENT_ID: "${SPOTIFY_CLIENT_ID}"
      SPOTIFY_CLIENT_SECRET: "${SPOTIFY_CLIENT_SECRET}"
      SPOTIFY_ACCESS_TOKEN: "${SPOTIFY_ACCESS_TOKEN}"
      SPOTIFY_REFRESH_TOKEN: "${SPOTIFY_REFRESH_TOKEN}"
      SPOTIFY_EXPIRES_AT: "${SPOTIFY_EXPIRES_AT}"
```
With `expiresAt` in the past, `isExpired()` is true on every start →
`ensureValid()` runs `_refreshTokens()` → a proper Basic-auth refresh call
(which returns HTTP 200 with the valid refresh token) → the fresh token is held
in memory for that session. `SPOTIFY_ACCESS_TOKEN` still has to be *present*
(the four-var gate above), but its value no longer matters — it's replaced by a
live refresh immediately. Confirmed working via `spotify_search` in the
LibreChat agent UI (real Radiohead discography returned).

**General lesson for stdio MCP servers using static token env vars:** if a
server takes an access token as a static env var, check whether it also honours
an expiry env var. A static access token with no expiry env var is a trap — the
server will trust a dead token. Prefer forcing refresh-on-boot over pasting a
"fresh" access token that's stale by the time the container reads it.

**Diagnostic that pinned this down (reusable):** read env values *inside* the
container and run the package's real refresh + a live `/v1/search` call in one
node script (never printing token values, only HTTP status + results). If the
raw refresh→search works but the MCP tool fails, the bug is in how the package
manages token lifecycle, not the credentials.

## MCP OAuth auth flow / credential store runs where the server runs

**Symptom:** Running the Spotify `authenticate.js` on the Windows host saved
credentials to `C:\Users\micha\.spotify-mcp\credentials.json` — but the actual
MCP server runs **inside the Docker `api` container**, whose home is `/root`,
so it never sees that file.

**Fix/workaround:** For a container-run stdio MCP server, get the tokens into
the container via `.env` env vars (per the four-token note above) rather than
relying on a host-side credential file. The refresh token from the host auth
flow is portable — reuse it via env var.

---

# 7. Git / hooks / repo hygiene

## Git hooks run in a non-login shell — user-local binaries not on PATH

**Symptom:** The gitleaks pre-commit hook (gitleaks installed at
`~/.local/bin`) would fail to find the binary when the hook ran.

**Root cause:** Git hooks execute in a non-login, non-interactive shell that
does NOT source `~/.bashrc`, so the PATH export that makes `~/.local/bin`
available interactively isn't present.

**Fix:** The hook script exports `~/.local/bin` to PATH explicitly within
itself, rather than assuming `~/.bashrc` ran.

## Local git identity was unset in `~/ai-context`

**Symptom:** First real local `git commit` in `~/ai-context` needed
`user.name`/`user.email` set.

**Root cause:** All earlier commits went through the GitHub API tool
(`create_or_update_file`), never a local commit — so local identity had never
been needed until Desktop Commander started doing local commits.

**Fix:** Set to match the GitHub account
(`user.name=michaelreynolds111-dev`, `user.email=michael.reynolds111@gmail.com`).
Now that pushing via local git is the default (§5), this stays set.

## Project-knowledge / cached-remote copies can silently lag GitHub

**Symptom:** A local or project-knowledge copy of a build doc can be several
commits behind GitHub while `git status` still reports "up to date."

**Root cause:** `git status` compares against a **cached** remote ref until
`git fetch` (or `git pull`) actually contacts the remote.

**When this matters:** only if a file is edited directly on GitHub via the web
UI, or if a different machine pushes to the repo. In the normal build workflow
all commits come from the same WSL2 clone (`~/ai-context/`), so after a `git
push` the local clone is already current — no pull needed. The "git pull"
reminder was removed from session-close rituals (8 Aug 2026) for this reason.

**Fix/workaround:** If you have edited a file on GitHub directly, run
`git pull --ff-only` in `~/ai-context` before the next session. Otherwise
skip it — it is a no-op and adds confusion.

---

# 8. LibreChat config

## `.env` corruption during manual nano edits

**Symptom (Aug 6):** A stray `f` character appeared before `#` on line 1 of
`.env` after a manual nano edit, and separately a paste once overwrote a whole
line.

**Fix/workaround:** Fixed with `sed` / nano undo (`Alt+U`). Prefer editing
`.env` via Desktop Commander against the UNC path, or be careful with nano
paste (it can replace a selection). When a paste goes wrong in nano: `Alt+U`
to undo, or `Ctrl+X` then `N` to discard all unsaved changes and reopen clean.

## `ADMIN_PANEL_SESSION_SECRET` is required but missing from the plan checklist

**Symptom (Aug 6):** The `admin-panel` container crash-loops without
`ADMIN_PANEL_SESSION_SECRET` set, but it wasn't in the master plan's §5.2
`.env` checklist.

**Fix:** Generated and set it (min 32 chars, `openssl rand -hex 32`).
**Plan TODO still open:** update master build plan §5.2 to include this for
future rebuilds.

## Missing session secret / port 3000 conflict (Phase 1, resolved)

- A missing session secret and a port-3000 conflict with a legacy
  `open-webui` container were hit during Phase 1 deploy. The `open-webui`
  container was stopped and removed (it's superseded by the LibreChat decision
  anyway). Port 3000 is used by LibreChat's bundled `admin-panel`.

## Deployment skills are scanned ONCE at container startup — not live-watched

**Symptom (8 Aug 2026, Phase 4):** Wrote 6 new `SKILL.md` files into
`~/ai-context/skills/` while the `api` container was already running. All 7
skill directories were confirmed visible inside the container at `/app/skill`
(bind mount is live for file content). But the LibreChat UI's Skills catalog
only showed the 1 skill (`session-close`) that existed **before** the
container started — the 6 new ones were invisible in the UI despite being
physically present in the mounted directory.

**Root cause (confirmed via logs, not guessed):**
```
[deploymentSkills] Loaded 1 deployment skill(s) from /app/skill
```
This log line appears exactly once, at container startup. LibreChat scans
`/app/skill` (or wherever `DEPLOYMENT_SKILLS_DIR` points) **once when the
process boots** and builds its in-memory skill catalog from that snapshot. It
does not re-scan on a live filesystem change, even though the bind mount
itself updates instantly.

**Fix:** restart the `api` container after adding or editing any skill file:
```bash
cd ~/LibreChat && docker compose up -d --force-recreate api
```
Then confirm the new count in the logs:
```bash
docker compose logs api 2>&1 | grep -i skill | tail -3
```
Expect `[deploymentSkills] Loaded N deployment skill(s) from /app/skill` with
`N` matching the actual directory count. Verified: after restart, count went
from 1 → 7 correctly.

**General lesson:** don't assume a bind mount being "live" means the
*application* treats it as live — the mount can update in real time while the
app's internal cache/catalog built from that mount only refreshes on next
boot. Always check for a one-time-scan log line before assuming a file change
took effect without a restart.

---

# 9. Deferred OAuth flows (ready to execute, not yet done)

## Google Drive MCP — what to do when you're ready

**Estimated time:** 30-45 minutes. Requires: browser access to Google Cloud
Console, a Google account, and a terminal.

**What gets configured:** LibreChat uses Google's *remote* Workspace MCP
servers (not a self-hosted package). Each product (Drive, Gmail, Calendar) is
a separate OAuth-enabled remote server. For this build, wire **Drive only**
first — it's what Clinical Work and Research clusters need. Gmail/Calendar
later if wanted.

**Steps:**
1. Go to `https://console.cloud.google.com` → create a new project (or reuse
   one). Note the Project ID.
2. Enable the Drive API: APIs & Services → Enable APIs → search "Google Drive
   API" → Enable.
3. Enable the Workspace MCP service:
   ```
   gcloud services enable drivetoolsservice.googleapis.com --project=<PROJECT_ID>
   ```
   (install gcloud CLI if not present: `https://cloud.google.com/sdk/docs/install`)
4. Google Auth Platform → Branding → fill in app name, support email.
5. Google Auth Platform → Audience → set to "External", add your own Gmail as
   a test user.
6. Google Auth Platform → Data Access → Add scopes:
   `https://www.googleapis.com/auth/drive.readonly` (read-only is enough for
   Research agent; add `.file` scope if you want write access later)
7. Google Auth Platform → Clients → Create Client → Web application.
   - Authorised redirect URI: `http://localhost:3080/api/mcp/gdrive/oauth/callback`
   - Download the JSON → note `client_id` and `client_secret` (do NOT paste
     into chat — add directly to `.env`).
8. Add to `~/LibreChat/.env` (in terminal, not chat):
   ```
   GOOGLE_DRIVE_CLIENT_ID=<value>
   GOOGLE_DRIVE_CLIENT_SECRET=<value>
   ```
9. Add to `librechat.yaml` under `mcpServers:`:
   ```yaml
   gdrive:
     type: streamable-http
     url: https://drive.googleapis.com/mcp/v1/sse
     oauth:
       authorization_url: https://accounts.google.com/o/oauth2/auth
       token_url: https://oauth2.googleapis.com/token
       client_id: "${GOOGLE_DRIVE_CLIENT_ID}"
       client_secret: "${GOOGLE_DRIVE_CLIENT_SECRET}"
       scope: "https://www.googleapis.com/auth/drive.readonly"
       redirect_uri: "http://localhost:3080/api/mcp/gdrive/oauth/callback"
     startup: false
     serverInstructions: true
   ```
   (`startup: false` means it won't try to connect until you manually
   authenticate in the LibreChat MCP Settings Panel — correct for OAuth servers.)
10. Restart `api` container: `cd ~/LibreChat && docker compose up -d --force-recreate api`
11. In LibreChat UI: click MCP Servers dropdown → gdrive → Authenticate.
    Complete the Google OAuth flow in the popup.
12. Add `gdrive` tools to the Research agent in the agent builder.

**Note:** Google marks these Workspace MCP servers as part of a Developer
Preview Program — review current docs at
`https://www.librechat.ai/docs/mcp_servers/google_workspace` before executing,
as scopes and endpoints may have changed.

---

## M365 MCP — what to do when you're ready

**Estimated time:** 30-45 minutes. Requires: browser access to Azure Portal
(`portal.azure.com`), a Microsoft account.

**Package:** `@softeria/ms-365-mcp-server` — run as an HTTP server alongside
the LibreChat stack, then point LibreChat's OAuth flow at it.

**IMPORTANT — personal Microsoft account caveat (June 2026):** Personal
Microsoft accounts (non-enterprise, non-work) have a known issue where refresh
tokens issued via the `common` authority are rejected at the first refresh,
killing the session ~1 hour after login. Fix: set `MS365_MCP_TENANT_ID` to
`consumers` (not `common`) in the server config. Verify this is still current
at `https://github.com/softeria/ms-365-mcp-server` before executing.

**Steps:**
1. Azure Portal → App registrations → New registration.
   - Name: `LibreChat-M365-MCP`
   - Supported account types: "Personal Microsoft accounts only" (or
     "Accounts in any organisational directory and personal" if you might use
     a work account later)
   - Redirect URI: Web → `http://localhost:3080/api/mcp/m365/oauth/callback`
2. Note the Application (client) ID and Directory (tenant) ID.
3. Certificates & Secrets → New client secret → note the value (do NOT paste
   into chat — add directly to `.env`).
4. API Permissions → Add:
   - `Mail.Read`, `Mail.Send` (Outlook)
   - `Files.Read.All` (OneDrive)
   - `Calendars.Read`
   - `User.Read`
   Grant admin consent if prompted.
5. Add to `~/LibreChat/.env` (in terminal):
   ```
   M365_CLIENT_ID=<value>
   M365_CLIENT_SECRET=<value>
   M365_TENANT_ID=consumers
   ```
6. Add the Softeria server to the LibreChat stack. The cleanest approach for a
   local single-user setup is to run it as a sidecar container. Add to
   `docker-compose.override.yml`:
   ```yaml
     m365-mcp:
       image: node:24-slim
       command: npx -y @softeria/ms-365-mcp-server --http --port 3100
       environment:
         MS365_MCP_CLIENT_ID: "${M365_CLIENT_ID}"
         MS365_MCP_TENANT_ID: "${M365_TENANT_ID}"
       ports:
         - "3100:3100"
       restart: unless-stopped
   ```
7. Add to `librechat.yaml` under `mcpServers:`:
   ```yaml
   m365:
     type: streamable-http
     url: http://m365-mcp:3100/mcp
     oauth:
       authorization_url: https://login.microsoftonline.com/${M365_TENANT_ID}/oauth2/v2.0/authorize
       token_url: https://login.microsoftonline.com/${M365_TENANT_ID}/oauth2/v2.0/token
       client_id: "${M365_CLIENT_ID}"
       client_secret: "${M365_CLIENT_SECRET}"
       scope: "Mail.Read Mail.Send Files.Read.All Calendars.Read User.Read offline_access"
       redirect_uri: "http://localhost:3080/api/mcp/m365/oauth/callback"
     startup: false
     serverInstructions: true
   ```
8. `cd ~/LibreChat && docker compose up -d m365-mcp && docker compose up -d --force-recreate api`
9. In LibreChat UI: MCP Servers → m365 → Authenticate. Complete Microsoft
   login in the popup.
10. Add `m365` tools to the Clinical Work agent in the agent builder.

**After wiring:** verify with a simple "list my recent emails" test through
the Clinical Work agent. Check the `api` logs for any token refresh errors.
If sessions die after ~1 hour, confirm `MS365_MCP_TENANT_ID=consumers` is
set and the server is picking it up.

---

# 10. Goose (Phase 7)

## Goose config locations on Windows (username = micha)

- **Install dir:** `C:\Users\micha\AppData\Local\Programs\Goose\`
- **Config dir:** `C:\Users\micha\AppData\Roaming\Block\goose\config\`
- **config.yaml:** `C:\Users\micha\AppData\Roaming\Block\goose\config\config.yaml`
- **Custom provider JSON:** `C:\Users\micha\AppData\Roaming\Block\goose\config\custom_providers\custom_deepinfra.json`
- **Global skills dir:** `C:\Users\micha\.config\agents\skills\`
- **Skills sync script:** `C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1`

## DeepInfra custom provider: base_url / base_path split

**Symptom:** 404 on `https://api.deepinfra.com/v1/openai/v1/chat/completions`
(duplicated `/v1`) or 404 on `https://api.deepinfra.com/v1/openai` (path
truncated). Took 3 iterations to resolve.

**Root cause:** Goose's OpenAI engine behaves differently depending on whether
`base_path` is set:
- If `base_path` is `null` or absent: engine auto-appends `/v1/chat/completions`
  to `base_url`. So `base_url: https://api.deepinfra.com/v1/openai` →
  `https://api.deepinfra.com/v1/openai/v1/chat/completions` — wrong (doubled).
- If `base_path` is set to a non-null string: engine uses `base_url + base_path`
  verbatim with **no further suffix added**.
- If `base_path` is `""` (empty string): behaves like `null` — still
  auto-appends the suffix.

**Fix (confirmed working):**
```json
"base_url": "https://api.deepinfra.com",
"base_path": "v1/openai/chat/completions"
```
This constructs `https://api.deepinfra.com/v1/openai/chat/completions` exactly.

## Skills: Windows junctions cannot cross the WSL UNC boundary

**Symptom:** `cmd /c mklink /J "C:\Users\micha\.config\agents\skills\clinical-writing" "\\wsl.localhost\Ubuntu-24.04\home\michael\ai-context\skills\clinical-writing"` fails with "Local volumes are required to create links" — the junction is created but resolves to nothing.

**Root cause:** Windows directory junctions require both source and target to be
on local NTFS volumes. WSL UNC paths (`\\wsl.localhost\...`) are a network-style
path as far as Windows is concerned, not a local volume.

**Fix:** Copy SKILL.md files to the Windows-native skills dir and maintain with
a sync script. After any skill edit in WSL:
```powershell
& "C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1"
```
The sync script copies all 7 skills from the WSL UNC path to
`C:\Users\micha\.config\agents\skills\`. Skills don't change often — this is
an acceptable trade-off.

## filesystem-mcp extension cannot write to WSL UNC paths

**Symptom:** Goose's `filesystem-mcp` extension (running as a Windows process)
can read from `\\wsl.localhost\...` paths but cannot write to them — the MCP
server's write calls fail silently or with access errors.

**Root cause:** The `@modelcontextprotocol/server-filesystem` process runs as a
Windows Node.js process. Windows write access to WSL's virtual filesystem via
the UNC path has limitations — reads work, writes are blocked for the MCP
server process.

**Fix/workaround:** Use Goose's built-in `developer` shell extension for any
write that needs to land in WSL. Goose self-corrects: when filesystem-mcp
write fails, it falls back to `shell` → `wsl -e cp` or equivalent. This is the
correct division of labour — `developer` shell for WSL ops, `filesystem-mcp`
for Windows-side file ops.

## Relative bind mounts in docker-compose.override.yml break on container restart

**Symptom:** `docker compose restart api` fails with:
`error mounting ".../docker-desktop-bind-mounts/Ubuntu-24.04/<hash>" to rootfs at "/app/librechat.yaml": no such file or directory`
The container was previously running fine; nothing changed in the filesystem.

**Root cause:** Docker Desktop translates WSL2 paths to internal bind-mount
paths at container creation time and stores the resolved path in the container
config. A relative `source: ./librechat.yaml` resolves correctly at first `up`,
but the stored hash path becomes stale after a Docker Desktop update or WSL2
restart. On next `restart`, Docker tries to remount using the stale hash and
fails.

**Fix:** Use absolute WSL2 paths for all bind mounts in
`docker-compose.override.yml`. Replace:
`- type: bind / source: ./librechat.yaml / target: /app/librechat.yaml`
With:
`- /home/michael/LibreChat/librechat.yaml:/app/librechat.yaml:ro`
All other mounts in the override already use absolute paths. Fixed 9 Aug 2026.

**Recovery:** When stuck in this state, `docker compose restart` will not work.
Use `docker compose up -d api` — this recreates the container from scratch
using the current override file.

## Admin panel access requires Sign Up flow, not npm run create-user

**Symptom:** User has `role: ADMIN` confirmed in MongoDB, login works fine,
but the Admin Panel (port 3000) rejects with "You do not have admin
privileges." API logs show:
  [requireCapability] Forbidden: user ... missing capability 'access:admin'

**Root cause:** Admin panel access is gated by an `access:admin` system
grant record in the `systemgrants` collection — not just the `role: ADMIN`
field on the user document. That grant is created by a first-user
bootstrap routine that runs during the real Sign Up / registration flow.
`npm run create-user` inserts directly into the `users` collection and
skips this seeding step.

**Fix:** If the FIRST/admin account needs to be recreated (e.g. after a
database reset), temporarily set ALLOW_REGISTRATION=true, delete any
CLI-created account (npm run delete-user), and register fresh through the
actual Sign Up UI. Then set ALLOW_REGISTRATION back to false. Remember to
recreate the api container with `up -d --force-recreate`, not `restart`,
after each .env change (see stale bind-mount gotcha above).
`npm run create-user` remains fine for additional, non-first accounts once
the instance is already bootstrapped.

## Docker Desktop HKCU\Run launcher starts Docker before WSL2 bridge is ready

**Symptom:** After every Windows reboot the LibreChat `api` container failed
to start (exit 127). Manual `docker compose up -d` afterwards always worked.

**Root cause:** Docker Desktop was auto-launched by an `HKCU\Run` registry
entry, which fires before the WSL2 cross-distro bind-mount bridge is fully
initialised. Docker tried to mount `librechat.yaml` (a single-file WSL2 bind
mount) before the mount path existed, so container create failed at OCI level
with exit 127. `restart: always` cannot heal a *create-time* failure — the
container never starts, so the restart policy never engages.

**Fix:** Remove Docker Desktop from `HKCU\Run`. Replace it with an orchestrated
Windows Scheduled Task that polls for WSL2 and Docker-engine readiness before
running `docker compose up -d`. Orchestrator script lives at
`C:\Users\micha\scripts\docker-boot-orchestrator.ps1` (logon trigger, 60s
delay, RunLevel Highest); it logs to
`C:\Users\micha\scripts\logs\docker-boot.log`. On a real boot it caught and
waited out a 39-second engine-startup gap. Fixed 11 Aug 2026.

## Single-file WSL2 bind mounts fail create-time on boot races

**Symptom:** Container create fails with a missing-path error for a single-file
bind mount (e.g. `librechat.yaml`) immediately after a host boot or Docker
restart, even though the file plainly exists once the system is warm.

**Root cause:** Single-file bind mounts across the WSL2 bridge are more fragile
to timing than directory mounts — the file path can be momentarily absent while
the bridge is still coming up. This is a create-time OCI failure, which no
`restart` policy can recover.

**Fix/workaround:** Design boot automation around an explicit
`docker compose up -d` on a warm system (see the boot orchestrator above), not
around `restart: always`. `up -d` recreates the container from the current
override file once mounts are live; `restart` cannot.

## Goose sync_skills.ps1 uses a HARDCODED skill list — new skills are silently omitted

**Symptom:** After committing a brand-new skill to `~/ai-context/skills/` and
running `& "C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1"`, the
new skill does NOT appear in the output or in
`C:\Users\micha\.config\agents\skills\`. The script only copies the skills
already in its list — it does NOT scan the directory.

**Root cause:** `sync_skills.ps1` (at
`C:\Users\micha\AppData\Roaming\Block\goose\sync_skills.ps1`) enumerates an
explicit, hardcoded array of skill names rather than auto-discovering the
`~/ai-context/skills/` directory. A newly committed skill is silently skipped
until its name is manually added to that array.

**Fix:** Before running the sync, edit `sync_skills.ps1` (e.g. in notepad) and
add the new skill's directory name to the `$skills` array, then save and re-run
the sync. Confirmed 15 Aug 2026 with the `state-update-guard` skill — after
adding it to the list, `Copied: state-update-guard\SKILL.md` appeared and the
skill showed up in the final list.

**General lesson:** "commit the skill" and "sync the skill" are two separate
steps, and the sync step has a manual list you must maintain. When adding a
new skill: (1) `cp` it into `~/ai-context/skills/`, (2) git add/commit/push,
(3) add its name to the `sync_skills.ps1` list, (4) run the sync. The script
also only copies `SKILL.md` by default — skills with `references/`/`templates/`
subdirectories (agent-builder, plan-executor, state-update-guard) need the
script to copy whole directories, so verify the subdirs landed after syncing.
# GOTCHAS UPDATE — 2026-08-16

Append the following entry to `~/ai-context/docs/GOTCHAS.md` (via `cat >>`).
Each entry: Symptom / Root cause / Fix.

---

# 11. Windows OpenSSH

## Admin account SSH keys go in `administrators_authorized_keys`, not `~/.ssh/authorized_keys`

**Symptom:** SSH key authentication fails for admin accounts on Windows even
when the public key is correctly placed in the user's `~/.ssh/authorized_keys`
file. The connection falls back to password auth or is rejected entirely.

**Root cause:** Windows OpenSSH server uses a different key file location for
members of the Administrators group. The standard `~/.ssh/authorized_keys` is
ignored for admin accounts.

**Fix:** Place the public key in:
```
C:\ProgramData\ssh\administrators_authorized_keys
```

**Critical:** File permissions must be set to **Administrators** and **SYSTEM**
only (no other users/groups), or the SSH server will ignore it.

**Commands to set permissions:**
```powershell
icacls C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r
icacls C:\ProgramData\ssh\administrators_authorized_keys /grant:r "Administrators:F" "SYSTEM:F"
```

**Context:** Discovered when setting up Termius SSH access to `michael-pc`
(Windows) from Michael's phone. Standard `authorized_keys` placement failed;
this was the fix. Confirmed working 14 Aug 2026.

## Goose `write` tool silently writes to Windows paths, not WSL2

**Problem:** Goose's built-in `write` tool (and `filesystem-mcp__write_file`) resolve
`/home/michael/...` as a Windows path (`C:\home\michael\...`), not the WSL2
filesystem root. WSL2 files live under `\\wsl.localhost\Ubuntu-24.04\home\michael\...`.
The tools report success because they correctly wrote to `C:\home\michael\...` — it's
just not the right location. There is **no error or warning** — the file silently
goes to the wrong place.

**Fix:** For any file that must land in a WSL2 path, use a two-step bridge:
1. Write to `C:\tmp\goose_bridge_<name>.md` via `filesystem-mcp__write_file`
2. `wsl -d Ubuntu-24.04 -- bash -lc "cp /mnt/c/tmp/goose_bridge_<name>.md ~/agent-workdir/outputs/GOOSE_RESULT_<name>.md"`
3. Verify with `ls -la` via shell

**For short files (<2KB):** A shell `cat << 'EOF'` heredoc also works, but
command-line length limits apply through the Windows→WSL2 pipe.

**Verified pattern (16 Aug 2026):** `filesystem-mcp__write_file` → `C:\tmp\...`
then `cp` through `wsl` shell. The `/mnt/c/` mount is always available in WSL2.

**Context:** Discovered during Session 10 item 4 (legacy pipeline audit) when the
`write` tool reported success but the file was invisible to both WSL2 `ls` and
the `filesystem-mcp__read_text_file` on the WSL2 path. File was found at
`C:\home\michael\agent-workdir\outputs\` on the Windows side.
## C: HouseholdDataRaw\Data staging tree is a stale one-time snapshot — D:\Data is the live pipeline

**Symptom:** During the §10.4.4 legacy-pipeline audit (Session 10 item 4), a
Tier-1 credential (`D:\Data\archive\gateway_old\.gateway_token`) was found still
present on the D: drive even though it had been deleted from C: during P6
cleanup. Components existed in different states on each drive.

**Root cause:** `C:\HouseholdDataRaw\Data` is a one-time quarantine snapshot
copied for the Tier-1 inventory (stale). The live pipeline lives at `D:\Data`.
Deleting/cleanup from C: alone does not touch the live D: copy. Any decommission
or cleanup must target BOTH drives.

**Fix:** Treat `C:\HouseholdDataRaw\Data` as a stale read-only snapshot and
`D:\Data` as the live source. Always check both locations before considering a
component gone. Gateway-adjacent components (`gateway_old/`) existed on D: only,
not C: — so a C:-only cleanup can miss them.

## gateway_old/ exists on D: but not on C: (P6 only removed the C: copy)

**Symptom:** P6 cleanup deleted the `.gateway_token` from `C:\HouseholdDataRaw\Data`
but the original remained at `D:\Data\archive\gateway_old\.gateway_token` on the
decrypted D: drive. Confirmed during the §10.4.4 audit.

**Root cause:** The earlier Tier-1 cleanup operated on the C: staging snapshot and
did not target `D:\Data\archive\gateway_old/`, which holds the original gateway
component (RETIRED.md, gateway_audit.log, tokens). The C: copy was a snapshot; the
D: original is authoritative.

**Fix:** Any credential/gateway cleanup must include `D:\Data\archive\gateway_old/`.
As of 2026-08-18 this was resolved (Michael deleted the D: token and the whole
`gateway_old/` directory). For future cleanups, enumerate a component on BOTH
drives before declaring it removed.
# 12. ai-workspace + Claude / GitHub MCP

## Claude Desktop deletion makes claude_desktop_config.json stale

**Symptom:** After Michael deleted Claude Desktop (18 Aug 2026), the
`live-systems/claude-desktop-mcp` path pointer in `C:\Users\micha\ai-workspace\`
points to a config file for an application that no longer runs. The path pointer
is harmless but stale — it adds no value to the single bounded root.

**Root cause:** The workspace consolidation task (Session 10 item 5) was designed
before Claude was removed from the stack. The `claude-desktop-mcp` path pointer
was created as a read-only awareness junction, but with Claude gone, GitHub MCP
is now LibreChat-managed only.

**Fix:** On the next workspace sweep, remove the stale `live-systems/claude-desktop-mcp`
path pointer (and its `docs/readmes/claude-desktop-mcp.md` README). The
claude_desktop_config.json file itself can remain on disk or be deleted — it's
out of scope for the AI stack now. Update the BUILD_STATE environment facts to
remove stale Claude references.

## 13. RAG diagnostics / secret-safe configuration inspection

### Unfiltered `docker compose config` can expose live secrets in agent output

**Symptom:** During the 22 August 2026 Cluster 6 RAG diagnostic, rendering or inspecting the effective Compose configuration surfaced interpolated live secret values in Goose tool output. The values were not copied into the result file, but they had already entered the execution trace.

**Root cause:** `docker compose config` resolves variables from `.env` and emits the effective configuration. Printing, broadly reading, or returning that render exposes injected API keys, JWT secrets, passwords, tokens, and connection credentials even when the diagnostic only intended to inspect non-secret RAG settings.

**Fix/workaround:** Never print or broadly read a complete interpolated Compose render in an AI/agent session. Extract only an explicit allow-list of non-secret fields (service image, ports, mounts, health checks, dependency names, and named non-secret RAG variables), redact any key whose name suggests secret/token/password/key/credential/URI, and delete temporary renders after use. If a complete render is essential, keep it in a permission-restricted temporary file, process it locally without returning its contents to the agent, output only the allow-listed summary, then delete it.

## 13. Cluster 6 RAG ingestion

### HTTP 200 from v1 `/embed` does not prove that a file was indexed

**Symptom:** Valid uploads can return HTTP 200 with `status:true` while creating no `/ids` entry and zero embedding rows. This occurred with structurally empty DOCX files and with other files from which the loader extracted no usable text.

**Root cause:** The v1 route reports successful request/file handling even when extraction produces zero text or the splitter produces zero chunks. HTTP success is therefore only a transport/application response, not proof of vector persistence.

**Fix/workaround:** Run a content-neutral extractability preflight, then verify every uploaded `file_id` appears in `/ids` and has at least one vector row before marking it indexed. Treat zero-row HTTP-200 outcomes as unindexable, remove any partial record scoped to that ID, and continue or quarantine according to the batch policy.

### Raw RAG database errors can copy document content and vectors into operational logs

**Symptom:** The production `failed.log` captured raw psycopg2 error payloads containing document text, chunk/vector arrays, metadata, and numeric values even though the indexing report itself did not print content.

**Root cause:** Logging the complete server/database exception serializes failed INSERT payloads, which can include the content and embedding values being written.

**Fix/workaround:** Never persist raw RAG exception bodies. Log only generated `file_id`, extension, timestamp, status, a bounded reason code, and cleanup outcome. Apply owner-only permissions to operational logs and audit them for document text, vectors, metadata payloads, credentials, and identifiers before retaining them.
