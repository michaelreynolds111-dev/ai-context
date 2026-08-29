#!/usr/bin/env python3
"""
bootstrap_registries.py — Build the four Computer File Steward v1 registries.

Registries:
  1. location_registry.json
  2. placement_policy_registry.json
  3. protection_registry.json
  4. project_registry.json

Each record carries provenance (source_documents, observed_at, freshness_status,
confidence, notes) and no secret values. The script is IDEMPOTENT: running twice
overwrites and never duplicates entries, and it preserves conflicts explicitly.

USAGE:
    python3 bootstrap_registries.py --out <output_dir>
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Observed-at stamp (task run date). Fact freshness uses these markers.
# ---------------------------------------------------------------------------
OBSERVED = "2026-08-30"                      # build/observation date
INVESTIGATION_DATE = "2026-08-29"            # when D: investigation reports ran
RECOVERY_DATE = "2026-08-29"                 # Task-04 recovery point
PRESERVATION_DATE = "2026-08-29"             # Task-02 preservation run

def src(*paths):
    """Tag a fact with its source document paths."""
    return list(paths)

# ---------------------------------------------------------------------------
# 1. LOCATION REGISTRY
# ---------------------------------------------------------------------------
# fields: record_id, canonical_path, path_style, physical_disk, filesystem_type,
# owner_project, role, live_or_inactive, real_directory_or_pointer, reparse_type,
# cloud_synchronised, approved_for_inspection, approved_for_modification,
# sensitivity_boundary, source_documents, observed_at, freshness_status, confidence, notes

R = "READ_ONLY_INSPECTION"

location_records = [
    # Hard policy — bounded workspace root
    dict(record_id="LOC-001", canonical_path="C:\\Users\\micha\\ai-workspace",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="workspace", role="single bounded root for AI file ops",
         live_or_inactive="live", real_directory_or_pointer="real_directory",
         reparse_type="none", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=True,
         sensitivity_boundary="workspace",
         source_documents=src("ai-workspace/README.md","ai-workspace/SCOPE.md","ai-workspace/AGENTS.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Decision 18 Aug 2026 Option A. Only path given to LibreChat filesystem MCP and Goose dev extension."),

    dict(record_id="LOC-002", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="workspace", role="junction + path-pointer view of live systems (NOT physical source)",
         live_or_inactive="live", real_directory_or_pointer="pointer_view",
         reparse_type="mixed_junctions_and_pointers", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_systems",
         source_documents=src("ai-workspace/README.md","ai-workspace/AGENTS.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Do not physically move, rename, delete, or re-junction any live-systems item. Physical source of truth is behind the junction."),

    # Live-system junctions (protected)
    dict(record_id="LOC-003", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\torbox-system",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="torbox-system", role="junction to Docker Compose stack (7 containers)",
         live_or_inactive="live", real_directory_or_pointer="junction",
         reparse_type="junction", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Resolves to C:\\torbox-system. Protected live system."),

    dict(record_id="LOC-004", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\stash",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="stash", role="junction to Stash native app data",
         live_or_inactive="live", real_directory_or_pointer="junction",
         reparse_type="junction", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Resolves to C:\\Users\\micha\\.stash (stash-go.sqlite, config.yml)."),

    dict(record_id="LOC-005", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\rdtclient",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="rdtclient", role="junction to RDT Client config",
         live_or_inactive="live", real_directory_or_pointer="junction",
         reparse_type="junction", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Resolves to C:\\appdata\\rdtclient."),

    dict(record_id="LOC-006", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\downloads-scanner",
         path_style="windows", physical_disk="Disk1", filesystem_type="NTFS",
         owner_project="downloads-scanner", role="junction to scan/watcher/server .ps1 + rules + logs",
         live_or_inactive="live", real_directory_or_pointer="junction",
         reparse_type="junction", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Resolves to D:\\Downloads\\_scanner."),

    dict(record_id="LOC-007", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\watchdog",
         path_style="windows", physical_disk="Disk1", filesystem_type="NTFS",
         owner_project="watchdog", role="scoped path pointer to resource_watchdog files",
         live_or_inactive="live", real_directory_or_pointer="path_pointer",
         reparse_type=".path_pointer", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Scoped pointer to 2 surviving resource_watchdog files in D:\\Data, NOT all of D:\\Data."),

    dict(record_id="LOC-008", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\librechat",
         path_style="wsl_pointer", physical_disk="Disk0(vhdx)", filesystem_type="WSL2 ext4",
         owner_project="librechat", role="WSL path pointer to /home/michael/LibreChat",
         live_or_inactive="live", real_directory_or_pointer="path_pointer",
         reparse_type=".path_pointer", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Junction cannot cross WSL UNC; single logical unit pointered via .path file."),

    dict(record_id="LOC-009", canonical_path="C:\\Users\\micha\\ai-workspace\\live-systems\\claude-desktop-mcp",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="claude-desktop", role="read-only awareness pointer (STALE)",
         live_or_inactive="inactive", real_directory_or_pointer="path_pointer",
         reparse_type=".path_pointer", cloud_synchronised=False,
         approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="awareness_only",
         source_documents=src("ai-workspace/README.md","ai-workspace/stack-map.md","docs/GOTCHAS.md"),
         observed_at=OBSERVED, freshness_status="STALE", confidence="MEDIUM",
         notes="Claude Desktop deleted 18 Aug 2026. Pointer slated for removal on next workspace sweep. claude_desktop_config.json holds live GitHub PAT - READ-ONLY awareness only."),

    # Drives
    dict(record_id="LOC-010", canonical_path="C:\\", path_style="windows_drive", physical_disk="Disk0",
         filesystem_type="NTFS", owner_project="system", role="system drive (FullyEncrypted)",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="system",
         source_documents=src("D:\\\\AI-System-Investigation\\\\01-SYSTEM-BASELINE.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Hosts Docker WSL vhdx (46GB) + Ubuntu WSL vhdx (24GB). Never scan whole drive."),

    dict(record_id="LOC-011", canonical_path="D:\\", path_style="windows_drive", physical_disk="Disk1",
         filesystem_type="NTFS", owner_project="data", role="data drive (FullyDecrypted, cannot BitLocker)",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="data",
         source_documents=src("D:\\\\AI-System-Investigation\\\\01-SYSTEM-BASELINE.md","ai-context/docs/GOTCHAS.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="2794 GB, NTFS. D:\\Data is the LIVE pipeline. Never scan whole drive."),

    dict(record_id="LOC-012", canonical_path="E:\\", path_style="windows_drive", physical_disk="Disk2",
         filesystem_type="NTFS", owner_project="external", role="external WD Elements USB (off-machine backup)",
         live_or_inactive="inactive_when_unplugged", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="external_backup",
         source_documents=src("D:\\\\AI-System-Preservation\\\\Task-02\\\\run-20260829-160940\\\\01-PHYSICAL-DISK-MAP.md"),
         observed_at=PRESERVATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Do not connect/mount E: if disconnected (per forbidden actions). 1863 GB external."),

    dict(record_id="LOC-013", canonical_path="T:\\Torbox", path_style="windows_virtual", physical_disk="virtual",
         filesystem_type="rclone_virtual_mount", owner_project="torbox", role="rclone virtual mount (NOT a real folder)",
         live_or_inactive="live", real_directory_or_pointer="virtual_mount", reparse_type="cloud_placeholder",
         cloud_synchronised=True, approved_for_inspection=False, approved_for_modification=False,
         sensitivity_boundary="out_of_scope",
         source_documents=src("ai-workspace/SCOPE.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Explicitly OUT of scope. Treated as cloud/remote view, never a physical directory."),

    # Live project / data locations
    dict(record_id="LOC-014", canonical_path="D:\\Data", path_style="windows", physical_disk="Disk1",
         filesystem_type="NTFS", owner_project="data-pipeline", role="LIVE legacy pipeline root + git repo",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="data",
         source_documents=src("ai-context/docs/GOTCHAS.md","D:\\\\AI-System-Investigation\\\\02-REPOSITORY-INVENTORY.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Git remote github.com/michaelreynolds111-dev/data-archive. DIRTY (many untracked). ~29.3GB."),

    dict(record_id="LOC-015", canonical_path="C:\\HouseholdDataRaw\\Data", path_style="windows", physical_disk="Disk0",
         filesystem_type="NTFS", owner_project="household", role="STALE one-time snapshot of HouseholdDataRaw",
         live_or_inactive="inactive", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=False, approved_for_modification=False,
         sensitivity_boundary="household_identity",
         source_documents=src("ai-context/docs/GOTCHAS.md"),
         observed_at=OBSERVED, freshness_status="STALE", confidence="MEDIUM",
         notes="[IDENTITY] household data. Cleanup on C: alone does not touch live D: copy. Do not inspect harmful bodies."),

    dict(record_id="LOC-016", canonical_path="/home/michael/ai-context", path_style="wsl", physical_disk="Disk0(vhdx)",
         filesystem_type="WSL2 ext4", owner_project="ai-context", role="Git repo - single source of truth (build docs/skills)",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=True, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="workspace",
         source_documents=src("ai-context/BUILD_STATE.md","D:\\\\AI-System-Investigation\\\\02-REPOSITORY-INVENTORY.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Git remote michaelreynolds111-dev/ai-context.git. Clean 28 Aug 2026. THE authoritative checkout per policy (WSL working copy)."),

    dict(record_id="LOC-017", canonical_path="C:\\Users\\micha\\Desktop\\New folder\\ai-context", path_style="windows",
         physical_disk="Disk0", filesystem_type="NTFS", owner_project="ai-context",
         role="Desktop working copy - DIRTY/uncommitted", live_or_inactive="live",
         real_directory_or_pointer="real_directory", reparse_type="none", cloud_synchronised=True,
         approved_for_inspection=True, approved_for_modification=False, sensitivity_boundary="workspace",
         source_documents=src("D:\\\\AI-System-Investigation\\\\02-REPOSITORY-INVENTORY.md","D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="CONFLICT: two ai-context checkouts. Authoritative = UNKNOWN. 17+ uncommitted changes. Do not overwrite either. HIGH local-only risk."),

    dict(record_id="LOC-018", canonical_path="/home/michael/agent-workdir", path_style="wsl", physical_disk="Disk0(vhdx)",
         filesystem_type="WSL2 ext4", owner_project="build", role="LibreChat<->Goose handoff folder + task/output work",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=True,
         sensitivity_boundary="workspace",
         source_documents=src("ai-context/AGENT_BOOTSTRAP.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="Bound to /app/agent-workdir in LibreChat. Authorized write scope for build artifacts."),

    dict(record_id="LOC-019", canonical_path="/home/michael/LibreChat", path_style="wsl", physical_disk="Disk0(vhdx)",
         filesystem_type="WSL2 ext4", owner_project="librechat", role="LibreChat source + compose stack",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=True, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("D:\\\\AI-System-Investigation\\\\04-LIBRECHAT-MAP.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="6-container stack; frontend :3080; .env secret-bearing; uploads live. Protected."),

    dict(record_id="LOC-020", canonical_path="/home/michael/household-vault", path_style="wsl", physical_disk="Disk0(vhdx)",
         filesystem_type="WSL2 ext4", owner_project="household", role="[IDENTITY] vault - NOT a git repo, never make it one",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=False, approved_for_modification=False,
         sensitivity_boundary="household_identity",
         source_documents=src("ai-context/AGENT_BOOTSTRAP.md","ai-context/BACKUP_AI_MASTER_BUILD_PLAN.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="[IDENTITY] Never part of workspace. Never git. Never inspect bodies."),

    # WSL/Docker vhdx (protected live storage)
    dict(record_id="LOC-021", canonical_path="C:\\Users\\micha\\AppData\\Local\\Docker\\wsl\\disk\\docker_data.vhdx",
         path_style="windows", physical_disk="Disk0", filesystem_type="WSL2 vhdx",
         owner_project="docker", role="Docker engine data store (46.20 GB)",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("D:\\\\AI-System-Investigation\\\\03-DOCKER-WSL-INVENTORY.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Contains 26 images, 22 containers, 19 volumes. Do not scan/alter."),

    dict(record_id="LOC-022", canonical_path="C:\\Users\\micha\\AppData\\Local\\wsl\\{23f0a123-...}\\ext4.vhdx",
         path_style="windows", physical_disk="Disk0", filesystem_type="WSL2 vhdx",
         owner_project="wsl", role="Ubuntu-24.04 WSL root filesystem (24.02 GB)",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="live_system",
         source_documents=src("D:\\\\AI-System-Investigation\\\\03-DOCKER-WSL-INVENTORY.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Do not recurse across WSL/Docker boundaries."),

    dict(record_id="LOC-023", canonical_path="C:\\Users\\micha\\AppData\\Roaming\\Block\\goose\\config",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="goose", role="Goose (Windows) config",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="config",
         source_documents=src("D:\\\\AI-System-Investigation\\\\05-GOOSE-AND-TOOLS-MAP.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Username = micha. Sync script at ...\\Block\\goose\\sync_skills.ps1 v2.0."),

    dict(record_id="LOC-024", canonical_path="C:\\Users\\micha\\.config\\agents\\skills", path_style="windows",
         physical_disk="Disk0", filesystem_type="NTFS", owner_project="goose",
         role="Goose global skills directory (sync target)",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=True, approved_for_modification=False,
         sensitivity_boundary="workspace",
         source_documents=src("C:\\Users\\micha\\AppData\\Roaming\\Block\\goose\\sync_skills.ps1","D:\\\\AI-System-Investigation\\\\05-GOOSE-AND-TOOLS-MAP.md"),
         observed_at=OBSERVED, freshness_status="HARD_POLICY", confidence="HIGH",
         notes="sync_skills.ps1 v2.0 auto-discovers skill dirs and copies complete trees (references/templates/scripts)."),

    dict(record_id="LOC-025", canonical_path="C:\\Users\\micha\\AppData\\Local\\Programs\\Goose",
         path_style="windows", physical_disk="Disk0", filesystem_type="NTFS",
         owner_project="goose", role="Goose desktop UI/CLI install",
         live_or_inactive="live", real_directory_or_pointer="real_directory", reparse_type="none",
         cloud_synchronised=False, approved_for_inspection=False, approved_for_modification=False,
         sensitivity_boundary="config",
         source_documents=src("D:\\\\AI-System-Investigation\\\\05-GOOSE-AND-TOOLS-MAP.md"),
         observed_at=INVESTIGATION_DATE, freshness_status="OBSERVED", confidence="HIGH",
         notes="Two Goose installs (Windows app v1.47.0 and WSL CLI /home/michael/.local/bin/goose). CONFLICT: which primary = design decision."),
]

# ---------------------------------------------------------------------------
# 2. PLACEMENT-POLICY REGISTRY
# ---------------------------------------------------------------------------
# fields: policy_id, asset_type, preferred_root, allowed_storage, forbidden_storage,
# git_allowed, encryption_required, retention_class, movement_approval_required,
# policy_status, policy_authority, rationale, source_documents, review_required

placement_records = [
    dict(policy_id="POL-001", asset_type="ai-context build docs (repo)",
         preferred_root="/home/michael/ai-context", allowed_storage="WSL git repo",
         forbidden_storage="household-vault; external secret dirs", git_allowed=True,
         encryption_required=False, retention_class="permanent", movement_approval_required=True,
         policy_status="HARD", policy_authority="AGENT_BOOTSTRAP.md + MASTER_BUILD_PLAN",
         rationale="SINGLE SOURCE OF TRUTH is ~/ai-context git repo, pushed to private GitHub after every session.",
         source_documents=src("ai-context/BACKUP_AI_MASTER_BUILD_PLAN.md","ai-context/AGENT_BOOTSTRAP.md"),
         review_required=False),

    dict(policy_id="POL-002", asset_type="[IDENTITY] household vault",
         preferred_root="/home/michael/household-vault", allowed_storage="encrypted local + 1 offsite encrypted copy",
         forbidden_storage="git; workspace; cloud without encryption", git_allowed=False,
         encryption_required=True, retention_class="permanent_sensitive", movement_approval_required=True,
         policy_status="HARD", policy_authority="MASTER_BUILD_PLAN + AGENT_BOOTSTRAP Credential Rule",
         rationale="[IDENTITY] physically separate, non-repo, never in git, backed up encrypted to a different destination than the repo.",
         source_documents=src("ai-context/BACKUP_AI_MASTER_BUILD_PLAN.md"),
         review_required=False),

    dict(policy_id="POL-003", asset_type="[IDENTITY] household data raw",
         preferred_root="C:\\HouseholdDataRaw (stale snapshot) / D:\\Data (live)",
         allowed_storage="outside workspace - never part of it",
         forbidden_storage="ai-workspace; git", git_allowed=False,
         encryption_required=True, retention_class="permanent_sensitive", movement_approval_required=True,
         policy_status="HARD", policy_authority="ai-workspace SCOPE.md + GOTCHAS",
         rationale="Household data never part of workspace. C: snapshot is stale; D: live. Do not inspect bodies.",
         source_documents=src("ai-workspace/SCOPE.md","ai-context/docs/GOTCHAS.md"),
         review_required=False),

    dict(policy_id="POL-004", asset_type="live-system junction targets (torbox, stash, rdtclient, scanner, watchdog, librechat)",
         preferred_root="resolved real path (e.g. C:\\torbox-system)",
         allowed_storage="in place (real path)",
         forbidden_storage="movement/rename/delete/re-junction", git_allowed=False,
         encryption_required=False, retention_class="live_system", movement_approval_required=True,
         policy_status="HARD", policy_authority="ai-workspace AGENTS.md",
         rationale="Moving breaks Task Scheduler hardcoded paths, docker bind mounts, host.docker.internal refs.",
         source_documents=src("ai-workspace/AGENTS.md","ai-workspace/SCOPE.md"),
         review_required=False),

    dict(policy_id="POL-005", asset_type="classification A (preserve now, non-sensitive)",
         preferred_root="per destination policy", allowed_storage="verified cross-disk archive",
         forbidden_storage="unverified single location", git_allowed=True,
         encryption_required=False, retention_class="preserve", movement_approval_required=True,
         policy_status="APPROVED", policy_authority="Task-02/Task-03 classification",
         rationale="A does NOT auto-authorize movement; separation of classification from action.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-006", asset_type="classification B (preserve securely, sensitive)",
         preferred_root="encrypted archive", allowed_storage="GPG-AES256 encrypted, 0600 perms",
         forbidden_storage="plaintext; git; cloud", git_allowed=False,
         encryption_required=True, retention_class="preserve_sensitive", movement_approval_required=True,
         policy_status="APPROVED", policy_authority="Task-04 recovery + credential rule",
         rationale="B does NOT auto-authorize copying. B-encrypted-only handling. Confirm sensitivity/duplicate before escalating.",
         source_documents=src("D:\\\\AI-System-Preservation\\\\Task-04-Staging\\*-reports","GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-007", asset_type="classification C (reproducible)",
         preferred_root="regenerate from source", allowed_storage="none (do not preserve)",
         forbidden_storage="archive", git_allowed=False,
         encryption_required=False, retention_class="regenerable", movement_approval_required=True,
         policy_status="APPROVED", policy_authority="Task-03 classification",
         rationale="C does NOT authorize deletion.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-008", asset_type="classification D (already preserved elsewhere)",
         preferred_root="existing preserved copy", allowed_storage="none (duplicate marker)",
         forbidden_storage="re-copy", git_allowed=False,
         encryption_required=False, retention_class="duplicate", movement_approval_required=True,
         policy_status="APPROVED", policy_authority="Task-03 child-level inventory",
         rationale="D does not prove the reviewed copy is disposable.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-009", asset_type="classification E (archive for historical reference)",
         preferred_root="historical archive (minor/operational)", allowed_storage="verified archive",
         forbidden_storage="destructive deletes", git_allowed=False,
         encryption_required=False, retention_class="historical", movement_approval_required=True,
         policy_status="APPROVED", policy_authority="Task-03 classification",
         rationale="E does not define the archive destination by itself.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-010", asset_type="classification F (candidate for deletion)",
         preferred_root="UNDEFINED - blocked in v1", allowed_storage="none",
         forbidden_storage="any deletion (v1 read-only)", git_allowed=False,
         encryption_required=False, retention_class="candidate_full", movement_approval_required=True,
         policy_status="PROVISIONAL", policy_authority="classification model only",
         rationale="F means candidate only; deletion is never a v1 action.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-011", asset_type="classification G (unknown, investigate safely)",
         preferred_root="UNDEFINED", allowed_storage="none",
         forbidden_storage="any action", git_allowed=False,
         encryption_required=False, retention_class="blocked_investigate", movement_approval_required=True,
         policy_status="HARD", policy_authority="classification model",
         rationale="G blocks action and requires investigation.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-012", asset_type="Git repository (any item within)",
         preferred_root="in place", allowed_storage="in place",
         forbidden_storage="move/archive/delete recommendation in v1",
         git_allowed=True, encryption_required=False, retention_class="repository",
         movement_approval_required=True, policy_status="HARD",
         policy_authority="GOOSE_TASK section 10.3",
         rationale="Repo or item within must be blocked from move/archive/delete unless repo-aware preservation+ownership established. v1 = report only.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md"),
         review_required=False),

    dict(policy_id="POL-013", asset_type="reparse point (junction/symlink/mount/.path)",
         preferred_root="in place (blocked)", allowed_storage="report only",
         forbidden_storage="traverse", git_allowed=False,
         encryption_required=False, retention_class="blocked", movement_approval_required=True,
         policy_status="HARD", policy_authority="GOOSE_TASK section 10.2 + ai-workspace AGENTS.md",
         rationale="Record, do not traverse, resolve only via safe metadata, block from automatic recommendation.",
         source_documents=src("GOOSE_TASK_COMPUTER_FILE_STEWARD_V1_READONLY.md","ai-workspace/AGENTS.md"),
         review_required=False),

    dict(policy_id="POL-014", asset_type="secret/credential-bearing file (Tier-1)",
         preferred_root="Bitwarden (pointer only)", allowed_storage="pointer to password manager",
         forbidden_storage="value in any file/trace/output", git_allowed=False,
         encryption_required=True, retention_class="Tier1_secret", movement_approval_required=True,
         policy_status="HARD", policy_authority="Credential Rule (AGENT_BOOTSTRAP §4)",
         rationale="Passwords/PINs/MFA seeds/recovery codes/private keys NEVER enter the system. Tier-1 = password manager only; pointer may exist, never value.",
         source_documents=src("ai-context/AGENT_BOOTSTRAP.md","ai-context/BACKUP_AI_MASTER_BUILD_PLAN.md"),
         review_required=False),
]

# ---------------------------------------------------------------------------
# 3. PROTECTION REGISTRY
# ---------------------------------------------------------------------------
# fields: asset_id, asset_name, primary_path, classification, sensitivity,
# unique_or_reproducible, recovery_source, last_verified_recovery,
# recovery_destination_status, checksum_reference, deletion_eligible,
# required_approval_level, protection_reason, source_documents, confidence

protect_records = [
    dict(asset_id="PROT-001", asset_name="RYM Unrated browser extension", primary_path="C:\\Users\\micha\\ai-workspace\\browser-extensions\\rym-unrated-ds-fix",
         classification="A", sensitivity="non-sensitive", unique_or_reproducible="UNIQUE (local-only, no remote)",
         recovery_source="D:\\AI-System-Preservation\\Task-02\\run-20260829-160940\\archives\\rym-unrated-ds-fix-full.tgz + .bundle",
         last_verified_recovery=PRESERVATION_DATE, recovery_destination_status="VERIFIED (D: + E:)",
         checksum_reference="SHA 6A8A5640... (tgz), 7211B002... (bundle); HEAD aab5c31",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="No git remote, local-only, highest preservation priority.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md","D:\\\\AI-System-Preservation\\\\Task-02\\run-20260829-160940\\*"),
         confidence="HIGH"),

    dict(asset_id="PROT-002", asset_name="AI-context (Desktop working copy)", primary_path="C:\\Users\\micha\\Desktop\\New folder\\ai-context",
         classification="A", sensitivity="non-sensitive", unique_or_reproducible="PARTLY (uncommitted work unique)",
         recovery_source="D:\\AI-System-Preservation\\Task-02\\...\\archives\\ai-context-desktop-full.tgz + .bundle",
         last_verified_recovery=PRESERVATION_DATE, recovery_destination_status="VERIFIED (D: + E:)",
         checksum_reference="SHA AA42CBC5... (tgz), AF41AAD... (bundle); HEAD a18cb303",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="17+ uncommitted changes; HIGH local-only risk; ship to GitHub/off-machine.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-003", asset_name="D:\\Data (legacy pipeline repo)", primary_path="D:\\Data",
         classification="A/B (mixed)", sensitivity="mixed", unique_or_reproducible="PARTLY (untracked scripts unique)",
         recovery_source="E:\\AI-System-Preservation\\Task-02-D-Data\\...\\ddata-selective-preserve.tgz + ddata.bundle",
         last_verified_recovery=PRESERVATION_DATE, recovery_destination_status="VERIFIED (E:)",
         checksum_reference="SHA 510F7B01... (tgz), E66B7674... (bundle); HEAD 3d83c76",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="Many untracked scripts + data; HIGH local-only; preserves deleted-file state via bundle.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-004", asset_name="LibreChat conversation data (Mongo)", primary_path="docker volume librechat_librechat_mongo_data",
         classification="B", sensitivity="sensitive", unique_or_reproducible="UNIQUE",
         recovery_source="/home/michael/librechat-backups/*.archive.gz (14 dumps)",
         last_verified_recovery=PRESERVATION_DATE, recovery_destination_status="VERIFIED (D:), no off-site verified",
         checksum_reference="librechat-checksums.csv (per-file SHA)",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="HIGH risk; only local 14-day WSL backups; no verified off-site copy; Mongo durability depends on named volume.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md","D:\\\\AI-System-Investigation\\\\04-LIBRECHAT-MAP.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-005", asset_name="LibreChat config (.env + .env.save)", primary_path="/home/michael/LibreChat/.env",
         classification="B-secret", sensitivity="SECRET (credential-bearing)", unique_or_reproducible="REPRODUCIBLE (recreate + re-key)",
         recovery_source="non-secret config archived (librechat.yaml, .env.example*); secrets NOT copied; recreate from Bitwarden",
         last_verified_recovery=PRESERVATION_DATE, recovery_destination_status="secrets excluded; recreation required",
         checksum_reference="non-secret config 5 files verified",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="Secrets never enter system; .env secret-bearing; recreate manually per Task-04 report 08.",
         source_documents=src("D:\\\\AI-System-Preservation\\Task-04-Staging\\*\\reports\\08-SECRETS-RECREATION-REQUIRED.md","D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-006", asset_name="Claude raw export (conversations.json)", primary_path="/home/michael/agent-workdir/claude-export/conversations.json",
         classification="B", sensitivity="sensitive (raw conversations)", unique_or_reproducible="UNIQUE (raw, irreplaceable)",
         recovery_source="Task-04 B-ENCRYPTED GPG archive",
         last_verified_recovery=RECOVERY_DATE, recovery_destination_status="VERIFIED (E: encrypted); cloud BLOCKED",
         checksum_reference="SHA 33cf13cb... (plaintext), B archive SHA 73c12391...",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="391 convs/7847 msgs; verified identical duplicate exists; raw irreplaceable; B-encrypted only.",
         source_documents=src("D:\\\\AI-System-Investigation\\Task-03-Deferred-Classification\\run-20260829-181433\\04-CLAUDE-EXPORT-COMPONENTS.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-007", asset_name="household-*/cluster6-* agent-workdir working trees", primary_path="/home/michael/agent-workdir/household-*, cluster6-*",
         classification="B", sensitivity="sensitive (household/cluster)", unique_or_reproducible="UNIQUE work",
         recovery_source="Task-04 B-ENCRYPTED GPG archive",
         last_verified_recovery=RECOVERY_DATE, recovery_destination_status="VERIFIED (E: encrypted)",
         checksum_reference="B archive SHA 73c12391...",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="17 household + 9 cluster6 working trees; ~144MB compressed; B-encrypted only.",
         source_documents=src("D:\\\\AI-System-Preservation\\Task-04-Staging\\*\\reports\\03-SENSITIVE-PACKAGE-MANIFEST.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-008", asset_name="D:\\Data\\briefings", primary_path="D:\\Data\\briefings",
         classification="B", sensitivity="sensitive (household synthesis)", unique_or_reproducible="UNIQUE (non-deterministic generation)",
         recovery_source="Task-04 B-ENCRYPTED GPG archive",
         last_verified_recovery=RECOVERY_DATE, recovery_destination_status="VERIFIED (E: encrypted)",
         checksum_reference="B archive SHA 73c12391...",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="49 items; household/personal synthesis; source sensitive; B-encrypted only.",
         source_documents=src("D:\\\\AI-System-Investigation\\Task-03-Deferred-Classification\\run-20260829-181433\\01-ASSET-CLASSIFICATIONS.csv"),
         confidence="HIGH"),

    dict(asset_id="PROT-009", asset_name="diva5-assessment", primary_path="/home/michael/agent-workdir/diva5-assessment",
         classification="B", sensitivity="clinical/health (ADHD/DIVA-5)", unique_or_reproducible="UNIQUE (artificial data only)",
         recovery_source="Task-04 B-ENCRYPTED GPG archive",
         last_verified_recovery=RECOVERY_DATE, recovery_destination_status="VERIFIED (E: encrypted)",
         checksum_reference="B archive SHA 73c12391...",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="Clinical domain, artificial data; B-encrypted only.",
         source_documents=src("D:\\\\AI-System-Investigation\\Task-03-Deferred-Classification\\run-20260829-181433\\01-ASSET-CLASSIFICATIONS.csv"),
         confidence="HIGH"),

    dict(asset_id="PROT-010", asset_name="Deep-research MCP (technical)", primary_path="/home/michael/agent-workdir/deep-research-mcp",
         classification="A", sensitivity="non-sensitive", unique_or_reproducible="UNIQUE tool",
         recovery_source="Task-04 A-deep-research-mcp.tar.gz",
         last_verified_recovery=RECOVERY_DATE, recovery_destination_status="VERIFIED (E:)",
         checksum_reference="SHA 0016dc2b...",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="4 items; credential-bearing .bak excluded.",
         source_documents=src("D:\\\\AI-System-Preservation\\Task-04-Staging\\*\\reports\\04-TECHNICAL-AND-HISTORICAL-MANIFEST.md"),
         confidence="HIGH"),

    dict(asset_id="PROT-011", asset_name="analyze_claude_export.py", primary_path="/home/michael/agent-workdir/claude-export/analyze_claude_export.py",
         classification="A", sensitivity="non-sensitive", unique_or_reproducible="UNIQUE tool",
         recovery_source="Task-04 A-analyze_claude_export.py.tar.gz",
         last_verified_recovery=RECOVERY_DATE, recovery_destination_status="VERIFIED (E:)",
         checksum_reference="SHA 4cbc1ab1...",
         deletion_eligible=False, required_approval_level="human",
         protection_reason="Unique non-sensitive tool.",
         source_documents=src("D:\\\\AI-System-Investigation\\Task-03-Deferred-Classification\\run-20260829-181433\\01-ASSET-CLASSIFICATIONS.csv"),
         confidence="HIGH"),
]

# ---------------------------------------------------------------------------
# 4. PROJECT REGISTRY
# ---------------------------------------------------------------------------
# fields: project_id, project_name, primary_path, repository_path, current_state,
# migration_status, authoritative_records, related_working_trees,
# sensitive_data_locations, temporary_outputs, archive_location,
# immediate_next_action, source_documents, confidence

project_records = [
    dict(project_id="PRJ-001", project_name="Backup AI System build", primary_path="/home/michael/ai-context",
         repository_path="/home/michael/ai-context (git, WSL clean) + C:\\Users\\micha\\Desktop\\New folder\\ai-context (dirty)",
         current_state="Phase 9 cutover IN PROGRESS; 9a/9B PASSED; Household Paperless design IN PROGRESS",
         migration_status="core built; Cluster 6 household DB deferred/unblocked NEXT",
         authoritative_records=src("ai-context/BUILD_STATE.md","ai-context/BACKUP_AI_MASTER_BUILD_PLAN.md"),
         related_working_trees=["/home/michael/agent-workdir","C:\\Users\\micha\\Desktop\\New folder\\ai-context"],
         sensitive_data_locations=["~/.config/goose/secrets.yaml","~/LibreChat/.env","C:\\HouseholdDataRaw"],
         temporary_outputs=["/home/michael/agent-workdir/tasks","/home/michael/agent-workdir/outputs","/home/michael/agent-workdir/staging-ai-context"],
         archive_location="D:\\AI-System-Preservation\\Task-02\\run-20260829-160940 + E: off-machine",
         immediate_next_action="Michael: LIVE Household Admin repoint (T10) gated on sign-off; then Cluster 6 household DB build.",
         source_documents=src("ai-context/BUILD_STATE.md","D:\\\\AI-System-Investigation\\\\02-REPOSITORY-INVENTORY.md"),
         confidence="HIGH"),

    dict(project_id="PRJ-002", project_name="LibreChat (self-hosted chat)", primary_path="/home/michael/LibreChat",
         repository_path="/home/michael/LibreChat (upstream github.com/danny-avila/LibreChat.git, DIRTY)",
         current_state="v0.8.7 live, 6-container stack, frontend :3080, Tailscale remote HTTPS",
         migration_status="production (replacing Claude Pro Desktop); custom code vs config-only NOT established",
         authoritative_records=src("D:\\\\AI-System-Investigation\\\\04-LIBRECHAT-MAP.md","ai-context/BUILD_STATE.md"),
         related_working_trees=["/home/michael/agent-workdir"],
         sensitive_data_locations=["/home/michael/LibreChat/.env","/home/michael/LibreChat/.env.save","librechat_spotify_mcp_credentials volume"],
         temporary_outputs=["/home/michael/agent-workdir"],
         archive_location="D:\\AI-System-Preservation\\Task-02\\...\\librechat\\* + E:",
         immediate_next_action="Confirm Mongo data location (volume vs data-node) before backup/restore design; push/offsite backups.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\04-LIBRECHAT-MAP.md","D:\\\\AI-System-Investigation\\\\08-UNKNOWNS-AND-BLOCKERS.md"),
         confidence="HIGH"),

    dict(project_id="PRJ-003", project_name="RYM Unrated browser extension", primary_path="C:\\Users\\micha\\ai-workspace\\browser-extensions\\rym-unrated-ds-fix",
         repository_path="same (local git, NO remote, branch master, clean)",
         current_state="v2.4.0, 8 commits, clean; NO remote - local-only",
         migration_status="recovered/preserved; no off-machine git remote",
         authoritative_records=src("D:\\\\AI-System-Investigation\\\\06-RYM-RECOVERY-EVIDENCE.md"),
         related_working_trees=["C:\\Users\\micha\\ai-workspace\\browser-extensions\\rym-unrated-aaudit"],
         sensitive_data_locations=["none known"],
         temporary_outputs=["D:\\AI-System-Preservation\\Task-02\\...\\archives\\rym-unrated-ds-fix-full.tgz"],
         archive_location="D:\\AI-System-Preservation\\Task-02\\... + E: off-machine",
         immediate_next_action="HIGH priority: push to GitHub / off-machine; confirm no Chrome loosely-loaded copy; decision on local-only risk.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\06-RYM-RECOVERY-EVIDENCE.md","D:\\\\AI-System-Investigation\\\\07-PRESERVATION-MATRIX.md"),
         confidence="HIGH"),

    dict(project_id="PRJ-004", project_name="D:\\Data legacy pipeline", primary_path="D:\\Data",
         repository_path="D:\\Data (git, github.com/michaelreynolds111-dev/data-archive.git, DIRTY)",
         current_state="live pipeline; many untracked scripts; ~29.3GB",
         migration_status="preserved selective; legacy decommission deferred (Session 10 item 4 retires parts)",
         authoritative_records=src("D:\\\\AI-System-Investigation\\\\02-REPOSITORY-INVENTORY.md","ai-context/docs/GOTCHAS.md"),
         related_working_trees=["C:\\HouseholdDataRaw\\Data (stale snapshot)"],
         sensitive_data_locations=["D:\\Data\\briefings","D:\\Data\\Mail","D:\\Data\\MailSarah","D:\\Data\\Michael","D:\\Data\\Sarah"],
         temporary_outputs=["E:\\AI-System-Preservation\\Task-02-D-Data\\..."],
         archive_location="E:\\AI-System-Preservation\\Task-02-D-Data\\run-20260829-160940",
         immediate_next_action="Dual-drive enumeration before decommissioning (C: snapshot vs D: live); Tier-1 quarantine of .eml parked/P5.",
         source_documents=src("D:\\\\AI-System-Investigation\\\\08-UNKNOWNS-AND-BLOCKERS.md","ai-context/docs/GOTCHAS.md"),
         confidence="HIGH"),

    dict(project_id="PRJ-005", project_name="Household Admin / paperless platform", primary_path="/home/michael/agent-workdir/household-* working trees",
         repository_path="working trees only (not a single repo)",
         current_state="Paperless Hybrid design IN PROGRESS; Cluster 6 household DB build NEXT (unblocked)",
         migration_status="Cluster 6 Step 3 complete: 1935 IDs/27803 rows/1935 files; retrieval verified",
         authoritative_records=src("ai-context/BUILD_STATE.md"),
         related_working_trees=["/home/michael/agent-workdir/household-01-*","cluster6-*"],
         sensitive_data_locations=["C:\\HouseholdDataRaw","/home/michael/household-vault","D:\\Data\\briefings"],
         temporary_outputs=["/home/michael/agent-workdir"],
         archive_location="Task-04 B-ENCRYPTED (household-* + cluster6-*)",
         immediate_next_action="T10 production repoint gated on sign-off; then Cluster 6 household DB agent build.",
         source_documents=src("ai-context/BUILD_STATE.md"),
         confidence="HIGH"),

    dict(project_id="PRJ-006", project_name="Claude Projects migration", primary_path="/home/michael/ai-context/projects",
         repository_path="/home/michael/ai-context (git)",
         current_state="DEFERRED until post-cutover; migration using LibreChat is the proof it replaced Claude Pro",
         migration_status="mostly DEFERRED; New Build (Stash) KNOWLEDGE-ONLY committed bf95d2e; Youth Mental Health Case M high-priority deferred; Chris Bank Accounts STAYING PUT",
         authoritative_records=src("ai-context/docs/MIGRATION_INVENTORY.md"),
         related_working_trees=["D:\\Data\\Michael\\Cherry Studio","/home/michael/agent-workdir"],
         sensitive_data_locations=["Tax Return [SENSITIVE-financial]","Youth Mental Health Case M [SENSITIVE-clinical]","Personal Finances [SENSITIVE]","seddon-source (investigate Chris bank accounts)"],
         temporary_outputs=["/home/michael/agent-workdir"],
         archive_location="Task-04 B-ENCRYPTED for sensitive projects",
         immediate_next_action="After cutover: migrate projects via 6-step process (copy instructions -> locate -> classify -> write INSTRUCTIONS + RAG + agent -> test -> MIGRATED with commit).",
         source_documents=src("ai-context/docs/MIGRATION_INVENTORY.md"),
         confidence="HIGH"),
]

# ---------------------------------------------------------------------------
# Output writer (idempotent)
# ---------------------------------------------------------------------------
def write_registry(outdir, filename, records, registry_name, schema_fields):
    path = os.path.join(outdir, filename)
    payload = {
        "registry": registry_name,
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "idempotent": True,
        "conflicts_visible": True,
        "no_secret_values": True,
        "fields": schema_fields,
        "record_count": len(records),
        "records": records,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path

def main():
    ap = argparse.ArgumentParser(description="Bootstrap Computer File Steward v1 registries (idempotent, secret-free)")
    ap.add_argument("--out", required=True, help="Output directory for the four registry JSON files")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    written = []
    written.append(write_registry(args.out, "location_registry.json", location_records,
        "LOCATION_REGISTRY",
        ["record_id","canonical_path","path_style","physical_disk","filesystem_type","owner_project",
         "role","live_or_inactive","real_directory_or_pointer","reparse_type","cloud_synchronised",
         "approved_for_inspection","approved_for_modification","sensitivity_boundary",
         "source_documents","observed_at","freshness_status","confidence","notes"]))
    written.append(write_registry(args.out, "placement_policy_registry.json", placement_records,
        "PLACEMENT_POLICY_REGISTRY",
        ["policy_id","asset_type","preferred_root","allowed_storage","forbidden_storage","git_allowed",
         "encryption_required","retention_class","movement_approval_required","policy_status",
         "policy_authority","rationale","source_documents","review_required"]))
    written.append(write_registry(args.out, "protection_registry.json", protect_records,
        "PROTECTION_REGISTRY",
        ["asset_id","asset_name","primary_path","classification","sensitivity","unique_or_reproducible",
         "recovery_source","last_verified_recovery","recovery_destination_status","checksum_reference",
         "deletion_eligible","required_approval_level","protection_reason","source_documents","confidence"]))
    written.append(write_registry(args.out, "project_registry.json", project_records,
        "PROJECT_REGISTRY",
        ["project_id","project_name","primary_path","repository_path","current_state","migration_status",
         "authoritative_records","related_working_trees","sensitive_data_locations","temporary_outputs",
         "archive_location","immediate_next_action","source_documents","confidence"]))

    print("Registries written (idempotent):")
    for p in written:
        print(f"  {p}")

    # Conflict listing (declarative) — kept visible, not resolved silently
    conflicts = [
        {"conflict_id":"CFL-001","topic":"ai-context authoritative checkout","records":["LOC-016","LOC-017"],
         "facts":"WSL copy clean (LOC-016); Desktop copy dirty/uncommitted (LOC-017)","status":"UNRESOLVED",
         "action_required":"MICHAEL decision; do not overwrite either"},
        {"conflict_id":"CFL-002","topic":"Mongo data location","records":["LOC-019","PROT-004"],
         "facts":"volume librechat_librechat_mongo_data vs /home/michael/LibreChat/data-node/","status":"UNRESOLVED",
         "action_required":"confirm which chat-mongodb reads live before backup/restore design"},
        {"conflict_id":"CFL-003","topic":"Goose primary install","records":["LOC-023","LOC-025"],
         "facts":"Windows app v1.47.0 vs WSL CLI v1.47.0","status":"UNRESOLVED",
         "action_required":"design decision"},
    ]
    conf_path = os.path.join(args.out, "conflicts.json")
    with open(conf_path, "w", encoding="utf-8") as f:
        json.dump({"declared_conflicts": conflicts, "note":"Conflicts are declared, not silently resolved."}, f, indent=2)
    print(f"  {conf_path}")
    print("Declared conflicts:", len(conflicts))

if __name__ == "__main__":
    main()
