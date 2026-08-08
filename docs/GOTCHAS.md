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
an expiry env var. A static access token with no expiry hint is a trap — the
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
