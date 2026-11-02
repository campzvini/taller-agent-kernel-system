---
name: decompose
description: Break one recorded task into ordered subtasks, as an optional decomposition.tdsl beside the task set. Use only when a single task has more than one independently validatable result and the operator asks for it. Never a routine phase — its absence is not a gap.
---

¶ - Break one task into subtasks; optional, operator-directed, never routed.

skill:
  id: @skill/decompose
  phase decompose
  output_dialect local:decomposition@1
  output_path .task/features/<feature_id>/decomposition.tdsl
  template {{KERNEL_HOME}}/skills/decompose/template.tdsl
  optional the artifact is absent by default; absence is never a finding

¶ 1 — When this exists at all

```text
propose_when one task's action holds more than one result that is validated separately
propose_when a task's file_refs span parts that are ordered against each other inside it
ban proposing it to make a task look more planned
ban authoring it without the operator saying to
rule the agent names the task and says why it should split; the operator decides
alternative if the split changes what the plan says, return to tasks; do not paper over it here
```

¶ 2 — Preconditions

1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py gate decompose
2 if: FAIL -> report and stop
3 read tasks.tdsl; every subtask names a parent that exists there

¶ 3 — Authoring contract

```text
sibling_not_nested subtasks live in their own container, never inside a task block
  reason the shared block parser reads fields exactly one level below an item, so a
    nested subtask is dropped silently — the worst outcome available
parent required; exactly one; a task id from tasks.tdsl
depends_on orders subtasks of the SAME parent only
  reason ordering between tasks is the task DAG's job; a second model competing
    with it is how two contradictory orders come to exist
status fixed at pending; runtime progress belongs to the execution journal
traceability none restated; the parent task already carries requirement, plan and validation refs
```

¶ 4 — Close

1 write the artifact
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check <path>
3 if: FAIL -> fix and recheck
4 report the parent task, the subtask count and their order
5 stop. O registro está escrito. Não existe passo de aceitação.
