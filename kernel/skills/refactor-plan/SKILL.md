---
name: refactor-plan
description: Map dependencies, risks and a safe step order before refactoring. Use before any non-trivial restructuring.
---

¶ - Plan refactoring with dependency mapping and risk assessment

skill:
  id: @skill/refactor-plan

¶ 1 — Gatilho

condition(before_non_trivial_refactor | operator_requests_reorganization | reviewer_flags_structural_need) -> invoke

¶ 2 — Procedimento

1 identify refactoring scope: files, modules, interfaces
2 map dependencies: who imports, calls, or extends the target code
3 identify existing tests covering the affected area
4 evaluate risks
  breaking changes in public interfaces
  side effects in adjacent code
  data or schema migrations needed
5 compose step sequence, from lowest risk to highest
6 define checkpoints between steps (commit and test)
7 present plan to operator for approval before execution

¶ 3 — Critérios

each step is independently verifiable
risks are specific, not generic
sequence minimizes broken intermediate state
plan preserves public interfaces unless change is explicit
