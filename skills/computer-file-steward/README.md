# computer-file-steward

Read-only directory inventory, classification, placement, and protection reports
for Michael-PC, backed by four machine-readable registries.

**Current mode:** `READ_ONLY_REVIEW` (v1.0.2). This skill **never moves, copies,
renames, deletes, archives, restores, or modifies** files. Every proposed action
is `blocked=true`.

**Runtime (v1.0.2):** Requires **PowerShell 7+ (`pwsh`)** for the `.ps1` scripts.
Scripts fail before scanning under any unsupported runtime (e.g. Windows PowerShell
5.1). Invoke with `pwsh`, never `powershell.exe`.

**Traversal safety (v1.0.2):** A target whose root is itself a reparse point is
rejected before enumeration; `.path` pointers are detected in the same guarded
walk (no unguarded `-Recurse`); sensitive/protected directories are pruned (blocked
parent records only, children never enumerated/hashed/inspected).

**Git read-only (v1.0.2):** Every Git subprocess runs with `GIT_OPTIONAL_LOCKS=0`
(optional locks disabled), using only read-only/plumbing commands and safe
argument-vector transport (a fixed base64-encoded wrapper for WSL/UNC), so
the full `.git` tree is left byte-identical and path names cannot inject commands.

## What it does
- Loads authoritative facts from the existing investigation, policy, classification,
  and recovery documents into four registries:
  - **location registry** — where things live, and whether they are live systems / pointers / sensitive.
  - **placement-policy registry** — where each asset type may or may not go (HARD/APPROVED/PROVISIONAL/HISTORICAL/UNKNOWN).
  - **protection registry** — what is unique/reproducible and verified as recovered.
  - **project registry** — project state, repos, sensitive locations, next actions.
- Accepts ONE explicit target directory.
- Inventories that target **without following reparse points** and **without
  enumerating sensitive/protected directory children**.
- Detects Git repositories, live-system paths, WSL/Docker storage, sensitive
  locations, recovery packages, cloud placeholders, and unknown assets.
- Produces a detailed read-only report with evidence, confidence, provisional
  placement recommendations, conflicts, unknowns, and all-blocked actions.

## Files
- `SKILL.md` — how to use (triggers, hard rules, process).
- `EXIT_TEST.md` — the checkable exit criteria.
- `references/` — operating modes, safety policy, classification model, approval
  protocol, registry schema, source priority, report format.
- `templates/` — DIRECTORY_REVIEW.md, INVENTORY.csv, PROPOSED_ACTIONS.csv, UNKNOWNS.md.
- `scripts/` — the read-only engine:
  - `bootstrap_registries.py` — builds the four registries (idempotent, secret-free).
  - `path_canonicalize.py` — shared canonical path model (Windows/UNC/WSL forms; fail-closed).
  - `classification_rules.py` — class-C evidence rules (filename inference never decisive).
  - `conflict_overlay.py` — history-preserving conflict-resolution overlay loader (idempotent, fail-safe).
  - `detect_reparse_points.ps1` — guarded walk detects junctions/symlinks/mounts/`.path` pointers + git boundaries, rejects reparse target roots, prunes sensitive dirs.
  - `inventory_directory.ps1` — metadata-only inventory with ISO 8601 timestamps + metadata_status; prunes sensitive dirs.
  - `inspect_git_state.ps1` — strictly read-only git repo state (`GIT_OPTIONAL_LOCKS=0`, argument-vector transport, sanitized remotes).
  - `validate_review_output.py` — validates path-safety, target-root reparse rejection, sensitive pruning, secret-safety, all-blocked, metadata, and outputs.

## Quick example
See **Example review (novice walkthrough)** in `SKILL.md`.

## Safety
- Read-only by design; ships no mutating file operation.
- Never reads or stores secret values; secure by category/pointer only.
- Never traverses reparse points; rejects a reparse-point target root; prunes sensitive directories.
- Git inspection leaves the full `.git` tree byte-identical (no mutation).
- Never scans a whole drive.
