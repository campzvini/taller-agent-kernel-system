---
name: specify
description: Author the feature specification as a spec@1 TDSL artifact in .task/features/<id>/spec.tdsl — objective, user journeys, atomic requirements, measurable success criteria, explicit unknowns. Use when the operator wants to turn intent or a brainstorm into the observable behavior contract for the active feature, or to clarify and replace an existing spec. Not for technical design (use plan).
---

¶ - Author feature behavior contract: objective, journeys, requirements, criteria, unknowns.

skill:
  id: @skill/specify
  phase specify
  output_dialect spec@1
  output_path .task/features/<feature_id>/spec.tdsl
  template {{KERNEL_HOME}}/skills/specify/template.tdsl

¶ 1 — Preconditions

1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py gate specify
2 if: FAIL -> report the blocking reason to the operator and stop. Do not author.
   constitution missing -> invoke_skill(constitution)
   no active feature -> ask the operator for an id, then `sdd_gate.py feature <NNN-name>`
3 if: spec already exists -> this is a CLARIFY replacement; go to ¶ 5

¶ 2 — Load

Read {{KERNEL_HOME}}/skills/specify/template.tdsl now — the authoring shape. Load no other
phase skeleton.

Then read {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl for the exact schema_revision.
Read {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl ONLY if the shape contains an
object splice `{#name}` or an enum-valued field you must fill.

¶ 3 — Elicit

  objective    the problem-to-outcome transition, once
  journeys     end-to-end value flows, minimum count, each independently testable
  requirements one normative proposition each, stable id
  criteria     measurable system or user outcomes
  non_goals    what this feature explicitly does not do

if: operator_input_is_a_brainstorm -> extract, then read back the requirement list for confirmation
if: material_fact_unresolved -> explicit_unknowns; never invent an assumption
ban: proposing components, files, stacks, or task ordering

¶ 4 — Authoring contract

objective states the transition once; it is not a summary of the requirements
requirement exactly one normative proposition, stable id, independently verifiable
journey.acceptance carries requirement ids, not rewritten Given/When/Then prose
journey is an end-to-end value flow, not a second requirement language
criterion is a measurable outcome, not a restatement of a requirement
edge_case with required behavior IS a requirement -> emit `edge_cases: []`
edge_case unresolved -> explicit_unknowns
conditions express only a trigger or guard; never smuggle kind, verify, or priority into the string
non_goals bound scope; dependencies declare semantic dependencies; entities only when a domain noun needs stable downstream meaning
ban emitting assumptions or risks by default — uncertainty is explicit_unknowns, implementation risk belongs to plan

format:
  identity_header tdsl, schema_revision, id, version, status, purpose, feature_ref
  schema_revision copy verbatim from {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl
  object_splice `{#name}` expands to the contract in {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl
  enum_field use only the vocabulary in field-contracts; any other value refuses
  indent 2 spaces; no tabs; no trailing whitespace; final newline
  collections [a b] whitespace-separated
  empty_required_container `edge_cases: []`
  output contains no placeholder and no directive

¶ 5 — Clarify replacement

input current_spec, material_unknowns, operator_dialogue
output next_spec_version

prohibited:
  in_place_mutation_without_version_bump
  a competing parallel clarification artifact
  inferring the operator answer

if: semantic_change -> version+1; run analyze and say what it made incoherent
if: source_only_reformulation -> same meaning, same version, report it

¶ 6 — Close

1 write the spec
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check <path>
3 if: FAIL -> fix and recheck
4 report requirement ids, criteria, explicit_unknowns, and what the operator must decide
5 stop. O registro está escrito. Se ele precisa mudar, o operador diz o que muda;
  silêncio é concordância. Não existe passo de aceitação.
