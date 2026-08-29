# EXIT TEST: computer-file-steward — Read-only directory review & registry foundation

**Date:** 2026-08-30
**Built by:** Goose (task COMPUTER_FILE_STEWARD_V1_READONLY)
**Agent type:** A (skill only — scripts run locally, no new MCP/infra)
**Change level:** 3 (new scope — new read-only capability)
**Mode under test:** READ_ONLY_REVIEW (v1)

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
- [x] Conflicting and stale facts visible (conflicts.json + report)
- [x] Registry generation idempotent (re-run produced no duplicates; file count identical)
- [x] No secret values stored (category/pointer only)

## Review engine
- [x] Requires an explicit target (scripts refuse without one)
- [x] Rejects/handles missing targets (exit 3 if target not found)
- [x] Does not default to current directory
- [x] Does not follow reparse points (symlink detected, blocked, not traversed)
- [x] Detects the fixture Git repository and dirty state (1 untracked file; branch master; sanitized remotes)
- [x] Treats the mixed backup child folder at child level (folder-name classification insufficient — documented)
- [x] Stops content inspection after sensitivity is established (sensitive count = 1, no content read)
- [x] Produces all six required review outputs (run-001 and run-002)
- [x] Every proposed action blocked=true (64/64 in each fixture run)

## Safety
- [x] No existing source file modified (mutation baseline verified — ai-context unchanged, fixture unchanged)
- [x] No live system modified
- [x] No real sensitive body read
- [x] No secret value appears in outputs (secret-safety audit PASS)
- [x] No whole-drive or home-directory scan occurred
- [x] No junction, symlink, mount point, or pointer traversed
- [x] No file-operation implementation exists that can move/copy/rename/delete/quarantine/archive/restore/purge user assets (scripts are read-only)

## Determinism
- [x] Two unchanged fixture runs (run-001, run-002) produce materially identical results
- [x] INVENTORY.csv byte-identical; PROPOSED_ACTIONS.csv byte-identical; classification counts identical
- [x] Output ordering stable
- [x] Registry entries not duplicated

## Documentation
- [x] Novice-readable usage example included (See "Example review" in SKILL.md + README anchor)
- [x] Report distinguishes fact, policy, inference, confidence, and approval requirement
- [x] Future Mode 2/3/4 described only as unimplemented design, not active capacity (OPERATING_MODES.md)

## Result
- [x] PASS — all mandatory items met
- [ ] FAIL

## Notes
- Skill is **staged only** at `/home/michael/agent-workdir/staging-ai-context/skills/computer-file-steward/`.
  NOT promoted/synced to `ai-context/skills/` or the Goose skills dir (Level 3 staged path).
- Review runs: `run-001-read-only-review` and `run-002-read-only-review` under
  `/home/michael/agent-workdir/computer-file-steward-v1/review-runs/`.
- The skill's scripts are invoked from Windows pwsh against WSL/UNC paths (validated working).
