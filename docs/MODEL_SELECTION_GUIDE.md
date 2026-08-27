# Model Selection Guide — Backup AI System

**Created:** 27 August 2026
**Supersedes:** `MODEL_SELECTION_MATRIX.md` (26 Aug 2026 — listed 20 models; now 30 available)
**Source of truth:** `/app/LibreChat/librechat.yaml` (version 1.3.13, live config)
**Catalog reference:** `deepinfra_live_models.md` (105 models, fetched 2026-08-27 07:16)

---

## 1. QUICK REFERENCE — WHICH MODEL FOR WHAT

Read this table first. It maps the task you're about to do to the cheapest model that can do it well. Escalate only when the recommended model's output isn't good enough.

| Task type | Primary model | $/1M out | Alt (cheaper) | Alt (stronger) | Notes |
|---|---|---|---|---|---|
| **Daily drafting / planning / state updates** | DeepSeek V4 Flash 0731 | $0.18 | GPT-OSS 120B ($0.17) | DeepSeek V3.2 ($0.38) | Agent default; 1M context, cached $0.016 |
| **Code generation / review / refactoring** | Qwen3 Coder 480B | $1.00 | Qwen3 235B Instruct ($0.55) | DeepSeek V4 Pro ($2.60) | Best value coder; agentic code tasks |
| **Architecture / deep technical analysis** | DeepSeek V4 Pro | $2.60 | Nemotron 3 Ultra 550B ($2.20) | Claude Sonnet 5 ($10.00) | Near-frontier reasoning; fraction of Claude cost |
| **Reasoning / math / logic** | DeepSeek R1 0528 | $2.15 | Tencent Hy3 ($0.58) | DeepSeek V4 Pro ($2.60) | Canonical thinking model; cached $0.35 |
| **Long-running agents / deep research** | Nemotron 3 Ultra 550B | $2.20 | Tencent Hy3 ($0.58) | DeepSeek V4 Pro ($2.60) | 550B MoE, 262K ctx; designed for agent loops |
| **Long-context doc analysis (text)** | GLM 5.2 | $2.40 | Gemini 3.1 Flash Lite ($1.50) | Kimi K3 ($14.25) | 1M context, multi-step reasoning; cached $0.14 |
| **Long-context doc analysis (structured output)** | Inkling Small | $1.20 | Qwen3 235B Instruct ($0.55) | GLM 5.2 ($2.40) | 524K ctx, tool calling + structured outputs |
| **Multimodal / vision (images)** | Llama 4 Maverick | $0.80 | Qwen3.5 35B ($1.00) | MiniMax M3 ($1.10) | Open MoE, 1M ctx; cheapest serious vision |
| **Multimodal / video (up to 3h)** | Gemini 2.5 Flash | $2.50 | MiniMax M3 ($1.10) | Kimi K3 ($14.25) | Native video understanding; 1M ctx |
| **Multimodal / general (text+image+video)** | MiniMax M3 | $1.10 | Llama 4 Maverick ($0.80) | Gemini 2.5 Flash ($2.50) | Best value all-round multimodal; 1M ctx |
| **Bulk / ETL / classification / extraction** | DeepSeek V4 Flash (Cheap) | $0.18 | GPT-OSS 120B ($0.17) | DeepSeek V3.2 ($0.38) | High-volume token throughput |
| **General-purpose chat (non-build)** | DeepSeek V3.2 | $0.38 | DeepSeek V4 Flash 0731 ($0.18) | Qwen3 235B Instruct ($0.55) | Best all-round value; agentic tool use |
| **Frontier general (competes with R1/o3-mini)** | Qwen3 235B Instruct | $0.55 | Tencent Hy3 ($0.58) | DeepSeek V4 Pro ($2.60) | 235B MoE; coding+math at budget price |
| **Cost-effective reasoning agent** | Tencent Hy3 | $0.58 | Qwen3 235B Instruct ($0.55) | Nemotron 3 Ultra 550B ($2.20) | 295B MoE (21B active); reasoning+agent; cached $0.035 |
| **Agentic knowledge work** | Kimi K2.5 | $2.25 | Seed 1.8 ($2.00) | Kimi K3 ($14.25) | Strong general reasoning + vision |
| **Clinical / household [SENSITIVE]** | Claude Sonnet 5 | $10.00 | — | Claude Opus 5 ($25.00) | **Required routing** — Anthropic direct, never OpenRouter |
| **Final critical review (rare)** | Claude Opus 5 | $25.00 | Claude Sonnet 5 ($10.00) | — | Highest stakes only; 95%+ of tasks never reach here |
| **Conversation title generation** | DeepSeek V4 Flash 0731 | $0.18 | — | — | Already set as `titleModel`; don't change |
| **Speech-to-text** | Whisper Large v3 Turbo | (STT rate) | — | — | Already configured; not an LLM selection |

---

## 2. GOVERNING PRINCIPLES

### Rule 1: Cheapest model that can do the job well
Always start at the cheapest tier. Only escalate when you've tried the recommendation and its output is insufficient for the task. "Sufficient" means: correct, complete, and usable without significant rework.

### Rule 2: Escalate one rung at a time
Never skip from the budget default to Claude Opus 5. Move up the escalation ladder (§5) one step at a time. If a mid-tier model fails, try the next one — don't jump to the top.

### Rule 3: [SENSITIVE] routing is mandatory
Clinical, household-identity, family-law, and legal content **must** route through Claude Sonnet 5 (or Claude Opus 5 for the highest-stakes subset). This is a hard rule from `AGENT_BOOTSTRAP.md` §4. Never send [SENSITIVE] content through DeepSeek, Qwen, or any non-Anthropic path. See §6.1.

### Rule 4: Cached input is your friend
Models with cached-input pricing (DeepSeek family, Tencent Hy3, Nemotron, GLM, Kimi, Qwen3 Coder, Inkling, Seed) are dramatically cheaper for multi-turn conversations and agent loops that resend the same context. If your task involves repeated context (system prompt + history), prefer a model with cache pricing. The cache discount ranges from 5× (DeepSeek V4 Flash: $0.016 vs $0.08) to 13× (DeepSeek V4 Flash Cheap: $0.018 vs $0.09).

### Rule 5: Output cost dominates
Output tokens are typically 2–5× more expensive than input tokens. When estimating cost, focus on how much the model will *write*, not how much it reads. A model that's cheap on input but expensive on output (e.g., Qwen3.5 35B at $0.14 in / $1.00 out) can cost more than a model with balanced pricing (e.g., DeepSeek V3.2 at $0.26 in / $0.38 out) for generation-heavy tasks.

### Rule 6: Context window matters for large inputs
If your task involves a large document (>128K tokens), you need a model with a large context window. The 1M-context models (DeepSeek V4 Flash 0731, Gemini 2.5 Flash, Llama 4 Maverick, Seed 1.8, GLM 5.2, MiniMax M3, Gemini 3.1 Flash Lite) can ingest entire documents. Models with 164K–524K (DeepSeek R1, Nemotron 3 Ultra, Qwen3 235B, Tencent Hy3, Inkling Small) handle large chapters but not whole books.

### Rule 7: Vision requires a 👁️ model
If your task involves images, screenshots, or video, you must select a model with vision capability (marked 👁️ in the dropdown). Non-vision models will reject image inputs. See §6.2.

---

## 3. FULL MODEL INVENTORY

All 30 models available via the DeepInfra endpoint, sorted by output cost (cheapest first). **D** = appears in LibreChat dropdown (`modelSpecs`). **A** = in endpoint allowlist (`models.default`). Both = usable from UI. A-only = available programmatically (agent, titleModel) but not in dropdown. D-only = in dropdown but not allowlisted (may not function — see §7).

### Tier 0 — Ultra-cheap (out < $0.10/1M)

| # | Model ID | Label | In | Out | Cache | Ctx | 👁️ | D | A | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | Llama 3.1 8B | $0.02 | $0.04 | — | std | No | ✅ | ⚠️ | Dirt-cheap bulk classification; token-level tasks |
| 2 | `openai/gpt-oss-20b` | GPT-OSS 20B | $0.03 | $0.14 | — | std | No | ✅ | ⚠️ | Quick tiny tasks at very low cost |
| 3 | `openai/gpt-oss-120b` | GPT-OSS 120B | $0.037 | $0.17 | — | std | No | ❌ | ✅ | Cheapest *capable* model; surprisingly strong reasoning |

### Tier 1 — Budget / workhorse (out $0.10–$0.20/1M)

| # | Model ID | Label | In | Out | Cache | Ctx | 👁️ | D | A | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | `deepseek-ai/DeepSeek-V4-Flash-0731` | DeepSeek V4 Flash 0731 | $0.08 | $0.18 | $0.016 | 1M | No | ✅ | ✅ | **Agent default** — daily drafting, loops, memory agent |
| 5 | `inclusionAI/Ling-3.0-flash` | Ling 3.0 Flash | $0.06 | $0.18 | — | std | No | ❌ | ✅ | Token-efficient agentic flash; high-volume loops |
| 6 | `deepseek-ai/DeepSeek-V4-Flash` | DeepSeek V4 Flash (Cheap) | $0.09 | $0.18 | $0.018 | std | No | ✅ | ✅ | Bulk tasks — classification, extraction, pipelines |
| 7 | `nvidia/NVIDIA-Nemotron-3.5-Lightning` | Nemotron 3.5 Lightning | $0.08 | $0.20 | — | std | No | ❌ | ✅ | Low-latency always-on agent model |

### Tier 2 — Value (out $0.20–$0.60/1M)

| # | Model ID | Label | In | Out | Cache | Ctx | 👁️ | D | A | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | `zai-org/GLM-4.7-Flash` | GLM 4.7 Flash | $0.06 | $0.40 | $0.01 | std | No | ✅ | ✅ | Fast cheap GLM — lightweight tasks, summarisation |
| 9 | `google/gemma-4-31B-it-turbo` | Gemma 4 31B Turbo | $0.09 | $0.34 | — | std | Yes | ❌ | ✅ | Cheap multimodal (text+image); quick vision tasks |
| 10 | `Qwen/Qwen3-235B-A22B-Instruct-2507` | Qwen3 235B Instruct | $0.09 | $0.55 | — | 256K | No | ✅ | ✅ | Flagship Qwen MoE; coding+math at budget price |
| 11 | `tencent/Hy3` | Tencent Hy3 | $0.14 | $0.58 | $0.035 | 256K | No | ✅ | ✅ | Cost-effective reasoning+agent; 295B MoE (21B active) |
| 12 | `deepseek-ai/DeepSeek-V3.2` | DeepSeek V3.2 | $0.26 | $0.38 | $0.13 | std | No | ✅ | ✅ | Best general-purpose value; solid all-rounder |

### Tier 3 — Mid-value (out $0.60–$1.20/1M)

| # | Model ID | Label | In | Out | Cache | Ctx | 👁️ | D | A | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| 13 | `Qwen/Qwen3.5-35B-A3B` | Qwen3.5 35B | $0.14 | $1.00 | $0.05 | std | Yes | ✅ | ✅ | Solid mid-size; drafting, everyday tasks, light vision |
| 14 | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` | Llama 4 Maverick | $0.20 | $0.80 | — | 1M | Yes | ✅ | ✅ | Open multimodal MoE; cheapest serious vision with 1M ctx |
| 15 | `Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo` | Qwen3 Coder 480B | $0.30 | $1.00 | $0.10 | std | No | ✅ | ✅ | **Best value coder** — code gen, review, refactoring |
| 16 | `MiniMaxAI/MiniMax-M3` | MiniMax M3 | $0.28 | $1.10 | $0.056 | 1M | Yes | ✅ | ✅ | Best value multimodal (text/image/video); 1M ctx |
| 17 | `thinkingmachines/Inkling-Small` | Inkling Small | $0.45 | $1.20 | $0.10 | 524K | No | ✅ | ✅ | Long-doc agents; tool calling + structured outputs |

### Tier 4 — Premium value (out $1.20–$2.60/1M)

| # | Model ID | Label | In | Out | Cache | Ctx | 👁️ | D | A | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| 18 | `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | $0.25 | $1.50 | — | 1M | No | ❌ | ✅ | Huge 1M ctx at low cost; bulk doc ingestion |
| 19 | `ByteDance/Seed-1.8` | Seed 1.8 | $0.25 | $2.00 | $0.05 | 1M | Yes | ✅ | ✅ | Agent+LLM+VLM blend; 1M ctx |
| 20 | `Qwen/Qwen3.5-122B-A10B` | Qwen3.5 122B | $0.29 | $2.40 | — | std | No | ❌ | ✅ | Near-frontier MoE; complex analysis, long technical writing |
| 21 | `moonshotai/Kimi-K2.5` | Kimi K2.5 | $0.45 | $2.25 | $0.07 | std | Yes | ✅ | ✅ | Strong general reasoning + vision; agentic knowledge work |
| 22 | `deepseek-ai/DeepSeek-R1-0528` | DeepSeek R1 0528 | $0.50 | $2.15 | $0.35 | 164K | No | ✅ | ✅ | Canonical reasoning/thinking model; math, logic, research |
| 23 | `nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B` | Nemotron 3 Ultra 550B | $0.50 | $2.20 | $0.10 | 256K | No | ✅ | ✅ | Frontier 550B MoE; long-running agents & deep research |
| 24 | `google/gemini-2.5-flash` | Gemini 2.5 Flash | $0.30 | $2.50 | — | 1M | Yes | ✅ | ✅ | Native multimodal thinking; 1M ctx, up to 3h video |
| 25 | `zai-org/GLM-5.2` | GLM 5.2 | $0.75 | $2.40 | $0.14 | 1M | No | ✅ | ✅ | All-round value ceiling; long-context reasoning |
| 26 | `deepseek-ai/DeepSeek-V4-Pro` | DeepSeek V4 Pro | $1.30 | $2.60 | $0.10 | std | No | ✅ | ✅ | Best reasoning-per-dollar; research, complex analysis |
| 27 | `deepseek-ai/DeepSeek-V4-Pro-0813` | DeepSeek V4 Pro 0813 | $1.30 | $2.60 | — | std | No | ❌ | ✅ | Same price as Pro; newer build (allowlist only) |

### Tier 5 — Flagship (out > $2.60/1M)

| # | Model ID | Label | In | Out | Cache | Ctx | 👁️ | D | A | Best for |
|---|---|---|---|---|---|---|---|---|---|---|
| 28 | `anthropic/claude-sonnet-5` | Claude Sonnet 5 | $2.00 | $10.00 | — | std | Yes | ✅ | ✅ | **[SENSITIVE] required routing**; clinical, legal, excellent prose |
| 29 | `moonshotai/Kimi-K3` | Kimi K3 | $2.85 | $14.25 | $0.285 | std | Yes | ✅ | ✅ | 2.8T params; long-horizon reasoning, big-context analysis |
| 30 | `anthropic/claude-opus-5` | Claude Opus 5 | $5.00 | $25.00 | — | std | Yes | ✅ | ✅ | **Highest cost** — ultimate capability, final review only |

**Pricing key:** All prices per 1M tokens. "Cache" = cached input price (discount on repeated context). "Ctx" = max context window (1M = 1,048,576; 524K = 524,288; 256K = 262,144; 164K = 163,840; std = standard 128K or vendor-default). "std" where exact context wasn't in the config description — verify on DeepInfra model card before relying on it for >128K inputs.

---

## 4. TASK-TYPE DEEP DIVES

Each section below covers a task category: when to use it, which models to consider (cheapest first), and when to escalate.

### 4.1 Daily drafting / planning / state updates / session management

**Default:** DeepSeek V4 Flash 0731 ($0.08/$0.18, cached $0.016, 1M ctx)

This is the agent default model — already configured in `librechat.yaml` as `agent.model`. It handles:
- BUILD_STATE updates, session event log entries
- GOOSE_TASK file staging
- Result file verification (reading + checking exit test criteria)
- Planning and architecture framing
- Memory agent operations (storing preferences, tone, systems, people)
- Conversation title generation (it's also the `titleModel`)

**When to stay:** 95%+ of build coordination work. If the task is "read a file, think about it, write a structured document," this is the model.

**When to escalate:**
- If the model produces shallow or incomplete analysis → DeepSeek V3.2 ($0.26/$0.38) for stronger general reasoning
- If the task requires deep multi-step reasoning → DeepSeek V4 Pro ($1.30/$2.60)
- If the task involves [SENSITIVE] content → Claude Sonnet 5 ($2.00/$10.00)

**Cheaper alternative:** GPT-OSS 120B ($0.037/$0.17) for high-volume routine work where you're generating many short responses. Not in the dropdown but available programmatically.

### 4.2 Code generation / review / refactoring

**Primary:** Qwen3 Coder 480B ($0.30/$1.00, cached $0.10)

The best value coder on the endpoint. Use for:
- Writing Python scripts (adapters, ingestion bridges, indexers)
- Docker compose edits and shell scripts
- Code review of Goose's output
- Agentic code tasks (multi-file refactoring, test generation)

**Cheaper alternative:** Qwen3 235B Instruct ($0.09/$0.55) — competitive on coding benchmarks at roughly half the output cost. Good for simpler code tasks or when you're iterating rapidly and cost matters.

**When to escalate:**
- Complex architecture decisions embedded in code → DeepSeek V4 Pro ($1.30/$2.60)
- Code review touching [SENSITIVE] data paths → Claude Sonnet 5 ($2.00/$10.00)
- Final critical review of safety-critical code → Claude Opus 5 ($5.00/$25.00)

### 4.3 Architecture / deep technical analysis

**Primary:** DeepSeek V4 Pro ($1.30/$2.60, cached $0.10)

Near-frontier reasoning at a fraction of Claude cost. Use for:
- Complex schema design, adapter contracts, API contracts
- Multi-step architecture decisions
- Acceptance criteria and exit-test design
- Deep technical analysis where correctness matters more than cost

**Cheaper alternative:** Nemotron 3 Ultra 550B ($0.50/$2.20) — frontier 550B MoE designed for long-running agents and deep research. Similar reasoning depth, slightly cheaper on output.

**Another option:** Qwen3 235B Instruct ($0.09/$0.55) — competitive with R1/o3-mini on coding/math at a fraction of the cost. Try this first for analytical tasks that don't need frontier-level reasoning.

**When to escalate:**
- If the analysis involves [SENSITIVE] content → Claude Sonnet 5 ($2.00/$10.00)
- If stakes are existential (irreversible infrastructure decisions, safety-critical design) → Claude Opus 5 ($5.00/$25.00)

### 4.4 Reasoning / math / logic

**Primary:** DeepSeek R1 0528 ($0.50/$2.15, cached $0.35)

The canonical reasoning/thinking model. Uses chain-of-thought before answering. Use for:
- Mathematical proofs and calculations
- Logical deduction and multi-step reasoning
- Research questions requiring systematic analysis

**Cheaper alternative:** Tencent Hy3 ($0.14/$0.58, cached $0.035) — cost-effective reasoning+agent model. 295B MoE with 21B active parameters. Try this first for reasoning tasks; escalate to R1 only if Hy3's output isn't rigorous enough.

**Another option:** Qwen3 235B Instruct ($0.09/$0.55) — competitive on math benchmarks at similar cost to Hy3 but without explicit chain-of-thought.

**When to escalate:**
- If the problem requires frontier-level reasoning → DeepSeek V4 Pro ($1.30/$2.60)
- If it's a research-grade problem with high stakes → Claude Opus 5 ($5.00/$25.00)

### 4.5 Long-running agents / deep research

**Primary:** Nemotron 3 Ultra 550B ($0.50/$2.20, cached $0.10)

Frontier 550B MoE specifically designed for long-running agent loops and deep research. Use for:
- Multi-step research with tool calling
- Agent workflows requiring sustained reasoning over many turns
- Tasks where the agent needs to plan, execute, observe, and adapt

**Cheaper alternative:** Tencent Hy3 ($0.14/$0.58, cached $0.035) — also designed for agent loops, much cheaper. Try first for agent tasks; escalate to Nemotron if the agent loses coherence over long horizons.

**When to escalate:**
- If the agent task needs frontier reasoning at each step → DeepSeek V4 Pro ($1.30/$2.60)
- If the task is a deep-research web search → use the searxng-search MCP tool with DeepSeek V4 Flash 0731 as the orchestrating model (cheapest capable model with 1M context for absorbing search results)

### 4.6 Long-context document analysis

**Primary (text):** GLM 5.2 ($0.75/$2.40, cached $0.14, 1M ctx)

Strong reasoning over large documents with 1M context. Use for:
- Analysing entire codebases or large specifications
- Multi-step reasoning over long technical documents
- Cross-referencing information across many files

**Primary (structured output):** Inkling Small ($0.45/$1.20, cached $0.10, 524K ctx)

Designed for long-doc agents with tool calling and structured outputs. Use for:
- Extracting structured data from long documents (JSON, tables)
- Multi-step extraction pipelines over large texts
- Agent workflows that need reliable structured output

**Cheaper alternative:** Gemini 3.1 Flash Lite ($0.25/$1.50, 1M ctx) — huge context at lower cost, but allowlist-only (not in dropdown). Good for bulk ingestion and summarisation where reasoning depth matters less than context size.

**Cheaper still:** DeepSeek V4 Flash 0731 ($0.08/$0.18, 1M ctx) — if the document fits in 1M context and the analysis is straightforward (summarisation, key-point extraction), the budget default can handle it. Escalate to GLM 5.2 only when the analysis requires deep multi-step reasoning.

**When to escalate:**
- If you need the absolute best long-context reasoning → Kimi K3 ($2.85/$14.25) — 2.8T params, designed for big-context analysis
- If the document contains [SENSITIVE] content → Claude Sonnet 5 ($2.00/$10.00)

### 4.7 Multimodal / vision

**Primary (images, cheapest):** Llama 4 Maverick ($0.20/$0.80, 1M ctx) — open multimodal MoE. Cheapest serious vision model with large context.

**Primary (all-round multimodal):** MiniMax M3 ($0.28/$1.10, cached $0.056, 1M ctx) — text/image/video, best value all-round multimodal.

**Primary (video, up to 3h):** Gemini 2.5 Flash ($0.30/$2.50, 1M ctx) — native multimodal thinking model with video understanding.

**Primary (light vision):** Qwen3.5 35B ($0.14/$1.00, cached $0.05) — solid mid-size with vision. Good for quick image tasks.

**Cheapest vision (allowlist only):** Gemma 4 31B Turbo ($0.09/$0.34) — cheap multimodal for quick vision tasks. Not in dropdown.

**When to escalate:**
- If vision task requires deep reasoning about image content → Kimi K2.5 ($0.45/$2.25) — strong general reasoning + vision
- If vision task involves [SENSITIVE] content (e.g., clinical images) → Claude Sonnet 5 ($2.00/$10.00) — vision-capable + required routing
- If stakes are highest → Claude Opus 5 ($5.00/$25.00) — vision-capable + ultimate capability

### 4.8 Bulk / ETL / classification / extraction

**Primary:** DeepSeek V4 Flash (Cheap) ($0.09/$0.18, cached $0.018)

Designed for bulk tasks. Use for:
- Classification of large document sets
- Extraction pipelines (entity extraction, field mapping)
- Batch processing where token throughput matters more than depth

**Cheaper alternative:** GPT-OSS 120B ($0.037/$0.17) — cheapest capable model. Not in dropdown but available programmatically (e.g., via agent endpoint). Use for high-volume batch jobs.

**Cheapest option (dropdown):** GPT-OSS 20B ($0.03/$0.14) — tiny but capable. Note: not in endpoint allowlist — may not function. Llama 3.1 8B ($0.02/$0.04) — dirt cheap, same caveat.

**When to escalate:**
- If extraction requires understanding document structure → Inkling Small ($0.45/$1.20) — designed for structured output
- If classification requires reasoning → Qwen3 235B Instruct ($0.09/$0.55) — strong reasoning at low cost

### 4.9 General-purpose chat (non-build)

**Primary:** DeepSeek V3.2 ($0.26/$0.38, cached $0.13)

Best general-purpose value — strong, cheap, reliable. Use for:
- General Q&A that isn't build coordination
- Agentic tool use outside the build context
- Tasks needing more capability than V4 Flash but not frontier-level

**Cheaper:** DeepSeek V4 Flash 0731 ($0.08/$0.18) — if the task is simple enough, the budget default is fine.

**Stronger:** Qwen3 235B Instruct ($0.09/$0.55) — near-frontier MoE at budget price. Try for tasks where V3.2's output isn't sophisticated enough.

### 4.10 Clinical / household [SENSITIVE] content

**Primary:** Claude Sonnet 5 ($2.00/$10.00, vision-capable)

**Mandatory routing** per `AGENT_BOOTSTRAP.md` §4. All clinical, household-identity, family-law, and legal content must route through Anthropic direct (never OpenRouter or logging-enabled paths). Use for:
- Clinical note drafting, CASP4 formulations
- Sensitive client-facing writing
- Family law document drafting
- Any content tagged [SENSITIVE]

**When to escalate:** Claude Opus 5 ($5.00/$25.00) — only for the highest-stakes [SENSITIVE] content where ultimate capability is needed (e.g., final review of a critical legal document, complex clinical formulation).

**Never use for [SENSITIVE]:** DeepSeek, Qwen, Llama, Gemini, MiniMax, Kimi, Nemotron, Tencent, ByteDance, Inkling, GLM, GPT-OSS — none of these meet the Anthropic-direct routing requirement.

### 4.11 Final critical review (rare)

**Primary:** Claude Opus 5 ($5.00/$25.00, vision-capable)

Reserve for the hardest problems and highest-stakes final review. Use for:
- Final review of safety-critical code before deployment
- Irreversible infrastructure decisions
- Research-grade analysis where being wrong is unacceptable

**This should be rare.** 95%+ of build tasks never reach this tier. Before selecting Opus 5, you must have considered and rejected every cheaper model with a stated reason.

---

## 5. THE ESCALATION LADDER (COST-AWARE)

```
Tier 0:  GPT-OSS 120B              ($0.037/$0.17)     ← cheapest capable; bulk/ETL
   ↓
Tier 1:  DeepSeek V4 Flash 0731    ($0.08/$0.18)       ← AGENT DEFAULT; daily drafting
   ↓
Tier 2:  Qwen3 235B Instruct       ($0.09/$0.55)       ← frontier general at budget price
         Tencent Hy3               ($0.14/$0.58)       ← cost-effective reasoning+agent
         DeepSeek V3.2             ($0.26/$0.38)       ← best general-purpose value
   ↓
Tier 3:  Llama 4 Maverick          ($0.20/$0.80)  👁️   ← cheapest serious vision
         Qwen3 Coder 480B          ($0.30/$1.00)       ← best value coder
         MiniMax M3                ($0.28/$1.10)  👁️   ← best value all-round multimodal
         Inkling Small             ($0.45/$1.20)       ← long-doc structured output
   ↓
Tier 4:  Seed 1.8                  ($0.25/$2.00)  👁️   ← agent+LLM+VLM blend
         Kimi K2.5                 ($0.45/$2.25)  👁️   ← agentic knowledge work
         DeepSeek R1 0528          ($0.50/$2.15)       ← canonical reasoning model
         Nemotron 3 Ultra 550B     ($0.50/$2.20)       ← long-running agents
         GLM 5.2                   ($0.75/$2.40)       ← long-context reasoning
         DeepSeek V4 Pro           ($1.30/$2.60)       ← best reasoning-per-dollar
   ↓
Tier 5:  Claude Sonnet 5           ($2.00/$10.00) 👁️   ← [SENSITIVE] required routing
         Kimi K3                   ($2.85/$14.25) 👁️   ← 2.8T params, big-context analysis
         Claude Opus 5             ($5.00/$25.00) 👁️   ← HIGHEST COST; final review only
```

**Escalation rules:**
1. Start at the cheapest tier that can plausibly handle the task.
2. If the output is insufficient, move up one tier — don't skip.
3. Never jump to Tier 5 (Claude) unless every cheaper option has been tried and rejected with a stated reason.
4. [SENSITIVE] content is an exception — it starts at Claude Sonnet 5 (Tier 5) by mandatory routing, not by escalation.
5. Vision tasks start at the cheapest 👁️ model that fits (Llama 4 Maverick for images, MiniMax M3 for all-round, Gemini 2.5 Flash for video).

---

## 6. SPECIAL ROUTING RULES

### 6.1 [SENSITIVE] routing (mandatory, non-negotiable)

**Rule:** All clinical, household-identity, family-law, and legal content **must** use Claude Sonnet 5 or Claude Opus 5. These are the only two Anthropic models on the endpoint.

**Why:** Per `AGENT_BOOTSTRAP.md` §4, [SENSITIVE] content must route via Anthropic direct, never through OpenRouter or logging-enabled paths. All non-Anthropic models on this endpoint are DeepInfra-hosted and do not meet the routing requirement.

**Enforcement:** This is a hard rule, not a preference. If you encounter [SENSITIVE] content:
1. Stop whatever you're doing with the current model.
2. Switch to Claude Sonnet 5 (or Opus 5 for the highest-stakes subset).
3. Do not pass [SENSITIVE] content through any other model, even briefly.

**Scope:** Clinical notes, CASP4 formulations, client names + health details, household identity records, family law documents, legal advice content. When in doubt, treat as [SENSITIVE].

### 6.2 Vision routing

**Rule:** Tasks involving images, screenshots, or video **must** use a model marked 👁️.

**Available vision models (by output cost):**

| Model | Out cost | Vision type | Context |
|---|---|---|---|
| Gemma 4 31B Turbo (A-only) | $0.34 | Text + image | std |
| Qwen3.5 35B | $1.00 | Text + image | std |
| Llama 4 Maverick | $0.80 | Text + image | 1M |
| MiniMax M3 | $1.10 | Text + image + video | 1M |
| Seed 1.8 | $2.00 | Text + image (VLM) | 1M |
| Gemini 2.5 Flash | $2.50 | Text + image + video (up to 3h) | 1M |
| Kimi K2.5 | $2.25 | Text + image | std |
| Claude Sonnet 5 | $10.00 | Text + image | std |
| Kimi K3 | $14.25 | Text + image | std |
| Claude Opus 5 | $25.00 | Text + image | std |

**Selection logic:**
- Just need to describe/extract from an image → Llama 4 Maverick ($0.80)
- Need text+image+video → MiniMax M3 ($1.10) or Gemini 2.5 Flash ($2.50 for long video)
- Need vision + reasoning → Kimi K2.5 ($2.25)
- Need vision + [SENSITIVE] → Claude Sonnet 5 ($10.00)

### 6.3 Agent model (automatic, not user-selectable)

The LibreChat agent (`agent.model`) is configured as `deepseek-ai/DeepSeek-V4-Flash-0731`. This is the model that powers:
- The memory agent (storing preferences, tone, systems, people, working_style)
- Agent-mode conversations when no modelSpec is explicitly selected
- Conversation title generation (`titleModel` is also V4 Flash 0731)

**Don't change this** unless you have a specific reason. V4 Flash 0731 at $0.08/$0.18 with cached input at $0.016 is the optimal price/performance point for the always-on agent layer.

### 6.4 Goose model context

Goose uses its own DeepInfra provider (`custom_deepinfra`) separate from LibreChat's config. Goose has 10 models configured (per `BUILD_STATE.md`). The model selection in this guide applies to **LibreChat model selection** — when you're working in LibreChat and choosing a model from the dropdown.

Goose's model is selected in the Goose UI/app, not via `librechat.yaml`. When handing off a GOOSE_TASK, the task file can include a "Recommended model" field for Michael to select in LibreChat before the next step — but Goose's own model is a separate consideration.

### 6.5 Speech-to-text (STT)

STT uses `openai/whisper-large-v3-turbo` via the DeepInfra endpoint. This is configured in `librechat.yaml` under `speech.stt.openai` and is not user-selectable per-conversation. Browser-native STT (WebSpeech API) also works over HTTPS without this config for basic dictation.

---

## 7. ACCESS NOTES — DROPDOWN VS ALLOWLIST

### How model availability works

LibreChat's DeepInfra endpoint has `fetch: false`, meaning it does NOT auto-discover models from the DeepInfra API. Instead, it uses two lists:

1. **`endpoints.custom[].models.default`** (the allowlist) — 28 model IDs. This is the definitive list of models LibreChat knows about on the DeepInfra endpoint. Used for programmatic access (agent model, titleModel, STT).

2. **`modelSpecs.list`** (the dropdown) — 23 presets. These are what appear in the model-selector UI. Each preset maps a display name to a specific endpoint + model ID + temperature.

### Discrepancies (as of 2026-08-27)

**In dropdown but NOT in allowlist (2 models — may not function):**

| Dropdown name | Model ID | Issue |
|---|---|---|
| `gpt-oss-20b` | `openai/gpt-oss-20b` | Allowlist has `openai/gpt-oss-120b` (the 120B variant), not the 20B |
| `llama-3-1-8b` | `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | Not in allowlist at all |

These two dropdown entries may fail when selected, because the endpoint allowlist doesn't include them. If you need ultra-cheap models, use GPT-OSS 120B (allowlisted, available programmatically) or request adding the 20B/8B IDs to the allowlist.

**In allowlist but NOT in dropdown (7 models — available programmatically only):**

| Model ID | Label | Price (out) | Why it's useful |
|---|---|---|---|
| `openai/gpt-oss-120b` | GPT-OSS 120B | $0.17 | Cheapest capable model; strong reasoning for price |
| `inclusionAI/Ling-3.0-flash` | Ling 3.0 Flash | $0.18 | Token-efficient agentic flash; high-volume loops |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning` | Nemotron 3.5 Lightning | $0.20 | Low-latency always-on agent model |
| `google/gemma-4-31B-it-turbo` | Gemma 4 31B Turbo | $0.34 | Cheap multimodal (text+image); vision at lowest cost |
| `google/gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | $1.50 | Huge 1M ctx at low cost; bulk doc ingestion |
| `Qwen/Qwen3.5-122B-A10B` | Qwen3.5 122B | $2.40 | Near-frontier MoE; complex analysis, long technical writing |
| `deepseek-ai/DeepSeek-V4-Pro-0813` | DeepSeek V4 Pro 0813 | $2.60 | Same price as V4 Pro; newer build |

To make any of these available in the dropdown, add a `modelSpecs.list` entry for them in `librechat.yaml` (a GOOSE_TASK for Goose to execute, per the Thinking→LibreChat / Doing→Goose protocol).

### Adding models to the dropdown

To add a new model to the LibreChat model selector:

1. **Check** the model ID is in `endpoints.custom[].models.default` (the allowlist). If not, add it there first.
2. **Add** a new `modelSpecs.list` entry following the existing format:
   ```yaml
       - name: "<kebab-case-name>"
         label: "<Display Name> 👁️"    # append 👁️ if vision-capable
         description: "<tier> — <strength>. $<in>/$<out> per 1M in/out."
         preset:
           endpoint: "DeepInfra"
           model: "<vendor/model-id>"
           modelLabel: "<Display Name>"
           temperature: 0.3    # 0.3 for flagship, 0.6 for value/budget
   ```
3. **Validate** the YAML (`python3 -c "import yaml; yaml.safe_load(open('librechat.yaml'))"`)
4. **Restart** the api container: `cd ~/LibreChat && docker compose up -d --force-recreate api` (NEVER bare `restart`)
5. **Verify** in the UI dropdown

This is a Goose-executed task (file edit + Docker restart), staged by LibreChat as a GOOSE_TASK file.

---

## 8. COST OPTIMIZATION TIPS

### 8.1 Use cached-input models for multi-turn conversations

Models with cache pricing give a massive discount on repeated context (system prompt + conversation history). For agent loops and multi-turn tasks:

| Model | Input | Cached input | Discount |
|---|---|---|---|
| DeepSeek V4 Flash 0731 | $0.08 | $0.016 | 5× cheaper |
| DeepSeek V4 Flash (Cheap) | $0.09 | $0.018 | 5× cheaper |
| DeepSeek V3.2 | $0.26 | $0.13 | 2× cheaper |
| Tencent Hy3 | $0.14 | $0.035 | 4× cheaper |
| GLM 4.7 Flash | $0.06 | $0.01 | 6× cheaper |
| DeepSeek V4 Pro | $1.30 | $0.10 | 13× cheaper |
| DeepSeek R1 0528 | $0.50 | $0.35 | 1.4× cheaper |
| Nemotron 3 Ultra 550B | $0.50 | $0.10 | 5× cheaper |
| GLM 5.2 | $0.75 | $0.14 | 5× cheaper |
| Qwen3.5 35B | $0.14 | $0.05 | 2.8× cheaper |
| MiniMax M3 | $0.28 | $0.056 | 5× cheaper |
| Qwen3 Coder 480B | $0.30 | $0.10 | 3× cheaper |
| Kimi K2.5 | $0.45 | $0.07 | 6.4× cheaper |
| Kimi K3 | $2.85 | $0.285 | 10× cheaper |
| Seed 1.8 | $0.25 | $0.05 | 5× cheaper |
| Inkling Small | $0.45 | $0.10 | 4.5× cheaper |

For agent loops that resend the same context each turn, prefer DeepSeek models (5× cache discount) or Tencent Hy3 (4× cache discount).

### 8.2 Match output cost to output volume

If your task generates a lot of tokens (long documents, code files, detailed analysis), output cost dominates. Compare:

- **Low output cost:** GPT-OSS 120B ($0.17), DeepSeek V4 Flash ($0.18), Qwen3 235B ($0.55), Tencent Hy3 ($0.58), DeepSeek V3.2 ($0.38)
- **High output cost:** Claude Sonnet 5 ($10.00), Kimi K3 ($14.25), Claude Opus 5 ($25.00)

A 5,000-token response costs $0.0009 on V4 Flash vs $0.125 on Claude Opus 5 — a 139× difference. Always ask: "Does this output need to be written by a $25/1M model, or is a $0.18/1M model sufficient?"

### 8.3 Use the 1M context window to avoid chunking

Models with 1M context (DeepSeek V4 Flash 0731, Gemini 2.5 Flash, Llama 4 Maverick, Seed 1.8, GLM 5.2, MiniMax M3, Gemini 3.1 Flash Lite) can ingest entire documents in one call. This avoids:
- Chunking overhead (multiple API calls)
- Lost context across chunks
- Higher total cost from repeated context

For document analysis, compare: one 1M-context call at $0.18/1M out (V4 Flash) vs multiple 128K-context calls at $2.60/1M out (V4 Pro) — the budget model with large context is often both cheaper *and* better.

### 8.4 Route ETL to the cheapest capable model

Bulk classification, extraction, and pipeline work should use the cheapest model that can handle the task. The progression:

1. GPT-OSS 120B ($0.037/$0.17) — cheapest capable; available programmatically
2. DeepSeek V4 Flash (Cheap) ($0.09/$0.18) — in dropdown, designed for bulk
3. DeepSeek V3.2 ($0.26/$0.38) — if the cheap model's quality is insufficient
4. Inkling Small ($0.45/$1.20) — if structured output extraction is needed

### 8.5 The 80/20 rule

Approximately 80% of build tasks can be handled by 3 models:
- **DeepSeek V4 Flash 0731** ($0.08/$0.18) — daily drafting, planning, state updates, verification
- **Qwen3 Coder 480B** ($0.30/$1.00) — code generation, review, refactoring
- **DeepSeek V4 Pro** ($1.30/$2.60) — architecture, deep analysis, reasoning

The remaining 20% need specialist models (vision, long-context, [SENSITIVE], bulk ETL). The 8 band models just added fill the gaps between V4 Flash and V4 Pro, giving you more granularity in the $0.18–$2.60 output-cost range.

---

## 9. MODEL-SPECIFIC QUICK NOTES

### DeepSeek family
- **V4 Flash 0731** — The workhorse. 1M ctx, 5× cache discount. Don't overthink it; start here.
- **V4 Flash (Cheap)** — Same family, slightly different variant. Use for bulk/ETL.
- **V3.2** — Previous-gen but strong general-purpose value. Good "step up" from Flash.
- **V4 Pro / Pro 0813** — Near-frontier reasoning. Pro is in dropdown; Pro 0813 is allowlist-only (same price, newer build).
- **R1 0528** — Canonical reasoning/thinking model. Chain-of-thought before answering. 164K ctx (smallest context of the tier 4 models — plan accordingly).

### Qwen family
- **Qwen3 Coder 480B** — Best value coder. Large model, high-quality code output.
- **Qwen3 235B Instruct** — Frontier general at budget price. Competitive with R1/o3-mini on coding/math. No cache pricing.
- **Qwen3.5 35B** — Solid mid-size with vision. Everyday tasks, light vision.
- **Qwen3.5 122B** — Near-frontier MoE (allowlist only). Complex analysis, long technical writing.

### Anthropic family
- **Claude Sonnet 5** — [SENSITIVE] required routing. Clinical, legal, excellent prose. Vision-capable.
- **Claude Opus 5** — Highest cost, ultimate capability. Final review only. Vision-capable.

### Google family
- **Gemini 2.5 Flash** — Native multimodal thinking, 1M ctx, up to 3h video. Premium vision.
- **Gemini 3.1 Flash Lite** — 1M ctx at low cost (allowlist only). Bulk doc ingestion.
- **Gemma 4 31B Turbo** — Cheap multimodal (allowlist only). Quick vision tasks.

### Other notable models
- **Nemotron 3 Ultra 550B** (Nvidia) — Frontier 550B MoE for long-running agents. 256K ctx.
- **Nemotron 3.5 Lightning** (Nvidia) — Low-latency always-on agent (allowlist only).
- **Llama 4 Maverick** (Meta) — Open multimodal MoE, 1M ctx. Cheapest serious vision.
- **Kimi K2.5 / K3** (Moonshot) — Strong general reasoning + vision. K3 is 2.8T params.
- **MiniMax M3** — Best value all-round multimodal (text/image/video), 1M ctx.
- **Tencent Hy3** — Cost-effective reasoning+agent. 295B MoE (21B active). 4× cache discount.
- **Seed 1.8** (ByteDance) — Agent+LLM+VLM blend, 1M ctx. Vision-capable.
- **Inkling Small** (Thinking Machines) — 524K ctx, tool calling + structured outputs for long-doc agents.
- **GLM 5.2 / 4.7 Flash** (Z.ai) — 5.2 is the all-round value ceiling (1M ctx); 4.7 Flash is the cheap lightweight variant.
- **GPT-OSS 120B / 20B** (OpenAI) — 120B is cheapest capable (allowlist); 20B is tiny (dropdown, may not function).
- **Ling 3.0 Flash** (InclusionAI) — Token-efficient agentic flash (allowlist only).
- **Llama 3.1 8B** (Meta) — Dirt cheap (dropdown, may not function — not in allowlist).

---

*This guide is the single source of truth for model selection in the Backup AI System. It should be reviewed whenever models are added or removed from `librechat.yaml`, or when DeepInfra changes pricing. The pricing in `librechat.yaml` modelSpecs descriptions is the authoritative source — if DeepInfra changes pricing, update this guide to match.*

*Supersedes `MODEL_SELECTION_MATRIX.md` (26 Aug 2026). To be committed to `ai-context/docs/` via GOOSE_TASK, replacing the old matrix.*
