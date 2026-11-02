---
name: execute
description: Execute the recorded task set as a delivery session — takes the package as already inspected, orchestrates a test author and an executor per feature in dependency order, and closes each feature on passing validations. Use when the operator opens an execution session, or says implement, execute, run the tasks, or build the feature. Refuses only when a record it needs does not exist.
---

¶ - Execute task DAG in order, validate each, confirm governance trail.

skill:
  id: @skill/execute
  phase execute
  source @speckit/implement # adapted; divergences are declared in ¶ 6
  posture writes_implementation_files, never_mutates_a_planning_record

¶ 1 — Confirm the trail

The operator opens an execution session only when the package is ready, so the
package is taken as already inspected (sdd ¶14). The trail is checked for
existence, never re-judged.

```text
run: python {{KERNEL_HOME}}/scripts/sdd_gate.py trail
record missing -> STOP; name it and the phase that writes it
coherence findings listed -> ignore at start; they were settled in the planning session
ban initial analysis, initial test run, or asking whether findings matter
```

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

This skill runs in the orchestrator. Roles and the loop are owned by sdd ¶14;
read it before the first spawn.

```text
orchestrator never edits source
1 classify every validation of the active plan by test-triage (skill test-protocol ¶3)
2 spawn test_author (agent test-agent) with the validations that need tests;
   tests come from spec, plan and independent references, before code, and land failing
3 spawn executor with tasks.tdsl, the test paths and the ban on test edits;
   it implements each task's `action`, bounded by its plan_refs, and keeps the journal
4 executor contests a test -> it returns the test and the reason; orchestrator judges
5 orchestrator runs the build check and the whole suite once
6 failures -> problem_triage over the whole feature scope -> precise failures to the same executor
7 every validation passes -> the executor's journal entries carry the evidence
   validation absent or unrunnable -> the task is NOT done; record it blocked and say why

ban writing code a requirement did not ask for
ban introducing architecture absent from the plan
ban marking done without the declared validation actually having run
ban silencing, skipping or weakening a validation to make a task pass
ban the executor running the test gate or escalating to the operator directly
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
  here coherence is settled in the planning session; the delivery session does not re-judge it
  the gate refuses only a missing record, which is a broken reference, not a verdict

speckit runs Pre-Execution and Mandatory Post-Execution hooks from .specify/extensions.yml
  dropped entirely: this package has no extension mechanism, and inventing one
  would be a second orchestration model competing with the skills

speckit creates ignore files by detecting the stack
  here project_structure in the plan says what exists; execute does not invent files
```

¶ 7 — Halting

```text
every difficulty -> problem_triage (global policy ¶10) before any halt
task_fails, answer known -> fix through the same executor; never proceed to a dependent task first
plan_contradicts_repository, answer in the records -> fix and record the decision in the journal
plan_contradicts_repository, no known answer -> halt; controlled return to plan
requirement_ambiguous with no known answer -> halt; controlled return to clarify
halt -> report the task, the validation, the output and why no known answer exists
stop only on a constitution stop_condition, a blocking explicit_unknown, or a production dependency
ban continuing past a failure to maximize the number of tasks touched
```

¶ 8 — Close

```text
1 report per task: id, outcome, validation run, evidence
2 report what remains pending and why
3 run `python {{KERNEL_HOME}}/scripts/sdd_gate.py trail` again and show it
4 state plainly whether the feature is complete or partial, and list every
  coherence finding carried knowingly
5 every task complete and every validation run:
  constitution authority pre-directs the close -> run
    python {{KERNEL_HOME}}/scripts/sdd_gate.py close <feature_id> --as delivered
    then follow sdd ¶14 to the next feature without asking
  otherwise -> propose a closing state and why (delivered, heritage, historical,
    superseded naming the successor, abandoned); the operator directs it, then close
  ban running close on your own initiative when no authority pre-directs it
6 register exhausted or a stop condition reached -> report and stop
```
