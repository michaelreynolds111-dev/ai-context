# CLASSIFICATION_MODEL.md — Classification model and its limits

## The model
```
A = Preserve now, non-sensitive
B = Preserve securely, sensitive
C = Reproducible, do not preserve
D = Already preserved elsewhere
E = Archive for historical reference
F = Candidate for deletion
G = Unknown, investigate safely
```
Plus an additional marker observed in the machine evidence: **T02 / "existing-task02"**
grouping for assets already preserved in the Task-02 recovery point, and B-ENCRYPTED
for the GPG-encrypted sensitive package in Task-04. These are preservation-state
labels, not classifications per se.

## Critical rule: classifications are NOT actions
- **A** does not automatically authorize movement.
- **B** does not automatically authorize copying.
- **C** does not authorize deletion.
- **D** does not prove the reviewed copy is disposable.
- **E** does not define the archive destination by itself.
- **F** means candidate only.
- **G** blocks action and requires investigation.

The report must always separate:
- classification;
- recommendation;
- confidence;
- policy status;
- action eligibility;
- approval requirement.

## Evidence-derived guidance (from Task-02/Task-03)
- **Folder-name classification is insufficient.** A folder named `backups/` can
  contain both historical-config (E) and reproducible-installer (C) content, plus a
  unique record. Inspect children; check duplicate/recoverability before escalating
  sensitivity.
- **Check for existing preserved copies before escalating to B.** If a verified
  matched copy exists (analysis outputs = C; source = B), reflect that.
- **Run a secret scan before archiving.** Structural field-name markers
  (`token`, `client_secret`, `api_key` in a config backup) are NOT real credentials.
  Confirm absence of real values before treating as non-sensitive.
- **Preserve Git full-history bundles** to capture deleted-file state, not just the
  working tree.
- **Defer non-deterministic / sensitive-unclassifiable items** to the owner rather
  than blind-archiving (e.g. D:\Data\briefings at G/B boundary).

## Confidence
- HIGH / MEDIUM-HIGH / MEDIUM / LOW.
- Confidence reflects source freshness, direct observation, and agreement across
  sources — not optimism.

## Protected/live-system and repo override
- Any item **in or belonging to a Git repository** → blocked from move/archive/delete
  in v1 (report only).
- Any item at a **reparse point** → blocked.
- Any **live-system / protected-path** match from the location/protection registries
  → blocked.
- These overrides out-rank any A–G label for *action* purposes.

## Classification is heuristic in v1
v1 assigns preliminary classifications from metadata + extension heuristics +
registry matches, always `blocked=true`, with documented confidence. It does not
assign final disposition or any action.
