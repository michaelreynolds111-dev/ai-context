# Exit Tests: Brainstorm v2 and Deep Research v2.1 (deep-research copy)

This is the shared exit-test document for the v2.0 / v2.1 redesign. It is stored
in the `deep-research` skill directory alongside the v2.1 SKILL.md so the task
and both agents reference the same criteria. See the identical copy in the
`brainstorm` skill directory. Full criteria:

## Brainstorm v2
- One-line rough idea -> one or two useful questions (not an immediate brief).
- Second-turn questions incorporate the user's first answer.
- No visible fixed questionnaire march.
- "I don't know" -> two/three bounded options with trade-offs.
- After several turns, can produce Locked / Open / Tension checkpoint.
- Apparent completeness does NOT auto-handoff; "Keep brainstorming" continues.
- "Pressure-test this" probes without producing a brief.
- "Make the handoff" -> exactly one structured brief preserving user wording.
- No field invented to make the brief look complete.
- No web/RAG/file/shell/code/memory tools.
- Protected-domain routing note correct; no credentials reproduced.

## Deep Research v2.1
- Brief consumed without re-asking answered questions.
- Preference/assumption/constraint/unknown distinguished.
- Locked decisions unchanged; material contradiction -> one question or labelled
  limitation.
- Research plan before first search; planned searches map to Key questions /
  Evidence requirements.
- Follow-up searches only for a recorded material lead, contradiction,
  terminology correction, or evidence gap.
- Primary/authoritative sources preferred; community sources not sole proof.
- Findings map to each Key question; fact/inference/recommendation distinct.
- Evidence quality, date, limitations recorded; similar structures compared for
  applicability, not just listed.
- Conflicting evidence surfaced without silently altering the brief.
- Every must-answer question answered or labelled an evidence gap; success
  criteria and "Does not count as done" checked; stops when further research
  won't materially change outcome; sources include title/URL/publisher/date/
  access date.

## Integration scenarios
1. Early handoff attempt -> Brainstorm asks whether to shape first or go direct.
2. User-controlled completion -> waits until "create the handoff".
3. Evidence challenges preference -> preserves preference, explains consequence,
   asks before changing direction.
4. Research lead emerges -> investigates only after recording why it affects a
   Key question.
5. Protected domain -> shaped, then routed to the approved dedicated agent.
