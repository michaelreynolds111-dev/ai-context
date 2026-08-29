<#
.SYNOPSIS
  inventory_directory.ps1 — Read-only inventory of an explicitly supplied
  target directory for the Computer File Steward v1 skill.

.DESCRIPTION
  This is the v1 review engine inventory step. It:
    - REQUIRES an explicit target directory (never defaults to cwd/root/home).
    - Walks the tree but does NOT follow reparse points (records them as
      blocked).
    - Collects metadata: path, type, size, timestamps, extension, attributes,
      reparse status, Git-boundary status, likely classification.
    - Does NOT hash by default. Hashing only when -HashWithReason is supplied
      for a stated verification purpose.
    - Never reads file content / never outputs content.

.PARAMETER Target
  REQUIRED. Explicit directory to inventory.

.PARAMETER OutputCsv
  Path to write INVENTORY.csv. If omitted prints records to the pipeline.

.PARAMETER MaxDepth
  Optional recursion depth limit (default 9999). Set to bound traversal.

.PARAMETER HashWithReason
  Optional. A stated verification reason. When provided, computes SHA256 of
  files that are NOT inside a sensitive-looking path and adds hash_* columns.
  Still never reads content into output.

.EXAMPLE
  pwsh -NoProfile -File inventory_directory.ps1 -Target "\\wsl.localhost\...\fixture-root" -OutputCsv INVENTORY.csv
#>
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [string]$OutputCsv,
    [int]$MaxDepth = 9999,
    [string]$HashWithReason = ''
)

$ErrorActionPreference = 'Stop'

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

$records = New-Object System.Collections.Generic.List[object]

$stack = New-Object System.Collections.Generic.List[object]   # @{ Path = string; Depth = int }
$stack.Add([pscustomobject]@{ Path = $Target; Depth = 0 })

while ($stack.Count -gt 0) {
    # Use pop from end for deterministic DFS order
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
            is_reparse = $true; reparse_tag = 'NOACCESS'; blocked = $true
            block_reason = 'unreadable directory'; is_git_boundary = $false
            depth = $depth; hash_sha256 = ''; sensitive = $false
        })
        continue
    }

    # Use Sort to make ordering deterministic (stable by name)
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
            $records.Add([pscustomobject]@{
                path = $child.FullName; item_type = 'directory'; size_bytes = 0
                extension = ''; created = ''; modified = ''
                attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                blocked = $isReparse; block_reason = if ($isReparse) { 'reparse point - not traversed' } else { '' }
                is_git_boundary = $isGitBoundary; depth = $depth + 1; hash_sha256 = ''
                sensitive = $sensitive
            })
            # Only descend into non-reparse directories
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
            $records.Add([pscustomobject]@{
                path = $child.FullName; item_type = 'file'
                size_bytes = $size; extension = $child.Extension
                created = ''; modified = ''
                attributes = $attrsStr; is_reparse = $isReparse; reparse_tag = $tag
                blocked = $isReparse; block_reason = if ($isReparse) { 'reparse point - not traversed' } else { '' }
                is_git_boundary = $isGitBoundary; depth = $depth + 1
                hash_sha256 = $hash; sensitive = $sensitive
            })
        }
    }
}

# Emit
if ($OutputCsv) {
    $records | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation -Encoding UTF8
    Write-Output "Inventory written to $OutputCsv ($($records.Count) items)"
} else {
    $records | ConvertTo-Json -Depth 4
}
