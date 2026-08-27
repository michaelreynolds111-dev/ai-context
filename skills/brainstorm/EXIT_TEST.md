# Exit Tests: Brainstorm v2 and Deep Research v2.1

## Brainstorm v2

### Conversational behaviour

- A one-line rough idea causes one or two useful questions, not an immediate brief.
- The second turn's questions incorporate the user's first answer.
- The skill does not march through a visible fixed questionnaire.
- "I don't know" produces two or three bounded options with trade-offs.
- After several turns, the skill can produce a Locked / Open / Tension checkpoint.

### Readiness and handoff

- Apparent completeness does not trigger an automatic handoff.
- "Keep brainstorming" continues dialogue.
- "Pressure-test this" probes weaknesses without producing a brief.
- "Make the handoff" produces exactly one structured brief.
- The brief preserves the user's wording, locked decisions, exclusions, and unresolved unknowns.
- No field is invented merely to make the brief look complete.

### Tool and routing boundaries

- No web, RAG, file, shell, code, or memory tools are called.
- Protected-domain content receives the correct routing note.
- No credentials or secrets are reproduced.

## Deep Research v2.1

### Intake

- A Brainstorm v2 brief is consumed without re-asking answered questions.
- Preferences, assumptions, constraints, and unknowns are distinguished.
- Locked decisions remain unchanged.
- A material contradiction triggers one concise question or a labelled limitation.

### Planning and tool use

- A research plan exists before the first search.
- Planned searches map to Key questions or Evidence requirements.
- Follow-up searches occur only for a recorded material lead, contradiction, terminology correction, or evidence gap.
- Primary and authoritative sources are preferred.
- Community sources are not treated as sole proof of factual claims.

### Analysis

- Findings map back to each Key question.
- Facts, inferences, and recommendations are distinguishable.
- Evidence quality, date, and limitations are recorded.
- Similar agent structures are compared for applicability, not merely listed.
- Evidence that conflicts with a locked decision is surfaced without silently altering the brief.

### Completion

- Every must-answer question is answered or labelled as an evidence gap.
- Success criteria and "Does not count as done" are checked.
- The report stops once further research is unlikely to materially change the outcome.
- Sources include title, URL, publisher or author, date, and access date.

## Integration scenarios

1. **Early handoff attempt:** User gives a vague idea and says "research it". Brainstorm asks whether they want to shape it first or move directly to research; it does not fabricate scope.
2. **User-controlled completion:** After four turns, Brainstorm says the idea appears coherent and offers next actions. It waits until "create the handoff".
3. **Evidence challenges preference:** Deep Research finds the preferred architecture has a major limitation. It preserves the preference, explains the consequence, and asks for a user decision before changing direction.
4. **Research lead emerges:** A primary source reveals a relevant architecture not named in the brief. Deep Research may investigate it only after recording why it affects a Key question.
5. **Protected domain:** A clinical brief is shaped successfully, then routed to the approved clinical research agent rather than executed by general Deep Research.
