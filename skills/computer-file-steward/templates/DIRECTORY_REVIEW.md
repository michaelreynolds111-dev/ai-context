# DIRECTORY_REVIEW.md

## 1. Target and resolved target
- Target: `<EXPLICIT TARGET PATH>`
- Resolved (realpath): `<RESOLVED PATH>`
- Run ID: `<run-id>`
- Generated: `<timestamp>`
- Mode: `READ_ONLY_REVIEW`

## 2. Scope boundaries
- Review limited to the explicit target only.
- No reparse point traversed; no path outside the target inventoried as content.
- No sensitive file content read; hashing of sensitive content disabled.

## 3. Sources and registry versions loaded
- `<source 1>`
- `<source 2>`
- Registries: location (N), placement-policy (N), protection (N), project (N).
- Gaps: `<any missing source>`

## 4. Counts by file type and classification
- By type: `<dict>`
- By classification (A–G): `<dict>`
- Classification is NOT an action.

## 5. Known protected assets
- `<items matching protection registry / sensitive markers, by category>`

## 6. Repository findings
- Repo root: `<path>`
- Branch: <branch> | Clean: <bool> | Counts: <dict>
- Stashes / submodules / local-only / remotes (sanitized)
- Items within the repository are BLOCKED from move/archive/delete in v1.

## 7. Reparse points and traversal blocks
- Reparse points found: <N> (all blocked, none traversed)
- `<blocked item> -> type <tag>, target(safe metadata) <target>`

## 8. Sensitive-category counts (no content excerpts)
- Items flagged sensitive-looking (metadata only): <N>

## 9. Placement recommendations
- Classification <X> (conf <Y>): <N> item(s)
- All recommendations ADVISORY; all BLOCKED in v1.

## 10. Policy status, confidence and evidence
- Per-item classification/confidence in INVENTORY.csv.
- Conflicts surfaced in UNKNOWNS.md.

## 11. Unknowns and conflicts
- See UNKNOWNS.md.

## 12. Proposed future actions
- See PROPOSED_ACTIONS.csv — advisory, all blocked=true in v1.

## 13. Strong statement
**NO ACTIONS PERFORMED.** Read-only review. No file was moved, copied, renamed, deleted, quarantined, archived, restored, or modified.
