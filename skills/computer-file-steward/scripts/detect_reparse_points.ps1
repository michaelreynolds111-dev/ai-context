<#
.SYNOPSIS
  detect_reparse_points.ps1 — Detect reparse points (junctions, symlinks, mount
  points, other reparse tags), .path pointer files, and Git boundaries under a
  target, WITHOUT traversing them.

.DESCRIPTION
  Read-only. Walks the target directory tree but never descends into a reparse
  point. Records each reparse point and its resolved target via safe metadata
  only. Also flags the presence of a Git repository boundary.

.PARAMETER Target
  REQUIRED. The explicit directory to inspect. Must be provided; never defaults.

.PARAMETER ResultFile
  Path to write the reparse-point report (JSON).

.EXAMPLE
  pwsh -NoProfile -ExecutionPolicy Bypass -File detect_reparse_points.ps1 `
       -Target "\\wsl.localhost\...\fixture-root" -ResultFile reparse.json
#>
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [string]$ResultFile
)

$ErrorActionPreference = 'Continue'   # never abort the whole walk on one item

if (-not $Target) {
    Write-Error "EXPLICIT TARGET REQUIRED — detect_reparse_points.ps1 refuses to run without an explicit directory."
    exit 2
}
if (-not (Test-Path -LiteralPath $Target -PathType Container)) {
    Write-Error "Target directory not found: $Target"
    exit 3
}

$results = New-Object System.Collections.Generic.List[object]
$deferredDirs = New-Object System.Collections.Generic.Queue[string]  # BFS, deterministic

# Seed with the target itself as a directory record
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
            # Try to resolve target via metadata only (no content read)
            try {
                $item = Get-Item -LiteralPath $child.FullName -Force -ErrorAction Stop
                if ($item.Target) { $resolved = $item.Target.FullName }
            } catch { $resolved = '<unresolvable-without-traversal>' }
        }

        if ($child.PSIsContainer) {
            $results.Add([pscustomobject]@{
                Path = $child.FullName; ItemType = 'directory'; SubType = 'dir'
                ReparseTag = $tag; ResolvedTarget = $resolved
                IsReparse = $isReparse; IsBlocked = $isReparse
                Reason = if ($isReparse) { 'reparse point - not traversed' } else { '' }
            })
            if (-not $isReparse) { $deferredDirs.Enqueue($child.FullName) }
        } else {
            $results.Add([pscustomobject]@{
                Path = $child.FullName; ItemType = 'file'; SubType = 'file'
                ReparseTag = $tag; ResolvedTarget = $resolved
                IsReparse = $isReparse; IsBlocked = $isReparse
                Reason = if ($isReparse) { 'reparse point file' } else { '' }
            })
        }
    }
}

# .path pointer files
$pointerFiles = @()
try {
    $pointerFiles = @(Get-ChildItem -LiteralPath $Target -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like '*.path' -or $_.Name -match '^.*\.path$' })
} catch { $pointerFiles = @() }

# Git boundaries (directory containing .git), not following reparse points
$gitRoots = New-Object System.Collections.Generic.List[string]
$queue2 = New-Object System.Collections.Generic.Queue[string]
$queue2.Enqueue($Target)
$g = 0
while ($queue2.Count -gt 0 -and $g -lt 100000) {
    $g++
    $d = $queue2.Dequeue()
    if (-not $d) { continue }
    if (Test-Path -LiteralPath (Join-Path $d '.git') -ErrorAction SilentlyContinue) {
        $gitRoots.Add($d)
        continue
    }
    foreach ($sub in @(Get-ChildItem -LiteralPath $d -Directory -Force -ErrorAction SilentlyContinue)) {
        if (-not $sub) { continue }
        $sa = ''
        try { $sa = (Get-Item -LiteralPath $sub.FullName -Force -ErrorAction SilentlyContinue).Attributes.ToString() }
        catch { $sa = '' }
        if ($sa -notmatch 'ReparsePoint') { $queue2.Enqueue($sub.FullName) }
    }
}

$output = @{
    target = $Target
    mode = 'READ_ONLY'
    reparse_points = $results
    pointer_files = @($pointerFiles | ForEach-Object { $_.FullName })
    git_boundaries = @($gitRoots)
    summary = @{
        reparse_point_count = @($results | Where-Object { $_.IsReparse }).Count
        pointer_file_count = @($pointerFiles).Count
        git_boundary_count = @($gitRoots).Count
    }
}

if ($ResultFile) {
    $output | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ResultFile -Encoding UTF8
    Write-Output "Reparse-point report written to $ResultFile"
} else {
    $output | ConvertTo-Json -Depth 12
}
