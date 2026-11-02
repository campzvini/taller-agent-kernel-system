---
name: plan
description: Author the technical plan as a plan@1 TDSL artifact in .task/features/<id>/plan.tdsl — components, boundaries, interfaces, data and state, and the validation map that proves the spec. Use when the operator wants the technical approach for an accepted specification. Not for task decomposition (use tasks) and not for behavior (use specify).
---

¶ - Author technical approach: components, boundaries, interfaces, data, validation map.

skill:
  id: @skill/plan
  phase plan
  output_dialect plan@1
  output_path .task/features/<feature_id>/plan.tdsl
  template {{KERNEL_HOME}}/skills/plan/template.tdsl

¶ 1 — Preconditions

1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py gate plan
2 if: FAIL -> report and stop. constitution and spec must exist; this plan cites their parts.
3 read the accepted spec and constitution before proposing anything
4 reflect repository reality: verify the current structure with Grep/Glob before
   declaring components or project_structure

¶ 2 — Load

Read {{KERNEL_HOME}}/skills/plan/template.tdsl now — the authoring shape. Load no other
phase skeleton.

Then read {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl for the exact schema_revision.
Read {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl ONLY if the shape contains an
object splice `{#name}` or an enum-valued field you must fill.

¶ 3 — Authoring contract

summary the technical approach in one paragraph; not a restatement of the spec
component id, purpose, responsibilities; depends_on only when a real edge exists
boundary between exactly two components, with its contract; authority refs bind material decisions
interface only for real public/internal/external contracts; otherwise `interfaces: []`
data_and_state defines persistence, lifetime, and state transitions
validation IS the single verification map — every `proves` entry is a spec or plan part reference
project_structure mirrors the repository as it will be, not a wish
decisions reference decision records; do not restate the decision text
explicit_unknowns technical facts still unresolved; never an invented assumption
risks implementation risk lives here, not in the spec

optional_only_when_material:
  research_refs, migration, performance, security, operations, complexity_exceptions
ban emitting an optional module as boilerplate — absent beats empty ceremony

coverage:
  every spec requirement must be provable by at least one validation
  if: a requirement has no validation -> report the gap before writing
  ban introducing architecture or authority absent from the accepted spec and constitution

format:
  identity_header tdsl, schema_revision, id, version, status, purpose, constitution_ref, spec_ref
  schema_revision copy verbatim from {{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl
  object_splice `{#name}` expands to the contract in {{KERNEL_HOME}}/skills/_shared/field-contracts.tdsl
  enum_field use only the vocabulary in field-contracts; any other value refuses
  indent 2 spaces; no tabs; no trailing whitespace; final newline
  collections [a b] whitespace-separated
  empty_required_container `interfaces: []`
  output contains no placeholder and no directive

¶ 4 — Close

1 write the plan
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check <path>
3 if: FAIL -> fix and recheck
4 report components, boundaries, the requirement-to-validation coverage map, and explicit_unknowns
5 stop. O registro está escrito. Se ele precisa mudar, o operador diz o que muda;
  silêncio é concordância. Não existe passo de aceitação.
