# System Improvement Rationale: Brainstorm to Deep Research

## Decision

Replace the current one-turn-oriented Brainstorm behaviour with a user-controlled conversational funnel:

`rough idea -> adaptive dialogue -> checkpoints -> explicit readiness gate -> structured handoff -> evidence layer`

The current skill allows up to three clarifying questions and then quickly emits a brief. That is efficient for task shaping, but it does not support the iterative co-development you want. The revised design separates **idea ownership** from **evidence acquisition**.

## Why this structure is stronger

1. **Socratic dialogue before delegation.** Comparable Socratic mentor agents use focused, layered questions and leave thinking space rather than immediately resolving the problem. The revised Brainstorm borrows the useful interaction pattern without adopting the overly rigid rule that the agent can never offer options.
2. **Explicit human control at the transition.** The handoff cannot occur until the user requests it. This prevents premature compression and makes "happy with it" an actual state controlled by the user.
3. **Structured state across the conversation.** Short Locked, Open, and Tension checkpoints reduce drift without forcing a full brief every turn.
4. **Clear agent boundaries.** Brainstorm owns intent and choices. Deep Research owns verification and synthesis. An executor owns implementation. This reduces duplicated work and prevents Deep Research from re-scoping the task.
5. **Adaptive research, within bounds.** A completely fixed query plan can miss important leads. The revised Deep Research starts from a bounded plan but permits justified follow-up searches when evidence exposes a contradiction or gap.
6. **Escalation instead of silent mutation.** If research challenges a locked decision, it returns the conflict and options to the user rather than rewriting the task.

## Important correction to the existing proposal

The earlier proposal says every search call must directly correspond to an original Key question. That protects tokens but is too rigid for genuine deep research. Research is path-dependent, and useful evidence often changes terminology, exposes contradictions, or reveals a missing dependency. The improved rule is:

> Every search must either answer a planned question or have a recorded, material reason tied to the brief.

This preserves scope while allowing depth.

## Recommended lifecycle

### Phase A: Brainstorm

- Ask one or two high-value questions per turn.
- Offer bounded options when the user is stuck.
- Periodically summarize Locked, Open, and Tension.
- Never research or claim validation.
- Wait for an explicit handoff command.

### Phase B: Deep Research

- Consume the brief as authoritative intake.
- Classify preferences, assumptions, constraints, and unknowns.
- Plan targeted research.
- Gather and evaluate evidence.
- Test assumptions and compare analogous systems.
- Return findings mapped directly to the brief.
- Escalate material decision conflicts to the user.

### Phase C: Implementation

- Occurs only after the researched recommendation is accepted.
- Uses a separate build plan or executor skill.

## Sources reviewed

- Anthropic, "How we built our multi-agent research system", 13 June 2025: https://www.anthropic.com/engineering/multi-agent-research-system
- Microsoft Azure Architecture Center, "AI agent orchestration patterns", updated 12 February 2026: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
- Huang et al., "Deep Research Agents: A Systematic Examination and Roadmap", 2025: https://arxiv.org/html/2506.18096v2
- dualverse-ai, "Socratic Mentor Agent": https://github.com/dualverse-ai/station-research-skills/blob/main/deep-research/agents/socratic_mentor_agent.md

## Immediate next action

Replace the proposed Brainstorm skill with `SKILL_BRAINSTORM_V2.md`, stage `SKILL_DEEP_RESEARCH_V2_1.md`, and run the accompanying exit tests before promoting either skill.
