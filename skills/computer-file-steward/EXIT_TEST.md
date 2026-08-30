# EXIT TEST: computer-file-steward — Read-only directory review & registry foundation

**Date:** 2026-08-30
**Built by:** Goose (tasks COMPUTER_FILE_STEWARD_V1_READONLY → HARDEN v1.0.1 → REMEDIATE v1.0.2 → V2_PLANNING)
**Agent type:** A (skill only — scripts run locally, no new MCP/infra)
**Change level:** 3 (new scope — read-only capability + Build 2 approval-ready planning), hardened v1.0.1, remediated v1.0.2, extended Mode 2 (Build 2)
**Modes under test:** READ_ONLY_REVIEW (v1.0.2) + Mode 2 PLAN_EXECUTION (Build 2, decision-only)

**Status:** v1.0.1 is PROMOTED (commit `9f6bd68`). v1.0.2 is being remediated, staged, verified, and promoted/synchronized by this task. Once the task completes, the skill is **live** at `~/ai-context/skills/computer-file-steward/` and deployed at `C:\Users\micha\.config\agents\skills\computer-file-steward\`. It is NOT staged-only after promotion.

## v1.0.2 safety remediation (Findings A–E re-verified)
- [x] Target root that is itself a reparse point (junction/symlink/mount/pointer) is **rejected before enumeration** by `detect_reparse_points.ps1` and `inventory_directory.ps1` (executable fixture proved sentinel behind reparse root never appears).
- [x] `.path` pointer files are detected **during the same guarded walk**; no separate unguarded `Get-ChildItem -Recurse` pointer pass remains (static + fixture).
- [x] No unguarded `-Recurse` remains in traversal-sensitive inspection code (static verification).
- [x] Sensitive/protected directories are **pruned**: parent recorded with metadata only, marked `blocked=true`, children never enqueued, enumerated, hashed, or Git/pointer-inspected (fixture proved children absent from outputs).
- [x] Sensitive files are **never hashed or opened** (metadata only).
- [x] Git inspection runs with `GIT_OPTIONAL_LOCKS=0` for every subprocess (optional locks disabled), using only read-only/plumbing commands; full `.git` path/size/mtime/hash baseline is identical before and after two inspections (executable, WSL and Windows git).
- [x] Git inspection uses **read-only commands and safe argument-vector transport** (native Windows via PowerShell splatting; WSL/UNC via a fixed base64-encoded wrapper that never interpolates path data into a shell string); paths with apostrophes/spaces/brackets/&/;/Unicode cannot inject commands (executable injection matrix).
- [x] Valid YAML skill frontmatter (`name` + `description` only) on canonical/staged `SKILL.md`.
- [x] Stale operational documentation reconciled: staged-only claim removed; original conflicts and effective overlay resolutions distinguished; obsolete open-decision language corrected; Credential Rule not overridable by human approval.

## Trigger test
- [x] Request: "review a folder read-only" → skill activates
- [x] Request: "inventory a directory safely" → skill activates
- [x] Request: "produce a placement/classification report for a folder" → skill activates
- [x] Request: "what's in this folder and where should each thing go" → skill activates
- [x] Non-trigger: "build me an agent" → agent-builder activates (not this skill)
- [x] Non-trigger: "write a clinical note" → clinical-writing activates (not this skill)

## Routing test
- [x] General-purpose build tool; routes via any endpoint
- [x] Never ingests sensitive content (never reads it), so no [SENSITIVE]/[IDENTITY] routing needed

## Tools test
- [x] Required: shell (pwsh for .ps1 scripts; python3 for registry/validator), filesystem/UNC access
- [x] Required: the five bundled scripts (bootstrap_registries.py, inventory_directory.ps1, detect_reparse_points.ps1, inspect_git_state.ps1, validate_review_output.py)
- [x] Forbidden: any tool that can mutate files is never used on reviewed content
- [x] Forbidden: web search / external API for reading sensitive content (not used)

## Skill structure
- [x] `computer-file-steward/` follows local skill standard (frontmatter name+description only; references/templates/scripts)
- [x] SKILL.md clearly defaults to read-only review
- [x] EXIT_TEST.md covers safety, privacy, registries, determinism, reporting
- [x] Supporting references/templates/scripts documented

## Registries
- [x] All four registries generated (location 25, placement-policy 14, protection 11, project 6)
- [x] Every record has provenance (source_documents, observed_at, freshness_status, confidence)
- [x] Policy status distinguishes HARD/APPROVED/PROVISIONAL/HISTORICAL/UNKNOWN
- [x] Conflicting and stale facts visible (conflicts.json + report); effective resolutions recorded in history-preserving overlay
- [x] Registry generation idempotent (re-run produced no duplicates; file count identical)
- [x] No secret values stored (category/pointer only)

## Review engine (v1.0.2)
- [x] Requires an explicit target (scripts refuse without one)
- [x] Rejects/handles missing targets (exit 3 if target not found)
- [x] **Rejects a target whose root is a reparse point before enumeration (exit 5)**
- [x] **Prunes sensitive directories (blocked parent, children absent)**
- [x] **Detects `.path` pointers within the guarded walk**
- [x] Does not default to current directory
- [x] Does not follow reparse points (junctions/symlinks detected, blocked, not traversed)
- [x] Detects the fixture Git repository and dirty state (1 untracked file; branch master; sanitized remotes)
- [x] Stops content inspection after sensitivity is established (sensitive count recorded, no content read)
- [x] Produces all six required review outputs
- [x] Every proposed action blocked=true

## Safety (v1.0.2)
- [x] No existing source file modified (mutation baseline verified — ai-context unchanged, fixture unchanged)
- [x] No live system modified
- [x] No real sensitive body read
- [x] No secret value appears in outputs (secret-safety audit PASS)
- [x] No whole-drive or home-directory scan occurred
- [x] No junction, symlink, mount point, or pointer traversed (target-root reparse rejected)
- [x] No sensitive-directory child appears in inventory, pointer, Git, report, raw evidence, or logs
- [x] No file-operation implementation exists that can move/copy/rename/delete/quarantine/archive/restore/purge user assets (static audit)

## Determinism
- [x] Two unchanged fixture runs produce materially identical results
- [x] INVENTORY.csv / PROPOSED_ACTIONS.csv ordering stable; counts identical
- [x] Git inspection leaves the full `.git` tree unchanged (GIT_OPTIONAL_LOCKS=0)

## Documentation (v1.0.2)
- [x] Staged-only claim removed (skill is promoted and deployed)
- [x] Original conflicts and effective overlay resolutions distinguished (SOURCE_PRIORITY, REGISTRY_SCHEMA)
- [x] Obsolete open-decision language corrected (OPERATING_MODES ai-context root resolved via overlay CFL-001)
- [x] Credential Rule cannot be overridden by human approval (APPROVAL_PROTOCOL)
- [x] Future Mode 2/3/4 described only as unimplemented design (OPERATING_MODES)
- [x] Version labels internally consistent (v1.0.2)

## Result
- [x] PASS — all mandatory items met
- [ ] FAIL

# Build 2 — Mode 2 PLAN_EXECUTION (decision-only planning)

**Status:** Build 2 is PROMOTED and DEPLOYED. Adds approval-ready planning on top of
the read-only review; the skill still ships no executor.

## Mode 2 plan package (Build 2)
- [x] One plan directory per source review (`planning-runs/<plan-id>/`) with all 8 files.
- [x] JSON is canonical; CSV is a human flat view; JSON/CSV reconcile by action ID + count.
- [x] Stable plan ID and stable per-action IDs `ACT-<12-hex-sha256>` from canonical
  immutable identity fields (same input ⇒ same ID/hash).
- [x] Canonical manifest is deterministic (sorted keys, UTF-8, no in-payload timestamp);
  `manifest_sha256` verified by re-hash.
- [x] `execution_capability=NONE`; every action `execution_implemented=false`.
- [x] Every plan package states plan-only warning.
- [x] Conservative blocking; no G/sensitive/protected/Tier-1/reparse/git/permanent-deletion
  action is ever approval-ready.
- [x] Approval-ready only for HARD/APPROVED, reversible, unchanged, evidence-backed,
  non-sensitive, non-reparse, non-git, collision-clear actions.
- [x] Permanent deletion is never approval-ready.
- [x] Approval requires explicit action IDs; blocked/unknown/overlapping IDs rejected.
- [x] Approval binds to the exact manifest hash; manifest tampering invalidates approval.
- [x] Drift check reports CURRENT/SOURCE_DRIFT/POLICY_DRIFT/MANIFEST_MISMATCH/
  TARGET_UNAVAILABLE/BLOCKED_BOUNDARY_CHANGED; approval marked STALE on material drift.
- [x] Real `docs\readmes` review converts to a correct zero-action plan (no manufactured
  cleanup; keep-in-place stated; target unmodified).
- [x] Static no-executor gate passes (no mutating file op, no executor module, no
  manifest-as-commands interpretation).
- [x] Essential tests 1–5 pass.
- [x] Existing Mode 1 READ_ONLY_REVIEW remains read-only and unchanged in purpose.
