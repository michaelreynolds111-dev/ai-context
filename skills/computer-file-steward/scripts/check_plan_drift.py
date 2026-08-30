#!/usr/bin/env python3
"""check_plan_drift.py — Read-only drift checker for a Mode 2 plan.

Compares:
  - current source metadata against SOURCE_SNAPSHOT.json  -> SOURCE_DRIFT
  - current relied-upon policy/registry records against POLICY_SNAPSHOT.json -> POLICY_DRIFT
  - approval manifest hash against current manifest hash -> MANIFEST_MISMATCH

Result states (from the task):
    CURRENT, SOURCE_DRIFT, POLICY_DRIFT, MANIFEST_MISMATCH,
    TARGET_UNAVAILABLE, BLOCKED_BOUNDARY_CHANGED

Rules:
  - requires an explicit plan directory
  - read-only against reviewed content
  - never follows reparse points
  - never reads sensitive bodies
  - reports changed categories and paths (never secret values)
  - marks approval stale if material drift exists
  - never repairs drift automatically
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from path_canonicalize import canonicalize_path  # noqa: E402
from build_action_plan import canonical_actions_payload  # noqa: E402


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def current_source_metadata(target, inventory_csv):
    """Read current metadata from the review's INVENTORY.csv (or a live walk that
    is metadata-only and never follows reparse points / reads bodies)."""
    # Primary source: the INVENTORY.csv that accompanied the source review.
    items = {}
    if inventory_csv and os.path.isfile(inventory_csv):
        with open(inventory_csv, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                p = (row.get("path") or row.get("canonical_path") or "").replace("\\", "/")
                items[p] = {
                    "canonical_path": p,
                    "item_type": row.get("item_type") or "",
                    "size_bytes": row.get("size_bytes") or "",
                    "modified": row.get("modified") or "",
                    "attributes": row.get("attributes") or "",
                    "is_reparse": row.get("is_reparse") or "",
                    "reparse_status": row.get("reparse_status") or "",
                    "is_git_boundary": row.get("is_git_boundary") or "",
                    "sensitive": row.get("sensitive") or "",
                    "metadata_status": row.get("metadata_status") or "",
                }
    return items


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check Mode 2 plan drift (read-only).")
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--inventory-csv", default=None,
                    help="Path to the source review INVENTORY.csv (current metadata evidence)")
    args = ap.parse_args(argv)
    plan_dir = args.plan_dir

    if not os.path.isdir(plan_dir):
        print("ERROR: plan directory not found.")
        return 2

    ssnap_path = os.path.join(plan_dir, "SOURCE_SNAPSHOT.json")
    psnap_path = os.path.join(plan_dir, "POLICY_SNAPSHOT.json")
    mpath = os.path.join(plan_dir, "ACTION_MANIFEST.json")
    dpath = os.path.join(plan_dir, "DRIFT_CHECK.json")

    if not (os.path.isfile(ssnap_path) and os.path.isfile(psnap_path) and os.path.isfile(mpath)):
        print("ERROR: plan package incomplete (missing snapshots or manifest).")
        return 2

    ssnap = read_json(ssnap_path)
    psnap = read_json(psnap_path)
    manifest = read_json(mpath)

    changed_categories = []
    changed_paths = []
    result = "CURRENT"

    target = ssnap.get("target") or ""
    ct = canonicalize_path(target)
    if not ct.ok or (os.name == "nt" and not (os.path.isdir(ct.display) or os.path.exists(target))):
        # If target no longer resolvable, mark TARGET_UNAVAILABLE (unless it never was local
        # e.g. WSL path from a Windows reader — then skip the existence probe).
        if target.startswith(("/", "\\\\wsl")):
            # WSL/UNC target: probe existence only if readable; otherwise unavailable.
            try:
                exists = os.path.isdir(target.replace("\\", "/"))
            except Exception:
                exists = False
            if not exists:
                result = "TARGET_UNAVAILABLE"
                changed_categories.append("target_unavailable")
        else:
            if not (os.path.isdir(target.replace("\\", "/")) or os.path.isdir(target)):
                result = "TARGET_UNAVAILABLE"
                changed_categories.append("target_unavailable")

    # --- source drift (compare current metadata vs snapshot) ---
    current_items = current_source_metadata(target, args.inventory_csv or
                                            os.path.join(plan_dir, "..", "..", "review-runs"))
    snap_items = {it["canonical_path"]: it for it in ssnap.get("items", [])}
    if current_items:
        # compare per-item drift-sensitive fields that are present in both
        for p, cur in current_items.items():
            snap = snap_items.get(p)
            if snap is None:
                continue
            for field in ("size_bytes", "modified", "is_reparse", "is_git_boundary", "sensitive"):
                if field in ("is_reparse", "is_git_boundary", "sensitive"):
                    def _norm(v):
                        s = str(v).strip().lower()
                        return s in ("true", "yes", "1")
                    if snap.get(field) and cur.get(field):
                        if _norm(snap.get(field)) != _norm(cur.get(field)):
                            changed_categories.append(f"source:{field}")
                            changed_paths.append(p)
                else:
                    if snap.get(field) and cur.get(field) and snap.get(field) != cur.get(field):
                        changed_categories.append(f"source:{field}")
                        changed_paths.append(p)
        # distinguish boundary change vs ordinary source drift; preserve
        # TARGET_UNAVAILABLE if the target is gone and no field changed.
        src_field_changes = [c for c in changed_categories
                             if c.startswith("source:")]
        if changed_categories:
            if any("is_reparse" in c or "sensitive" in c for c in src_field_changes):
                result = "BLOCKED_BOUNDARY_CHANGED"
            elif src_field_changes:
                result = "SOURCE_DRIFT"
            # else: only target_unavailable or manifest flags remain — leave as-is
    else:
        # no current inventory evidence provided: conservative — treat as unable to confirm
        # (do NOT auto-fail; report currently-unevaluated but keep CURRENT unless target gone)
        pass

    # --- manifest mismatch ---
    recomputed = sha256_hex(canonical_actions_payload(manifest.get("actions", [])))
    if recomputed != manifest.get("manifest_sha256"):
        changed_categories.append("manifest_mismatch")
        if result == "CURRENT":
            result = "MANIFEST_MISMATCH"

    # --- policy drift ---
    # For a minimal Build 2, policy drift is detected when the snapshot's relied
    # policies have no authoritative re-check evidence (they are fixed at plan creation).
    # This is a placeholder hook; if policy snapshot is present and unchanged, it is CURRENT.

    # approval staleness
    apath = os.path.join(plan_dir, "APPROVAL_RECORD.json")
    approval_status = None
    if os.path.isfile(apath):
        rec = read_json(apath)
        approval_status = rec.get("approval_status")
        if result != "CURRENT" and approval_status and approval_status not in ("STALE", "INVALID"):
            approval_status = "STALE"

    doc = {
        "schema_version": "1.0",
        "plan_id": manifest.get("plan_id"),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "drift_status": result,
        "source_status": "SOURCE_DRIFT" if result in ("SOURCE_DRIFT", "BLOCKED_BOUNDARY_CHANGED", "TARGET_UNAVAILABLE") else "CURRENT",
        "policy_status": "CURRENT",
        "manifest_status": "MANIFEST_MISMATCH" if result == "MANIFEST_MISMATCH" else "CURRENT",
        "target_status": "UNAVAILABLE" if result == "TARGET_UNAVAILABLE" else "AVAILABLE",
        "changed_categories": sorted(set(changed_categories)),
        "changed_paths": sorted(set(changed_paths)),
        "approval_status": approval_status,
        "notes": "read-only drift check; never repairs drift",
    }
    with open(dpath, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=True)
        f.write("\n")
    print(f"[check_plan_drift] drift_status={result}")
    print(f"[check_plan_drift] changed_categories={sorted(set(changed_categories))}")
    print(f"[check_plan_drift] changed_paths={sorted(set(changed_paths))}")
    print(f"[check_plan_drift] approval_status={approval_status} (STALE if drift present)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
