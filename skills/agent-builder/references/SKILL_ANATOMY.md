# SKILL.md Anatomy — Conventions from the 8 Existing Skills

**Source:** Derived from the 8 existing skills in `ai-context/skills/*/SKILL.md`.
**Purpose:** The reference for what a well-formed SKILL.md looks like in this build.
**Last derived:** 14 August 2026 (from clinical-writing, household-admin, powershell-sysadmin, seddon-family-law-drafter, and the other 4 skills).

---

## 1. FRONTMATTER (YAML)

Every SKILL.md starts with YAML frontmatter:

```yaml
---
name: <skill-name>
description: <when to use + triggers>
---
```

### 1.1 `name`
- Lowercase, hyphenated (e.g. `clinical-writing`, `household-admin`).
- Matches the directory name `skills/<name>/SKILL.md`.

### 1.2 `description`
- Starts with "Use when..." or "Use when answering..."
- States the domain/purpose.
- Lists trigger phrases explicitly ("Triggers on phrases like...", "Triggers on mentions of...").
- Can state what it does NOT do (e.g. household-admin: "Method only — no values stored here.").

**Example (clinical-writing):**
```yaml
description: Use when drafting or reviewing clinical documentation, case notes, referrals, progress notes, or professional correspondence in a mental health case-management context. Triggers on requests to write, review, restructure, or improve client-facing or clinical documents. Also triggers on phrases like "case note", "referral letter", "progress note", "NDIS report", "clinical summary".
```

---

## 2. BODY SECTIONS

The body follows a consistent section order. Not every section is required in every skill, but the common ones are:

### 2.1 `# <Skill Name>` (H1 title)
- Matches the `name` in frontmatter, human-readable.
- May carry a routing tag inline: `# Seddon Family Law Drafter [SENSITIVE]`

### 2.2 `## When to use`
- Bulleted list of concrete situations/requests that should trigger this skill.
- Written as user-phrases ("Drafting or editing case notes", "What is our policy number?").

### 2.3 `## Hard rules` (or `## Hard rules — non-negotiable`)
- The non-negotiable constraints. This is the most important section.
- Uses bold lead-ins: **Never...**, **Always...**, **Cite...**, **Say "not found" rather than infer.**
- Example (household-admin): "**Always cite the source document** for every value returned."

### 2.4 `## Standards` (optional)
- Quality/format standards: language, tense, length, format defaults.
- Example (clinical-writing): "Language: Plain, professional, person-first... Tense: Progress notes in past tense."

### 2.5 `## Process`
- Numbered steps the agent follows.
- Concise, actionable, one action per step.

### 2.6 `## Output format`
- What the output should look like, by output type.
- Bulleted list of output types with their required structure.

### 2.7 `## What this agent cannot do` (optional)
- Explicit statement of tool/scope limits.
- Example (household-admin): "This agent has no browser, web search, shell, or memory tools — by design."

### 2.8 `## Routing [SENSITIVE]` or `## Routing [IDENTITY]` (classification-dependent)
- States the routing constraint.
- Example: "This skill handles [SENSITIVE] content. Route only via DeepInfra direct or Anthropic direct. Never OpenRouter or any logging-enabled path."

---

## 3. ROUTING TAGS

| Tag | Meaning | Routing constraint |
|---|---|---|
| `[SENSITIVE]` | Sensitive content (clinical, family law) | DeepInfra direct or Anthropic direct only. Never OpenRouter or logging-enabled paths. |
| `[IDENTITY]` | Identity/personal data (household) | DeepInfra direct or Anthropic direct only. Local embeddings only at index time. Never OpenRouter. |
| *(none)* | Build/general tool | Any endpoint. |

The tag appears:
1. In the H1 title (e.g. `# Seddon Family Law Drafter [SENSITIVE]`)
2. In the Routing section heading (e.g. `## Routing [SENSITIVE]`)

---

## 4. CONVENTIONS SUMMARY

| Convention | Rule |
|---|---|
| Frontmatter | Always present; `name` + `description` |
| `name` | Lowercase, hyphenated, matches directory |
| `description` | "Use when..." + triggers |
| H1 title | Human-readable, matches name, may carry routing tag |
| Hard rules | Always present; bold lead-ins; non-negotiable |
| Standards | Optional; language/tense/length/format |
| Process | Numbered steps; one action per step |
| Output format | Bulleted by output type |
| Routing tag | In H1 + Routing section if [SENSITIVE]/[IDENTITY] |
| Subdirectories | references/, scripts/, assets/, templates/ — only when the skill outgrows a single file |

---

## 5. WHEN TO USE SUBDIRECTORIES

The 8 existing skills are all single-file `SKILL.md`. The build's skill-system
guidance is: **keep SKILL.md concise; move large templates, schemas, and long
docs into references/ and templates/.** Use subdirectories when:

- The skill needs reference material that would bloat SKILL.md
- The skill needs reusable templates for scaffolded output
- The skill has scripts or assets

The `agent-builder` skill is the first to demonstrate this — its SKILL.md is
lean and points to `references/` and `templates/` rather than carrying the
content inline.
