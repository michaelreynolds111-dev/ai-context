# SAFETY_POLICY.md — Computer File Steward safety and privacy policy

This skill inherits the build's safety architecture (Self-Improvement Protocol §3)
and applies read-only guarantees on top.

## 1. Credential Rule (absolute)
- Passwords, PINs, MFA seeds, recovery codes, security answers, and private keys
  **never enter this system in any form** — not in chat, RAG, memory, git, or skills.
- **Human approval can never override the Credential Rule.** No approval level
  authorises moving, staging, reading, or otherwise handling a secret value or a
  secret-bearing file body through the steward.
- The skill may hold a **pointer** ("NRMA login is in Bitwarden, item X") but never the value.
- The skill never reads: `.env`, `.env.save`, `secrets.yaml`, OAuth stores,
  private keys, Bitwarden data, `conversations.json`, household/clinical/legal/
  financial bodies, mailbox bodies, database bodies, uploads, or recovery-package bodies.

## 2. No-mutation guarantee
- READ_ONLY_REVIEW performs no file operations on reviewed content.
- The skill ships no executable that can move, copy, rename, delete, quarantine,
  archive, restore, or purge user assets.
- All proposed actions are `blocked=true` in v1.
- Git inspection is strictly read-only: `GIT_OPTIONAL_LOCKS=0` (optional locks
  disabled) for every subprocess; only read-only/plumbing commands; no
  fetch/pull/push/network; the full `.git` tree is left byte-identical before and
  after inspection.

## 3. Reparse-point discipline (v1.0.2)
- Junctions, symlinks, mount points, and `.path` pointer files are **recorded and
  blocked**, never traversed.
- **A target whose root is itself a reparse point is rejected before enumeration**
  (exit 5) by `detect_reparse_points.ps1` and `inventory_directory.ps1`.
- `.path` pointer files are detected during the same guarded walk; no unguarded
  `Get-ChildItem -Recurse` passes exist in inspection code.
- Resolve targets only through safe metadata, never by following.
- Report the limitation rather than copying files around a junction (per ai-workspace AGENTS.md).

## 4. Scope discipline
- Review only the ONE explicit target. Never scan a whole drive, home directory,
  workspace root, current directory, or live-system root.
- WSL/Docker data directories are never scanned.
- External recovery packages are never opened.

## 5. Sensitive-data minimisation (v1.0.2)
- Prefer metadata + known registries over content.
- **Sensitive/protected directories are pruned**: the parent is recorded with
  metadata only and marked blocked (`sensitive boundary - not traversed`); its
  children are never enqueued, enumerated, hashed, or Git/pointer-inspected.
- A sensitive **file** is recorded with metadata only and is never hashed or opened.
- Use category detection, not excerpts. Do not output matching content.
- Stop deeper inspection once sensitivity is established.
- Do not hash by default; hash only for a stated verification purpose; never hash
  protected/sensitive content.

## 6. Level 4 invariants respected
- Does not change routing boundaries (stays general-purpose, never ingests sensitive content).
- Does not add tools to Clinical Work / Household Admin / Paperwork.
- Does not contradict a GOTCHAS entry.
- Does not modify the improver or agent-builder.

## 6b. PowerShell 7 runtime contract (v1.0.1, Correction C)
- The skill's `.ps1` scripts require **PowerShell 7 or later** (`pwsh`), enforced by
  `#Requires -Version 7.0` and a runtime guard that fails **before scanning** under
  any unsupported runtime.
- Invoke scripts with `pwsh` (PowerShell 7), never `powershell.exe` (5.1).
- No system file associations, PowerShell profiles, PATH, or execution policy are
  modified. (A per-invocation `-ExecutionPolicy Bypass` in examples is a command-line
  scoping override, not a system change.)

## 6c. Metadata honesty (v1.0.1, Correction B)
- A metadata field that cannot be read is left blank **only** with a machine-readable
  `metadata_status` (e.g. `timestamp_unavailable:created`, `access_error:attributes`).
- No timestamp is ever invented, and an access failure is never silently converted
  into a stale classification.
- Aggregate metadata failures are reported by category + count, never as sensitive
  exception bodies.

## 6d. Safe command transport (v1.0.2, Corrections C/D)
- Git inspection never builds a shell command string from paths or arguments.
- Native Windows git uses the `&` argument-vector operator.
- WSL git uses `wsl.exe -e env ... git <args>` (argument vector), never
  `bash -lc "<concatenated string>"`.
- Paths containing apostrophes, spaces, brackets, `&`, `;`, or non-ASCII characters
  cannot inject commands or break quoting.

## 7. Stop conditions (from the governing task)
Stop safely and write a partial result if:
1. A required operation would read/expose a secret value.
2. The target resolves outside the explicitly supplied directory.
3. A reparse point would need traversing, or a target root is a reparse point.
4. An existing live/sensitive directory would need modification.
5. Source reports are insufficient to build safe registries.
6. Registry conflicts cannot be represented without guessing.
7. Testing reveals any source mutation.
8. Report generation exposes sensitive content.
9. The build requires broad system access beyond the task.
10. A script attempts a move/rename/copy/delete/archive/restore/Git-write/service mutation.

Never weaken a safety check to make a test pass.
