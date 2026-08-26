# Readonly Observer (File Investigator) — Design Specification

**Status:** Draft for review — no live changes yet.
**Date:** 26 August 2026
**Agent type:** E (Skill + infrastructure)
**Change level:** 3 (new capability with OS-level security boundary)
**Reachability:** Standalone read-only MCP endpoint (recommended; see §4) for the local filesystem surface; already-wired read-only remote connectors for web/GitHub/Drive (see §10).

---

## 1. Purpose

Provide a **file investigator / information gatherer** that makes the filesystem and its connected read-only data sources visible to an LLM **without any possibility of mutation**, and without exposing the sensitive vaults. The guarantee must be enforced by the operating system / connector design and the MCP endpoints, **not** by the model's goodwill or a prompt instruction.

The two requirements are distinct and both must hold:

1. **Cannot wreck anything** — no write/modify/delete/rename can reach the
   filesystem, even if the model tries, is jailbroken, or makes a mistake.
2. **Cannot read the sensitive vaults** — even "read-only" must not leak
   secrets into model context, traces, or logs.

---

## 2. Scope decision (locked with Michael)

- **Exposed scope:** `EVERYTHING_EXCEPT_SENSITIVE`
- **Approach:** `OPTION_C` — hybrid: OS read-only identity + sensitive-root
  exclusion + bounded read-verb MCP endpoint + adversarial exit test.

---

## 3. The five enforcement layers

| # | Layer | Mechanism | What it protects against |
|---|---|---|---|
| 1 | OS read-only identity | Dedicated Windows local account `micha-ro`, no interactive login, used only as a process token with Read+List ACLs and no write | Any write reaching the filesystem from a rogue/buggy model |
| 2 | Sensitive-root exclusion | A deny-list of vaults that is **never** in the endpoint's allowed roots, and is additionally denied for `micha-ro` | Secrets being read into model context, traces, or logs |
| 3 | Read-only toolset | The MCP endpoint exposes only read verbs; no write/edit/move/create/delete/exec tools exist in its schema | Accidental mutation through tool misuse |
| 4 | Path allow-list | The endpoint refuses any path outside the configured roots (belt-and-braces on top of ACLs) | A misconfiguration or future change not leaking |
| 5 | Adversarial exit test | Scripted battery that actively *attempts* writes + denied reads; must return 0 mutations + 0 leaked secrets | Proving the guarantee is real, not aspirational |

---

## 4. Reachability — why a standalone MCP endpoint (not a LibreChat agent, not Goose)

**REVISED 26 Aug 2026 (Michael decision):** The local filesystem surface WILL be
attached to a LibreChat agent for phone-easy use (no Goose bounce), using
`host.docker.internal` to bridge the `api` container to the host loopback
endpoint. The endpoint stays bound to `127.0.0.1:8941` (loopback only — not
published to LAN/WAN); the `api` container reaches it at
`http://host.docker.internal:8941/mcp`. Michael explicitly accepted the
reachability trade-off. The read-only + sensitive-root guarantees are unchanged
— enforced by the `micha-ro` OS token, the read-verb schema, and the ACLs,
not by network reachability. GOOSE_RESULT_READONLY_OBSERVER_INFRA.md Step 4's
"cannot be consumed by LibreChat" note is superseded by this bridge.

| Option | Verdict | Reason |
|---|---|---|
| LibreChat agent | ❌ rejected | Runs inside the `api` Docker container as root-in-container; OS-level `micha-ro` boundary would require escaping the container, which fights the Docker model |
| Separate Goose session | ❌ rejected | Goose ships a write-capable `developer` shell; "read-only Goose" is a contradiction that must be constantly re-guarded |
| **Standalone MCP endpoint** | ✅ chosen (now bridged to LibreChat via host.docker.internal) | Read-only property lives in ONE place (endpoint process + `micha-ro` token); LibreChat agent + phone reach it through the loopback bridge; ACLs enforced once at the point files are actually touched |

**Consequence:** the endpoint is a small local process (Node) launched under the
`micha-ro` Windows account, exposing a read-verb MCP schema over loopback only
(`127.0.0.1`, no LAN/WAN exposure — consistent with the SearXNG loopback pattern).
It is *not* inside any Docker container.

---

## 5. The `micha-ro` identity model

- **Account:** `micha-ro`, a standard Windows local user, **never** used for
  interactive login. It exists only so a process can run under a token that
  physically lacks write permission.
- **Michael stays logged in as `micha`** at all times. No switching, no second
  desktop, no daily use of the second account. The only human interaction is
  one-time creation + password set (§8 step 1).
- **ACL model per exposed root:**
  - `micha-ro` → **Read & Execute + List folder contents** (allow).
  - `micha-ro` → **Write / Modify / Delete / Full control** (explicit deny).
  - Sensitive roots → **no access at all** (deny read, deny list).
- Because Windows 11 Home has no Group Policy editor, ACLs are applied directly
  with `icacls` (see Goose task). This is sufficient and auditable.

---

## 6. Sensitive-root exclusion list (CONFIRMED by Michael — 26 Aug 2026, no changes)

The following are **never** exposed and additionally denied to `micha-ro`:

| Path | Why |
|---|---|
| `~/LibreChat/.env` (and any `*.env*`) | Live tokens, JWT/session secrets, API keys |
| Bitwarden data dir + `/snap/bin/bw` vault | Passwords, recovery, decryption secrets |
| `~/household-vault/` | Household identity + sensitive docs (never a git repo, never exposed) |
| `D:\Data\archive\gateway_old\` (and any `gateway*`) | Historical credential residue (largely deleted, pattern retained) |
| Clinical records trees | Clinical content — [SENSITIVE] routing boundary |
| Seddon / family-law trees (`/app/seddon-source`, `seddon-*`) | Legal matters outside authorised household scope |
| Any `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `kubeconfig`, `credentials.json` file | Private keys, creds |
| `~/.config/` browser session/key material where present | Session tokens |

**Default rule:** even if a path isn't on this list, **any file whose name or
content matches a credential pattern is never returned**. The endpoint refuses
to return content for anything matching key/token/password patterns (a second,
content-level guard on top of the path-level exclusion).

> **Status:** CONFIRMED and locked by Michael on 26 Aug 2026 — "happy with the
> exclusion list provided", no additions. The GOOSE result applies the concrete
> working set: denied = .ssh, .aws, .azure, .config, .claude, .docker, .copilot,
> C:\HouseholdDataRaw, D:\Data\archive, D:\Quarantine; D:\Data write-denied.
> Exposed read-only = C:\Users\micha\Documents, C:\Users\micha\Downloads.

---

## 7. MCP endpoint schema (read verbs only)

| Tool | Purpose |
|---|---|
| `list_directory` | List entries in a path (names, types, sizes) |
| `directory_tree` | Recursive tree view |
| `read_text_file` | Read a text file's content (bounded, secret-filtered) |
| `read_file_info` | Metadata only (size, mtime, permissions) |
| `search_files` | Glob-style search within allowed roots |

**Deliberately absent:** `write_file`, `edit_file`, `move_file`,
`create_directory`, any `exec`/`shell`, any `read_media` for binary. The schema
simply has no write verbs — an agent cannot call what does not exist.

**Content filtering:** `read_text_file` and `search_files` pass results through a
secret-pattern filter (key/token/password/private-key regex) and return `[REDACTED]`
if matched. This is layer 2's content guard, independent of the path allow-list.

---

## 8. Build sequence (7 steps)

1. **Michael (one-time):** create `micha-ro` + set password (Termius command
   below). Never enters the system.
2. **Goose:** apply `icacls` ACLs — read-allow on exposed roots, explicit deny
   write, deny read on sensitive roots.
3. **Goose:** stand up the Node MCP endpoint under `micha-ro` (loopback only).
4. **Goose:** register the endpoint in the LibreChat MCP allowlist (or a
   separate config) so the Readonly Observer agent can reach it.
5. **Goose:** run the adversarial exit test.
6. **LibreChat (this agent):** verify the result against the exit test.
7. **Michael:** review + sign-off; promote skill via git (sync + commit).

---

## 9. Hard rules (carried from AGENT_BOOTSTRAP §4)

- No credentials ever enter the system — `micha-ro`'s password is set by
  Michael alone, never stored or logged.
- Endpoint binds loopback only (`127.0.0.1`) — no LAN/WAN, matching SearXNG.
- `~/household-vault/` never becomes a git repo and never exposed.
- Clinical/household/legal content is [SENSITIVE]/[IDENTITY] — out of scope for
  this visibility agent's served content, and the exclusion list enforces that.
- Gitleaks pre-commit hook stays active; no secrets in any staged artifact.

---

## 10. Remote observation surfaces (investigator scope, locked with Michael)

Michael asked for a "file investigator / information gatherer" that can
investigate **anything, anywhere, read-only**. In addition to the local
whole-computer filesystem view (§1–§9), the SAME agent attaches the build's
already-wired read-only remote connectors as additional observation surfaces.
Electively, the scope is: local filesystem + web (SearXNG) + GitHub (read-only)
+ Google Drive (read-only, once its one-time OAuth step is done) —
"all of the above and anything that expands what it can see," minus the
sensitive zones.

### 10.1 One core guarantee across all surfaces
All surfaces share the same contract: **read-only, no mutation, minimum
disclosure, sensitive content never returned.** They differ only in *reach*.

| Surface | Writer is enforced away by | Notes |
|---|---|---|
| Local filesystem | `micha-ro` OS ACL + read-verb MCP schema | the core guarantee (this spec) |
| Web (SearXNG `searxng-search`) | read-only connector design; `search_web`/`fetch_page` are the only tools; SSRF-bounded | zero API keys, loopback backend |
| GitHub (`github-buildstate`) | hosted read-only MCP (X-MCP-Readonly:true, read-only toolset) | static read-only PAT via env pointer |
| Google Drive (`drive`) | read-only OAuth scope (`drive.readonly`) | optional; requires the one-time OAuth step first |

### 10.2 Difference from the local guarantee
- The local filesystem view is enforced by the **OS** (`micha-ro` has no write
  permission). This is the airtight core.
- The remote connectors are read-only **by their connector design** (read-only
  toolset / read-only OAuth scope). They are not wrapped in `micha-ro` — they
  are inherently online and authenticated — but they expose no write verbs to
  the agent.

### 10.3 How the agent is presented
Recommended shape (locked): **one combined investigator agent** that holds all
read-only observation surfaces. The local `micha-ro` filesystem view is the
core surface; web, GitHub, and (optionally) Drive are attached read-only
connectors on the same agent. `references/SKILL.md` and `SKILL.md` document the
combined routing.

### 10.4 Connector readiness status
- Web: **ready** (`searxng-search` wired, test-passed).
- GitHub: **ready** (`github-buildstate` wired, test-passed, read-only).
- Drive: **not yet authed** — the one-time Google OAuth step (GOTCHAS §9) is a
  separate manual step. Until done, the agent says Drive is unavailable.

---

*End of design spec. Next document: SKILL.md.*
