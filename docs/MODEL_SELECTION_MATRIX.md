# Model Selection Matrix for the Build Coordinator

**Created:** 26 August 2026
**Purpose:** Defines which model the Build Coordinator should recommend at the end of each response, based on the next task in the build sequence. Preferences budget inference models; reserves frontier models for tasks that strictly require them.

**Source of truth for model availability:** `librechat.yaml` modelSpecs (20 models, all via DeepInfra endpoint).

---

## Pricing tiers (per 1M input/output tokens)

### Budget tier (default — use unless a reason below escalates)

| Model ID (librechat.yaml) | Label | In/Out per 1M | Cached in | Strength |
|---|---|---|---|---|
| `openai/gpt-oss-120b` | GPT-OSS 120B | $0.037/$0.17 | — | Cheapest; surprisingly strong reasoning & agentic for the price |
| `inclusionAI/Ling-3.0-flash` | Ling 3.0 Flash | $0.06/$0.18 | — | Token-efficient agentic flash; high-volume loops |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning` | Nemotron 3.5 Lightning | $0.08/$0.20 | — | Low-latency always-on agent model |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | DeepSeek V4 Flash 0731 | $0.08/$0.18 | $0.016 | **Build Coordinator default** — daily drafting, planning, memory agent |
| `deepseek-ai/DeepSeek-V4-Flash` | DeepSeek V4 Flash (Cheap) | $0.09/$0.18 | $0.018 | Bulk classification, extraction, ETL pipelines |
| `google/gemma-4-31B-it-turbo` | Gemma 4 31B Turbo | $0.09/$0.34 | — | Cheap multimodal (text+image), quick vision tasks |
| `Qwen/Qwen3.5-35B-A3B` | Qwen3.5 35B | $0.14/$1.00 | $0.05 | Everyday drafting, summaries, light reasoning |

### Value tier (use when budget model isn't enough)

| Model ID | Label | In/Out per 1M | Cached in | Strength |
|---|---|---|---|---|
| `deepseek-ai/DeepSeek-V3.2` | DeepSeek V3.2 | $0.26/$0.38 | $0.13 | Best general-purpose value; solid all-rounder, agentic tool use |
| `Qwen/Qwen3.5-122B-A10B` | Qwen3.5 122B | $0.29/$2.40 | — | Near-frontier MoE; complex analysis, long technical writing |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo` | Qwen3 Coder 480B | $0.30/$1.00 | $0.10 | **Best value coder** — code gen, review, refactoring, agentic code tasks |
| `MiniMaxAI/MiniMax-M3` | MiniMax M3 | $0.28/$1.10 | $0.056 | Best value multimodal (text/image/video), 1M context |
| `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | $0.25/$1.50 | — | Huge 1M context at low cost; bulk doc ingestion, extraction pipelines |
| `moonshotai/Kimi-K2.5` | Kimi K2.5 | $0.45/$2.25 | $0.07 | Strong general reasoning, vision; capable cheaper flagship alternative |
| `zai-org/GLM-5.2` | GLM 5.2 | $0.75/$2.40 | $0.14 | All-round value ceiling; long-context reasoning, structured output |

### Flagship tier (reserve for strictly necessary cases only)

| Model ID | Label | In/Out per 1M | Strength |
|---|---|---|---|
| `deepseek-ai/DeepSeek-V4-Pro-0813` | DeepSeek V4 Pro 0813 | $1.30/$2.60 | Near-frontier reasoning, math, deep technical analysis at a fraction of Claude cost |
| `anthropic/claude-sonnet-5` | Claude Sonnet 5 | $2.00/$10.00 | **Clinical/legal writing [SENSITIVE]** — required routing; excellent prose |
| `moonshotai/Kimi-K3` | Kimi K3 | $2.85/$14.25 | 2.8T params, long-horizon reasoning, big-context analysis |
| `anthropic/claude-opus-5` | Claude Opus 5 | $5.00/$25.00 | **Highest cost** — ultimate capability, final review of critical work only |

---

## Task-type → Model mapping

### Default (Build Coordinator routine work)
- **Model:** `deepseek-ai/DeepSeek-V4-Flash-0731` (DeepSeek V4 Flash 0731)
- **Why:** $0.08/$0.18 — the Build Coordinator's existing agent model. Fast, cheap, good enough for planning, session opening, task staging, state updates, verification of result files.

### Architecture / Design / Deep technical analysis
- **Model:** `deepseek-ai/DeepSeek-V4-Pro-0813` (DeepSeek V4 Pro 0813)
- **Why:** $1.30/$2.60 — near-frontier reasoning at a fraction of Claude Opus cost. Use for complex schema design, adapter contracts, acceptance criteria, multi-step architecture decisions. Escalate here from the budget default only when the task genuinely needs deeper reasoning.

### Code generation / review / refactoring
- **Model:** `Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo` (Qwen3 Coder 480B)
- **Why:** $0.30/$1.00 — best value coder. Use for writing Python scripts (adapter, ingestion bridge, indexer), Docker compose edits, shell scripts, code review of Goose's output.

### Safety / security review / acceptance gate assessment
- **Model:** `deepseek-ai/DeepSeek-V4-Pro-0813` (DeepSeek V4 Pro 0813)
- **Why:** Deep reasoning needed for cross-subject leakage checks, supersession verification, OCR quality gating, not-found threshold validation. Cheaper than Claude and sufficient for the technical review. Only escalate to Claude if the review involves clinical/household [SENSITIVE] content.

### Clinical / household [SENSITIVE] content
- **Model:** `anthropic/claude-sonnet-5` (Claude Sonnet 5)
- **Why:** $2.00/$10.00 — **required routing** per hard rules. Clinical, family-law, household identity content must route via Anthropic direct, never OpenRouter or logging-enabled paths. Use for clinical note drafting, CASP4 formulations, sensitive client-facing writing.

### Documentation / synthesis / state updates
- **Model:** `deepseek-ai/DeepSeek-V4-Flash-0731` (DeepSeek V4 Flash 0731)
- **Why:** Budget tier is sufficient for BUILD_STATE updates, HANDOFF docs, session event logs, task file staging. These are structured writing tasks that don't need frontier reasoning.

### Bulk / pipeline / ETL tasks
- **Model:** `deepseek-ai/DeepSeek-V4-Flash` (DeepSeek V4 Flash Cheap) or `openai/gpt-oss-120b` (GPT-OSS 120B)
- **Why:** Cheapest options ($0.09/$0.18 and $0.037/$0.17). Use for classification, extraction, batch processing — tasks where token throughput matters more than depth.

### Long-context / big-document analysis
- **Model:** `zai-org/GLM-5.2` (GLM 5.2) or `google/gemini-3.1-flash-lite` (Gemini 3.1 Flash Lite)
- **Why:** Both have 1M context. GLM 5.2 ($0.75/$2.40) for complex multi-step reasoning over large docs; Gemini 3.1 Flash Lite ($0.25/$1.50) for bulk ingestion/summarisation at lower cost.

### Final critical review (rare — only when stakes are highest)
- **Model:** `anthropic/claude-opus-5` (Claude Opus 5)
- **Why:** $5.00/$25.00 — reserve for the hardest problems, deepest research, final review of safety-critical work. Use sparingly; the budget and value tiers cover 95%+ of build tasks.

---

## Escalation ladder (cost-aware)

```text
Default:     DeepSeek V4 Flash 0731       ($0.08/$0.18)
  ↓ (needs deeper reasoning)
Reasoning:   DeepSeek V4 Pro 0813          ($1.30/$2.60)
  ↓ (needs code focus)
Code:        Qwen3 Coder 480B              ($0.30/$1.00)
  ↓ (needs SENSITIVE routing)
Clinical:    Claude Sonnet 5               ($2.00/$10.00)
  ↓ (absolute highest stakes only)
Critical:    Claude Opus 5                 ($5.00/$25.00)
```

**Rule:** Always recommend the cheapest model that can do the job well. Escalate one rung at a time. Never jump to Claude Opus 5 unless every cheaper option has been considered and rejected with a stated reason.

---

## Implementation recommendation

### Where to put this

1. **`docs/MODEL_SELECTION_MATRIX.md`** (this file) — the reference doc, committed to `ai-context/docs/`. This is the single source of truth for model-to-task mapping.

2. **`AGENT_BOOTSTRAP.md`** — add a new section §7 referencing this doc and defining the model recommendation practice:

```markdown
## 7. MODEL RECOMMENDATION PRACTICE

At the end of **every response**, the Build Coordinator must include a model
recommendation line for the next task in the build sequence:

    **Recommended model for next step:** [model label] — [one-line rationale]

Guidance: see `docs/MODEL_SELECTION_MATRIX.md` for the full task-type → model
mapping. Prefer budget-tier models (DeepSeek V4 Flash 0731 is the default).
Escalate to value/flagship tiers only when the task type requires it, and
never skip the escalation ladder. Clinical/household [SENSITIVE] content
must always recommend Claude Sonnet 5 (required routing).
```

3. **`prompts/GOOSE_TASK_TEMPLATE.md`** — add an optional field at the end:

```markdown
## Recommended model (optional)
[Model label and ID from MODEL_SELECTION_MATRIX.md — for Michael to select
in LibreChat before executing the next step. Leave blank if same as
current.]
```

4. **Build Coordinator system prompt** (in LibreChat agent definition / MongoDB) — add the same instruction: "End every response with a recommended model for the next step, per MODEL_SELECTION_MATRIX.md."

### How it works in practice

At the end of each Build Coordinator response, you'll see a line like:

> **Recommended model for next step:** Qwen3 Coder 480B — T8 ingestion bridge script needs code generation; best value coder at $0.30/$1.00.

Or for routine work:

> **Recommended model for next step:** DeepSeek V4 Flash 0731 (current) — T9 parallel observation staging is documentation/planning; budget tier sufficient.

### Maintenance

- The matrix should be reviewed when models are added/removed from `librechat.yaml`.
- The pricing in `librechat.yaml` modelSpecs descriptions is the authoritative source — if DeepInfra changes pricing, update the matrix to match.
- The `references/CURRENT_METHODS.md` staleness check (3 months) in the agent-builder skill should also trigger a matrix review.

---

*End of Model Selection Matrix.*
