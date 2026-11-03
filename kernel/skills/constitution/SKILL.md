---
name: constitution
description: Author or amend the project constitution as a constitution@2 TDSL artifact in .task/constitution.tdsl. Use when the operator wants to establish, review, or amend durable project policy — principles, authority boundaries, quality bar, safety rules, evidence requirements. Not for feature behavior (use specify) and not for technical design (use plan).
---

¶ - Author durable project policy: principles, authority, quality, safety, evidence.

skill:
  id: @skill/constitution
  phase constitution
  output_dialect constitution@2
  output_path .task/constitution.tdsl
  template {{KERNEL_HOME}}/skills/constitution/template.tdsl

¶ 1 — Preconditions

1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py state
2 if: no_.task_anchor -> propose `sdd_gate.py init --name <project>` -> await operator
3 if: constitution exists -> this is an AMENDMENT, not authoring; go to ¶ 5

¶ 2 — Load

Read {{KERNEL_HOME}}/skills/constitution/template.tdsl now — the authoring shape. Load no other
phase skeleton.

Then read {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl for the exact schema_revision.
Read {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl ONLY if the shape contains an
object splice `{#name}` or an enum-valued field you must fill.

¶ 3 — Elicit

Constitution owns durable policy only. Ask the operator for, in order:

  principles       one normative proposition each, stable id, UPPERCASE-free title
  authority        who decides what — role boundaries stated once, project-wide
  quality          the non-negotiable bar and how it is measured
  safety           destructive-action and blast-radius rules
  evidence         what counts as proof that a claim is true
  amendment        how this document changes and who may change it

optional_only_when_material:
  language_policy, architecture_refs, workflow_refs, profiles

offer_as_defaults: # propose; the operator keeps, edits or drops each
  principle problem-triage    global policy ¶10 problem_triage, stated for this project
  principle test-triage       skill test-protocol ¶3, stated for this project
  authority delivery_close    whether the delivery session may close a feature as delivered
                              on passing validations without asking (sdd ¶12 validation_and_closure)
  authority stop_conditions   what halts a delivery session besides explicit_unknowns

ban: asking for feature behavior, technical stack, task decomposition

¶ 4 — Authoring contract

principle one_normative_proposition_per_principle
rationale emit only when it changes interpretation; never restate the rule
applies_to emit only to narrow an otherwise project-wide rule
exceptions explicit, finite, intentional; absence means no declared exception
refs architecture and workflow mechanics belong in referenced artifacts, not copied here
authority defined once; feature-specific authority belongs in spec, plan or a decision
unknown material uncertainty goes to explicit_unknowns; never convert it into an assumption

format:
  identity_header tdsl, schema_revision, id, version, status, purpose — in that order
  schema_revision copy verbatim from {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl
  object_splice `{#name}` expands to the contract in {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl
  enum_field use only the vocabulary in field-contracts; any other value refuses
  indent 2 spaces; no tabs; no trailing whitespace; final newline required
  collections [a b] whitespace-separated, never mixed with commas
  empty_required_container emit `field: []`, never an empty indented block
  ln bodies use `key ln: |` one indent level deeper
  output contains no placeholder and no directive

¶ 5 — Amendment

if: meaning_changes -> explicit_revision_authority, preserve_previous_version, version+1, status: proposed
if: change_to_published_version -> preserve_then_emit_next_version
always: run analyze and say what the change made incoherent downstream

¶ 6 — Close

1 preserve the existing published version before writing the next .task/constitution.tdsl
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check .task/constitution.tdsl
3 if: FAIL -> fix and recheck; never accept a failing source
4 report the principle ids, the explicit_unknowns, and the amendment impact
5 return to protocol; continue within declared authority; material undelegated choices go to operator

¶ 7 — Immutable Versions and Authority

constitution:
  each_version: immutable
  amendment: preserve_previous_in_.task/history/constitution/<version>.tdsl
  authority: explicit_autonomous_scope_closure_rights_stop_conditions
  code: observed_behavior_never_overrides_policy
rule: explicit_revision_authority_required
rule: planning_mode_never_delegates_execution_authority
