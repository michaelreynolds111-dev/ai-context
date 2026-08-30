#!/usr/bin/env python3
"""classification_rules.py — Classification evidence rules for Computer File
Steward v1.0.1 (Correction D).

Class C minimum evidence: Class C (reproducible) may be assigned ONLY when at
least one explicit regeneration basis is present. A filename, extension,
directory name, or generic 'documentation' appearance is INSUFFICIENT by itself.

Forbidden name/extension inference: README/Markdown, .tmp, .bak, installer,
cache, and backup names must NOT directly determine classification.

Metadata-only behavior: when only metadata is available with no regeneration
evidence and no authoritative registry match, default to G (unknown) with an
honest missing-evidence note. An authoritative registry match may override weak
filename inference.

Classification remains SEPARATE from action eligibility: no classification
directly authorizes an action. All proposed actions stay blocked in v1.

This module is used by the classification regression tests and may be consulted
by the steward when assigning provisional classifications. It is pure; no
filesystem access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Names/extensions that are NEVER sufficient, on their own, to establish class C.
FORBIDDEN_AUTO_C_NAMES = {
    "README", "README.md", "readme", "readme.md", "MARKDOWN", "markdown",
    "CHANGELOG", "changelog", "LICENSE", "license", "installer", "setup",
    "cache", "cached", "backup", "backups", "old", "historical",
}
FORBIDDEN_AUTO_C_EXTENSIONS = {".md", ".markdown", ".txt", ".tmp", ".bak",
                                ".cache", ".exe", ".msi", ".installer", ".dmg",
                                ".pkg", ".deb", ".rpm"}


@dataclass
class Evidence:
    """Evidence available for a candidate item's classification."""
    name: str = ""
    extension: str = ""
    is_directory: bool = False
    # Provider of an explicit regeneration basis.
    has_package_manifest: bool = False          # recognized package/dep env + source manifest
    has_generator_app: bool = False             # generated cache with known generating application
    has_derived_source_process: bool = False    # derived output + identified source + documented regen
    has_authoritative_duplicate: bool = False   # authoritative duplicate/upstream that can regenerate
    has_policy_record: bool = False             # existing policy explicitly classifies asset type as reproducible
    # Registry override (authoritative).
    registry_classification: Optional[str] = None   # e.g. from protection registry
    registry_confidence: Optional[str] = None
    # Metadata-only marker / flags set by caller.
    metadata_only: bool = False

    @property
    def has_regeneration_evidence(self) -> bool:
        return bool(self.has_package_manifest or self.has_generator_app or
                    self.has_derived_source_process or self.has_authoritative_duplicate or
                    self.has_policy_record)


@dataclass
class ClassificationResult:
    classification: str            # A..G
    confidence: str                # HIGH/MEDIUM-HIGH/MEDIUM/LOW
    missing_evidence_for_c: List[str] = field(default_factory=list)
    evidence_source: str = ""      # e.g. 'registry_match', 'regeneration_evidence', 'metadata_only'
    note: str = ""


def classify_from_evidence(ev: Evidence) -> ClassificationResult:
    """Assign a provisional classification from evidence using the v1.0.1 rules.

    Returns a ClassificationResult. Classification NEVER authorizes an action.
    """
    # 1. Authoritative registry override (strongest non-filename evidence).
    if ev.registry_classification is not None:
        return ClassificationResult(
            classification=ev.registry_classification,
            confidence=ev.registry_confidence or "MEDIUM",
            evidence_source="registry_match",
            note="authoritative registry classification overrides weak filename inference",
        )

    # 2. Class C requires explicit regeneration evidence.
    if ev.has_regeneration_evidence:
        return ClassificationResult(
            classification="C",
            confidence="MEDIUM-HIGH" if not ev.metadata_only else "MEDIUM",
            evidence_source="regeneration_evidence",
            note="explicit regeneration basis recorded",
        )

    # 3. Metadata-only OR forbidden-name/extension with NO regeneration evidence.
    #    Never auto-classify C from appearance alone.
    forbidden = (
        ev.name in FORBIDDEN_AUTO_C_NAMES
        or ev.extension.lower() in FORBIDDEN_AUTO_C_EXTENSIONS
    )
    if ev.metadata_only or forbidden:
        missing = _missing_c_evidence(ev)
        # Default to G (unknown) unless an authoritative registry already
        # returned an evidence-backed classification above (step 1).
        return ClassificationResult(
            classification="G",
            confidence="LOW",
            missing_evidence_for_c=missing,
            evidence_source="metadata_only" if ev.metadata_only else "filename_inference_insufficient",
            note="insufficient evidence to classify; appearance alone cannot establish C",
        )

    # 4. Otherwise (has direct metadata suggesting ordinary, non-sensitive file),
    #    still cannot claim reproducibility -> G unless more evidence appears.
    return ClassificationResult(
        classification="G",
        confidence="LOW",
        missing_evidence_for_c=_missing_c_evidence(ev),
        evidence_source="insufficient_evidence",
        note="no regeneration basis and no registry classification",
    )


def _missing_c_evidence(ev: Evidence) -> List[str]:
    out = []
    if not ev.has_package_manifest:
        out.append("recognized package/dependency environment with a source manifest")
    if not ev.has_generator_app:
        out.append("generated cache with a known generating application/process")
    if not ev.has_derived_source_process:
        out.append("derived output with an identified source plus documented regeneration process")
    if not ev.has_authoritative_duplicate:
        out.append("authoritative duplicate or upstream source that can regenerate the item")
    if not ev.has_policy_record:
        out.append("existing policy record explicitly classifying the asset type as reproducible")
    return out
