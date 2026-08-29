# APPROVAL_PROTOCOL.md — Authorisation model for file stewardship actions

## Purpose
v1 is READ-ONLY. No action is executed. This document defines the authorisation
model that a future execute-capable mode must honour, so that the read-only
reports clearly record approval requirements. It is design/contract, not active
execution capability.

## Approval levels
| Level | Who | When required |
|---|---|---|
| NONE | — | Never for any action in v1 (all blocked). |
| REVIEW | Machine pre-check only | Every proposed action must pass safety/path/secret checks. |
| HUMAN | Michael | Any movement_approval_required=true action, any repo-adjacent action, any action touching sensitive/deletion candidate, any B/A/E/F/G disposition. |
| HUMAN + PASSWORD MANAGER | Michael + password manager | Any action touching Tier-1 secrets (only pointer, never the value). |

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

## Gate conditions for future execution (design only)
Before ANY execution mode could run, ALL of the following must hold:
1. Authoritative placement architecture confirmed (ai-context root decision resolved).
2. The placement-policy registry has only HARD/APPROVED destinations referenced.
3. Repository-aware preservation + ownership is established for any repo-adjacent item.
4. No secret-bearing file is ever moved/staged (Credential Rule).
5. Every operation is reversible or covered by a verified recovery point.
6. Full provenance captured; dual-drive enumeration for any deletion.
7. Human approval per action and per sensitive/deletion candidate.

These are not implemented in v1 and are not waived by any automatic approval.
