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

## `UID`/`GID` unset — printed on every compose command, and possibly load-bearing

**Symptom:** Every `docker compose` command prints:
```
The "UID" variable is not set. Defaulting to a blank string.
The "GID" variable is not set. Defaulting to a blank string.
```

**Root cause:** The base `docker-compose.yml` uses `user: "${UID}:${GID}"` for
`mongodb` and `meilisearch`, but `UID`/`GID` aren't exported in the shell/env
that Compose reads (they're normally set by a login shell; the non-login
`bash -lc` invocations and/or `.env` don't provide them).

**Why it matters:** With both empty, those services can run as an unexpected
user against their bind-mounted data dirs. **This is the leading suspect in
the Aug 7 MongoDB data-loss incident** (see §4) — worth fixing before trusting
the DB again. Candidate fix: set `UID`/`GID` in `~/LibreChat/.env` (e.g.
`UID=1000`, `GID=1000` for the `michael` user) so Compose stops defaulting
them to blank. **Not yet applied — verify the right values first.**

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

**Root cause:** Not fully pinned down at time of writing. Leading hypothesis:
the mongod restart on Aug 7 evening (following a host sleep/wake or Docker
Desktop restart — see §3 exit-127 note) didn't recover the existing WiredTiger
data and reinitialized in place instead. The unset `UID`/`GID` (§3) is the
prime suspect for a permission/ownership mismatch that could cause this. **This
is an OPEN issue — to be troubleshot in a dedicated session.**

**Status / next steps (not yet done):**
1. **Back up `data-node/` before anything else touches it** — cheap, safe,
   preserves the option to attempt WiredTiger salvage/repair later.
2. Decide: attempt recovery of the old data vs. accept the loss and create a
   fresh account (the lost data is only early-phase test content — no
   household/clinical data was in there yet).
3. Fix `UID`/`GID` (§3) so this can't recur, regardless of recovery choice.

**What was NOT lost:** all build progress. The plan, BUILD_STATE, config files,
skills, and this session's work live in git and on disk — not in LibreChat's
DB. Phase 1/2 exit tests remain validly passed; only the chat history behind
them is gone.

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

**Note:** In env-var mode the package logs "refreshed tokens will NOT be
persisted" — it re-derives a fresh access token from the refresh token in
memory on each container start. Long-term fine (refresh tokens are durable),
but it means the `spotify_mcp_credentials` Docker volume we created for this
server currently goes unused in the env-var-only config.

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

**Fix/workaround:** Always `git pull --ff-only` at the start of a session
before reading/editing docs locally. The GitHub connector (when available)
sees true live state; a stale local clone does not.

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
