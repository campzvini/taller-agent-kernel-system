---
name: analyze
description: The only tool in the lifecycle that emits a verdict — runs the deterministic coherence pass over constitution, spec, plan and tasks, then judges what a script cannot: policy alignment, duplicated propositions, intent drift. Emits an analysis@2 record with routed findings. Use before executing, or whenever the operator wants the records checked against each other for contradiction, ambiguity or gaps. Read-only and advisory: it reports, the operator decides.
---

¶ - Deterministic coherence pass over records, then judges alignment and drift.

skill:
  id: @skill/analyze
  phase analyze
  output_dialect analysis@2
  output_path .task/features/<feature_id>/analysis.tdsl
  template {{KERNEL_HOME}}/skills/analyze/template.tdsl
  posture read_only

¶ 1 — Preconditions

```text
1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py gate analyze
2 FAIL -> a predecessor record does not exist yet; say which, and stop
3 read {{KERNEL_HOME}}/skills/analyze/template.tdsl; load no other phase skeleton

scope:
  gradual the active feature
  integral the whole package in one pass, run by one subagent (sdd ¶6 planning_modes);
    one analysis.tdsl per feature; a cross-feature finding routes to the record that owns it
```

¶ 2 — Posture

```text
read_only with respect to inspected artifacts, implementation files, external effects
may_write only its own analysis record
ban editing an inspected artifact to make a finding disappear
ban treating verdict as authority; resolve within delegated scope or report real choices
ban inventing approval layers; unresolved_integrity_and_declared_stop_conditions_remain_enforced
```

¶ 3 — Deterministic pass first

```text
run: python {{KERNEL_HOME}}/scripts/sdd_gate.py analyze
reads .agent-cache/protocol-analysis.json
```

It settles mechanically, and you must not re-derive by reading:

```text
requirement_unproved   a spec requirement no plan validation proves
unresolved_reference   a part reference pointing at an id that does not exist
malformed_reference    a member that is not a valid part reference
component_unexercised  a plan component no task references
criterion_unmeasured   a spec criterion no validation measures
explicit_unknown       material uncertainty still open
artifact_absent        a record the analysis needs does not exist
```

Carry every one of these into your findings verbatim. Never soften a severity the
script assigned, and never restate a passing check as a finding.

¶ 4 — Read by stages, never end to end

The deterministic pass already resolved everything mechanical, so the reading
that follows is narrow by construction.

```text
1 index python {{KERNEL_HOME}}/scripts/code_map.py <all artifacts in scope> # ONE call
2 triage reason over the indices plus .agent-cache/protocol-analysis.json;
    name the chapters that could hold a judgment defect
3 targeted Read(offset, limit) only those ranges
4 full only on express operator request, or when stage 2 or 3 produced evidence
    that the defect cannot be bounded to a range

ban opening an artifact end to end because it is "safer"
ban re-reading what the deterministic pass already settled
report attribute each finding to the stage that produced it
```

¶ 5 — Then judge what no script can

These require reading the artifacts and reasoning about meaning:

```text
policy_alignment    a plan or task decision the constitution does not permit, or contradicts
duplication         one normative proposition stated authoritatively in two artifacts
drift               a plan or task that solves a problem the spec never posed
silent_scope        behavior in plan or tasks that no requirement asked for
atomicity           a requirement carrying more than one normative proposition
verifiability       a criterion whose measure cannot actually be observed
authority           a boundary asserting authority no decision record grants
runtime_leak        progress or evidence authored into a planning record instead of the journal
```

```text
rule cite the exact artifact and part id for every finding
rule a finding with no cited source is not a finding
ban inventing a defect to justify the pass having run
```

¶ 6 — Findings

```text
severity blocking | material | minor | observation
result pass | fail | inconclusive

pass requires complete coverage and zero unresolved blocking or material findings
zero findings -> `findings: []`, never an empty indented block
inconclusive when an artifact could not be read or a reference could not be resolved at all
```

Every finding routes to the artifact that owns the defect, or to an operator
decision boundary. A finding never proposes a silent mutation.

¶ 7 — Controlled return

```text
finding(blocking|material) -> record from_phase, to_phase, owner_artifact_ref,
  affected_artifact_refs, reason
rule return to the artifact owning the semantic defect, never to a convenient one
rule preserve current, rejected and replacement versions
rule a rewritten record replaces the old one; say what downstream it makes incoherent
rule attempt count is telemetry, never authority

routing:
  requirement wrong, missing, ambiguous -> specify | clarify
  requirement contested by the operator -> clarify
  design wrong, coverage gap -> plan
  decomposition wrong, traceability broken -> tasks
  policy itself is wrong -> constitution, and say what it makes incoherent everywhere
```

¶ 8 — Close

```text
1 write the analysis artifact
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check <path>
3 report result, findings by severity, and each routed return
4 integral -> the planning session fixes every finding with a known answer (problem_triage),
  then re-runs check; the operator receives only real unknowns and choices of direction
  gradual -> report what the operator must decide: which findings matter, which they tolerate
5 stop. Your verdict is advice. It withholds nothing, and you never declare a
  phase complete.
```

¶ 9 — Extended Coherence

scope:
  intended: constitution_architecture_feature_spec_plan_task
  observed: resolved_file_section_destinations
  historical: relevant_decisions_failures_execution
checks:
  mechanical: dangling_refs_duplicate_identity_feature_DAG_write_conflicts
  judgment: policy_alignment_decision_precedence_structure_and_scope
  precedence: explicit_supersession_not_timestamp
  provisional: scaffold_not_implementation
rule: identify_index_or_targeted_read_stage_for_each_finding
rule: route_known_defects_to_owner_within_authority
