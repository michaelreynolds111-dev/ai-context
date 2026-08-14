---
name: build-session-close
description: End-of-session closing routine for the Backup AI System build. Trigger when a phase exit test passes, or when the user says "we're done", "what's next", "session wrap", "update the build state", "write me a handover", or any equivalent. Also trigger at the natural end of a build conversation. Do not wait to be asked.
---

# Build Session Close

Produce a complete BUILD_STATE.md replacement (not a diff) containing:

1. Updated date and current phase/sub-step
2. Updated phase status table
3. Any new environment facts discovered
4. Every file created or modified this session, with full paths
5. Decisions made, each with a one-line rationale
6. Blockers: what failed, what was tried, what to try next
7. The exact next step, specific enough to start cold

Then state in one line: what to paste into project knowledge and what to commit to the ai-context repo.

Also: if this session hit any environment-specific surprise that a future session would otherwise re-discover from scratch (Node/npm-on-Windows, shell-layer quoting, Docker UID/volume behaviour, MCP auth quirks, etc.), add or update an entry in docs/GOTCHAS.md - Symptom / Root cause / Fix - and commit it alongside BUILD_STATE.md. Never put secret values in it.

Verify before firing create_or_update_file or push_files: the content parameter must contain the actual file body, not a placeholder or truncated draft. A silent placeholder push wipes the file to a few bytes and requires immediate recovery. Read the intended content back before submitting the tool call.

Push path (default): local git from the WSL2 clone at ~/ai-context/ - git add -A && git commit -m 'session: <phase>' && git push. Report the commit SHA. No git pull is needed after the push - all commits originate from the same clone, so the local copy is current after git push returns. Only pull if a file was edited directly on GitHub (e.g. via the web UI, or via the GitHub MCP connector by another session).

If the GitHub MCP connector was used to push (not local git): the local WSL2 clone is now behind. Instruct the user to run cd ~/ai-context && git pull --ff-only before their next session-open, or the next git commit && push will fail on a non-fast-forward.

## Anti-patterns to avoid
- Summarising the conversation instead of producing the artifact.
- Partial updates that assume the reader remembers earlier context.
- Vague next steps ("continue setup") instead of a runnable action.

Do not summarise the conversation. Produce the artifact.
