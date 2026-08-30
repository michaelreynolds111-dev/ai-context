# computer-file-steward

Read-only directory inventory, classification, placement, and protection reports
for Michael-PC, backed by four machine-readable registries.

**Current mode:** `READ_ONLY_REVIEW` (v1.0.1). This skill **never moves, copies,
renames, deletes, archives, restores, or modifies** files. Every proposed action
is `blocked=true`.

**Runtime (v1.0.1):** Requires **PowerShell 7+ (`pwsh`)** for the `.ps1` scripts.
Scripts fail before scanning under any unsupported runtime (e.g. Windows PowerShell
5.1). Invoke with `pwsh`, never `powershell.exe`.

## What it does
- Loads authoritative facts from the existing investigation, policy, classification,
  and recovery documents into four registries:
  - **location registry** — where things live, and whether they are live systems / pointers / sensitive.
  - **placement-policy registry** — where each asset type may or may not go (HARD/APPROVED/PROVISIONAL/HISTORICAL/UNKNOWN).
  - **protection registry** — what is unique/reproducible and verified as recovered.
  - **project registry** — project state, repos, sensitive locations, next actions.
- Accepts ONE explicit target directory.
- Inventories that target **without following reparse points**.
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
  - `detect_reparse_points.ps1` — finds junctions/symlinks/mounts/`.path` pointers + git boundaries, without traversing.
  - `inventory_directory.ps1` — metadata-only inventory with ISO 8601 timestamps + metadata_status.
  - `inspect_git_state.ps1` — read-only git repo state (sanitized remotes).
  - `validate_review_output.py` — validates path-safety, secret-safety, all-blocked, metadata, and outputs.

## Quick example
See **Example review (novice walkthrough)** in `SKILL.md`.

## Safety
- Read-only by design; ships no mutating file operation.
- Never reads or stores secret values; secure by category/pointer only.
- Never traverses reparse points; never scans a whole drive.
