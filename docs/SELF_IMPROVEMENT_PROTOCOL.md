# SELF-IMPROVEMENT PROTOCOL

**Version:** 2.0 (reconciled merge of the skill-focused draft and the whole-system plan)
**Date:** 13 August 2026
**Author:** LibreChat (planner/verifier), reviewed by Michael
**Status:** Staged — awaiting commit to `ai-context/docs/`
**Supersedes:** `~/agent-workdir/SELF_IMPROVEMENT_LOOP_BUILD_PLAN.md` (v1, skill-only draft)
**Depends on:** Phase 9 cutover, Deferred item 4 PASSED, Goose↔LibreChat file handoff proven
**Predecessor docs:** `BUILD_STATE.md`, `docs/USAGE_PATTERNS.md`, `AGENT_BOOTSTRAP.md`, `docs/GOTCHAS.md`, master plan §14/§16

---

## 0. EXECUTIVE SUMMARY

The Backup AI System already has a **propose→review→promote loop**: LibreChat
plans, Goose executes, LibreChat verifies against an exit test, and the result
is archived or flagged. This protocol extends that loop so the system can
**improve its own skills, agent instructions, MCP capabilities, models, and
configuration over time** — with a human checkpoint before any change is
promoted, and with automatic revert if a change degrades measured
performance.

The design draws on three principles from the self-improving-agent literature:

1. **Separation of modification from execution** — the agent that proposes a
   change is not the agent that applies it, and neither is the agent that
   evaluates whether the change helped \ue202turn2search1.
2. **Lineage tracking + rollback** — every change is versioned, every prior
   state is restorable without redeployment \ue202turn0search0.
3. **Evaluation harness as the objective** — the system can only safely
   self-improve toward what it can objectively measure \ue202turn2search0.

**What is in scope:** human-in-the-loop self-improvement across the whole
system — agent instructions, skills, MCP capabilities, models/endpoints, and
core configuration.

**What is out of scope:** fully autonomous self-modification. No change is
promoted without a human checkpoint. No change touching a Level 4 (forbidden)
boundary is proposed at all — the boundary is structural, not advisory.

---

## 1. WHAT EXISTS ALREADY (DO NOT REBUILD)

| Component | Location | Role in the self-improvement loop |
|---|---|---|
| Propose→review→promote protocol | `docs/USAGE_PATTERNS.md` §2 | The handoff cycle is the skeleton of the improvement loop |
| Skills system | `ai-context/skills/*/SKILL.md` (8 skills) | The *artifacts* that get improved — each skill is a versioned, reviewable bundle |
| LibreChat Agent Skills (v0.8.7) | `librechat.yaml`, agent configs | Model-invoked skills with ACLs, scoping, and import/sync \ue202turn1search1 \ue202turn1search2 |
| Task/result file protocol | `agent-workdir/tasks/`, `outputs/` | The *trace* format — every Goose execution is already a structured record |
| Exit tests | Every `GOOSE_TASK_*.md` | The *evaluation criteria* — already checkable, already used for sign-off |
| State tracking | `BUILD_STATE.md` | The *behavioral snapshot log* — records what changed and when |
| Git version control | `ai-context/` repo | The *rollback mechanism* — `git revert` restores any prior skill state |
| `goose-task` alias | `agent-workdir/scripts/goose-task.sh` | Scaffolding for new improvement cycles |
| `docs/GOTCHAS.md` | Hard-won failure modes | The *safety invariant* list the improver must respect |
| Admin panel (v0.8.7) | LibreChat UI, port 3000 | Per-role/group config overrides, MCP allowlist changes — no restart needed |
| MCP allowlist (v0.8.7) | LibreChat UI | MCP servers addable via UI without restart |

**Key insight:** the system already has most of the components a
self-improving agent needs \ue202turn0search0. The missing piece is the
**improvement loop itself** — a structured cycle that captures traces,
analyzes them, proposes changes, measures whether the changes helped, and
reverts if they did not.

---

## 2. SCOPE — WHOLE SYSTEM

The self-improvement loop covers five categories of change, each with a
different change path (dynamic vs. staged — see §4):

| Category | Examples | Change path |
|---|---|---|
| **Agent behaviour** | Agent instructions, system prompts, routing rules | Dynamic (API PATCH, no restart) |
| **Skills** | New skills, skill revisions, skill retirement | Dynamic (UI authoring, no restart for UI-registered skills) |
| **MCP / capabilities** | New MCP server registration, tool allowlist changes | Dynamic (UI registration, no restart) |
| **Models / endpoints** | Model swaps, endpoint changes, provider config | Dynamic (admin panel override, no restart) OR staged (`librechat.yaml`, restart) |
| **Core config** | Memory block keys, endpoint defaults, feature flags | Dynamic (admin panel) OR staged (`librechat.yaml`, restart) |

The scope is deliberately wider than skills-only. A system that can improve
its skills but not its own instructions, MCP tools, or workflows is not really
self-improving — it is just skill-editing. The whole-system scope is what
makes this genuine self-improvement.

---

## 3. SAFETY ARCHITECTURE — 4-LEVEL CHANGE CLASSIFICATION

Every proposed change is classified into one of four levels. The level
determines the change path and the safety constraints. This classification is
**structural** — Level 4 changes are not merely discouraged, they are
**forbidden by design**. The improver does not propose them; the protocol
does not permit them.

### 3.1 The four levels

| Level | Description | Change path | Human checkpoint | Auto-revert |
|---|---|---|---|---|
| **Level 1 — Wording** | Rephrasing, clarification, tone adjustment within an existing instruction or skill | Dynamic (API PATCH or UI edit) | Required | Yes (eval suite) |
| **Level 2 — Process** | New step in a workflow, revised handoff format, new eval task | Dynamic or staged (depends on target) | Required | Yes (eval suite) |
| **Level 3 — Scope** | New skill, new MCP server, new model, new agent, expanded tool access | Staged (staging dir → validate → promote) | Required | Yes (eval suite) |
| **Level 4 — Forbidden** | Changes to safety rules, routing boundaries, tool exclusion lists, or the improver itself | **NOT PERMITTED** | N/A — never proposed | N/A |

### 3.2 Named hard invariants (Level 4 — never touch)

These are the structural boundaries the improver must never propose changes
to. They are inherited from the existing build's safety architecture and are
non-negotiable:

1. **Credential Rule** — no credentials, tokens, or secrets in any
   `ai-context/` file, skill, agent instruction, or trace. The gitleaks
   pre-commit hook enforces this at commit time; the improver must not
   propose changes that would violate it.

2. **Clinical Work tool exclusion** — the `Clinical Work` agent has
   `tools: []` (hard exclusion, verified at Phase 8). The improver must never
   propose adding tools to this agent. This is the routing boundary that
   keeps clinical output on DeepInfra/Anthropic direct ONLY, with no
   filesystem, MCP, or external-tool access.

3. **Household Admin tool exclusion** — the `Household Admin` agent has
   `tools: []` (hard exclusion, verified at Phase 8). The improver must never
   propose adding tools to this agent. Household identifiers are retrieved
   via scoped RAG only, never via tool calls.

4. **Paperwork agent routing** — the Paperwork agent routes to
   DeepInfra/Anthropic direct ONLY, with no tools. Classification [SENSITIVE].
   The improver must never propose changing this routing or adding tools.

5. **GOTCHAS invariants** — every entry in `docs/GOTCHAS.md` is a
   hard-won environmental fact. The improver must not propose changes that
   contradict a GOTCHAS entry. If a GOTCHAS entry is stale, that is a
   separate human decision — the improver does not update GOTCHAS
   autonomously.

6. **Read-only safety boundary** — `/app/ai-context` and `/app/LibreChat`
   are read-only to the improver (via LibreChat filesystem MCP). The improver
   stages changes to `agent-workdir/staging-ai-context/` and
   `agent-workdir/staging-librechat/`; promotion is a human/Goose action via
   local git. The improver never writes directly to production paths.

7. **Self-modification of the improver** — the improver must not propose
   changes to its own instructions, its own eval suite, or its own safety
   classification. Any change to the improvement loop itself is a human-only
   decision, made by editing this protocol document directly.

### 3.3 Why structural, not advisory

A general "human approves before promotion" gate puts the entire safety burden
on the human catching every problem in review. The 4-level classification
makes the boundaries structural — Level 4 changes are **forbidden by design**,
not just discouraged. This matters specifically for this system because it
has SENSITIVE-classified agents (Paperwork) with hard tool exclusions and
routing boundaries. If an improver could rewrite those tool lists or routing
rules, even with human approval, it would create a path to bypass the security
architecture. The classification makes that path structurally impossible.

---

## 4. v0.8.7 CAPABILITY MAP — DYNAMIC VS. STAGED

LibreChat v0.8.7 introduced several capabilities that allow changes without
restart. This determines whether a change follows the **dynamic path**
(apply live, no restart) or the **staged path** (stage → validate → promote →
restart). Full capability details are in `docs/V0_8_7_CAPABILITIES.md`.

### 4.1 Dynamic path (no restart)

| Capability | Mechanism | What it enables |
|---|---|---|
| Agent instructions | API PATCH to agent endpoint | Update system prompts, routing rules, tool lists — live |
| Skills (UI-registered) | Admin panel / agent UI | Author, edit, import, sync skills — live |
| MCP server registration | Admin panel UI | Add MCP servers to the allowlist — live |
| Model / endpoint overrides | Admin panel per-role/group config | Swap models, change endpoints per role or group — live |
| Feature flags | Admin panel | Toggle features without restart |

### 4.2 Staged path (restart required)

| Capability | Mechanism | Why restart |
|---|---|---|
| `librechat.yaml` changes | Edit file → restart `api` container | YAML is parsed at startup; changes require container restart |
| Endpoint definitions | `librechat.yaml` `endpoints:` block | Same — parsed at startup |
| Memory block `validKeys` | `librechat.yaml` `memory:` block | Same |

### 4.3 Decision rule

```
Can the change be applied via admin panel or API PATCH?
  YES → Dynamic path (stage in staging-librechat/ for review, apply live)
  NO  → Staged path (stage in staging-librechat/, validate, promote, restart)
```

For `ai-context/` changes (skills, docs, GOTCHAS, agent instructions stored as
files): always staged via `staging-ai-context/`, promoted via git commit.
These are not live-applied — they are version-controlled documents.

---

## 5. THE IMPROVEMENT LOOP

### 5.1 Loop overview

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   1. CAPTURE    2. ANALYZE    3. PROPOSE   4. REVIEW       │
    │       │             │            │           │            │
    │       ▼             ▼            ▼           ▼            │
    │   task traces   failure      draft change   human          │
    │   + results     patterns     + eval plan    checkpoint     │
    │                  + metrics                                  │
    │                                                             │
    │   5. APPLY      6. MEASURE    7. PROMOTE / REVERT          │
    │       │             │                  │                    │
    │       ▼             ▼                  ▼                    │
    │   stage change  run eval         keep if better,           │
    │   in staging     suite against     revert if not            │
    │                  baseline                                │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

This mirrors the "Loop Engineering" pattern: capture traces → analyze →
propose fixes → present for approval → apply → verify against baseline →
keep or revert \ue202turn0search1.

### 5.2 How it maps to the existing handoff

| Loop step | Existing mechanism | What's new |
|---|---|---|
| 1. Capture | `GOOSE_RESULT_*.md` files | A structured *trace log* that aggregates results across tasks |
| 2. Analyze | LibreChat reads result files | A dedicated *improvement skill* that looks for patterns across traces |
| 3. Propose | LibreChat writes `GOOSE_TASK_*.md` | A *change-delta* format (proposed change to a skill, agent instruction, or config — not just a task for Goose) |
| 4. Review | LibreChat verifies against exit test | A *human checkpoint* — Michael approves or rejects the delta |
| 5. Apply | Goose executes the task | Goose stages the change in the appropriate staging directory |
| 6. Measure | Exit test pass/fail | An *eval suite* — a set of test tasks that exercise the target before and after |
| 7. Promote/revert | Archive task+result | *Git commit* (promote) or *git revert* (rollback); for dynamic changes, API PATCH or admin panel apply |

### 5.3 The two trigger types

**Bottom-up (self-initiated):** The system analyses its own execution traces,
finds patterns (a skill that consistently produces a certain error, an agent
instruction that causes routing confusion, a model that underperforms on a
task type), and proposes a fix. This is the differentiating capability —
without it, the system is a change-management system, not a self-improving
system.

**Top-down (user-initiated):** Michael requests a change via chat ("add a
skill that checks medication interactions", "swap the Research agent to a
cheaper model for simple queries"). The agent determines whether the change
is dynamic or staged, drafts the change, and presents it for approval. This
is feature-request handling — useful, but not what makes the system
self-improving.

Both trigger types are supported. Bottom-up trace analysis is the
differentiating capability; top-down is a convenience.

---

## 6. SEPARATION OF ROLES

The self-modifying-agent literature identifies a conflict of interest when
an agent improves itself \ue202turn2search1. The solution is separation: the
agent that proposes a change is not the agent that applies it, and neither
is the agent that evaluates whether the change helped.

This system already satisfies the separation principle via its existing
two-agent split — no new agents are needed:

| Role | Agent | How |
|---|---|---|
| **Propose** | LibreChat (planner) | Analyses the need, drafts the change, writes the eval plan |
| **Apply** | Goose (executor) | Stages the change in the appropriate staging directory via file handoff |
| **Evaluate** | LibreChat (verifier) | Runs the eval suite against Goose's result, checks pass-rate, signs off or flags |

The file handoff protocol (`docs/USAGE_PATTERNS.md` §2) is the mechanism that
enforces this separation. LibreChat writes a task file; Goose executes it
and writes a result file; LibreChat reads the result and evaluates. No agent
both proposes and applies its own change.

---

## 7. GOOSE INTEGRATION — FILE HANDOFF ONLY

The Goose integration model is the **file-based handoff** established in
Deferred item 4 and documented in `docs/USAGE_PATTERNS.md`. This protocol
uses the same model. No Goose MCP server is built.

**Rationale:** The file handoff was chosen on 12 Aug 2026 with documented
rationale: "deliberately simple, debuggable, and sufficient for the current
workload." It was tested end-to-end on 13 Aug 2026 (Docker anomaly verify
task). The file handoff already does everything an MCP server's tools would
do:

| Hypothetical MCP tool | File handoff equivalent |
|---|---|
| `goose_plan` | Write a `GOOSE_TASK_*.md` file to `tasks/` |
| `goose_status` | Check for a `GOOSE_RESULT_*.md` file in `outputs/` |
| `goose_result` | Read the `GOOSE_RESULT_*.md` file |
| `goose_validate` | Run the eval suite against the result (LibreChat-side) |
| `goose_promote` | Git commit the staged change (human/Goose action) |

Building an MCP server would wrap file I/O in a live Node process for no
functional gain, add a failure surface, require a `librechat.yaml` restart to
register, and contradict a committed decision. If the file handoff ever
proves insufficient, that is the trigger to revisit — not now.

**Established directories (no duplicates):**
- `agent-workdir/tasks/` — Goose task files (existing, do not duplicate)
- `agent-workdir/outputs/` — Goose result files (existing, do not duplicate)

---

## 8. DIRECTORY CONVENTION

All new directories live under `~/agent-workdir/`. No existing directories
are renamed or restructured. No duplicate task/result directories are created.

```
~/agent-workdir/
├── traces/              ← NEW: structured trace log (one file per task execution)
│   ├── TRACE_<name>_<timestamp>.md
│   └── README.md
├── eval-suites/         ← NEW: test task sets for measuring skill/agent quality
│   ├── <skill-or-agent-name>/
│   │   ├── EVAL_TASK_01.md
│   │   ├── EVAL_TASK_02.md
│   │   └── BASELINE.md
│   └── README.md
├── validation-logs/     ← NEW: test results, diffs, pass/fail records
│   ├── VALIDATION_<change>_<timestamp>.md
│   └── README.md
├── staging-ai-context/ ← EXISTING: stages ai-context/ doc changes (git-promoted)
├── staging-librechat/   ← NEW: stages librechat.yaml + config changes (restart-promoted)
│   ├── librechat.yaml.staged
│   └── README.md
├── tasks/               ← EXISTING: Goose task files (do not duplicate)
├── outputs/             ← EXISTING: Goose result files (do not duplicate)
├── archive/             ← EXISTING
├── scripts/             ← EXISTING
└── prompts/             ← EXISTING
```

### 8.1 What each new directory holds

- **`traces/`** — Structured execution traces, one file per Goose task
  execution. Captures: task name, timestamp, skills invoked, model used,
  routing path, exit test results, token counts. This is the data source for
  bottom-up improvement (§5.3).

- **`eval-suites/`** — Test task sets, one subdirectory per skill or agent.
  Each contains `EVAL_TASK_*.md` files and a `BASELINE.md` with the
  established pass-rate. Without these, there is no measurement (§9).

- **`validation-logs/`** — Test results from eval-suite runs. One file per
  validation pass: the diff, the pass-rate before and after, the
  keep-or-revert decision. This is the audit trail.

- **`staging-librechat/`** — Staged `librechat.yaml` and config changes that
  require restart. Mirrors the existing `staging-ai-context/` naming
  convention. Promoted by human/Goose via `docker compose restart api`.

### 8.2 Directories NOT created (and why)

| Directory | Why not |
|---|---|
| `improvements/` | Redundant with `staging-ai-context/` + `staging-librechat/`. Staging dirs already hold proposed changes. |
| `promoted/` | Redundant. Promoted changes go to their real destination (`ai-context/` via git, `librechat.yaml` via restart). A `promoted/` dir is just a second copy. |
| `goose-tasks/` + `goose-outputs/` | Exact duplicates of existing `tasks/` + `outputs/`. |
| `mcp-registry/` | The canonical MCP server list already lives at `ai-context/mcp/mcp-servers.json`. Stage changes to that file, not a fork. |
| `skills-staging/` (inside `ai-context/`) | Skill changes stage in `staging-ai-context/skills/`, consistent with the existing staging convention. No separate dir needed. |

---

## 9. MEASUREMENT — EVAL SUITES + AUTO-REVERT

Without measurement, "self-improvement" is just "self-change." The system
has no way to know if a change actually improved anything. The eval-suite
mechanism is the work item here, not speculative complexity.

### 9.1 Eval suite structure

Each skill or agent that is in scope for improvement has an eval suite in
`eval-suites/<name>/`:

```
eval-suites/session-close/
├── EVAL_TASK_01.md    ← a test task that exercises the skill
├── EVAL_TASK_02.md    ← another test task
├── EVAL_TASK_03.md
└── BASELINE.md        ← established pass-rate (e.g., "3/3 pass, avg quality 4.2/5")
```

### 9.2 Measurement cycle

1. **Before the change:** Run the eval suite against the current skill/agent.
   Record the pass-rate in `BASELINE.md`.
2. **Apply the change** to staging.
3. **After the change:** Run the eval suite against the staged version.
   Record the pass-rate in `validation-logs/`.
4. **Compare:** If pass-rate ≥ baseline, the change is a candidate for
   promotion. If pass-rate < baseline, auto-revert fires.

### 9.3 Auto-revert threshold

**Default threshold: any drop in pass-rate triggers auto-revert.**

If the baseline is 3/3 and the post-change result is 2/3, the change is
reverted automatically — no human intervention needed. The validation log
records the revert and the reason.

This is especially important for the mobile/Tailscale use case: Michael
might approve a change from his phone, not be at the machine to notice it's
degraded, and the system should protect itself.

### 9.4 Minimum eval suites for v1

Start with the highest-usage, lowest-risk targets:

| Target | Why first | Risk |
|---|---|---|
| `session-close` | Used every session | Low — no tools, no routing |
| `clinical-writing` (seddon-family-law-drafter) | Highest-stakes output | Low — no tools, routing already locked |
| `workplace-law-research` | Research agent, measurable quality | Low — tools already scoped |

Expand after the loop is proven on these three.

---

## 10. NEW SKILLS

Two new skills support the improvement loop:

### 10.1 `trace-capture` skill

**Location:** `ai-context/skills/trace-capture/SKILL.md`

**Purpose:** After any Goose task completes, LibreChat (or Goose) writes a
structured trace file to `~/agent-workdir/traces/`. The trace captures:
- Task name and timestamp
- Skill(s) invoked
- Model used and routing path
- Exit test results (pass/fail per criterion)
- Token counts (prompt, completion, total)
- Any anomalies or deviations

### 10.2 `skill-improver` skill

**Location:** `ai-context/skills/skill-improver/SKILL.md`

**Purpose:** Analyzes traces in `~/agent-workdir/traces/` for patterns —
recurring failures, quality regressions, routing anomalies. When a pattern is
found, drafts a proposed change (a *change-delta* document) and an eval plan,
then presents both for human review.

**Safety constraints (encoded in the skill itself):**
- Must check every proposed change against the 4-level classification (§3)
- Must reject any change that touches a Level 4 invariant
- Must include an eval plan with every proposal
- Must not propose changes to itself or to this protocol
- Must cite the traces that motivated the proposal

---

## 11. CHANGE-DELTA FORMAT

When the `skill-improver` (or a top-down user request) proposes a change, it
produces a change-delta document in `staging-ai-context/` or
`staging-librechat/`:

```markdown
# CHANGE DELTA: <target> — <short description>

**Date:** <timestamp>
**Proposed by:** LibreChat (bottom-up trace analysis | top-down user request)
**Target:** <skill name / agent name / config file>
**Change level:** 1 (wording) | 2 (process) | 3 (scope)
**Change path:** dynamic (API PATCH) | staged (git commit) | staged (restart)

## Motivation
<What traces or user request motivated this? Cite specific trace files.>

## Proposed change
<The actual diff — before/after, or the new content.>

## Eval plan
<Which eval suite will measure this? What is the baseline pass-rate?>
<What is the auto-revert threshold?>

## Safety check
- [ ] Does not touch a Level 4 invariant (§3.2)
- [ ] Does not modify the improver itself
- [ ] Does not contradict a GOTCHAS entry
- [ ] Does not introduce credentials or secrets
```

---

## 12. OPEN QUESTIONS

1. **Trace storage location:** Should traces live inside the `ai-context`
   repo (version-controlled, visible in git history) or outside it (in
   `agent-workdir/`, not git-tracked)? Recommendation: outside, in
   `agent-workdir/traces/` — traces are operational data, not build
   artifacts. They accumulate fast and would bloat the repo.

2. **Eval-suite ownership:** Should eval suites live in `ai-context/`
   (version-controlled, part of the build) or in `agent-workdir/`? 
   Recommendation: in `ai-context/eval-suites/` — they are part of the
   build's safety architecture and should be version-controlled. The
   `agent-workdir/eval-suites/` path in §8 is the working copy; the
   canonical copy is in `ai-context/`.

3. **Cost monitoring:** How should eval-run costs be tracked? The trace
   format has token counts, but LibreChat's model accounting may not expose
   per-request cost. Recommendation: use DeepInfra's pricing API to estimate,
   log the estimate in the trace, cap at $0.50 per cycle.

4. **Dynamic-change rollback:** For dynamic changes (applied via API PATCH
   or admin panel, no restart), how is rollback handled? Git revert doesn't
   apply — the change was applied live. Recommendation: the change-delta
   document records the before-state (the old instruction/config), and
   rollback is an API PATCH that restores it. The validation log records
   both the change and the rollback.

---

## 13. SUCCESS CRITERIA

The self-improvement loop is "done" when:

- [ ] Every Goose task execution produces a trace file in `traces/`
- [ ] At least 3 skills/agents have eval suites with established baselines
- [ ] The `skill-improver` can analyze traces and produce well-formed
      change-delta proposals
- [ ] One real improvement has been proposed, reviewed, applied, measured,
      and either promoted (with git commit or API PATCH) or reverted (with
      reason)
- [ ] The improvement is visible in `BUILD_STATE.md` and the target's git
      history
- [ ] This protocol document is committed to `ai-context/docs/`
- [ ] The loop has been run at least once without human intervention *between
      steps 1–3 and 5–7* (human only intervenes at step 4 — the checkpoint)

---

## 14. REFERENCES

- Self-improving AI agents overview — behavioral snapshot log, rollback
  mechanism, human checkpoint trigger \ue202turn0search0
- Loop Engineering — four nested control loops for self-improving agents \ue202turn0search1
- LibreChat Agent Skills (v0.8.6-rc1) — SKILL.md bundles, ACLs, scoping \ue202turn1search1
- LibreChat Skills documentation — model-invoked, import, sync \ue202turn1search2
- Self-modifying agent safety — separate modification from execution, version
  control everything, validate against safety invariants \ue202turn2search1
- Self-modifying agent horizon — evaluation harness as the self-modification
  objective \ue202turn2search0
- Bounded self-modification — four-level change classification \ue202turn2search2
- LibreChat v0.8.7 changelog — admin panel per-role/group config, MCP allowlist
  without restart, agent skill authoring
- LibreChat MCP documentation — MCP server registration \ue202turn1search1
- LibreChat `librechat.yaml` documentation — restart-required config changes

---

## 15. RECONCILIATION NOTES

This document merges two prior plans:

1. **`~/agent-workdir/SELF_IMPROVEMENT_LOOP_BUILD_PLAN.md`** (v1, 13 Aug
   2026) — skill-focused, 4-level change classification, eval suites,
   auto-revert, SI-1…SI-5 phase structure. Contributed: the safety
   architecture (§3), the measurement system (§9), the separation-of-roles
   principle (§6), the bottom-up trace-analysis trigger (§5.3), and the
   literature references (§14).

2. **User's pasted "Self-Improving Build Plan — Mapped onto Existing
   LibreChat Build"** (v1.0, 13 Aug 2026) — whole-system scope, v0.8.7
   capability findings, dynamic-vs-staged classification, Goose MCP server
   proposal, Phase 10A/10B/10C structure. Contributed: the whole-system
   scope (§2), the v0.8.7 capability map (§4), the dynamic-vs-staged change
   paths (§4.3), and the `staging-librechat/` directory (§8).

**Dropped from the merge (no meaningful improvement):**
- Goose MCP server (§7 — file handoff already does everything; reopens a
  committed decision)
- `goose-tasks/` + `goose-outputs/` directories (duplicates of existing
  `tasks/` + `outputs/`)
- `admin-panel-client/config-override.js` (speculative helper for an API
  flow that doesn't exist yet)
- Phase 10A/10B/10C formal phase structure (build is past formal phases;
  self-improvement is operational hardening, same category as Backup
  Automation and Restore Drill)
- SI-1…SI-5 formal phase structure (same reasoning)
- Mobile/Tailscale workflow diagram (Tailscale already live, Phase 9a PASSED)
- `mcp-registry/` directory (canonical list already at
  `ai-context/mcp/mcp-servers.json`)
- `improvements/` directory (redundant with staging dirs)
- `promoted/` directory (redundant — promoted changes go to their real
  destination)

---

*End of protocol. Staged at
`agent-workdir/staging-ai-context/docs/SELF_IMPROVEMENT_PROTOCOL.md` —
awaiting commit to `ai-context/docs/`.*
