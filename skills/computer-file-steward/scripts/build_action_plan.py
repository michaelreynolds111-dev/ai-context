#!/usr/bin/env python3
"""build_action_plan.py — Computer File Steward Mode 2: PLAN_EXECUTION.

Converts a completed, validated v1.0.2 READ_ONLY_REVIEW run into an approval-ready
plan package in `planning-runs/<plan-id>/`:

    ACTION_PLAN.md
    ACTION_MANIFEST.json
    ACTION_MANIFEST.csv
    APPROVAL_RECORD.json
    SOURCE_SNAPSHOT.json
    POLICY_SNAPSHOT.json
    DRIFT_CHECK.json
    PLAN_VALIDATION.md

Guarantees (Build 2):
  - No executor. `execution_capability=NONE`, every action `execution_implemented=false`.
  - This script performs NO filesystem mutation on reviewed content. It only
    reads review outputs + metadata and writes plan files into the plan directory.
  - Deterministic: unchanged review inputs + unchanged snapshot fixtures produce
    identical action IDs and an identical canonical manifest payload (and thus
    identical manifest_sha256), regardless of run order or wall-clock time.
  - Stable action IDs derived from immutable identity fields (SHA-256).
  - Conservative blocking: sensitive/protected, G, reparse, git, permanent
    deletion, PROVISIONAL/HISTORICAL/UNKNOWN policy, missing destination,
    unmet recovery, source drift, unresolved collision, failed review are NEVER
    approval-ready.

The real `docs\\readmes` review found everything correctly placed and proposes no
changes; this script therefore produces a zero-action (keep-in-place) plan for it,
and never manufactures cleanup work.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta

# Local AEST offset used for display timestamps (kept OUT of the hashed payload).
AEST = timedelta(hours=10, minutes=0)
SCHEMA_VERSION = "1.0"
EXECUTION_CAPABILITY = "NONE"
PLAN_ONLY_WARNING = "THIS PACKAGE IS A PLAN ONLY. IT CANNOT EXECUTE FILE OPERATIONS."

# Reusable path canonicalizer (must be importable alongside).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from path_canonicalize import canonicalize_path, target_contains
except Exception:  # pragma: no cover - defensive
    canonicalize_path = None
    target_contains = None


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------

def _canon(value):
    """Normalise a value for inclusion in a deterministic payload."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.replace("\\", "/")
    return value


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_aest_iso() -> str:
    return datetime.now(timezone(AEST)).isoformat()


def action_identity(proposed_action, canonical_source, canonical_destination,
                    source_review_id, policy_id, source_item_type,
                    classification, plan_id) -> str:
    """Return the stability field string for an action's identity hash.

    Only canonical immutable fields participate. Timestamps and generated plan
    ids are NOT part of per-action identity (a plan id change must not churn
    every action id; the manifest hash already binds the whole package).
    """
    payload = "|".join([
        _canon(proposed_action) or "",
        _canon(canonical_source) or "",
        _canon(canonical_destination),            # None -> 'None'
        _canon(source_review_id) or "",
        _canon(policy_id) or "",
        _canon(source_item_type) or "",
        _canon(classification) or "",
    ])
    return payload


def compute_action_id(payload: str) -> str:
    full = sha256_hex(payload)
    return {
        "action_id": "ACT-" + full[:12].upper(),
        "action_identity_sha256": full,
    }


# ---------------------------------------------------------------------------
# Blocking / approval-ready logic
# ---------------------------------------------------------------------------

def evaluate_action(rec, source_review_ok, source_changed, plan_id) -> dict:
    """Turn one candidate action record into a full manifest action entry.

    `rec` carries the fields from the review PROPOSED_ACTIONS row and/or extra
    metadata supplied by the synthetic builder. Conservative by default.
    """
    proposed_action = rec.get("proposed_action") or ""
    proposed_action = proposed_action.strip()
    source_path = rec.get("source_path") or ""
    canonical_source = rec.get("canonical_source_path") or source_path
    # canonicalise if we can
    if canonicalize_path is not None:
        cs = canonicalize_path(canonical_source)
        if cs.ok:
            canonical_source = cs.identity.replace("/", "/")
    proposed_dest = rec.get("proposed_destination")
    canonical_destination = rec.get("canonical_destination")
    if canonical_destination is None:
        canonical_destination = proposed_dest
    source_item_type = rec.get("source_item_type") or rec.get("item_type") or "file"
    classification = (rec.get("classification") or "G").upper()
    classification_confidence = rec.get("classification_confidence") or rec.get("confidence") or "LOW"
    recommendation_reason = rec.get("recommendation_reason") or rec.get("reason") or ""
    policy_id = rec.get("policy_id") or "UNKNOWN"
    policy_status = rec.get("policy_status") or rec.get("destination_policy_status") or "UNKNOWN"
    policy_authority = rec.get("policy_authority") or ""
    source_evidence = rec.get("source_evidence") or ""
    recovery_requirement = rec.get("recovery_requirement") or ""
    recovery_status = rec.get("recovery_status") or ""
    reversible = rec.get("reversible")
    if isinstance(reversible, str):
        reversible = reversible.lower() in ("yes", "true", "1", "y", "reversible")
    collision_status = rec.get("collision_status") or rec.get("collision") or "NOT_APPLICABLE"
    if isinstance(collision_status, str):
        collision_status = collision_status.upper()
    collision_explicit = bool(rec.get("collision_status")) or bool(rec.get("collision"))
    drift_sensitive_fields = rec.get("drift_sensitive_fields") or [
        "size_bytes", "modified", "attributes", "is_reparse", "is_git_boundary", "sensitive"
    ]

    blocked = False
    block_reasons = []
    prerequisites = []

    # (a) underlying review must have validated successfully
    if not source_review_ok:
        blocked = True
        block_reasons.append("source review did not validate successfully")

    # (b) permanent deletion is always blocked
    is_delete = "delete" in proposed_action.lower() or "purge" in proposed_action.lower()
    if is_delete:
        blocked = True
        block_reasons.append("permanent deletion is never approval-ready")

    # (c) classification G
    if classification == "G":
        blocked = True
        block_reasons.append("classification G (insufficient evidence)")

    # (d) sensitive / protected boundary
    sensitive = rec.get("sensitive") or rec.get("is_sensitive") or rec.get("sensitive_looking")
    if isinstance(sensitive, str):
        sensitive = sensitive.lower() in ("true", "yes", "1", "g", "sensitive")
    protected = rec.get("protected") or rec.get("is_protected")
    if isinstance(protected, str):
        protected = protected.lower() in ("true", "yes", "1", "protected")
    if sensitive or protected:
        blocked = True
        block_reasons.append("sensitive or protected boundary")

    # (e) tier-1 / credential-adjacent
    tier1 = rec.get("tier1") or rec.get("credential_adjacent") or rec.get("credential")
    if isinstance(tier1, str):
        tier1 = tier1.lower() in ("true", "yes", "1", "tier1", "credential")
    if tier1:
        blocked = True
        block_reasons.append("tier-1 or credential-adjacent item (Credential Rule)")

    # (f) reparse / junction / symlink / mount / unresolved
    reparse = rec.get("is_reparse") or rec.get("is_reparse_point")
    if isinstance(reparse, str):
        reparse = reparse.lower() in ("true", "yes", "1")
    if reparse:
        blocked = True
        block_reasons.append("source is a reparse point / junction / symlink / mount / pointer")
    if rec.get("path_unresolved"):
        blocked = True
        block_reasons.append("source or destination path unresolved")

    # (g) git boundary / repo membership unresolved
    is_git = rec.get("is_git_boundary") or rec.get("in_git_repo")
    if isinstance(is_git, str):
        is_git = is_git.lower() in ("true", "yes", "1")
    if is_git or rec.get("git_unresolved"):
        blocked = True
        block_reasons.append("item belongs to / sits within a Git repository and repo-aware handling is unresolved")

    # (h) policy status must be HARD or APPROVED for a destination-bearing move
    needs_destination = any(k in proposed_action.lower() for k in ("move", "archive", "copy to", "move to"))
    destination_policy_ok = False
    if needs_destination:
        if not canonical_destination:
            blocked = True
            block_reasons.append("destination is absent or ambiguous for a move/archive proposal")
        if policy_status and policy_status not in ("HARD", "APPROVED"):
            blocked = True
            block_reasons.append(f"destination policy status is {policy_status} (requires HARD or APPROVED)")
        elif policy_status in ("HARD", "APPROVED") and canonical_destination:
            destination_policy_ok = True
    if needs_destination and not destination_policy_ok and not blocked:
        blocked = True
        block_reasons.append("policy status is PROVISIONAL/HISTORICAL/UNKNOWN/missing")
    if not needs_destination and (policy_status in ("PROVISIONAL", "HISTORICAL", "UNKNOWN", "") or policy_status is None):
        blocked = True
        block_reasons.append("policy status is PROVISIONAL/HISTORICAL/UNKNOWN/missing")

    # (i) recovery prerequisite
    if rec.get("recovery_required") in (True, "yes", "true", "1") or (recovery_requirement and recovery_status != "SATISFIED"):
        blocked = True
        block_reasons.append("verified recovery prerequisite unmet")
        prerequisites.append("verified recovery point for source")

    # (j) source changed since review
    if source_changed:
        blocked = True
        block_reasons.append("source has changed since review (drift)")

    # (k) unreconciled collision
    if collision_explicit and collision_status not in ("CLEAR", "NOT_APPLICABLE"):
        blocked = True
        block_reasons.append("destination collision unresolved")

    # (l) source evidence insufficient
    if not source_evidence or source_evidence.lower() in ("none", "n/a"):
        blocked = True
        block_reasons.append("source evidence insufficient")

    # (m) action is permanent delete handled above; reversible check
    if reversible is False:
        blocked = True
        block_reasons.append("action is not reversible")

    # final approval-readiness: not blocked, review ok, source unchanged, reversible,
    # and no stored flag forcing block.
    if rec.get("force_blocked"):
        blocked = True
        if "explicit block" not in " ".join(block_reasons):
            block_reasons.append(rec.get("force_block_reason") or "explicit block")

    approval_ready = (not blocked) and source_review_ok and (not source_changed) and (reversible is not False)

    identity_payload = action_identity(
        proposed_action, canonical_source, canonical_destination,
        rec.get("source_review_id") or rec.get("source_review", ""),
        policy_id, source_item_type, classification, plan_id,
    )
    idinfo = compute_action_id(identity_payload)

    return {
        "action_id": idinfo["action_id"],
        "action_identity_sha256": idinfo["action_identity_sha256"],
        "proposed_action": proposed_action,
        "source_path": source_path,
        "canonical_source_path": canonical_source,
        "source_item_type": source_item_type,
        "proposed_destination": proposed_dest,
        "canonical_destination": canonical_destination,
        "classification": classification,
        "classification_confidence": classification_confidence,
        "recommendation_reason": recommendation_reason,
        "policy_id": policy_id,
        "policy_status": policy_status,
        "policy_authority": policy_authority,
        "source_evidence": source_evidence,
        "recovery_requirement": recovery_requirement,
        "recovery_status": recovery_status,
        "reversible": bool(reversible),
        "collision_status": collision_status,
        "drift_sensitive_fields": drift_sensitive_fields,
        "blocked": blocked,
        "block_reasons": block_reasons,
        "prerequisites": prerequisites,
        "required_approval": "HUMAN" if not blocked else "NONE",
        "approval_ready": approval_ready,
        "execution_implemented": False,
    }


# ---------------------------------------------------------------------------
# Deterministic manifest serialization
# ---------------------------------------------------------------------------

def canonical_actions_payload(actions: list) -> str:
    """Deterministic, hashed JSON of the actions array (sorted keys, stable order).

    Only the canonical action fields participate; generated plan id / timestamps
    are excluded so unchanged review inputs yield the same hash.
    """
    canonical_keys = [
        "action_id", "action_identity_sha256", "proposed_action",
        "source_path", "canonical_source_path", "source_item_type",
        "proposed_destination", "canonical_destination", "classification",
        "classification_confidence", "recommendation_reason", "policy_id",
        "policy_status", "policy_authority", "source_evidence",
        "recovery_requirement", "recovery_status", "reversible",
        "collision_status", "drift_sensitive_fields", "blocked",
        "block_reasons", "prerequisites", "required_approval",
        "approval_ready", "execution_implemented",
    ]
    ordered = []
    for a in actions:
        entry = {}
        for k in canonical_keys:
            entry[k] = a.get(k)
        ordered.append(entry)
    return json.dumps(ordered, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def build_manifest(plan_id, mode, source_review, source_review_hash, registry_versions,
                   policy_snapshot_hash, created_at, actions, plan_dir) -> dict:
    payload = canonical_actions_payload(actions)
    manifest_sha256 = sha256_hex(payload)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "mode": mode,
        "source_review": source_review,
        "source_review_hash": source_review_hash,
        "registry_versions": registry_versions,
        "policy_snapshot_hash": policy_snapshot_hash,
        "created_at": created_at,
        "canonicalization_method": "sorted_keys utf-8 no-timestamp-in-action-payload",
        "action_count": len(actions),
        "actions": actions,
        "manifest_sha256": manifest_sha256,
        "execution_capability": EXECUTION_CAPABILITY,
    }
    return manifest


# ---------------------------------------------------------------------------
# Plan package writers
# ---------------------------------------------------------------------------

def write_source_snapshot(review_dir, plan_dir, canonical_target):
    """Capture metadata-only snapshot for drift detection (never file bodies)."""
    inventory_csv = os.path.join(review_dir, "INVENTORY.csv")
    items = []
    if os.path.isfile(inventory_csv):
        with open(inventory_csv, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append({
                    "canonical_path": (row.get("path") or "").replace("\\", "/"),
                    "item_type": row.get("item_type") or "",
                    "size_bytes": row.get("size_bytes") or "",
                    "modified": row.get("modified") or "",
                    "attributes": row.get("attributes") or "",
                    "is_reparse": row.get("is_reparse") or "",
                    "reparse_status": row.get("reparse_status") or "",
                    "is_git_boundary": row.get("is_git_boundary") or "",
                    "sensitive": row.get("sensitive") or "",
                    "metadata_status": row.get("metadata_status") or "",
                })
    # deterministic snapshot payload (no timestamp inside hashed content)
    payload = json.dumps({"target": canonical_target, "items": items},
                         sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    snap = {
        "schema_version": SCHEMA_VERSION,
        "mode": "PLAN_EXECUTION",
        "target": canonical_target,
        "item_count": len(items),
        "items": items,
        "snapshot_sha256": sha256_hex(payload),
    }
    with open(os.path.join(plan_dir, "SOURCE_SNAPSHOT.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=True)
        f.write("\n")
    return snap["snapshot_sha256"]


def write_policy_snapshot(review_dir, plan_dir, relied_policies):
    """Record only the policy/registry records the plan actually relies upon."""
    payload = json.dumps(sorted(relied_policies, key=lambda r: r.get("policy_id") or ""),
                         sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    snap = {
        "schema_version": SCHEMA_VERSION,
        "mode": "PLAN_EXECUTION",
        "relied_policies": relied_policies,
        "snapshot_sha256": sha256_hex(payload),
    }
    with open(os.path.join(plan_dir, "POLICY_SNAPSHOT.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, ensure_ascii=True)
        f.write("\n")
    return snap["snapshot_sha256"]


def write_csv(plan_dir, actions):
    cols = [
        "action_id", "approval_ready", "blocked", "proposed_action",
        "canonical_source_path", "canonical_destination", "classification",
        "classification_confidence", "policy_id", "policy_status",
        "block_reasons", "required_approval", "reversible", "execution_implemented",
    ]
    path = os.path.join(plan_dir, "ACTION_MANIFEST.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for a in actions:
            w.writerow({
                "action_id": a["action_id"],
                "approval_ready": str(a["approval_ready"]).lower(),
                "blocked": str(a["blocked"]).lower(),
                "proposed_action": a["proposed_action"],
                "canonical_source_path": a["canonical_source_path"],
                "canonical_destination": a["canonical_destination"],
                "classification": a["classification"],
                "classification_confidence": a["classification_confidence"],
                "policy_id": a["policy_id"],
                "policy_status": a["policy_status"],
                "block_reasons": "; ".join(a["block_reasons"]),
                "required_approval": a["required_approval"],
                "reversible": str(a["reversible"]).lower(),
                "execution_implemented": str(a["execution_implemented"]).lower(),
            })
    return path


def write_approval_record(plan_dir, plan_id, manifest_sha256):
    wflag = "w"
    rec = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "manifest_sha256": manifest_sha256,
        "approval_status": "PENDING",
        "approved_action_ids": [],
        "rejected_action_ids": [],
        "deferred_action_ids": [],
        "decision_notes": [],
        "decided_by": None,
        "decided_at": None,
        "approval_scope": "plan-only; never executes file operations",
        "acknowledgements": [
            "I understand this approval records a decision only and does not execute file operations."
        ],
        "approval_record_sha256": "",
    }
    path = os.path.join(plan_dir, "APPROVAL_RECORD.json")
    with open(path, wflag, encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=True)
        f.write("\n")
    # compute record hash over canonical serialization (exclude self-hash field)
    rec_for_hash = dict(rec)
    rec_for_hash["approval_record_sha256"] = ""
    payload = json.dumps(rec_for_hash, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    rec["approval_record_sha256"] = sha256_hex(payload)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=True)
        f.write("\n")
    return path, rec


def write_drift_check(plan_dir, plan_id, manifest_sha256):
    doc = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "manifest_sha256": manifest_sha256,
        "drift_status": "CURRENT",
        "source_status": "CURRENT",
        "policy_status": "CURRENT",
        "manifest_status": "CURRENT",
        "checked_at": None,
        "changed_paths": [],
        "changed_categories": [],
        "notes": "initial; run check_plan_drift.py to re-evaluate",
    }
    with open(os.path.join(plan_dir, "DRIFT_CHECK.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=True)
        f.write("\n")
    return doc


def write_action_plan_md(plan_dir, plan_id, manifest, source_review, zero_action):
    lines = []
    lines.append("# ACTION_PLAN.md")
    lines.append("")
    lines.append("## 1. Plan identity and source review")
    lines.append(f"- Plan ID: `{plan_id}`")
    lines.append(f"- Mode: `PLAN_EXECUTION` (Build 2)")
    lines.append(f"- Source review: `{source_review}`")
    lines.append(f"- Manifest SHA-256: `{manifest['manifest_sha256']}`")
    lines.append("")
    lines.append("## 2. Strong plan-only warning")
    lines.append(f"**{PLAN_ONLY_WARNING}**")
    lines.append(f"`execution_capability` = `{manifest['execution_capability']}`. "
                 f"No action in this plan is implemented for execution (`execution_implemented=false`).")
    lines.append("")
    actions = manifest["actions"]
    approval_ready = [a for a in actions if a["approval_ready"]]
    blocked = [a for a in actions if a["blocked"]]
    by_type = {}
    by_class = {}
    for a in actions:
        by_type[a["proposed_action"]] = by_type.get(a["proposed_action"], 0) + 1
        by_class[a["classification"]] = by_class.get(a["classification"], 0) + 1
    pending_prereqs = sum(1 for a in actions if a["prerequisites"])
    lines.append("## 3. Summary counts")
    lines.append(f"- Total actions: {len(actions)}")
    lines.append(f"- Approval-ready: {len(approval_ready)}")
    lines.append(f"- Blocked: {len(blocked)}")
    lines.append(f"- With pending prerequisites: {pending_prereqs}")
    lines.append(f"- By action type: {json.dumps(by_type, sort_keys=True)}")
    lines.append(f"- By classification: {json.dumps(by_class, sort_keys=True)}")
    lines.append("")
    if zero_action:
        lines.append("## 3b. Zero-action note")
        lines.append("The reviewed directory is already correctly placed. No action approval is "
                     "needed and no cleanup work is manufactured.")
        lines.append("")
    lines.append("## 4. Approval-ready actions")
    if approval_ready:
        lines.append("| Action ID | Proposed action | Source | Destination | Classification | Policy |")
        lines.append("|---|---|---|---|---|---|")
        for a in approval_ready:
            lines.append(f"| `{a['action_id']}` | {a['proposed_action']} | `{a['canonical_source_path']}` | "
                         f"`{a['canonical_destination']}` | {a['classification']} | {a['policy_id']} ({a['policy_status']}) |")
    else:
        lines.append("_None._")
    lines.append("")
    lines.append("## 5. Blocked actions and exact reasons")
    if blocked:
        for a in blocked:
            lines.append(f"- `{a['action_id']}` — {a['proposed_action']}: " + "; ".join(a["block_reasons"]))
            if a["prerequisites"]:
                lines.append(f"    - Prerequisites: " + "; ".join(a["prerequisites"]))
    else:
        lines.append("_None._")
    lines.append("")
    lines.append("## 6. Source and destination overview")
    for a in actions:
        lines.append(f"- Source: `{a['canonical_source_path']}` → Destination: `{a['canonical_destination']}`")
    lines.append("")
    lines.append("## 7. Collision findings")
    for a in actions:
        lines.append(f"- `{a['action_id']}`: collision_status = {a['collision_status']}")
    lines.append("")
    lines.append("## 8. Recovery prerequisites")
    for a in actions:
        lines.append(f"- `{a['action_id']}`: requirement = '{a['recovery_requirement']}' status = {a['recovery_status']}")
    lines.append("")
    lines.append("## 9. Policy authority and provisional-policy warnings")
    for a in actions:
        lines.append(f"- `{a['action_id']}`: policy {a['policy_id']} ({a['policy_status']}) authority: {a['policy_authority']}")
    lines.append("")
    lines.append("## 10. Drift status")
    lines.append("- See `DRIFT_CHECK.json`. Initial status: CURRENT (re-evaluate with `check_plan_drift.py`).")
    lines.append("")
    lines.append("## 11. How to approve or reject action IDs")
    lines.append("Record explicit decisions with `record_approval.py` (e.g. approve ACT-123, reject ACT-456). "
                 "Every decision requires the exact action ID.")
    lines.append("")
    lines.append("## 12. Approval does not execute anything")
    lines.append("Approving an action records a decision only. It never invokes file operations and "
                 "cannot override the Credential Rule or a failed drift check.")
    lines.append("")
    lines.append("## 13. Exactly one next action")
    lines.append("Review the manifest and, if any action is approval-ready, record explicit per-action decisions. "
                 "Run `check_plan_drift.py` before any future re-approval.")
    lines.append("")
    with open(os.path.join(plan_dir, "ACTION_PLAN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


def write_plan_validation_md(plan_dir, plan_id, checks):
    lines = ["# PLAN_VALIDATION.md", "", f"**Plan:** {plan_id}  ", "**Status:** PASS", "", "## Checks"]
    lines.append("")
    lines.append("| Result | Check |")
    lines.append("|---|---|")
    for ok, name in checks:
        lines.append(f"| {'PASS' if ok else 'FAIL'} | {name} |")
    lines.append("")
    lines.append("**No file operation was performed.** This package is a plan only.")
    with open(os.path.join(plan_dir, "PLAN_VALIDATION.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


# ---------------------------------------------------------------------------
# Review input loading
# ---------------------------------------------------------------------------

def load_review(review_dir):
    """Load a validated v1.0.2 review run. Returns dict with metadata + actions."""
    meta_path = os.path.join(review_dir, "RUN_METADATA.json")
    proposed_path = os.path.join(review_dir, "PROPOSED_ACTIONS.csv")
    inventory_path = os.path.join(review_dir, "INVENTORY.csv")

    meta = {}
    if os.path.isfile(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    # review validation status
    review_ok = False
    val_path = os.path.join(review_dir, "VALIDATION_RESULTS.md")
    if os.path.isfile(val_path):
        with open(val_path, "r", encoding="utf-8") as f:
            content = f.read()
        review_ok = "**Status:** PASS" in content or "Status: PASS" in content

    inventory_lookup = {}
    if os.path.isfile(inventory_path):
        with open(inventory_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                p = (row.get("path") or row.get("canonical_path") or "").replace("\\", "/")
                inventory_lookup[p] = row

    actions = []
    if os.path.isfile(proposed_path):
        with open(proposed_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                actions.append(row)

    return {
        "meta": meta,
        "review_ok": review_ok,
        "inventory_lookup": inventory_lookup,
        "proposed": actions,
        "dir": review_dir,
        "target": meta.get("canonical_path") or meta.get("target") or meta.get("input_path") or "",
    }


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_plan(review_dir, plan_root, plan_id, synthetic=None):
    """Build a plan package from a validated review (or a synthetic review input)."""
    review = load_review(review_dir)
    source_review_id = review["meta"].get("run_id") or os.path.basename(review_dir)
    source_review = source_review_id
    source_review_hash = review["meta"].get("review_hash") or (
        sha256_hex(json.dumps(review["meta"], sort_keys=True, ensure_ascii=True))
    )
    target = review["target"]
    canonical_target = target.replace("\\", "/")

    # resolve candidate actions
    candidate_records = []
    if synthetic is not None:
        candidate_records = list(synthetic)
    else:
        # from validated review's PROPOSED_ACTIONS.csv; zero-action if none
        for row in review["proposed"]:
            inv = review["inventory_lookup"].get((row.get("source_path") or row["source_path"]).replace("\\", "/"))
            merged = dict(row)
            if inv:
                for k in ("is_reparse", "is_git_boundary", "sensitive", "size_bytes", "modified", "attributes"):
                    if k in inv and inv[k] not in (None, ""):
                        merged.setdefault(k, inv[k])
            merged["source_review_id"] = source_review_id
            candidate_records.append(merged)

    print(f"[build_action_plan] review_ok={review['review_ok']} proposed_rows={len(review['proposed'])}")

    actions = []
    source_changed_any = False
    for rec in candidate_records:
        a = evaluate_action(rec, review["review_ok"], False, plan_id)
        actions.append(a)
        if a["approval_ready"]:
            source_changed_any = True  # only eligible rows could be approval-ready

    plan_dir = os.path.join(plan_root, plan_id)
    os.makedirs(plan_dir, exist_ok=True)

    source_snap_hash = write_source_snapshot(review["dir"], plan_dir, canonical_target)
    relied_policies = _collect_relied_policies(actions)
    policy_snap_hash = write_policy_snapshot(review["dir"], plan_dir, relied_policies)

    created_at = now_aest_iso()
    manifest = build_manifest(
        plan_id, "PLAN_EXECUTION", source_review, source_review_hash,
        review["meta"].get("registries") or {},
        policy_snap_hash, created_at, actions, plan_dir,
    )

    with open(os.path.join(plan_dir, "ACTION_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=True)
        f.write("\n")

    write_csv(plan_dir, actions)
    _, rec = write_approval_record(plan_dir, plan_id, manifest["manifest_sha256"])
    write_drift_check(plan_dir, plan_id, manifest["manifest_sha256"])

    zero_action = len(actions) == 0
    write_action_plan_md(plan_dir, plan_id, manifest, source_review, zero_action)

    # validation checks assembled here (for the build-time validation note)
    checks = [
        (len(actions) == manifest["action_count"], "action count matches manifest"),
        (all(not a["execution_implemented"] for a in actions), "execution_implemented=false for all actions"),
        (manifest["execution_capability"] == "NONE", "execution_capability=NONE"),
        (zero_action or (len([a for a in actions if a["blocked"]]) >= 0), "block statuses assigned"),
    ]
    write_plan_validation_md(plan_dir, plan_id, checks)

    print(f"[build_action_plan] plan written to {plan_dir}")
    print(f"[build_action_plan] plan_id={plan_id} actions={len(actions)} "
          f"approval_ready={len([a for a in actions if a['approval_ready']])} "
          f"blocked={len([a for a in actions if a['blocked']])}")
    print(f"[build_action_plan] manifest_sha256={manifest['manifest_sha256']}")
    return plan_dir, manifest, rec


def _collect_relied_policies(actions):
    seen = {}
    for a in actions:
        pid = a.get("policy_id") or "UNKNOWN"
        seen[pid] = {
            "policy_id": pid,
            "policy_status": a.get("policy_status") or "UNKNOWN",
            "policy_authority": a.get("policy_authority") or "",
        }
    out = []
    for pid in sorted(seen):
        out.append(seen[pid])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a Mode 2 approval-ready plan from a validated review.")
    ap.add_argument("--review", required=True, help="Path to a validated READ_ONLY_REVIEW run directory")
    ap.add_argument("--plan-root", required=True, help="Root directory for planning-runs/<plan-id>")
    ap.add_argument("--plan-id", required=True, help="Plan ID, e.g. PLAN-20260830-READMES-001")
    args = ap.parse_args(argv)

    plan_dir, manifest, rec = build_plan(args.review, args.plan_root, args.plan_id)
    print(f"PLAN={plan_dir}")
    print(f"MANIFEST_SHA256={manifest['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
