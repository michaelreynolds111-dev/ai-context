# REGISTRY_SCHEMA.md — The four registries: fields, provenance, and policy status

The skill generates four versioned, machine-readable registries under the skill
test/work area (JSON preferred; flat CSV views allowed). Every record carries
provenance. Registry generation is **idempotent** — running twice never duplicates
entries and preserves conflicts.

## 1. Location registry
| Field | Meaning |
|---|---|
| record_id | unique id (LOC-###) |
| canonical_path | canonical resolved path |
| path_style | windows / wsl / windows_drive / wsl_pointer / windows_virtual |
| physical_disk | Disk0/1/2 or vhdx |
| filesystem_type | NTFS / WSL2 ext4 / rclone_virtual_mount |
| owner_project | governing project/owner |
| role | purpose of the location |
| live_or_inactive | live / inactive / inactive_when_unplugged |
| real_directory_or_pointer | real_directory / junction / path_pointer / virtual_mount / pointer_view |
| reparse_type | none / junction / .path_pointer / cloud_placeholder / mixed |
| cloud_synchronised | bool |
| approved_for_inspection | bool |
| approved_for_modification | bool |
| sensitivity_boundary | workspace / live_system / config / data / house_identity / system / external_backup / out_of_scope / awareness_only |
| source_documents | provenance |
| observed_at | date |
| freshness_status | HARD_POLICY / OBSERVED / STALE / UNKNOWN |
| confidence | HIGH/MEDIUM-HIGH/MEDIUM/LOW |
| notes | context / conflicts |

Example entries in the built registry: bounded workspace root (LOC-001), the
`live-systems` junction/pointer view (LOC-002), each live-system junction
(LOC-003..009), drives (LOC-010..013), D:\Data (LOC-014), the stale
C:\HouseholdDataRaw snapshot (LOC-015), ai-context WSL + Desktop checkouts
(LOC-016/017), agent-workdir (LOC-018), LibreChat (LOC-019), household-vault
(LOC-020), WSL/Docker vhdx (LOC-021/022), Goose config/skills (LOC-023/024/025).

## 2. Placement-policy registry
| Field | Meaning |
|---|---|
| policy_id | unique id (POL-###) |
| asset_type | what the policy governs |
| preferred_root | preferred destination |
| allowed_storage | permitted storage |
| forbidden_storage | prohibited storage |
| git_allowed | bool |
| encryption_required | bool |
| retention_class | permanent / sensitive / live_system / regenerable / historical / repository / Tier1_secret ... |
| movement_approval_required | bool |
| policy_status | **HARD / APPROVED / PROVISIONAL / HISTORICAL / UNKNOWN** |
| policy_authority | source authority |
| rationale | why |
| source_documents | provenance |
| review_required | bool |

## 3. Protection registry
| Field | Meaning |
|---|---|
| asset_id | unique id (PROT-###) |
| asset_name | asset |
| primary_path | location |
| classification | A/B/C/D/E/F/G |
| sensitivity | non-sensitive / sensitive / SECRET / mixed / clinical ... |
| unique_or_reproducible | UNIQUE / REPRODUCIBLE / PARTLY |
| recovery_source | where the verified recovery copy lives |
| last_verified_recovery | date |
| recovery_destination_status | VERIFIED / OFF-MACHINE / BLOCKED / recreation-required ... |
| checksum_reference | SHA reference (no raw secrets) |
| deletion_eligible | bool |
| required_approval_level | human / human+pm |
| protection_reason | why protected |
| source_documents | provenance |
| confidence | level |

## 4. Project registry
| Field | Meaning |
|---|---|
| project_id | unique (PRJ-###) |
| project_name | name |
| primary_path | location |
| repository_path | git repo + state |
| current_state | phase/state |
| migration_status | status |
| authoritative_records | source documents |
| related_working_trees | related paths |
| sensitive_data_locations | sensitive locations (no values) |
| temporary_outputs | scratch/output paths |
| archive_location | verified archive path |
| immediate_next_action | next step |
| source_documents | provenance |
| confidence | level |

## Provenance rules
Every imported fact answers:
- Where did this fact come from? (`source_documents`)
- When was it observed? (`observed_at`)
- Is it hard policy, observed fact, historical record, or inference? (`freshness_status` / policy_status)
- Is a newer fact known to supersede it? (conflict/supersession records)
- What confidence applies? (`confidence`)

Do not silently resolve contradictory facts — store conflicts and surface them in
reports. The built registries include a `conflicts.json` declaring the **original
conflict records** (ai-context authority CFL-001, Mongo location CFL-002, Goose
primary install CFL-003). Each of these also has an **effective resolution** in
the history-preserving overlay (`registries/conflict_resolutions.json`, loaded by
`scripts/conflict_overlay.py`): CFL-001 RESOLVED (WSL ai-context authoritative;
Desktop dirty copy preserved non-authoritative), CFL-002 RESOLVED (live Mongo data
= named Docker volume `librechat_librechat_mongo_data` → `/data/db`; `data-node/`
is a historical artefact), CFL-003 RESOLVED (Goose coexistence: Windows primary
skill consumer, WSL CLI secondary). The original UNRESOLVED facts are preserved as
history; the overlay carries the effective resolved state and its review trigger.

## No-secret rule
Registries store pointers and categories, never secret values.
