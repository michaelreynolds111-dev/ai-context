---
name: computer-file-steward
description: Use when importing existing machine knowledge and producing a privacy-preserving, READ-ONLY inventory and review report for ONE explicitly supplied directory on Michael-PC, using four machine-readable registries (location, placement-policy, protection, project). Triggers on requests to "review a folder read-only", "inventory a directory safely", "steward a directory without touching it", "produce a placement/classification report", "what's in this folder and where should it go", "review a directory without moving anything". Defaults to READ-ONLY mode; never moves, copies, renames, deletes, archives, restores, or modifies files.
---

# Computer File Steward [READ-ONLY v1]

## When to use
- "Review this directory read-only and tell me what's in it"
- "Inventory a folder safely and classify its contents"
- "Produce a placement/classification report for a directory"
- "What's in this folder, and where should each thing go?"
- "Steward a directory without moving or changing anything"
- "Check a folder for git repos, junctions, symlinks, and live-system risks, read-only"
- Any request to see classification, placement, or protection status of a specific folder, without mutating it

## Hard rules — non-negotiable
- **Always require an explicit target path.** Never default to a drive root, home directory, workspace root, or current working directory. If no explicit target is supplied, STOP and ask.
- **Default mode is READ-ONLY.** This skill never moves, copies, renames, deletes, quarantines, archives, restores, or modifies any file. It performs no file operations on the reviewed content. Proposed actions are advisory and always `blocked=true` in v1.
- **Never proceed on memory.** Read the authoritative build/policy documents fresh: `BUILD_STATE.md`, `docs/GOTCHAS.md`, and the four registries. This is the same ritual as AGENT_BOOTSTRAP.md.
- **Never read, output, or store any secret value.** Passwords, PINs, MFA seeds, recovery codes, security answers, and private keys never enter this system. Store pointers only. Never read `.env`, `.env.save`, `secrets.yaml`, OAuth stores, private keys, Bitwarden data, `conversations.json`, or credential files.
- **Never traverse a reparse point.** Junctions, symlinks, mount points, `.path` pointers, and WSL/Docker boundaries are recorded and blocked — never followed.
- **Never scan a whole drive, home directory, or live system.** Review is limited to the one explicit target.
- **Stop deeper inspection once sensitivity is established.** Use metadata and known registries; use category detection, not content excerpts. Do not output matching content.
- **Do not hash by default.** Hash only for a stated verification purpose, and never hash protected or sensitive content to seek duplicates.
- **Separate classification from action.** Classification (A–G) does not authorize any action. Report classification, recommendation, confidence, policy status, action eligibility, and approval requirement separately.
- **Report conflicts, do not silently resolve them.** Store conflicting/stale facts and surface them in reports.
- **Cite source documents** rather than duplicating their content where the policy is already recorded.

## Standards
- Language: Plain, direct, factual. Distinguish fact vs policy vs inference vs confidence.
- Length: Concise with clear structure; counts and tables for classifications.
- Format: Structured Markdown report + CSV inventories + JSON metadata, per templates.
- Provenance: Every imported registry fact carries source, observed-at, policy/fact/history/inference status, supersession, and confidence.

## Process

### Step 1 — INTAKE
Obtain ONE explicit target directory from the user. If none supplied, do not proceed. Confirm the target is within an allowed inspection scope (not a live system root, not a secret-bearing path, not the whole drive).

### Step 2 — LOAD POLICY + REGISTRIES
Read fresh:
- `BUILD_STATE.md`, `docs/GOTCHAS.md` (authoritative build docs)
- The four registries (location, placement-policy, protection, project) from the skill test/work area
- `ai-workspace/README.md`, `SCOPE.md`, `AGENTS.md` (bounded-workspace policy) when available
Record which sources loaded and any gaps.

### Step 3 — RUN READ-ONLY INSPECTION
Run the skill scripts (all read-only) against the explicit target:
1. `detect_reparse_points.ps1 -Target <target>` — find junctions/symlinks/mounts/`.path` pointers and Git boundaries, WITHOUT traversing.
2. `inventory_directory.ps1 -Target <target> -OutputCsv INVENTORY.csv` — metadata-only inventory (path, type, size, extension, attributes, reparse status, git-boundary status, sensitive flag). No content, no default hashing.
3. `inspect_git_state.ps1` on each detected Git boundary — branch, HEAD, sanitized remotes, clean/dirty, counts, stashes, worktrees, submodules, local-only branches.

### Step 4 — CLASSIFY + RECOMMEND
Using the classification model (A–G) and the registries, assign each item a classification, recommendation, confidence, policy status, action eligibility, and approval requirement. Blocks:
- Any item in or belonging to a Git repository → blocked from move/archive/delete in v1.
- Any reparse point → blocked, not traversed.
- Any sensitive-looking item → block further inspection, do not read.
- Any item matching a live-system / protected-path registry entry → blocked.
Never output a recommendation that an action be executed — all proposed actions are `blocked=true`.

### Step 5 — PRODUCE REVIEW OUTPUTS
Create a timestamped run directory under the test-output root:
```text
review-runs/<run-id>/
├── DIRECTORY_REVIEW.md
├── INVENTORY.csv
├── PROPOSED_ACTIONS.csv
├── UNKNOWNS.md
├── RUN_METADATA.json
└── VALIDATION_RESULTS.md
```
Use the templates in `templates/`. Every row of PROPOSED_ACTIONS.csv has `blocked=true`.

### Step 6 — VALIDATE
Run `validate_review_output.py --run <run-dir> --target <explicit-target>`:
- Path-safety (no path outside the explicit target; no reparse traversed)
- Secret-safety (no secret patterns in outputs)
- All proposed actions blocked
- All six outputs present
Only a PASS is reported as a completed review.

### Step 7 — REPORT
Present: target, run id, mode `READ_ONLY_REVIEW`, counts, repository findings, reparse points (blocked), sensitive-category counts (no content), placement recommendations with policy/confidence, unknowns/conflicts, proposed future actions (all blocked), and the strong statement `NO ACTIONS PERFORMED`.

## Output format
- **DIRECTORY_REVIEW.md**: as per `templates/DIRECTORY_REVIEW.md` — target/resolved, run id/timestamps, mode, scope, sources/registries, counts, protected assets, repo findings, reparse points, sensitive counts, placement recs, policy status, confidence/evidence, unknowns/conflicts, proposed actions, `NO ACTIONS PERFORMED`.
- **INVENTORY.csv**: one record per item (or documented aggregates for very large dirs) with all metadata columns.
- **PROPOSED_ACTIONS.csv**: advisory-only; every row `blocked=true`.
- **UNKNOWNS.md**: missing/stale/conflicting evidence, unclassifiable items, decisions required, next investigation.
- **RUN_METADATA.json**: run id, mode, target, registries, counts, flags.
- **VALIDATION_RESULTS.md**: generated by the validator with PASS/FAIL.

## What this skill cannot do
- Cannot move, copy, rename, delete, quarantine, archive, or restore any file.
- Cannot read secret-bearing files, `.env`, `conversations.json`, household/clinical/legal/financial bodies, database bodies, mailboxes, or recovery-package bodies.
- Cannot follow junctions, symlinks, mount points, or `.path` pointers.
- Cannot scan whole drives, home directories, or live systems.
- Cannot alter Docker, WSL, services, scheduled tasks, apps, repositories, cloud remotes, or configuration.
- Cannot implement execution, approval consumption, quarantine, purge, or automatic watchers (future modes only, not active).

## Read-only vs future modes (design only)
- **Mode 1 (current): `READ_ONLY_REVIEW`** — active. Reviews, classifies, recommends, all blocked.
- **Mode 2 (design): `PLAN_EXECUTION`** — contemplated, NOT implemented. Would present approved actions.
- **Mode 3 (design): `EXECUTE`** — contemplated, NOT implemented. Would apply human-approved actions only.
These future modes are described only as unimplemented design. Nothing in v1 executes actions.

## Example review (novice walkthrough)
The user says: "review the folder `D:\SomeProject` read-only".

1. **Ask for/confirm the explicit target** — `D:\SomeProject`. (If the user just says
   "review everything", stop and ask for ONE directory; never default to a drive root.)
2. Load the build docs and the four registries.
3. Run, from Windows PowerShell against the target:
   ```powershell
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/detect_reparse_points.ps1 -Target "D:\SomeProject" -ResultFile out\_reparse.json
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/inventory_directory.ps1 -Target "D:\SomeProject" -OutputCsv out\INVENTORY.csv
   # then, for each git boundary reported by detect_reparse_points:
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/inspect_git_state.ps1 -RepoPath "<boundary>" -ResultFile out\_git_0.json
   ```
4. Build the six outputs (DIRECTORY_REVIEW.md, INVENTORY.csv, PROPOSED_ACTIONS.csv,
   UNKNOWNS.md, RUN_METADATA.json, VALIDATION_RESULTS.md) using the templates and the
   registry/classification rules.
5. Run the validator:
   ```bash
   python3 scripts/validate_review_output.py --run out --target "D:\SomeProject"
   ```
6. Present the DIRECTORY_REVIEW.md to the user. It will end with
   `**NO ACTIONS PERFORMED.**` — nothing was moved or changed.

Result: a safe, privacy-preserving, read-only picture of the folder plus advisory,
all-blocked classification and placement recommendations.

## Routing
Build/general tool — not [SENSITIVE] or [IDENTITY]. This skill works on metadata and registries and must never ingest sensitive content; route via any endpoint. (It never sends sensitive content because it never reads it.)
