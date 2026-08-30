# OPERATING_MODES.md — Computer File Steward operating modes

## Current mode: READ_ONLY_REVIEW (v1)

The only implemented mode. The skill reviews ONE explicitly supplied directory and
produces a privacy-preserving, read-only report. It performs **no action** on the
reviewed files.

Guarantees of READ_ONLY_REVIEW:
- Requires an explicit target path. Never defaults to a drive root, home, workspace root, or cwd.
- Requires PowerShell 7+ (`pwsh`); fails before scanning under an unsupported runtime (v1.0.1).
- Populates ISO 8601 timestamps with an explicit `metadata_status` when a field cannot be read (v1.0.1).
- Uses one shared canonical path model; Windows/UNC/WSL forms compare by whole components and fail closed (v1.0.1).
- Never follows reparse points (junctions, symlinks, mount points, `.path` pointers).
- Never reads sensitive file content; never outputs content excerpts.
- Never hashes by default.
- Never moves/copies/renames/deletes/quarantines/archives/restores.
- Reports classification, recommendation, confidence, policy status, action
  eligibility, and approval requirement **separately**.
- Every proposed action is `blocked=true` in v1.

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
- A confirmed authoritative placement architecture (open decision: ai-context
  root path).
- Repository-aware handling established before any repo-adjacent move.
- Reversible operations and full provenance capture.
- The Credential Rule (never move/stage secret-bearing files).

### Mode 4 — QUARANTINE / PURGE (design)
Contemplated for Tier-1 secret quarantine and legacy retirement. Strongly gated:
- Never in v1.
- Requires the Tier-1 quarantine plan and password-manager decision (H3).
- Never deletes without dual-drive enumeration (C: snapshot vs D: live).

## Mode transition guard
v1 is read-only and stays read-only. Promotion to any future mode is a separate,
human-approved change. Nothing in the current scripts can mutate files.
