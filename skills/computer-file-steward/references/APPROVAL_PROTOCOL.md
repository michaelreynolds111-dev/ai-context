# APPROVAL_PROTOCOL.md — Authorisation model for file stewardship actions

## Purpose
v1 is READ-ONLY. No action is executed. This document defines the authorisation
model that a future execute-capable mode must honour, so that the read-only
reports clearly record approval requirements. It is design/contract, not active
execution capability.

## The Credential Rule is ABSOLUTE
Passwords, PINs, MFA seeds, recovery codes, security answers, private keys, and
other Tier-1 secret values **never enter or move through this system in any form**.
**Human approval can never override the Credential Rule.** No approval level —
including HUMAN or HUMAN + PASSWORD MANAGER — authorises moving, staging, reading,
or otherwise handling a secret value or a secret-bearing file body through the
steward. The only allowed handling of Tier-1 material is:

- recording a **pointer** to where the secret lives (e.g. "NRMA login is in Bitwarden, item X");
- a **manual password-manager workflow** performed outside the steward.

Any future execute mode that a user or other agent approves still must respect
this absolute rule; approval authority does not extend to Tier-1 values or bodies.

## Approval levels
| Level | Who | When required |
|---|---|---|
| NONE | — | Never for any action in v1 (all blocked). |
| REVIEW | Machine pre-check only | Every proposed action must pass safety/path/secret checks. |
| HUMAN | Michael | Any movement_approval_required=true action, any repo-adjacent action, any action touching sensitive/deletion candidate, any B/A/E/F/G disposition. |
| HUMAN + PASSWORD MANAGER | Michael + password manager | Any action **planning to record a pointer** to Tier-1 secrets (never the value, never the body). |

## Required per proposed action
Every `PROPOSED_ACTIONS.csv` row must record:
- `proposed_action` (advisory)
- `source_path`
- `proposed_destination`
- `destination_policy_status` (hard/approved/provisional/historical/unknown)
- `classification`
- `reason`
- `confidence`
- `reversible`
- `blocked` (always `true` in v1)
- `block_reason`
- `required_approval`
- `source_evidence`

## Build 2: approval record (Mode 2, decision-only)

Mode 2 produces `APPROVAL_RECORD.json`, a human decision record that **binds to the
exact manifest hash** and **never executes**. Rules:
- `approval_status` ∈ {PENDING, PARTIAL, APPROVED, REJECTED, STALE, INVALID}; default PENDING.
- Approve/reject/defer IDs are mutually exclusive; every referenced ID must exist in
  the manifest; blocked actions cannot be approved; unknown IDs rejected.
- Approval cannot change an action's fields; if the manifest changes, approval becomes
  INVALID/STALE.
- Approval never overrides the Credential Rule, protected boundaries, a failed drift
  check, or an unresolved policy requirement.
- Required acknowledgement:
  `I understand this approval records a decision only and does not execute file operations.`
- Approval requires explicit action IDs; vague phrases ("looks good", "go ahead") are
  never accepted as structured approval.
- Approval creates no filesystem action.

## Gate conditions for future execution (design only)
Before ANY execution mode could run, ALL of the following must hold:
1. Authoritative placement architecture confirmed. (The ai-context root decision is
   **RESOLVED** by overlay CFL-001: WSL `/home/michael/ai-context` authoritative;
   Desktop dirty copy preserved non-authoritative. Any other placement authority
   must be settled before execution.)
2. The placement-policy registry has only HARD/APPROVED destinations referenced.
3. Repository-aware preservation + ownership is established for any repo-adjacent item.
4. **No secret-bearing file is ever moved/staged, and human approval cannot waive
   the Credential Rule.**
5. Every operation is reversible or covered by a verified recovery point.
6. Full provenance captured; dual-drive enumeration for any deletion.
7. Human approval per action and per sensitive/deletion candidate.

These are not implemented in v1 and are not waived by any automatic approval.
