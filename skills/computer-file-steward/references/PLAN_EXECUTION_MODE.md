# PLAN_EXECUTION_MODE.md — Computer File Steward Mode 2: PLAN_EXECUTION

**Status (Build 2):** Implemented as a **planning-only** capability. It produces
approval-ready plan packages. It **cannot execute** any file operation.

Every plan package must contain:

```text
THIS PACKAGE IS A PLAN ONLY. IT CANNOT EXECUTE FILE OPERATIONS.
```

## 1. What Mode 2 does

Given a completed, validated v1.0.2 `READ_ONLY_REVIEW` run, Mode 2 converts the
advisory recommendations into a stable, immutable, human-readable,
approval-ready plan package:

```text
planning-runs/<plan-id>/
├── ACTION_PLAN.md
├── ACTION_MANIFEST.json
├── ACTION_MANIFEST.csv
├── APPROVAL_RECORD.json
├── SOURCE_SNAPSHOT.json
├── POLICY_SNAPSHOT.json
├── DRIFT_CHECK.json
└── PLAN_VALIDATION.md
```

- **ACTION_MANIFEST.json** is canonical for hashing and machine validation.
- **ACTION_MANIFEST.csv** is a human flat view. JSON and CSV reconcile by action ID and count.
- **APPROVAL_RECORD.json** is a human decision record bound to the exact manifest hash.
- **SOURCE_SNAPSHOT.json** / **POLICY_SNAPSHOT.json** capture metadata + relied policy for drift checks.
- **DRIFT_CHECK.json** records source/policy/manifest drift state.
- **PLAN_VALIDATION.md** records the result of `validate_action_plan.py`.

## 2. Stable identity

- **Plan ID:** readable unique, e.g. `PLAN-20260830-READMES-001`.
- **Action ID:** `ACT-<12-hex-sha256>` derived from canonical immutable identity
  fields (canonical source path, proposed action type, canonical destination or
  explicit null, source review ID, governing policy ID/unknown marker,
  item type, classification). The full SHA-256 is retained in JSON.
- Same unchanged action input ⇒ same action ID. Material change ⇒ ID or manifest hash changes.

## 3. Canonical manifest hashing

`ACTION_MANIFEST.json` uses deterministic serialization:
- UTF-8; sorted object keys; defined array order; consistent newlines; no comments.
- No generated timestamp inside the hashed action payload.
- `manifest_sha256` = SHA-256 over the canonicalised, sorted actions payload.

## 4. Blocking and approval-ready rules

Planning is not permission. An action is **blocked** (never approval-ready) when any
of the following applies:

- classification **G**;
- sensitive or protected boundary;
- Tier-1 / credential-adjacent item (Credential Rule is absolute);
- source/destination is a reparse point, junction, pointer, mount, or unresolved path;
- item is in / belongs to a Git repository and repo-aware handling is unresolved;
- policy status is PROVISIONAL / HISTORICAL / UNKNOWN / missing;
- destination is absent/ambiguous for a move/archive proposal;
- verified recovery prerequisite unmet;
- source changed since review;
- destination collision unresolved;
- governing conflict effectively unresolved;
- the proposal is permanent deletion;
- source evidence insufficient;
- the underlying review did not validate successfully.

An action may be **approval-ready** only when all of these hold:

- source review validation passed;
- source path canonical and unchanged;
- classification evidence-backed;
- destination policy HARD/APPROVED (if a destination is needed);
- no sensitive/credential boundary;
- no reparse/Git block;
- collision_status CLEAR or NOT_APPLICABLE;
- recovery satisfied or not applicable;
- action reversible;
- no unresolved prerequisite.

**Even approval-ready rows are not executable in Build 2** (`execution_implemented=false`,
`execution_capability=NONE`).

## 5. Approval record

`APPROVAL_RECORD.json`:

- `approval_status` ∈ {PENDING, PARTIAL, APPROVED, REJECTED, STALE, INVALID}; default PENDING.
- Approve/reject/defer IDs mutually exclusive; every referenced ID must exist; blocked actions cannot be approved.
- Approval binds to the exact `manifest_sha256`; if the manifest changes, approval becomes INVALID/STALE.
- Approval never invokes execution and cannot override the Credential Rule /
  protected boundaries / a failed drift check / an unresolved policy requirement.
- Required acknowledgement includes:
  `I understand this approval records a decision only and does not execute file operations.`

Approval requires **explicit action IDs**. Vague phrases ("looks good", "go ahead",
"do it") are never accepted as structured approval.

## 6. Drift check

`check_plan_drift.py` is read-only. Result states:

```text
CURRENT, SOURCE_DRIFT, POLICY_DRIFT, MANIFEST_MISMATCH,
TARGET_UNAVAILABLE, BLOCKED_BOUNDARY_CHANGED
```

It requires an explicit plan directory, never follows reparse points, never reads
sensitive bodies, reports changed categories/paths without secret values, marks
approval stale on material drift, and never repairs drift automatically.

## 7. Mode boundaries (Mode 2 may / may not)

**May:** read completed validated reviews; read registries + conflict overlay; create
plan files in an output directory; calculate hashes of planning files + metadata
snapshots; create blank/completed human approval records; validate a plan; report drift.

**May NOT:** perform any proposed action; contain an executor; invoke mutating
filesystem commands on reviewed content; interpret approval as execution authority;
change the reviewed source directory; update destinations; create quarantine/archive
directories; automatically select permanent deletion.

## 8. Supported planning interactions

```text
Build an approval-ready plan from review run <path>.
Show me which actions in plan <plan-id> are approval-ready and which are blocked.
Record approval for ACT-123 and rejection for ACT-456 in plan <plan-id>.
Check whether plan <plan-id> is still current.
```

None of these execute file operations.

## 9. Zero-action plans

A correctly-placed review (e.g. the real `docs\readmes` review) validly yields a
**zero-action plan** — no manufactured cleanup work. The plan states the directory
is already correctly placed and no action approval is needed.
