# OPERATING_MODES.md — Computer File Steward operating modes

## Current mode: READ_ONLY_REVIEW (v1.0.2)

The only implemented mode. The skill reviews ONE explicitly supplied directory and
produces a privacy-preserving, read-only report. It performs **no action** on the
reviewed files.

Guarantees of READ_ONLY_REVIEW (v1.0.2):
- Requires an explicit target path. Never defaults to a drive root, home, workspace root, or cwd.
- **Rejects a target whose root is itself a reparse point** (junction/symlink/mount/pointer boundary) before enumeration.
- Requires PowerShell 7+ (`pwsh`); fails before scanning under an unsupported runtime.
- Populates ISO 8601 timestamps with an explicit `metadata_status` when a field cannot be read.
- Uses one shared canonical path model; Windows/UNC/WSL forms compare by whole components and fail closed.
- Never follows reparse points (junctions, symlinks, mount points, `.path` pointers); `.path`
  pointers are detected within the same guarded walk.
- **Prunes sensitive/protected directories** automatically: the parent is recorded with metadata
  only and marked blocked; its children are never enumerated, hashed, or Git/pointer-inspected.
- Never reads sensitive file content; never outputs content excerpts; never hashes sensitive files.
- Never hashes by default.
- Never moves/copies/renames/deletes/quarantines/archives/restores.
- Git inspection runs strictly read-only (`GIT_OPTIONAL_LOCKS=0`, optional locks disabled,
  read-only/plumbing commands only; no fetch/pull/push/network) and uses safe argument-vector
  transport (a fixed base64-encoded wrapper for WSL/UNC, PowerShell splatting for native), so
  the full `.git` tree is left byte-identical and path names cannot inject commands.
- Reports classification, recommendation, confidence, policy status, action
  eligibility, and approval requirement **separately**.
- Every proposed action is `blocked=true`.

## Future modes: design only (NOT implemented)

These are described as unimplemented design so the reader is not misled into
thinking they are active capacity.

### Mode 2 — PLAN_EXECUTION (design)
Contemplated. Would take the advisory `PROPOSED_ACTIONS.csv` and assemble a plan
of human-reviewed, irreversible-aware actions. Still would not apply them without
explicit approval. Requires a placement-policy registry with `APPROVED`/`HARD`
destinations, and a human approval gate for every `movement_approval_required`.

### Mode 3 — EXECUTE (design)
Contemplated. Would apply human-approved actions only (move/copy/archive into
approved destinations). Strictly requires:
- A confirmed authoritative placement architecture. (The ai-context root decision
  is **RESOLVED** by conflict overlay CFL-001: WSL `/home/michael/ai-context` is
  authoritative; the Desktop checkout is dirty/preserved/non-authoritative.)
- Repository-aware handling established before any repo-adjacent move.
- Reversible operations and full provenance capture.
- The **absolute Credential Rule** (never move/stage/read secret-bearing files).
  Human approval can never override the Credential Rule.

### Mode 4 — QUARANTINE / PURGE (design)
Contemplated for Tier-1 secret quarantine and legacy retirement. Strongly gated:
- Never in v1.
- Any future Tier-1 handling is limited to recording pointers and password-manager
  workflows only; Tier-1 secret values and secret-bearing files remain outside
  normal steward execution.
- Never deletes without dual-drive enumeration (C: snapshot vs D: live).

## Mode transition guard
v1 is read-only and stays read-only. Promotion to any future mode is a separate,
human-approved change. Nothing in the current scripts can mutate files.
