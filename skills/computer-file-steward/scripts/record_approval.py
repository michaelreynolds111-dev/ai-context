#!/usr/bin/env python3
"""record_approval.py — Record human approval decisions on a Mode 2 plan.

Features:
  - item-level approve / reject / defer by exact action ID
  - binds to the exact manifest_sha256
  - rejects: blocked actions, unknown action IDs, overlapping approvals
  - detects manifest tampering -> approval becomes INVALID/STALE
  - NEVER invokes execution (approval is a decision record only)

Read-only against reviewed content. Only writes APPROVAL_RECORD.json in the
plan package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_action_plan import PLAN_ONLY_WARNING  # noqa: E402


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_record(rec: dict) -> str:
    r = dict(rec)
    r["approval_record_sha256"] = ""
    return json.dumps(r, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def load_plan(plan_dir):
    mpath = os.path.join(plan_dir, "ACTION_MANIFEST.json")
    apath = os.path.join(plan_dir, "APPROVAL_RECORD.json")
    with open(mpath, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(apath, "r", encoding="utf-8") as f:
        rec = json.load(f)
    return manifest, rec


def save_record(plan_dir, rec):
    rec["approval_record_sha256"] = sha256_hex(canonical_record(rec))
    with open(os.path.join(plan_dir, "APPROVAL_RECORD.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=True)
        f.write("\n")
    print(f"[record_approval] saved APPROVAL_RECORD.json (sha256={rec['approval_record_sha256']})")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Record approval decisions on a plan (decision-only).")
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--approve", action="append", default=[], help="action ID(s) to approve")
    ap.add_argument("--reject", action="append", default=[], help="action ID(s) to reject")
    ap.add_argument("--defer", action="append", default=[], help="action ID(s) to defer")
    ap.add_argument("--note", action="append", default=[], help="decision note")
    ap.add_argument("--decided-by", default="Michael")
    args = ap.parse_args(argv)

    manifest, rec = load_plan(args.plan_dir)
    actions = manifest["actions"]
    by_id = {a["action_id"]: a for a in actions}
    ids = set(by_id.keys())

    approved = set(args.approve)
    rejected = set(args.reject)
    deferred = set(args.defer)

    errors = []

    # all referenced ids must exist
    referenced = approved | rejected | deferred
    unknowns = referenced - ids
    if unknowns:
        errors.append(f"unknown action ID(s): {sorted(unknowns)}")

    # blocked actions cannot be approved
    for aid in approved:
        if aid in by_id and by_id[aid].get("blocked"):
            errors.append(f"cannot approve blocked action {aid}")

    # mutual exclusivity
    overlapping = (approved & rejected) | (approved & deferred) | (rejected & deferred)
    if overlapping:
        errors.append(f"overlapping approve/reject/defer: {sorted(overlapping)}")

    # manifest tamper detection
    from validate_action_plan import canonical_actions_payload
    recomputed = sha256_hex(canonical_actions_payload(manifest["actions"]))
    manifest_ok = recomputed == manifest.get("manifest_sha256")
    if not manifest_ok:
        errors.append("MANIFEST TAMPERED: stored manifest_sha256 does not match the actions")

    if errors:
        print("ERROR: approval NOT recorded.")
        for e in errors:
            print(f"  - {e}")
        return 1

    # also: does the record's manifest_sha256 already differ from current manifest?
    if rec.get("manifest_sha256") != manifest.get("manifest_sha256"):
        print("ERROR: APPROVAL_RECORD is bound to a different manifest (STALE). Refuse to record.")
        return 1

    # record
    existing = (set(rec.get("approved_action_ids", [])) |
                set(rec.get("rejected_action_ids", [])) |
                set(rec.get("deferred_action_ids", [])))
    for aid in approved:
        if aid in existing:
            print(f"WARN: {aid} already decided; leaving existing decision.")
            continue
        rec["approved_action_ids"].append(aid)
    for aid in rejected:
        if aid in existing:
            print(f"WARN: {aid} already decided; leaving existing decision.")
            continue
        rec["rejected_action_ids"].append(aid)
    for aid in deferred:
        if aid in existing:
            print(f"WARN: {aid} already decided; leaving existing decision.")
            continue
        rec["deferred_action_ids"].append(aid)
    rec["decision_notes"] = (rec.get("decision_notes") or []) + list(args.note)
    rec["decided_by"] = args.decided_by

    # approval_status: PENDING (nothing decided), PARTIAL (some), APPROVED (all eligible),
    # REJECTED (all rejected), else PARTIAL
    eligible = [a["action_id"] for a in actions if a.get("approval_ready")]
    decided = set(rec.get("approved_action_ids", [])) | \
              set(rec.get("rejected_action_ids", [])) | \
              set(rec.get("deferred_action_ids", []))
    if not decided:
        rec["approval_status"] = "PENDING"
    elif decided == set(e for e in eligible if e) and eligible and set(eligible) <= decided:
        rec["approval_status"] = "APPROVED"
    elif rec.get("rejected_action_ids") and not rec.get("approved_action_ids") and not (set(eligible) - decided):
        rec["approval_status"] = "REJECTED"
    else:
        rec["approval_status"] = "PARTIAL"

    save_record(args.plan_dir, rec)
    print(f"[record_approval] approval_status={rec['approval_status']}")
    print(f"[record_approval] approved={sorted(rec['approved_action_ids'])} "
          f"rejected={sorted(rec['rejected_action_ids'])} deferred={sorted(rec['deferred_action_ids'])}")
    print(f"[record_approval] {PLAN_ONLY_WARNING}")
    print(f"[record_approval] NO FILE OPERATIONS PERFORMED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
