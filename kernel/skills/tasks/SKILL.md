---
name: tasks
description: Author the executable task set as a tasks@1 TDSL artifact in .protocol/features/<id>/tasks.tdsl — an acyclic dependency DAG whose every node traces to a requirement, a plan part, and a validation. Use when the operator wants the recorded plan decomposed into work. Not for technical design (use plan) and not for tracking runtime progress.
---

¶ - Author acyclic task DAG, each traces to requirement, plan part, validation.

skill:
  id: @skill/tasks
  phase tasks
  output_dialect tasks@1
  output_path .protocol/features/<feature_id>/tasks.tdsl
  template {{KERNEL_HOME}}/skills/tasks/template.tdsl

¶ 1 — Preconditions

1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py gate tasks
2 if: FAIL -> report and stop. constitution, spec and plan must exist; tasks cite their parts.
3 read the accepted spec and plan; the task set derives from them, not from conversation

¶ 2 — Load

Read {{KERNEL_HOME}}/skills/tasks/template.tdsl now — the authoring shape. Load no other
phase skeleton.

Then read {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl for the exact schema_revision.
Read {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl ONLY if the shape contains an
object splice `{#name}` or an enum-valued field you must fill.

¶ 3 — Authoring contract

task one coherent implementation result; split when independent validation or dependency ordering differs
traceability every task carries at least one requirement_ref, one plan_ref, and one validation_ref
file_refs exact paths when known; the whole-field state `unknown` when legitimately deferred
depends_on IS the authoritative dependency DAG; it must be acyclic
execution_order a deterministic topological linearization of that DAG only; it never adds an edge
status fixed at `pending` for every task
story_refs omitted — journey-to-requirement traceability already exists upstream
parallel omitted — safe parallelism is derived from dependency and file constraints, never authored as a second dependency model
checkpoints omitted; evidence_refs omitted; runtime risks omitted
  reason readiness, in-progress state, completion evidence, findings and blockers are
  runtime state; it belongs to the execution journal, never to this record
completion fixed: all_required_validation_pass, evidence_required, operator_acceptance required
ban introducing architecture or authority absent from the plan

format:
  identity_header tdsl, schema_revision, id, version, status, purpose, spec_ref, plan_ref
  schema_revision copy verbatim from {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl
  object_splice `{#name}` expands to the contract in {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl
  enum_field use only the vocabulary in field-contracts; any other value refuses
  indent 2 spaces; no tabs; no trailing whitespace; final newline
  nesting tdsl-language ¶6: `tasks:` at column 0, `task T001:` at 2, its fields at 4
  reason the `for` directive vanishes on expansion; it never contributes an indent level
  collections [a b] whitespace-separated
  output contains no placeholder and no directive

¶ 4 — Close

1 write the tasks artifact
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check <path>
   the check enforces unique ids, acyclic depends_on, complete traceability,
   and that execution_order does not contradict the DAG
3 if: FAIL -> fix and recheck
4 report the task count, the DAG roots and leaves, and any deferred file_refs
5 stop. O registro está escrito. Se ele precisa mudar, o operador diz o que muda;
  silêncio é concordância. Não existe passo de aceitação.
