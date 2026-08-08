---
name: powershell-sysadmin
description: Use when working with PowerShell, Windows administration, WSL2, Docker Desktop on Windows, scheduled tasks, Windows services, or the Windows/Linux hybrid environment on Michael-PC. Triggers on requests to write, debug, or explain PowerShell scripts, WSL2 configuration, Docker Compose on Windows, or any Windows sysadmin task.
---

# PowerShell / Sysadmin

## When to use
- Writing or debugging PowerShell scripts
- WSL2 configuration, distro management, .wslconfig tuning
- Docker Desktop on Windows (WSL2 backend)
- Windows scheduled tasks (Task Scheduler, schtasks)
- Windows services, registry, file system operations
- Cross-environment work (PowerShell → WSL2 → bash → Docker)
- Network configuration, firewall rules, port forwarding
- BitLocker and encryption management

## This machine (Michael-PC)
- Windows 11 Home 26200, i5-12400, 15.8 GB RAM
- WSL2 default distro: Ubuntu-24.04 (explicitly target with `-d Ubuntu-24.04`)
- Docker Desktop with WSL2 backend, Ubuntu-24.04 integration enabled
- Project files live in WSL2 native fs (`~/`), never `/mnt/c/`
- LibreChat stack at `~/LibreChat/`, ai-context at `~/ai-context/`
- gitleaks at `~/.local/bin/gitleaks`, on PATH via `~/.bashrc`

## Hard rules
- **Always specify the environment** for every command: WSL2 bash, PowerShell, or container shell.
- **Never use bare `wsl` without `-d Ubuntu-24.04`** — docker-desktop distro may be default.
- **Never use /mnt/c/ paths** for project files — use WSL2 native paths or UNC (`\\wsl.localhost\Ubuntu-24.04\...`).
- **Dollar-sign hazard in PowerShell:** `$` in inline strings causes silent variable interpolation. For file content with `$`, write to a temp file via UNC path, execute via `wsl bash ~/script.sh`.
- **`sudo` hangs** in the Desktop Commander PowerShell console — no visible prompt. Avoid `sudo`; use user-local installs or `docker exec` as root.
- **`docker compose exec` uses service name** (`mongodb`); **`docker exec` uses container name** (`chat-mongodb`). Not interchangeable.

## Common patterns

### WSL2 command (correct form)
```powershell
wsl -d Ubuntu-24.04 -- bash -lc "your command here"
```

### Write a file with special characters (avoid PowerShell interpolation)
```
Desktop Commander write_file to \\wsl.localhost\Ubuntu-24.04\home\michael\script.sh
then: wsl -d Ubuntu-24.04 -- bash -lc "bash ~/script.sh"
```

### Docker operations (from WSL2, in ~/LibreChat)
```bash
cd ~/LibreChat
docker compose ps
docker compose logs --tail=30 api
docker compose up -d --force-recreate api
docker compose stop       # ALWAYS before host sleep/shutdown
```

### Scheduled tasks
Use `schtasks /query /fo LIST /v` to audit. Scripts likely hardcode `D:\Data` — check before touching.

## Output format
- Always label shell environment: `# PowerShell`, `# WSL2 bash`, `# Container (docker exec)`
- Runnable commands, not pseudocode
- For multi-step operations: numbered steps, one command per step
