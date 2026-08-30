#!/usr/bin/env python3
"""conflict_overlay.py — Durable, history-preserving conflict-resolution overlay
for Computer File Steward v1.0.1 (Correction E).

The three machine-knowledge conflicts declared in conflicts.json remain intact.
This module loads an optional overlay (conflict_resolutions.json), applies it at
read time to produce an EFFECTIVE resolved view, and never deletes or obscures
the historical conflicting evidence.

Design rules:
  - Overlay loading is OPTIONAL. If absent/malformed, fail safely (no crash, no
    mutation, report the issue).
  - Application is IDEMPOTENT (loading/applying twice yields the same result).
  - Secret values never present (overlay is assertions/pointers only).
  - Each resolution carries provenance, superseded alternatives, and a
    review_trigger for future revalidation.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional


def load_overlay(overlay_path: str) -> dict:
    """Load and validate the overlay. Returns a dict with 'resolutions' list.

    Fail safe: on any missing/malformed case, return a dict with
    'load_error' set and an empty resolutions list rather than raising.
    """
    base = {"load_error": None, "resolutions": [], "source_path": overlay_path}
    if not overlay_path or not os.path.isfile(overlay_path):
        base["load_error"] = "overlay_missing"
        return base
    try:
        with open(overlay_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        base["load_error"] = f"overlay_malformed:{type(e).__name__}"
        return base
    if not isinstance(data, dict) or not isinstance(data.get("resolutions"), list):
        base["load_error"] = "overlay_malformed:schema"
        return base
    base.update(data)
    return base


def apply_overlay(original_conflicts: List[dict], overlay_resolutions: List[dict]) -> List[dict]:
    """Return an effective view of conflicts with overlay applied.

    Each original conflict (which carries the historical UNRESOLVED facts) is
    returned unchanged, plus an 'effective_status' and 'resolution' pulled from
    the overlay when a matching conflict_id exists. Original records are never
    mutated or deleted. Idempotent: applying the same overlay twice yields the
    same effective view.
    """
    by_id = {r.get("conflict_id"): r for r in overlay_resolutions if isinstance(r, dict)}
    effective = []
    for c in original_conflicts:
        cid = c.get("conflict_id")
        entry = dict(c)  # copy, do not mutate original
        if cid in by_id:
            entry["effective_status"] = by_id[cid].get("resolution_status", "RESOLVED")
            entry["resolution"] = by_id[cid].get("resolution", "")
            entry["review_trigger"] = by_id[cid].get("review_trigger", "")
            entry["superseded_alternatives"] = by_id[cid].get("superseded_alternatives", [])
            entry["overlay_applied"] = True
        else:
            entry["effective_status"] = entry.get("status", "UNRESOLVED")
            entry["overlay_applied"] = False
        effective.append(entry)
    return effective
