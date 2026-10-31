---
name: execute
description: Execute the recorded task set — confirms the whole governance trail, then implements task by task in dependency order, running each task's declared validation before marking it done. Use when the operator wants the planned work actually built, or says implement, execute, run the tasks, or build the feature. Refuses only when a record it needs does not exist; coherence findings are reported to the operator, never used to withhold execution.
---

¶ - Execute task DAG in order, validate each, confirm governance trail.

skill:
  id: @skill/execute
  phase execute
  source @speckit/implement # adapted; divergences are declared in ¶ 6
  posture writes_implementation_files, never_mutates_a_planning_record

¶ 1 — Confirm the trail

Nothing is executed on trust. One command answers the whole question:

```text
run: python {{KERNEL_HOME}}/scripts/sdd_gate.py trail
```

It reports which records exist, what the coherence pass found, the task count
and what remains in the execution order.

```text
record missing -> STOP; name it and the phase that writes it
coherence findings open -> do NOT stop; present them and ask whether they matter
  reason analyze advises, it does not gate; the operator decides what is tolerable
operator says proceed -> proceed, and report which findings were carried knowingly
```

`trail` derives coherence itself rather than reading `result:` out of
`analysis.tdsl`, because a record never judges itself.

¶ 2 — Load context

```text
required tasks.tdsl # the DAG and the per-task references
required plan.tdsl # components, boundaries, interfaces, data_and_state, validations
required spec.tdsl # what each requirement actually demands
required constitution.tdsl # the policy every implementation choice answers to
if_present analysis.tdsl # findings the operator already saw and chose to carry

method index first: `python {{KERNEL_HOME}}/scripts/code_map.py <file>` then read the
  chapter ranges you need; read a whole artifact only when it is genuinely small
```

Read the repository as it is before writing: verify with Grep/Glob that the
paths in `file_refs` and `project_structure` describe reality. A plan that
disagrees with the repository is a finding, not a licence to improvise.

¶ 3 — Order

```text
authority depends_on IS the dependency graph
execution_order a valid linearization of it, already checked by `check`
parallel two tasks may run together only when neither depends on the other AND their file_refs are disjoint
ban inventing a phase grouping the task set does not declare
ban reordering to make a blocked task reachable
```

¶ 4 — Per task

```text
1 announce the task id and what it will change
2 implement exactly its `action`, bounded by its plan_refs
3 run the validation named by every validation_refs entry
   validation absent or unrunnable -> the task is NOT done; record it blocked and say why
4 validation fails -> stop this branch; do not proceed to a dependent task
5 validation passes -> append the completion record to the journal, with evidence
6 report progress before moving on

ban writing code a requirement did not ask for
ban introducing architecture absent from the plan
ban marking done without the declared validation actually having run
ban silencing, skipping or weakening a validation to make a task pass
```

¶ 5 — The journal

Runtime state never enters a planning record. `tasks.tdsl` states what the work
is; the journal states what happened. Mixing them makes the plan unreadable as a
plan and the history unreadable as history.

```text
path .protocol/features/<feature_id>/execution.journal.tdsl
owner this skill; the gate reads it, the planning records never do

entry ln: |
  entry <task_id>:
    outcome: completed | blocked | failed
    at: <UTC timestamp>
    validation_refs: [...]        # what was run
    evidence ln: |                # command, exit status, what it proved
      ...
    when blocked: reason ln: | ...
```

Append only. Never rewrite a past entry; a retried task gets a new entry.

¶ 6 — Declared divergences from Spec Kit

```text
speckit marks `[X]` inside tasks.md
  here the plan record stays a plan; completion lives in the journal

speckit groups execution by phase labels (Setup, Tests, Core, Integration, Polish)
  here the DAG is the only ordering authority; labels would be a second, competing model

speckit gates on a checklist table and asks the operator to override
  here coherence findings are presented and the operator decides; nothing is withheld
  the gate refuses only a missing record, which is a broken reference, not a verdict

speckit runs Pre-Execution and Mandatory Post-Execution hooks from .specify/extensions.yml
  dropped entirely: this package has no extension mechanism, and inventing one
  would be a second orchestration model competing with the skills

speckit creates ignore files by detecting the stack
  here project_structure in the plan says what exists; execute does not invent files
```

¶ 7 — Halting

```text
non_parallel_task_fails -> halt; report the task, the validation and the output
parallel_task_fails -> finish the independent siblings, then halt; report each outcome
plan_contradicts_repository -> halt; this is a controlled return to plan, not a fix in place
requirement_ambiguous_at_implementation_time -> halt; controlled return to clarify
ban continuing past a failure to maximize the number of tasks touched
```

¶ 8 — Close

```text
1 report per task: id, outcome, validation run, evidence
2 report what remains pending and why
3 run `python {{KERNEL_HOME}}/scripts/sdd_gate.py trail` again and show it
4 state plainly whether the feature is complete or partial, and list every
  coherence finding carried knowingly
5 stop. Feature completion is an operator decision; this skill never declares it.
6 every task complete and every validation run -> propose a closing state and say
  why: delivered, heritage, historical, superseded (naming the successor) or
  abandoned. The operator directs it; then, and only then:
    python {{KERNEL_HOME}}/scripts/sdd_gate.py close <feature_id> --as <state>
  ban running close on your own initiative
  ban treating the close as permission to open the next feature
```
