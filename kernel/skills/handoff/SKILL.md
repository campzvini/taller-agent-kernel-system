---
name: handoff
description: Produce a session state document for a model switch, a pause, or a transfer to another agent. Use at end of session with pending work, or when the operator asks for a handoff.
---

¶ - Generate session state document for handoff between agents

skill:
  id: @skill/handoff

¶ 1 — Gatilho

condition(operator_requests_handoff | end_session_pending_work | planned_model_transfer) -> invoke

¶ 2 — Procedimento

1 execute `python {{KERNEL_HOME}}/scripts/handoff_snapshot.py`
2 read `.agent-cache/handoff-snapshot.md` as source material
3 from snapshot, compose interpretive document with
  work completed this session
  work pending (with progress level)
  decisions taken (with rationale)
  next concrete actionable step
  relevant files
  commands to resume
4 maintain model-agnostic format, no provider-specific terminology
5 present to operator or save per context

¶ 3 — Critérios

document is self-contained: another agent without this session's access can resume
does not use model or provider jargon
next step is actionable, not abstract
decisions include rationale, not just result
