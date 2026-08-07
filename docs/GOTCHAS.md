# GOTCHAS.md

Permanent, citable facts about Michael-PC's specific environment, discovered
the hard way during the build. This is NOT a discussion log or a TODO list --
that's what GitHub Issues on this repo are for. Entries here are settled
facts: "X behaves this way on this machine," not "we're not sure why X
happens" or "revisit Y later."

Each entry: what happened, the root cause (if known), and the fix/workaround.
Add a new entry whenever a session burns real time on an environment-specific
surprise -- something a fresh Claude session wouldn't otherwise know without
re-discovering it.

---

## Windows Node install is missing the `npx.cmd` shim

**Symptom:** Running `npx <anything>` in PowerShell or cmd.exe fails with
`'"node"' is not recognized as an internal or external command` -- note the
literal quote marks baked into the error, which is the tell.

**Root cause:** `C:\Program Files\nodejs\` has `npm`, `npm.cmd`, and `npm.ps1`
(all three shim variants), but only `npx` and `npx.ps1` -- the `npx.cmd` file
is missing. `node.exe` itself is present and correctly on PATH; this is not a
PATH problem, it's specifically a broken/incomplete `npx` shim.

**Fix/workaround:** Don't rely on bare `npx` in PowerShell/cmd on this
machine. Either:
- `npm install -g <package>` then run the package's own installed bin
  directly (creates its own proper `.cmd` shim), or
- Invoke the target script directly with `node "<full path to the .js
  file>"`, bypassing the package's bin/CLI routing entirely.

This does NOT affect `npx` running inside WSL2 or inside Docker containers --
confirmed node v24.16.0 / npx 11.13.0 both work correctly inside the
LibreChat `api` container. Only the Windows-host shim is broken.

---

## PowerShell → WSL2 → Docker exec is three layers of shell quoting

**Symptom:** Inline JS/bash one-liners passed as `node -e "..."` or similar
through `pwsh:execute_command` → `wsl -d Ubuntu-24.04 -- bash -lc "..."` →
`docker compose exec api ...` get mangled -- PowerShell's parser trips over
the nested quotes before they even reach WSL.

**Fix/workaround:** For anything beyond a trivial one-liner, base64-encode
the payload in PowerShell (no special characters to mangle), then decode and
pipe it into the target process on the other side:
```powershell
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))
wsl -d Ubuntu-24.04 -- bash -lc "echo $b64 | base64 -d | docker compose exec -T api node"
```
This matches the existing heredoc-avoidance principle already in
BUILD_STATE.md's key learnings -- same root problem, one more layer deep now
that Docker's in the chain.

---

## `docker compose up -d --force-recreate <service>` can recreate more than asked

**Symptom:** Running `--force-recreate api` also recreated `rag_api`, which
wasn't named. This produced a transient (~15-20s) "RAG API is either not
running or not reachable" warning in the `api` logs -- purely a startup
race (rag_api's local sentence-transformers model takes real time to load on
CPU), not a config regression. Confirmed via direct HTTP check once rag_api
finished loading.

**Fix/workaround:** Not a bug to fix -- just don't panic at this specific
warning immediately after a recreate. Give `rag_api` ~20s to finish loading
its embeddings model before concluding something's actually broken. Verify
with a real connectivity check (`node`'s built-in `fetch` from inside the
`api` container, since `curl` isn't installed in that image) rather than
assuming from the warning text alone.

---

## `@tbrgeek/spotify-mcp-server`'s own README doesn't match its published CLI behavior

**Symptom:** README documents `spotify-mcp-server auth` (after global
install) as an interactive wizard that prompts for Client ID/Secret and
opens a browser. Running it actually just starts the MCP server in stdio
mode ("Starting without credentials - authentication tools available") --
the `auth` argument is silently ignored.

**Root cause:** `package.json` has `"auth": "node dist/scripts/authenticate.js"`
as an **npm script** (meant to be run as `npm run auth` from inside the
package's own directory), but the `bin` entry only maps
`spotify-mcp-server` -> `dist/index.js`, which never routes to that script.
Documentation describes a workflow the published `bin` doesn't implement.

**Fix/workaround:** Invoke the script directly instead of going through the
broken CLI routing:
```powershell
node "<global npm root>\@tbrgeek\spotify-mcp-server\dist\scripts\authenticate.js"
```
Find `<global npm root>` via `npm config get prefix` (on this machine:
`C:\Users\micha\AppData\Roaming\npm\node_modules`).

Separately: env-var-based auth for this package requires **all four** of
`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_ACCESS_TOKEN`, and
`SPOTIFY_REFRESH_TOKEN` present together (confirmed by reading
`dist/auth/token-manager.js` -- it's a single `if` with all four ANDed).
Missing just `SPOTIFY_ACCESS_TOKEN` silently falls through to "no
credentials found," exposing only the 3 setup tools instead of the real
10-tool set. In this mode, refreshed tokens are NOT persisted back to disk
(logged explicitly by the package) -- it re-derives a fresh access token
from the refresh token in memory on every container start, which is fine
long-term but means the `spotify_mcp_credentials` Docker volume created for
this server currently goes unused in our env-var-only configuration.

---

## GitHub MCP connector tools can silently drop out of the active tool set mid-session

**Symptom:** `github:get_file_contents` worked at session start, but after
many `tool_search` calls for other tool namespaces (Desktop Commander,
claude-in-chrome, etc.) during a long session, `github:*` tools returned
"not found" -- and `tool_search` couldn't rediscover them either (the
`github` namespace isn't in tool_search's own catalog listing at all).

**Fix/workaround:** Don't depend on the GitHub MCP connector surviving a
long session. Use local git instead -- `~/ai-context` is already a cloned
repo with push access from Phase 0. Write files via Desktop Commander to the
WSL2 UNC path, then `git add / commit / push` through the WSL2 shell. This
is more reliable than the connector for anything beyond a quick read at the
very start of a session, and should probably be the default push method
going forward rather than a fallback.
