# Evidence Gate — The Three-Tier Claim Classification

**Source:** Derived from the state-update-guard skill design, informed by modern
agent-framework provenance patterns (event-sourced append-only logs,
validate-before-write hooks, false-completion testing).
**Purpose:** The canonical reference for classifying session claims. Read this
when you are unsure whether something is [DONE] or [DISCUSSED].

---

## The core problem this solves

LLMs confuse three distinct things:
1. **What was discussed** (an idea, a plan, a proposed improvement).
2. **What a user reported doing** (a manual step the user says they completed).
3. **What is verifiably true in the system** (a file exists, a commit landed, a
   tool returned the expected result).

When these collapse into a single "we did X" claim in the state file, the state
file becomes fiction. The next session trusts fiction and builds on it. This is
how builds drift.

The three-tier classification keeps them separate.

---

## Tier definitions

### [DONE] — verifiably complete

The work is complete AND you can prove it with evidence from THIS session.

**Accepted evidence (one required):**

| Evidence type | What it looks like | Example |
|---|---|---|
| Commit SHA | A SHA you read from a `GOOSE_RESULT_*.md`, a git log output, or a file-info timestamp — NOT a SHA you remember from a prior session | `— evidence: commit 1e8f27a (read from GOOSE_RESULT_PROMOTE_PLAN_EXECUTOR_SKILL.md)` |
| Tool result | A `read_text_file_mcp_filesystem` or `list_directory_mcp_filesystem` call whose output confirms the file exists with expected content | `— evidence: list_directory_mcp_filesystem on /app/ai-context/skills showed 9 dirs` |
| Explicit user completion of a manual step | The user names the specific deliverable AND the deliverable matches your claim. Only for steps the user alone can perform (UI clicks, physical actions). | `— evidence: user stated "I clicked Save on the Build Coordinator agent in the LibreChat admin panel"` |

**NOT accepted as [DONE] evidence:**
- "The user said they did step 3" → that's evidence for step 3, not step 5.
- "We discussed creating the agent" → discussion is not creation.
- "The plan says to do X" → the plan is a roadmap, not a result.
- A SHA you remember from a prior session → memory is not evidence; read it fresh.
- "It should work" / "it's probably done" → inference, not verification.

### [DISCUSSED] — talked about, planned, or user-reported but unverified

The work was the subject of conversation. The user may have reported doing it.
But no tool result or commit from THIS session confirms the outcome.

**This is the most dangerous tier** because it feels like progress. It is not
progress until verified. Common [DISCUSSED] situations:

- The user said "I copied the recipe into Goose" — you did not read the
  destination directory to confirm the file is there with the right content.
- You and the user agreed on a model recommendation — but the agent using that
  model has not been created or tested.
- A Goose task was written to `tasks/` — but no `GOOSE_RESULT_*.md` exists yet,
  so execution is not confirmed.
- The user said "done" in response to a multi-step instruction — but "done"
  may mean "I did the part I understood," not "all steps completed and verified."

**[DISCUSSED] entries must state the verification step** that would promote
them to [DONE]:
> `— evidence: user statement (unverified). Verify: read /app/ai-context/skills/<name>/SKILL.md to confirm it exists.`

### [PLANNED] — not started

On the roadmap. No action taken this session. No discussion that advanced it.
These do not get event-log entries (they're already in BUILD_STATE's roadmap
sections). Only mention in the "Next step" line if they're what's next.

---

## The promotion gate

```
[DISCUSSED] → [DONE]  requires NEW evidence from THIS session
                        (tool result, commit SHA, or verified user step)

[PLANNED]   → [DISCUSSED] requires the work to have been actually discussed
                          or a task file written

[PLANNED]   → [DONE]    FORBIDDEN — you cannot skip DISCUSSED
```

**Never promote [DISCUSSED] to [DONE] without new evidence.** "The user said
they did it" is [DISCUSSED], not [DONE]. "I read the file and it contains the
expected content" is [DONE].

---

## Worked examples

### Example 1 — the failure mode this skill was built to prevent

**Session reality:** The user was given a 5-step checklist. They completed
steps 1-3 (copied a recipe, relaunched Goose). Steps 4-5 (create the agent,
test it) were NOT done.

| Wrong claim | Tier | Why wrong |
|---|---|---|
| "Build Coordinator agent created and tested" | [DONE] | No evidence. The user completed steps 1-3, not 4-5. Collapsing "user did some steps" into "all steps done" is a false-completion claim. |
| "Build Coordinator agent created" | [DISCUSSED] | The user reported completing recipe steps, but agent creation (step 4) was not confirmed by a tool result or a specific user statement naming the agent. |
| "Steps 1-3 of the 5-step checklist completed by user" | [DONE] | The user explicitly stated they completed these specific steps. This is a manual user step with a named deliverable. |
| "Steps 4-5 (create + test agent) — not yet done" | [PLANNED] | No action taken. Correct. |

### Example 2 — a commit

**Session reality:** Goose promoted the plan-executor skill. A
`GOOSE_RESULT_PROMOTE_PLAN_EXECUTOR_SKILL.md` file exists in `outputs/`.

| Claim | Tier | Evidence |
|---|---|---|
| "plan-executor skill promoted to ai-context" | [DONE] | `— evidence: GOOSE_RESULT_PROMOTE_PLAN_EXECUTOR_SKILL.md reports commit c514c9f, pushed 1aea0c2..c514c9f` |
| "8 skills synced to Goose" | [DONE] | `— evidence: same GOOSE_RESULT file reports 8 skills synced` |

### Example 3 — a model recommendation

**Session reality:** You and the user discussed and agreed that
`deepseek-ai/DeepSeek-V4-Flash-0731` should be the Build Coordinator model.
The setup doc was updated to reflect this and committed.

| Claim | Tier | Evidence |
|---|---|---|
| "Model recommendation: DeepSeek V4 Flash" | [DONE] | `— evidence: commit 1e8f27a updated BUILD_COORDINATOR_AGENT_SETUP.md model line (read via read_text_file_mcp_filesystem)` |
| "Build Coordinator agent is running on DeepSeek V4 Flash" | [DISCUSSED] | The agent may not be created yet, or may not use this model. Verify: check the agent's model setting in LibreChat. |

---

## Anti-patterns (the false-completion taxonomy)

These are the specific ways LLMs fabricate progress. Test your draft against
each before writing:

1. **Step collapse** — the user did steps 1-3 of 5; you write "all 5 steps
   done." Fix: list each step with its own tier tag.
2. **Discussion-as-implementation** — "we decided to use model X" becomes "the
   agent uses model X." Fix: decision = [DISCUSSED]; agent running on model X =
   [DONE] (requires verification).
3. **Memory-as-evidence** — citing a commit SHA you remember from a prior
   session, not one you read this session. Fix: read the result file fresh.
4. **Optimistic rounding** — "it should work" / "probably done" becomes [DONE].
   Fix: if you can't cite evidence, it's [DISCUSSED].
5. **User-said-done collapse** — the user said "done" to a multi-step
   instruction; you mark all steps [DONE]. Fix: "done" is evidence only for the
   specific step the user named, and only if it's a manual step.
6. **State-as-action** — "the recipe is installed in Goose" (state) written as
   evidence for "the user copied the recipe" (action). These are different
   claims. The action is [DISCUSSED] until you read the destination file; the
   state is [DONE] only if the file read confirms it.
7. **Invented file** — claiming a file was created when you never called a
   write tool for it. Fix: if no write tool was called, no file was created.

---

*End of reference. The canonical skill lives at
`skills/state-update-guard/SKILL.md`.*
