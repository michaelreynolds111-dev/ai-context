<#
.SYNOPSIS
  detect_reparse_points.ps1 — Detect reparse points (junctions, symlinks, mount
  points, other reparse tags), .path pointer files, and Git boundaries under a
  target, WITHOUT traversing any of them.

.DESCRIPTION
  Read-only. Walks the target directory tree with ONE guarded explicit stack
  walk (never -Recurse) and never descends into a reparse point, a sensitive/
  protected boundary, or a Git repository child. Records each reparse point and
  its resolved target via safe metadata only; records .path pointer files during
  the same guarded walk; flags Git repository boundaries.

  v1.0.2 (Fix A): removes the unguarded Get-ChildItem -Recurse pointer discovery.
  .path pointer files are detected during the guarded stack walk, so nothing
  behind a reparse/sensitive boundary can be discovered. An explicit target whose
  root is a reparse point or a .path pointer file is REJECTED before enumeration.
  v1.0.2 (Fix B): directories matching a sensitive/protected boundary marker are
  recorded with metadata only, marked blocked, and never enqueued; their children
  are never inspected for Git boundaries, pointers, hashes, or content.

  v1.0.1 (Correction C): explicitly requires PowerShell 7+ (pwsh). Fails before
  scanning under an unsupported runtime.

.PARAMETER Target
  REQUIRED. The explicit directory to inspect. Must be provided; never defaults.

.PARAMETER ResultFile
  Path to write the reparse-point report (JSON).

.EXAMPLE
  pwsh -NoProfile -ExecutionPolicy Bypass -File detect_reparse_points.ps1 `
       -Target "\\wsl.localhost\...\fixture-root" -ResultFile reparse.json
#>
#Requires -Version 7.0
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [string]$ResultFile
)

$ErrorActionPreference = 'Continue'   # never abort the whole walk on one item

if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "UNSUPPORTED RUNTIME: Computer File Steward requires PowerShell 7+ (pwsh). Detected $($PSVersionTable.PSVersion). Refusing to scan."
    exit 100
}

if (-not $Target) {
    Write-Error "EXPLICIT TARGET REQUIRED - detect_reparse_points.ps1 refuses to run without an explicit directory."
    exit 2
}
if (-not (Test-Path -LiteralPath $Target)) {
    Write-Error "Target directory not found: $Target"
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

$results = New-Object System.Collections.Generic.List[object]
$pointerFiles = New-Object System.Collections.Generic.List[string]
$gitRoots = New-Object System.Collections.Generic.List[string]
$blockedBoundaries = New-Object System.Collections.Generic.List[string]

# Seed with the target itself as a directory record; the target root is already
# proven to be a normal directory (reparse/pointer rejected above).
$deferredDirs = New-Object System.Collections.Generic.Queue[string]  # BFS, deterministic
$results.Add([pscustomobject]@{
    Path = $Target; ItemType = 'directory'; SubType = 'root'; ReparseTag = 'NONE'
    ResolvedTarget = $null; IsReparse = $false; IsBlocked = $false; Reason = ''
})
$deferredDirs.Enqueue($Target)

$guard = 0
while ($deferredDirs.Count -gt 0 -and $guard -lt 100000) {
    $guard++
    $dir = $deferredDirs.Dequeue()
    if (-not $dir) { continue }
    $children = @(Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue)
    $children = @($children | Sort-Object -Property @{Expression={$_.Name}}, @{Expression={$_.PSIsContainer}})

    foreach ($child in $children) {
        if (-not $child) { continue }
        $isReparse = $false
        $tag = 'NONE'
        $resolved = $null

        $attrs = ''
        try { $attrs = (Get-Item -LiteralPath $child.FullName -Force -ErrorAction SilentlyContinue).Attributes.ToString() }
        catch { $attrs = 'UNKNOWN' }
        if ($attrs -match 'ReparsePoint') {
            $isReparse = $true
            $tag = 'REPARSE'
            # Try to resolve target via metadata only (no content read, no traversal)
            try {
                $item = Get-Item -LiteralPath $child.FullName -Force -ErrorAction Stop
                if ($item.Target) { $resolved = $item.Target.FullName }
            } catch { $resolved = '<unresolvable-without-traversal>' }
        }

        $sensitive = Test-SensitivePath -Path $child.FullName
        $protectedBoundary = Test-ProtectedBoundary -Path $child.FullName
        $isPointerFile = ($child.Name -match '\.path$')

        if ($child.PSIsContainer) {
            $isBoundary = ($isReparse -or $sensitive -or $protectedBoundary)
            $reason = ''
            if ($isReparse) { $reason = 'reparse point - not traversed' }
            elseif ($sensitive) { $reason = 'sensitive boundary - not traversed' }
            elseif ($protectedBoundary) { $reason = 'protected boundary - not traversed' }
            $results.Add([pscustomobject]@{
                Path = $child.FullName; ItemType = 'directory'; SubType = 'dir'
                ReparseTag = $tag; ResolvedTarget = $resolved
                IsReparse = $isReparse; IsBlocked = $isBoundary; Reason = $reason
            })
            # Fix A/B: never enqueue a reparse, sensitive, or protected boundary,
            # and never descend into Git internal metadata (.git).
            $isGitInternal = ($child.Name -eq '.git')
            if (-not $isBoundary -and -not $isGitInternal) {
                # If this directory is a repo root (contains .git), record it as a
                # Git boundary and still enqueue it for reparse/pointer discovery in
                # its WORKING TREE. .git internals themselves are never descended into.
                if (Test-Path -LiteralPath (Join-Path $child.FullName '.git') -ErrorAction SilentlyContinue) {
                    $gitRoots.Add($child.FullName)
                }
                $deferredDirs.Enqueue($child.FullName)
            } elseif ($isBoundary) {
                $blockedBoundaries.Add($child.FullName)
            }
        } else {
            # Fix A: .path pointer files are detected during the SAME guarded walk.
            if ($isPointerFile) {
                $pointerFiles.Add($child.FullName)
                $results.Add([pscustomobject]@{
                    Path = $child.FullName; ItemType = 'file'; SubType = 'pointer'
                    ReparseTag = $tag; ResolvedTarget = $resolved
                    IsReparse = $isReparse; IsBlocked = $true; Reason = 'path pointer file - never opened'
                })
            } else {
                $results.Add([pscustomobject]@{
                    Path = $child.FullName; ItemType = 'file'; SubType = 'file'
                    ReparseTag = $tag; ResolvedTarget = $resolved
                    IsReparse = $isReparse; IsBlocked = ($isReparse -or $sensitive)
                    Reason = if ($isReparse) { 'reparse point file' } elseif ($sensitive) { 'sensitive file - not opened' } else { '' }
                })
            }
        }
    }
}

$output = @{
    target = $Target
    mode = 'READ_ONLY'
    reparse_points = $results
    pointer_files = @($pointerFiles)
    git_boundaries = @($gitRoots)
    blocked_boundaries = @($blockedBoundaries)
    summary = @{
        reparse_point_count = @($results | Where-Object { $_.IsReparse }).Count
        pointer_file_count = @($pointerFiles).Count
        git_boundary_count = @($gitRoots).Count
        blocked_boundary_count = @($blockedBoundaries).Count
    }
}

if ($ResultFile) {
    $output | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ResultFile -Encoding UTF8
    Write-Output "Reparse-point report written to $ResultFile"
} else {
    $output | ConvertTo-Json -Depth 12
}
