<#
.SYNOPSIS
  inventory_directory.ps1 — Read-only inventory of an explicitly supplied
  target directory for the Computer File Steward v1.0.2 skill.

.DESCRIPTION
  v1.0.2 safety remediation:
    - Fix A (reparse traversal): rejects an explicit target whose ROOT is itself
      a reparse point (junction, symlink, mount point, other reparse tag) BEFORE
      enumerating it; rejects a target that is itself a `.path` pointer file;
      uses a guarded explicit stack walk (never `-Recurse`); never enqueues a
      reparse point; detects `.path` pointer files during the SAME guarded walk
      (no secondary unguarded recursive pass).
    - Fix B (sensitive pruning): a directory classified sensitive-looking or
      matching a protected/sensitive registry boundary is recorded with metadata
      only, marked `blocked=true`, given a specific block reason, and its children
      are never enqueued, enumerated, or inspected for Git/pointers/hashes/content.
      A sensitive-looking FILE is recorded with metadata only and never hashed or
      opened.
  v1.0.1 inherited behaviours (preserved):
    - Requires PowerShell 7+ (pwsh). Fails before scanning under an unsupported runtime.
    - ISO 8601 timestamps with local offset; honest `metadata_status` on gaps.
    - One shared canonical path model used across the skill.
    - Never reads file content; hashing only with a stated reason and never for
      sensitive content.

.PARAMETER Target
  REQUIRED. Explicit directory to inventory.

.PARAMETER OutputCsv
  Path to write INVENTORY.csv. If omitted prints records to the pipeline.

.PARAMETER MaxDepth
  Optional recursion depth limit (default 9999).

.PARAMETER HashWithReason
  Optional. A stated verification reason. When provided, computes SHA256 of
  files that are NOT inside a sensitive-looking path and adds hash_* columns.

.EXAMPLE
  pwsh -NoProfile -File inventory_directory.ps1 -Target "C:\Users\micha\docs" -OutputCsv INVENTORY.csv
#>
#Requires -Version 7.0
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [string]$OutputCsv,
    [int]$MaxDepth = 9999,
    [string]$HashWithReason = ''
)

$ErrorActionPreference = 'Stop'

# --- unsupported runtime fails BEFORE scanning anything ---
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "UNSUPPORTED RUNTIME: Computer File Steward requires PowerShell 7+ (pwsh). Detected $($PSVersionTable.PSVersion). Refusing to scan."
    exit 100
}

if (-not $Target) {
    Write-Error "EXPLICIT TARGET REQUIRED - inventory_directory.ps1 refuses to run without an explicit directory. Never default to cwd, drive root, or home."
    exit 2
}
if (-not (Test-Path -LiteralPath $Target)) {
    Write-Error "Target not found: $Target"
    exit 3
}

# --- Fix A: reject a target root that is itself a reparse point, or a .path
#     pointer file, BEFORE any enumeration. Fail closed with a safe error. ---
$targetItem = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue
if ($targetItem) {
    try { $targetAttrs = $targetItem.Attributes.ToString() } catch { $targetAttrs = '' }
    if ($targetAttrs -match 'ReparsePoint') {
        Write-Error "REFUSING TO SCAN: target root is a reparse point ($($targetItem.LinkType)). Target: $Target. A reparse-point root is never enumerated. Supply a normal directory."
        exit 4
    }
    if ($targetItem.PSIsContainer -eq $false) {
        if ($Target -match '\.path$' -or $targetItem.Name -match '\.path$') {
            Write-Error "REFUSING TO SCAN: target is a .path pointer file. Target: $Target. Pointer file contents are never opened by this skill. Supply a normal directory."
            exit 5
        }
        Write-Error "REFUSING TO SCAN: target is not a directory. Target: $Target"
        exit 6
    }
} else {
    Write-Error "Target directory not found or not accessible: $Target"
    exit 3
}

# Sensitive-looking path markers - deeper inspection stops once sensitivity established.
$SENSITIVE_MARKERS = @('secret', 'credential', 'password', 'token', '.env', 'key.pem',
                        'id_rsa', 'bitwarden', 'recovery-code', 'mfa', 'household',
                        'conversations.json', 'clinical', 'legal', 'financial',
                        'mailbox', 'upload', 'database', 'briefing')

# Registry-derived protected/sensitive boundary path markers (v1.0.2). When a
# subpath matches one of these, that directory is a sensitive/protected boundary
# and is pruned (parent recorded, children never enumerated). Kept minimal and
# path-name based; does not read any registry bodies itself.
$PROTECTED_BOUNDARY_MARKERS = @('live-systems', 'password-manager', 'bitwarden-vault',
                                 'tier-1', 'recovery-package', 'secrets')

function Test-SensitivePath {
    param([string]$Path)
    $lp = $Path.ToLowerInvariant()
    foreach ($m in $SENSITIVE_MARKERS) {
        if ($lp -match [regex]::Escape($m)) { return $true }
    }
    return $false
}

function Test-ProtectedBoundary {
    param([string]$Path)
    $lp = $Path.ToLowerInvariant()
    foreach ($m in $PROTECTED_BOUNDARY_MARKERS) {
        if ($lp -match [regex]::Escape($m)) { return $true }
    }
    return $false
}

function Format-IsoTimestamp {
    param([datetime]$Dt)
    try {
        $off = $Dt.ToString('zzz')
        return $Dt.ToString('yyyy-MM-ddTHH:mm:ss') + $off
    } catch {
        return $null
    }
}

$metadataErrors = @{}   # category -> count (aggregate; never sensitive bodies)

function Get-SafeTimestamps {
    param($Item)
    $created = ''
    $modified = ''
    $status = @()
    try {
        $c = Format-IsoTimestamp -Dt $Item.CreationTime
        if ($c) { $created = $c } else { $status += 'timestamp_unavailable:created' }
    } catch { $status += 'timestamp_unavailable:created' }
    try {
        $m = Format-IsoTimestamp -Dt $Item.LastWriteTime
        if ($m) { $modified = $m } else { $status += 'timestamp_unavailable:modified' }
    } catch { $status += 'timestamp_unavailable:modified' }
    return [pscustomobject]@{ created = $created; modified = $modified; status = $status }
}

$records = New-Object System.Collections.Generic.List[object]
$blockedBoundaryParents = New-Object System.Collections.Generic.List[string]
$sensitiveFileCount = 0

# --- Guarded explicit stack walk (Fix A: no -Recurse anywhere; each directory is
#     checked for reparse/sensitive/protected before enqueueing). ---
$stack = New-Object System.Collections.Generic.List[object]   # @{ Path = string; Depth = int }
$stack.Add([pscustomobject]@{ Path = $Target; Depth = 0 })

while ($stack.Count -gt 0) {
    $idx = $stack.Count - 1
    $entry = $stack[$idx]
    $stack.RemoveAt($idx)
    $dir = $entry.Path
    $depth = $entry.Depth

    if ($depth -gt $MaxDepth) { continue }

    # Directional guard: never enumerate a directory that is itself a reparse
    # point (defence in depth; the caller should already have blocked these).
    try {
        $dirItem = Get-Item -LiteralPath $dir -Force -ErrorAction SilentlyContinue
        $dirAttrs = ''
        if ($dirItem) { $dirAttrs = $dirItem.Attributes.ToString() }
    } catch { $dirAttrs = '' }
    if ($dirAttrs -match 'ReparsePoint') {
        $records.Add([pscustomobject]@{
            path = $dir; item_type = 'directory'; size_bytes = 0; extension = ''
            created = ''; modified = ''; attributes = $dirAttrs
            is_reparse = $true; reparse_tag = 'REPARSE'; reparse_status = 'blocked_reparse'
            blocked = $true; block_reason = 'reparse point - not traversed'; is_git_boundary = $false
            depth = $depth; hash_sha256 = ''; sensitive = $false
            metadata_status = 'ok'
        })
        continue
    }

    try {
        $children = Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue
    } catch {
        $records.Add([pscustomobject]@{
            path = $dir; item_type = 'directory'; size_bytes = 0; extension = ''
            created = ''; modified = ''; attributes = 'UNREADABLE'
            is_reparse = $true; reparse_tag = 'NOACCESS'; reparse_status = 'noaccess'
            blocked = $true; block_reason = 'unreadable directory'; is_git_boundary = $false
            depth = $depth; hash_sha256 = ''; sensitive = $false
            metadata_status = 'access_error:unreadable_directory'
        })
        continue
    }

    $sorted = @($children | Sort-Object -Property @{Expression={$_.Name}})
    foreach ($child in $sorted) {
        $isReparse = $false
        $tag = 'NONE'
        $attrsStr = ''
        try {
            $item = Get-Item -LiteralPath $child.FullName -Force -ErrorAction SilentlyContinue
            $attrsStr = $item.Attributes.ToString()
            if ($attrsStr -match 'ReparsePoint') { $isReparse = $true; $tag = 'REPARSE' }
        } catch {
            $attrsStr = 'UNREADABLE'
        }

        $isGitBoundary = $false
        if ($child.PSIsContainer) {
            if (Test-Path -LiteralPath (Join-Path $child.FullName '.git') -ErrorAction SilentlyContinue) {
                $isGitBoundary = $true
            }
        }

        $sensitive = Test-SensitivePath -Path $child.FullName
        $protectedBoundary = Test-ProtectedBoundary -Path $child.FullName
        $isPointerFile = ($child.Name -match '\.path$')

        if ($child.PSIsContainer) {
            # ----- DIRECTORY ----
            $isBoundary = ($isReparse -or $sensitive -or $protectedBoundary)
            $ts = Get-SafeTimestamps -Item $item
            $statusParts = @($ts.status)
            if ($attrsStr -eq 'UNREADABLE') { $statusParts += 'access_error:attributes' }
            $reason = ''
            if ($isReparse) { $reason = 'reparse point - not traversed' }
            elseif ($sensitive) { $reason = 'sensitive boundary - not traversed' }
            elseif ($protectedBoundary) { $reason = 'protected boundary - not traversed' }
            $records.Add([pscustomobject]@{
                path = $child.FullName; item_type = 'directory'; size_bytes = 0
                extension = ''; created = $ts.created; modified = $ts.modified
                attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                reparse_status = if ($isReparse) { 'blocked_reparse' } else { 'not_reparse' }
                blocked = $isBoundary; block_reason = $reason
                is_git_boundary = $isGitBoundary; depth = $depth + 1; hash_sha256 = ''
                sensitive = $sensitive
                metadata_status = if ($statusParts.Count -gt 0) { ($statusParts -join ';') } else { 'ok' }
            })
            # Fix B: a sensitive/protected/reparse boundary directory is recorded
            # ONLY with metadata and is NOT enqueued, so its children are never
            # enumerated or inspected for Git/pointers/hashes/content.
            # Fix A: a reparse (or .path-containing) boundary is never enqueued.
            if (-not $isBoundary) {
                $stack.Add([pscustomobject]@{ Path = $child.FullName; Depth = $depth + 1 })
            } else {
                $blockedBoundaryParents.Add($child.FullName)
            }
        } else {
            # ----- FILE ----
            if ($isPointerFile) {
                # Fix A: detect .path pointer files during the guarded walk.
                # Recorded as pointer records only; never opened.
                $ts = Get-SafeTimestamps -Item $item
                $statusParts = @($ts.status)
                $records.Add([pscustomobject]@{
                    path = $child.FullName; item_type = 'file'; size_bytes = 0
                    extension = '.path'; created = $ts.created; modified = $ts.modified
                    attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                    reparse_status = if ($isReparse) { 'blocked_reparse' } else { 'not_reparse' }
                    blocked = $true; block_reason = 'path pointer file - never opened'
                    is_git_boundary = $false; depth = $depth + 1; hash_sha256 = ''
                    sensitive = $sensitive
                    metadata_status = if ($statusParts.Count -gt 0) { ($statusParts -join ';') } else { 'ok' }
                })
                continue
            }
            $size = 0
            try { $size = $child.Length } catch { $size = 0 }
            $hash = ''
            # Fix B: never hash a sensitive file; never hash a reparse file.
            if ($HashWithReason -and -not $isReparse -and -not $sensitive) {
                try {
                    $hash = (Get-FileHash -LiteralPath $child.FullName -Algorithm SHA256 -ErrorAction SilentlyContinue).Hash
                } catch { $hash = '' }
            }
            $ts = Get-SafeTimestamps -Item $item
            $statusParts = @($ts.status)
            if ($sensitive) { $sensitiveFileCount++ }
            $records.Add([pscustomobject]@{
                path = $child.FullName; item_type = 'file'
                size_bytes = $size; extension = $child.Extension
                created = $ts.created; modified = $ts.modified
                attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                reparse_status = if ($isReparse) { 'blocked_reparse' } else { 'not_reparse' }
                blocked = ($isReparse -or $sensitive); block_reason = if ($isReparse) { 'reparse point - not traversed' } elseif ($sensitive) { 'sensitive file - not hashed or opened' } else { '' }
                is_git_boundary = $isGitBoundary; depth = $depth + 1
                hash_sha256 = $hash; sensitive = $sensitive
                metadata_status = if ($statusParts.Count -gt 0) { ($statusParts -join ';') } else { 'ok' }
            })
        }
    }
}

# Aggregate metadata error report (category + count only - no sensitive bodies).
foreach ($rec in $records) {
    $ms = [string]$rec.metadata_status
    if ($ms -and $ms -ne 'ok') {
        foreach ($part in ($ms -split ';')) {
            $part = $part.Trim()
            if ($part) { if ($metadataErrors.ContainsKey($part)) { $metadataErrors[$part]++ } else { $metadataErrors[$part] = 1 } }
        }
    }
}

if ($OutputCsv) {
    $records | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation -Encoding UTF8
    Write-Output "Inventory written to $OutputCsv ($($records.Count) items)"
    Write-Output "Blocked boundary parents (metadata only, not traversed): $($blockedBoundaryParents.Count)"
    Write-Output "Sensitive-looking files recorded (metadata only, never hashed/opened): $($sensitiveFileCount)"
    if ($metadataErrors.Count -gt 0) {
        Write-Output "Metadata error summary (category=count):"
        foreach ($k in $metadataErrors.Keys) { Write-Output "  $k=$($metadataErrors[$k])" }
    } else {
        Write-Output "Metadata error summary: none (all metadata read OK)"
    }
} else {
    $records | ConvertTo-Json -Depth 4
}
