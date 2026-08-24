# SCRIPT_DEPLOYMENT — How to Get the Analysis Script Running

**Purpose:** Step-by-step for deploying `analyze_claude_export.py` and running the first analysis. This is a GOOSE_TASK (Goose executes; LibreChat plans and verifies).

---

## Prerequisites
- The Claude export zip has been downloaded and unzipped to `/app/agent-workdir/claude-export/`
- `conversations.json` is present in that directory
- Python 3.8+ is available in the WSL2 environment

## Steps

### 1. Unzip the export (if not already done)
```bash
mkdir -p /app/agent-workdir/claude-export
# If the zip is in Downloads:
unzip ~/Downloads/claude-export.zip -d /app/agent-workdir/claude-export/
# Verify
ls -la /app/agent-workdir/claude-export/
# Should see: conversations.json (and possibly projects.json, account.json)
```

### 2. Copy the analysis script to a runnable location
The script lives in the staged skill bundle. Copy it to the export directory for easy execution:
```bash
cp /app/agent-workdir/staging-ai-context/skills/claude-usage-analyzer/scripts/analyze_claude_export.py \
   /app/agent-workdir/claude-export/
```

### 3. (Optional) Install ijson for streaming large files
```bash
pip3 install ijson
```
If the export is under 50MB, this is unnecessary — the script falls back to standard `json.load`.

### 4. Run the analysis
```bash
cd /app/agent-workdir/claude-export
python3 analyze_claude_export.py \
  --input ./conversations.json \
  --output ./analysis/
```

### 5. Verify outputs
```bash
ls -la ./analysis/
# Should see:
#   summary.json
#   usage_report.md
#   feature_usage.json
#   temporal_patterns.json
#   topic_clusters.json
```

### 6. Read the report
```bash
cat ./analysis/usage_report.md
```

### 7. Hand off to LibreChat
The `summary.json` and individual JSON files are the structured aggregates. LibreChat (via the claude-usage-analyzer skill) reads these and produces the final gap-analysis report.

## Success criteria (exit test)
- [ ] `conversations.json` is present and valid JSON
- [ ] Script runs without errors
- [ ] `analysis/summary.json` exists and contains `basic_stats` with `total_conversations > 0`
- [ ] `analysis/usage_report.md` exists and is non-empty
- [ ] No raw conversation text appears in any output file (only aggregates)

## Constraints
- Do NOT send the export or analysis files to any external service
- Do NOT commit the `claude-export/` directory to git (it contains [SENSITIVE] data)
- Add `claude-export/` to `.gitignore` if not already excluded
