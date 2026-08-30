<#
.SYNOPSIS
  inspect_git_state.ps1 — Read-only inspection of Git repository state for the
  Computer File Steward v1.0.2 skill.

.DESCRIPTION
  Collects read-only repository metadata: root, branch, HEAD, remotes (with
  userinfo/credentials SANITIZED), clean/dirty status, counts of modified /
  deleted / untracked / conflicted / staged entries, stashes, worktrees,
  submodules, and local-only branch indicators.

  v1.0.2 (Fix C — genuinely read-only Git inspection):
    - Sets GIT_OPTIONAL_LOCKS=0 for every Git subprocess so read-only commands
      cannot lazily refresh/rewrite repository metadata (index/refs).
    - Uses read-only/plumbing commands only. No fetch/pull/ls-remote or any
      network Git operation is ever issued.
    - Safe command transport: NO shell string is built by concatenating
      user-controlled paths or arguments. For the WSL route, the full git
      argument vector (including the repo path) is base64-encoded and passed as
      a single opaque positional argument to a FIXED, constant bash wrapper that
      decodes it into an argv array and execs git directly. No user data is ever
      interpolated into a shell command string, so apostrophes, spaces, brackets,
      ampersands, semicolons, and non-ASCII path characters cannot inject.
    - Remote URLs are sanitized (any userinfo user:pass@ is removed).
    - Submodules are treated as metadata only and are never initialized or
      recursed into.

  v1.0.1 (Correction C): explicitly requires PowerShell 7+ (pwsh).

.PARAMETER RepoPath
  REQUIRED. The repository working tree to inspect (Windows or WSL/UNC path).

.PARAMETER ResultFile
  Path to write the git-state JSON report.

.EXAMPLE
  pwsh -NoProfile -ExecutionPolicy Bypass -File inspect_git_state.ps1 `
       -RepoPath "\\wsl.localhost\...\fixture-root\fake-repository" -ResultFile gitstate.json
#>
#Requires -Version 7.0
param(
    [Parameter(Mandatory = $true)][string]$RepoPath,
    [string]$ResultFile
)

$ErrorActionPreference = 'Continue'

if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "UNSUPPORTED RUNTIME: Computer File Steward requires PowerShell 7+ (pwsh). Detected $($PSVersionTable.PSVersion). Refusing to scan."
    exit 100
}

if (-not (Test-Path -LiteralPath $RepoPath)) {
    Write-Error "Repository path not found: $RepoPath"
    exit 3
}

$useWsl = $RepoPath -match '^\\\\wsl\.localhost\\' -or $RepoPath -match '^/'
$grepPath = $RepoPath
if ($useWsl -and $RepoPath -match '^\\\\wsl\.localhost\\([^\\]+)\\(.*)$') {
    $distro = $Matches[1]
    $rest = $Matches[2] -replace '\\', '/'
    $grepPath = "/$rest"
}

# ---------------------------------------------------------------------------
# v1.0.2 Fix C: safe command transport + read-only Git.
#
# Windows route : invoke git directly with an argument vector (PowerShell
#                 splatting) — no string shell. Set GIT_OPTIONAL_LOCKS=0.
# WSL route     : encode the full git argument vector (incl. -C <path>) into a
#                 single base64 string and pass it to a CONSTANT bash wrapper as
#                 a positional arg. The wrapper decodes into an argv array (no
#                 eval, no word-splitting) and `exec`s git. No user-controlled
#                 text ever appears in a shell command string.
# ---------------------------------------------------------------------------
$OldGitOptionalLocks = $env:GIT_OPTIONAL_LOCKS

# Constant, never-interpolated bash wrapper used only for the WSL route.
$WSL_GIT_WRAPPER = 'export GIT_OPTIONAL_LOCKS=0; payload="$1"; a=(); while IFS= read -r -d "" x; do a+=("$x"); done < <(printf "%s" "$payload" | base64 -d); exec git "${a[@]}"'

function Invoke-Git {
    param([string[]]$GitArgs)
    if ($useWsl) {
        # Full argv including -C <repo-path> then the git args.
        $argv = @('-C', $grepPath) + $GitArgs
        # Encode as NUL-separated then base64 (single opaque token; safe charset).
        $joined = ($argv -join [string][char]0) + [string][char]0
        $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($joined))
        # Run the CONSTANT wrapper; $b64 is passed as a positional argument, never
        # interpolated into any command string.
        $out = & wsl.exe -d Ubuntu-24.04 -e bash -c $WSL_GIT_WRAPPER _ $b64 2>$null
        return ($out -join "`n")
    } else {
        $env:GIT_OPTIONAL_LOCKS = '0'
        try {
            $out = & git -C $grepPath @GitArgs 2>$null
            return ($out -join "`n")
        } finally {
            if ($null -eq $OldGitOptionalLocks) { Remove-Item Env:GIT_OPTIONAL_LOCKS -ErrorAction SilentlyContinue }
            else { $env:GIT_OPTIONAL_LOCKS = $OldGitOptionalLocks }
        }
    }
}

function Sanitize-Url {
    param([string]$Url)
    if ($Url -match '^([a-zA-Z][a-zA-Z0-9+.-]*://)([^@/]+)@(.*)$') {
        return $Matches[1] + '<redacted>@' + $Matches[3]
    }
    return $Url
}

$repoRoot = (Invoke-Git @('rev-parse','--show-toplevel')).Trim()
$branch = (Invoke-Git @('rev-parse','--abbrev-ref','HEAD')).Trim()
$head = (Invoke-Git @('rev-parse','HEAD')).Trim()

$remoteLines = Invoke-Git @('remote','-v')
$remotes = @()
foreach ($line in ($remoteLines -split "`n")) {
    if ($line -match '^(\S+)\s+(\S+)\s+\((fetch|push)\)\s*$') {
        $remotes += [pscustomobject]@{
            name = $Matches[1]
            url = (Sanitize-Url $Matches[2])
            direction = $Matches[3]
        }
    }
}

$statusCounts = Invoke-Git @('status','--porcelain')
$trackedModified = 0; $trackedDeleted = 0; $trackedNew = 0; $untracked = 0; $conflicted = 0
foreach ($line in ($statusCounts -split "`n")) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line.Length -lt 2) { continue }
    $xy = $line.Substring(0,2)
    if ($xy -match 'U|AA|DD|AU|UA|DU|UD') { $conflicted++; continue }
    if ($xy[1] -eq '?') { $untracked++; continue }
    $y = $xy[1]; $x = $xy[0]
    if ($y -eq 'D') { $trackedDeleted++ }
    if ($x -eq 'A' -and $y -eq ' ') { $trackedNew++ }
    if ($y -eq 'M' -or $y -eq 'T' -or $y -eq 'R' -or $y -eq 'C') { $trackedModified++ }
}

$clean = ($trackedModified -eq 0 -and $trackedDeleted -eq 0 -and $trackedNew -eq 0 -and $untracked -eq 0 -and $conflicted -eq 0)

$stashList = Invoke-Git @('stash','list')
$stashCount = @($stashList -split "`n" | Where-Object { $_.Trim() -ne '' }).Count

$wtRaw = Invoke-Git @('worktree','list')
$worktrees = @($wtRaw -split "`n" | Where-Object { $_.Trim() -ne '' })

$submoduleRaw = (Invoke-Git @('submodule','status')).Trim()
$submoduleCount = if ($submoduleRaw) { @($submoduleRaw -split "`n").Count } else { 0 }

$localOnly = @()
$branchRaw = Invoke-Git @('for-each-ref','refs/heads','--format=%(refname:short)')
$branchNames = @($branchRaw -split "`n" | Where-Object { $_.Trim() -ne '' })
foreach ($br in $branchNames) {
    $ups = $br + '@{upstream}'
    $up = (Invoke-Git @('rev-parse','--abbrev-ref','--symbolic-full-name',$ups)).Trim()
    if (-not $up -or $up -match 'no upstream|@{upstream}') { $localOnly += $br }
}

# Resolve repo root back to display path (WSL -> UNC) if needed
$displayRoot = $repoRoot
if ($useWsl -and $repoRoot -match '^/') {
    # leave as /home/... WSL path for clarity
    $displayRoot = $repoRoot
}

$report = @{
    repo_path = $RepoPath
    repository_root = if ($displayRoot) { $displayRoot } else { $null }
    current_branch = if ($branch) { $branch } else { $null }
    head = if ($head -and $head -notmatch '^usage:') { $head } else { $null }
    remotes = $remotes
    clean = $clean
    counts = @{
        tracked_modified = $trackedModified
        tracked_deleted = $trackedDeleted
        tracked_added = $trackedNew
        untracked = $untracked
        conflicted = $conflicted
    }
    stash_count = $stashCount
    worktrees = $worktrees
    submodule_count = $submoduleCount
    local_only_branches = $localOnly
    mode = 'READ_ONLY'
    read_only_git = $true
    optional_locks_disabled = $true
    credentials_redacted = $true
    routed_through_wsl = $useWsl
}

if ($ResultFile) {
    $report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ResultFile -Encoding UTF8
    Write-Output "Git-state report written to $ResultFile"
} else {
    $report | ConvertTo-Json -Depth 10
}
