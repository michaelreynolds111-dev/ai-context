---
name: clinical-writing
description: Use when drafting or reviewing clinical documentation, case notes, referrals, progress notes, or professional correspondence in a mental health case-management context. Triggers on requests to write, review, restructure, or improve client-facing or clinical documents. Also triggers on phrases like "case note", "referral letter", "progress note", "NDIS report", "clinical summary".
---

# Clinical Writing

## When to use
- Drafting or editing case notes, progress notes, session summaries
- Writing referral letters to GPs, psychiatrists, allied health
- NDIS reports, functional capacity assessments, support plans
- Professional correspondence with stakeholders, carers, services
- Clinical summaries for handover or review

## Hard rules
- **Never invent clinical detail.** Use only what is explicitly provided.
- **Never suggest a diagnosis** unless one is already documented and you are quoting it.
- **Cite the source** for every clinical fact used (session notes, referral, assessment).
- If information is missing, say so explicitly rather than inferring.
- Do not use first-person voice for the clinician unless instructed.

## Standards
- Language: Plain, professional, person-first ("the client", not "the patient" unless the service uses that convention).
- Tense: Progress notes in past tense; plans and goals in future tense.
- Length: Case notes factual and concise. Referrals include all clinically relevant history.
- Format: Default to SOAP (Subjective / Objective / Assessment / Plan) for case notes unless instructed otherwise.

## Process
1. Identify the document type and audience (internal record, external referral, NDIS portal, GP correspondence).
2. Confirm what information is available and note any gaps explicitly.
3. Draft, flagging anything inferred or uncertain with [CONFIRM].
4. On review pass, resolve or remove all [CONFIRM] flags.

## Output format
- Case notes: structured paragraphs under SOAP headings, or prose if instructed.
- Referral letters: formal letter format, date/addressee/subject line, signed-off line placeholder.
- NDIS documents: follow the plan's stated goal structure; use functional language.
- Flag any section where clinical detail was absent with [MISSING: describe what's needed].

## Routing [SENSITIVE]
This skill handles [SENSITIVE] content. Route only via DeepInfra direct or Anthropic direct. Never OpenRouter or any logging-enabled path.
