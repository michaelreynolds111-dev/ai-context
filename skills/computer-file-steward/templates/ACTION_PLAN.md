# ACTION_PLAN.md — plan-only report (template)

## 1. Plan identity and source review
- Plan ID: `PLAN-...`
- Mode: `PLAN_EXECUTION` (Build 2)
- Source review: `<review-run-id>`
- Manifest SHA-256: `<sha256>`

## 2. Strong plan-only warning
**THIS PACKAGE IS A PLAN ONLY. IT CANNOT EXECUTE FILE OPERATIONS.**
`execution_capability` = `NONE`. No action is implemented for execution.

## 3. Summary counts
_(filled by build_action_plan.py)_

## 4. Approval-ready actions
_(none unless genuine eligible actions exist)_

## 5. Blocked actions and exact reasons
_(none for a correctly-placed review)_

## 6. Source and destination overview
_(per-action source/destination)_

## 7. Collision findings

## 8. Recovery prerequisites

## 9. Policy authority and provisional-policy warnings

## 10. Drift status
See `DRIFT_CHECK.json`.

## 11. How to approve or reject action IDs
Use `record_approval.py` with explicit action IDs.

## 12. Approval does not execute anything
Approval records a decision only.

## 13. Exactly one next action
_(filled by build_action_plan.py)_
