---
name: protocol
description: Entry point and router for any governed project workflow — reports where the project stands, which phase comes next, and dispatches the right phase skill. Use whenever the operator wants to start or resume governed work: initialize a project, write or amend a constitution, specify, clarify, plan, decompose into tasks, analyze, or execute. It reads the project state and picks the tree; never pick a phase skill yourself.
---

¶ - Route SDD workflow state and report project phase.

skill:
  id: @skill/protocol
  role workflow_router
  authority none # routes and reports; never accepts, never promotes a phase

¶ 1 — Contract

principle:
  one_phase_one_skill loading a phase template outside its own skill is forbidden
  gate_before_author every authoring skill runs its gate first and refuses on FAIL
  acceptance_is_operator_only agent proposes, operator accepts, script records
  no_self_promotion no artifact and no skill declares its own acceptance or freshness
  lifecycle_is_position_not_merit a feature's recorded state says where it sits, never how good it is
  closing_is_an_operator_act propose a closing state; never run close on your own initiative

¶ 2 — Where the policy lives

```text
development lifecycle -> {{KERNEL_HOME}}/docs/sdd.tdsl
rule this skill routes and reports; it never restates that document
reason a copy drifts, and the copy is what gets read
```

¶ 3 — Determine the tree first; it decides which gate you speak to

```text
anchor exists -> read `workflow:` from .protocol/project.tdsl
no anchor, no artifacts -> the operator's stated intent declares it; confirm before init
artifacts present but no workflow field -> read the evidence
  spec.tdsl present -> development
ambiguous -> ask; never infer a workflow from a directory name
```

```text
development -> gate is {{KERNEL_HOME}}/scripts/sdd_gate.py, policy {{KERNEL_HOME}}/docs/sdd.tdsl
ban running one workflow's gate against the other's records
```

¶ 4 — Routing the phase

```text
run: python {{KERNEL_HOME}}/scripts/<gate>.py state

next_phase=initialize -> run(init) after the operator confirms
next_phase=constitution -> invoke_skill(constitution)
next_phase=feature -> ask the operator for an id, run(feature <id>)
next_phase=idle -> report it and STOP. Nothing governed is open. Say what was
  closed last and what the register holds; then wait. Do not open a feature, do
  not reopen one, do not propose the next cycle as if delivery implied it.
feature finished -> propose a closing state and why; the operator directs it; then run(close ...)

development:
  next_phase=specify -> invoke_skill(specify)
  next_phase=plan -> invoke_skill(plan)
  next_phase=tasks -> invoke_skill(tasks)
  next_phase=analyze -> invoke_skill(analyze)
  next_phase=execute -> invoke_skill(execute)
  spec exists with material explicit_unknowns -> invoke_skill(clarify)
  a task holds more than one independently validated result -> propose skill(decompose); the operator decides


operator asks for state -> run(state) or run(trail), render, stop
```

planning_mode (read it from `state`; the anchor records it, `mode <value>` switches it):
  gradual -> next_phase belongs to the cursor feature; it walks specify..execute before the next opens
  integral -> next_phase names `feature: <id>`; run(feature <id>) when it differs from the cursor,
    then invoke that phase's skill. Every active feature reaches analysis before any execute.
  integral_start -> agree the full feature list with the operator, open each id with run(feature <id>),
    author spec, plan and tasks for every feature, then ONE skill(analyze) over the whole package
    (sdd ¶13 integral_package); fix, and stop when `roadmap` reports "all features planned"
  integral_execute -> a separate session the operator opens; skill(execute) runs the sdd ¶14 loop
    in id order without asking between features

¶ 5 — Commands


```text
state   python {{KERNEL_HOME}}/scripts/<gate>.py state
trail   python {{KERNEL_HOME}}/scripts/<gate>.py trail
init    python {{KERNEL_HOME}}/scripts/<gate>.py init --name <project>
feature python {{KERNEL_HOME}}/scripts/<gate>.py feature <NNN-kebab-name> [--reopen]
close   python {{KERNEL_HOME}}/scripts/<gate>.py close <id> --as delivered|heritage|historical|superseded|abandoned
scaffold python {{KERNEL_HOME}}/scripts/<gate>.py scaffold # re-place the authoring skeletons
gate    python {{KERNEL_HOME}}/scripts/<gate>.py gate <phase>
check   python {{KERNEL_HOME}}/scripts/<gate>.py check <path.tdsl>

development only:
  analyze python {{KERNEL_HOME}}/scripts/sdd_gate.py analyze

modelling only:
```

¶ 6 — What this skill must not do

```text
ban declaring a record good, complete, accepted or approved
ban treating an analyze finding as a blocker; present it, the operator decides
ban restating layout, derivation or return rules that docs/sdd.tdsl owns
ban closing a feature without the operator saying so
ban reading a delivered, heritage or historical feature as if it still routed work
```

¶ 7 — Reporting

Render state as a compact table: artifact and whether it exists, then the feature
register with each feature's lifecycle, then next_phase. There is no acceptance
column and no freshness column — the model has neither. Report only what changed
plus decisions owed to the operator.
