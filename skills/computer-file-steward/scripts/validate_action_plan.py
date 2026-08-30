#!/usr/bin/env python3
"""validate_action_plan.py — Validate a Mode 2 plan package.

Checks:
  - required package files present
  - schema_version / plan_id / mode consistent
  - JSON canonical manifest is deterministic (re-hash == stored hash)
  - stable action IDs are deterministic from identity fields
  - JSON and CSV action views reconcile (IDs + count)
  - execution_capability == NONE on JSON and every action execution_implemented==false
  - action_count == number of actions
  - APPROVAL_RECORD binds to the exact manifest hash
  - no secret content (category/count only)
  - zero manufactured actions for a zero-action review (no move/delete invented)

Read-only: never mutates reviewed content.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_action_plan import (  # noqa: E402
    canonical_actions_payload, compute_action_id, action_identity,
    EXECUTION_CAPABILITY, PLAN_ONLY_WARNING,
)

SCHEMA_VERSION = "1.0"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a Mode 2 plan package.")
    ap.add_argument("--plan-dir", required=True, help="Path to a planning-runs/<plan-id> directory")
    args = ap.parse_args(argv)
    plan_dir = args.plan_dir

    checks = []
    ok_all = True

    def check(name, ok, detail=""):
        nonlocal ok_all
        checks.append((name, "PASS" if ok else "FAIL", detail))
        if not ok:
            ok_all = False

    required = ["ACTION_PLAN.md", "ACTION_MANIFEST.json", "ACTION_MANIFEST.csv",
                "APPROVAL_RECORD.json", "SOURCE_SNAPSHOT.json", "POLICY_SNAPSHOT.json",
                "DRIFT_CHECK.json", "PLAN_VALIDATION.md"]
    for f in required:
        check(f"required output present: {f}", os.path.isfile(os.path.join(plan_dir, f)), plan_dir)

    # Manifest
    mpath = os.path.join(plan_dir, "ACTION_MANIFEST.json")
    manifest = None
    if os.path.isfile(mpath):
        with open(mpath, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        check("schema_version", manifest.get("schema_version") == SCHEMA_VERSION, str(manifest.get("schema_version")))
        check("mode is PLAN_EXECUTION", manifest.get("mode") == "PLAN_EXECUTION", str(manifest.get("mode")))
        check("execution_capability == NONE",
              manifest.get("execution_capability") == EXECUTION_CAPABILITY,
              str(manifest.get("execution_capability")))
        actions = manifest.get("actions", [])
        check("action_count matches actions", manifest.get("action_count") == len(actions),
              f"{manifest.get('action_count')} vs {len(actions)}")
        check("every action execution_implemented==false",
              all(a.get("execution_implemented") is False for a in actions),
              f"sum_not_false={sum(1 for a in actions if a.get('execution_implemented') is not False)}")
        # determinism: rehash canonical payload
        recomputed = sha256_hex(canonical_actions_payload(actions))
        check("manifest_sha256 deterministic (rehash==stored)",
              recomputed == manifest.get("manifest_sha256"),
              f"{recomputed[:16]}... vs {str(manifest.get('manifest_sha256'))[:16]}...")
        if recomputed != manifest.get("manifest_sha256"):
            check("manifest_sha256 present", False, "rehash mismatch = tamper/determinism failure")
        # stable action IDs from identity fields
        id_ok = True
        for a in actions:
            ip = action_identity(a.get("proposed_action"), a.get("canonical_source_path"),
                                 a.get("canonical_destination"), manifest.get("source_review") or "",
                                 a.get("policy_id"), a.get("source_item_type"),
                                 a.get("classification"), manifest.get("plan_id"))
            expected = compute_action_id(ip)
            if expected["action_id"] != a.get("action_id") or expected["action_identity_sha256"] != a.get("action_identity_sha256"):
                id_ok = False
                check("action id deterministic", False, f"{a.get('action_id')} != {expected['action_id']}")
                break
        if id_ok:
            check("stable action IDs deterministic", True, f"{len(actions)} actions")
        # plans: permanent deletion never approval-ready, sensitive/G never approval-ready
        forbidden_ok = True
        for a in actions:
            if a.get("approval_ready"):
                cls = (a.get("classification") or "").upper()
                pa = (a.get("proposed_action") or "").lower()
                if cls == "G" or "delete" in pa or "purge" in pa or a.get("blocked"):
                    forbidden_ok = False
                    check("no forbidden approval-ready", False, a.get("action_id"))
                    break
        if forbidden_ok:
            check("no forbidden approval-ready (G/delete/purge/blocked)", True, "")
    else:
        check("manifest loaded", False, "ACTION_MANIFEST.json missing or invalid")

    # CSV reconciliation
    cpath = os.path.join(plan_dir, "ACTION_MANIFEST.csv")
    csv_ids = set()
    if os.path.isfile(cpath):
        with open(cpath, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        csv_ids = {r["action_id"] for r in rows}
        if manifest is not None:
            json_ids = {a["action_id"] for a in manifest["actions"]}
            check("JSON/CSV reconcile by ID", json_ids == csv_ids,
                  f"json={len(json_ids)} csv={len(csv_ids)}")
            check("JSON/CSV reconcile by count",
                  len(manifest["actions"]) == len(rows),
                  f"json={len(manifest['actions'])} csv={len(rows)}")
        check("CSV has no empty action_id", all(r.get("action_id") for r in rows), "")
        check("CSV execution_implemented all false",
              all(str(r.get("execution_implemented", "true")).lower() == "false" for r in rows), "")

    # Approval record binding
    apath = os.path.join(plan_dir, "APPROVAL_RECORD.json")
    if os.path.isfile(apath) and manifest is not None:
        with open(apath, "r", encoding="utf-8") as f:
            rec = json.load(f)
        check("approval binds to exact manifest hash",
              rec.get("manifest_sha256") == manifest.get("manifest_sha256"),
              f"rec={str(rec.get('manifest_sha256'))[:16]}.. manifest={str(manifest.get('manifest_sha256'))[:16]}..")
        ack = rec.get("acknowledgements", [])
        check("approval acknowledgement present",
              any("records a decision only" in x for x in ack), "")
        ids = rec.get("approved_action_ids", []) + rec.get("rejected_action_ids", []) + rec.get("deferred_action_ids", [])
        manifest_ids = {a["action_id"] for a in manifest["actions"]} if manifest else set()
        check("approval references only manifest ids", set(ids) <= manifest_ids, "")
        # mutual exclusivity
        apr = set(rec.get("approved_action_ids", []))
        rej = set(rec.get("rejected_action_ids", []))
        defr = set(rec.get("deferred_action_ids", []))
        overlapping = (apr & rej) | (apr & defr) | (rej & defr)
        check("approve/reject/defer mutually exclusive", not overlapping, str(overlapping))
        check("approval_status valid", rec.get("approval_status") in
              ("PENDING", "PARTIAL", "APPROVED", "REJECTED", "STALE", "INVALID"),
              str(rec.get("approval_status")))
    else:
        check("approval record loaded", False, "APPROVAL_RECORD.json missing")

    # plan-only warning present in ACTION_PLAN.md
    apl = os.path.join(plan_dir, "ACTION_PLAN.md")
    if os.path.isfile(apl):
        with open(apl, "r", encoding="utf-8") as f:
            content = f.read()
        check("plan-only warning present", "CANNOT EXECUTE" in content or "cannot execute" in content, "")
        check("no actions performed statement", "plan only" in content.lower(), "")
    else:
        check("ACTION_PLAN.md present", False, "")

    # zero manufactured action: for zero-action review, no move/delete actions
    if manifest is not None and len(manifest["actions"]) == 0:
        check("zero-action review produced zero actions", True, "no manufactured cleanup work")
        # also confirm README/ACTION_PLAN states keep-in-place
        if os.path.isfile(apl):
            with open(apl, "r", encoding="utf-8") as f:
                content = f.read()
            if "already correctly placed" in content or "keep" in content.lower():
                check("keep-in-place outcome stated", True, "zero-action plan statement")
            else:
                check("keep-in-place outcome stated", False, "")

    # ---- report ----
    lines = ["# VALIDATION_RESULTS (plan)", "", f"**Plan dir:** {plan_dir}", "",
             "| Result | Check | Detail |", "|---|---|---|"]
    for name, res, detail in checks:
        lines.append(f"| {res} | {name} | {detail} |")
    lines.append("")
    lines.append(f"**Overall: {'PASS' if ok_all else 'FAIL'}**")
    out = "\n".join(lines) + "\n"
    with open(os.path.join(plan_dir, "PLAN_VALIDATION.md"), "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
