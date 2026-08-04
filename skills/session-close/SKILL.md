---
name: session-close
description: End-of-session closing routine. Trigger when a meaningful chunk of work completes, or when the user says "we're done", "what's next", "session wrap", "update state", "write me a handover", or equivalent. Produces a complete state-file replacement, not a diff or a conversational summary.
---

# Session Close

## When to use
At the natural end of a working session, or on explicit request, once there
is something concrete to record (a file changed, a decision made, a step
completed).

## Process
1. Identify the current phase/task and its status.
2. List every file created or modified this session, with full paths.
3. List decisions made, each with a one-line rationale.
4. List open blockers: what failed, what was tried, what to try next.
5. State the exact next step, specific enough to start cold with no
   additional context.

## Output format
Produce a full replacement of the relevant state-tracking file (e.g.
BUILD_STATE.md) -- not a diff, not a narrative recap of the conversation.
End with one line stating where the output should be saved/committed.

## Anti-patterns to avoid
- Summarising the conversation instead of producing the artifact.
- Partial updates that assume the reader remembers earlier context.
- Vague next steps ("continue setup") instead of a runnable action.

