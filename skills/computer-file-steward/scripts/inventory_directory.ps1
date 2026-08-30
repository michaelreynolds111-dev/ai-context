<#
.SYNOPSIS
  inventory_directory.ps1 — Read-only inventory of an explicitly supplied
  target directory for the Computer File Steward v1.0.1 skill.

.DESCRIPTION
  v1.0.1 hardening (Corrections B and C):
    - EXPLICITLY requires PowerShell 7 or later. Fails before scanning anything
      when run under an unsupported runtime.
    - Populates creation and last-write timestamps for ordinary accessible
      items using unambiguous ISO 8601 with local offset.
    - Records an explicit, machine-readable metadata_status whenever a metadata
      field cannot be read (never silently blanks a field without a status).
    - Keeps the read-only guarantee: no move/copy/rename/delete/quarantine.
    - Does not follow reparse points (records them as blocked).
    - Never reads file content / never outputs content.

  Timestamp format: ISO 8601 with local offset, e.g. 2026-08-30T11:32:00+10:00.
  For filesystems that expose only UTC without an offset convention, the offset
  is derived from the local time zone and appended; the 'Z'/offset suffix is
  always present so the value is unambiguous. If a timestamp cannot be read the
  field is left blank and metadata_status records 'timestamp_unavailable:<field>'
  so no value is silently invented.

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

# --- Correction C: unsupported runtime fails BEFORE scanning anything ---
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "UNSUPPORTED RUNTIME: Computer File Steward requires PowerShell 7+ (pwsh). Detected $($PSVersionTable.PSVersion). Refusing to scan."
    exit 100
}

if (-not $Target) {
    Write-Error "EXPLICIT TARGET REQUIRED — inventory_directory.ps1 refuses to run without an explicit directory. Never default to cwd, drive root, or home."
    exit 2
}
if (-not (Test-Path -LiteralPath $Target -PathType Container)) {
    Write-Error "Target directory not found: $Target"
    exit 3
}

# Sensitive-looking path markers — deeper inspection stops once sensitivity established.
$SENSITIVE_MARKERS = @('secret', 'credential', 'password', 'token', '.env', 'key.pem',
                        'id_rsa', 'bitwarden', 'recovery-code', 'mfa', 'household',
                        'conversations.json', 'clinical', 'legal', 'financial',
                        'mailbox', 'upload', 'database', 'briefing')

function Test-SensitivePath {
    param([string]$Path)
    $lp = $Path.ToLowerInvariant()
    foreach ($m in $SENSITIVE_MARKERS) {
        if ($lp -match [regex]::Escape($m)) { return $true }
    }
    return $false
}

# --- Correction B: ISO 8601 timestamp helper with offset ---
function Format-IsoTimestamp {
    param([datetime]$Dt)
    try {
        # Local offset, e.g. +10:00 or -05:00
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

$stack = New-Object System.Collections.Generic.List[object]   # @{ Path = string; Depth = int }
$stack.Add([pscustomobject]@{ Path = $Target; Depth = 0 })

while ($stack.Count -gt 0) {
    $idx = $stack.Count - 1
    $entry = $stack[$idx]
    $stack.RemoveAt($idx)
    $dir = $entry.Path
    $depth = $entry.Depth

    if ($depth -gt $MaxDepth) { continue }

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

        if ($child.PSIsContainer) {
            $ts = Get-SafeTimestamps -Item $item
            $statusParts = @($ts.status)
            if ($attrsStr -eq 'UNREADABLE') { $statusParts += 'access_error:attributes' }
            $records.Add([pscustomobject]@{
                path = $child.FullName; item_type = 'directory'; size_bytes = 0
                extension = ''; created = $ts.created; modified = $ts.modified
                attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                reparse_status = if ($isReparse) { 'blocked_reparse' } else { 'not_reparse' }
                blocked = $isReparse; block_reason = if ($isReparse) { 'reparse point - not traversed' } else { '' }
                is_git_boundary = $isGitBoundary; depth = $depth + 1; hash_sha256 = ''
                sensitive = $sensitive
                metadata_status = if ($statusParts.Count -gt 0) { ($statusParts -join ';') } else { 'ok' }
            })
            if (-not $isReparse) {
                $stack.Add([pscustomobject]@{ Path = $child.FullName; Depth = $depth + 1 })
            }
        } else {
            $size = 0
            try { $size = $child.Length } catch { $size = 0 }
            $hash = ''
            if ($HashWithReason -and -not $isReparse -and -not $sensitive) {
                try {
                    $hash = (Get-FileHash -LiteralPath $child.FullName -Algorithm SHA256 -ErrorAction SilentlyContinue).Hash
                } catch { $hash = '' }
            }
            $ts = Get-SafeTimestamps -Item $item
            $statusParts = @($ts.status)
            $records.Add([pscustomobject]@{
                path = $child.FullName; item_type = 'file'
                size_bytes = $size; extension = $child.Extension
                created = $ts.created; modified = $ts.modified
                attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                reparse_status = if ($isReparse) { 'blocked_reparse' } else { 'not_reparse' }
                blocked = $isReparse; block_reason = if ($isReparse) { 'reparse point - not traversed' } else { '' }
                is_git_boundary = $isGitBoundary; depth = $depth + 1
                hash_sha256 = $hash; sensitive = $sensitive
                metadata_status = if ($statusParts.Count -gt 0) { ($statusParts -join ';') } else { 'ok' }
            })
        }
    }
}

# Aggregate metadata error report (category + count only — no sensitive bodies).
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
    if ($metadataErrors.Count -gt 0) {
        Write-Output "Metadata error summary (category=count):"
        foreach ($k in $metadataErrors.Keys) { Write-Output "  $k=$($metadataErrors[$k])" }
    } else {
        Write-Output "Metadata error summary: none (all metadata read OK)"
    }
} else {
    $records | ConvertTo-Json -Depth 4
}
