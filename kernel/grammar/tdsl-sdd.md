# TDSL SDD Dialects and Workflow Contract

¶ - Define the host-neutral constitution-to-planning backbone, artifact ownership, phase packages, controlled returns, and acceptance authority.

document:
  id: tdsl.sdd@3
  version: 3
  status: proposed
  authority_basis: [@constitution/current @arch/tdsl-language @arch/tdsl-schema-contract @arch/tdsl-runtime-contract @arch/product]
  scope: constitution, feature_activation, specify, clarify, plan, tasks, analyze, planning_accept, planning_ready
  excludes: implementation_phase, host_adapter, provider_selection, product_packaging

¶ 1 — Backbone

```text
project:
  discover
  -> initialize
  -> constitution_author
  -> constitution_accept
  -> governed

feature:
  propose
  -> provisional
  -> operator_activate
  -> active
  -> specify
  -> clarify_or_accept_spec
  -> plan
  -> accept_plan
  -> tasks
  -> accept_tasks
  -> analyze
  -> satisfy_assurance
  -> operator_accept_planning
  -> planning_ready
```

Conversation remains free. Only authenticated operations and decision records
create project, feature, artifact, or transition authority.

¶ 2 — Actor Authority

```text
operator:
  intent
  project_principles
  feature_activation
  material_decisions
  artifact_acceptance
  risk_acceptance
  planning_acceptance

agent:
  interpretation
  targeted_questions
  semantic_artifact_proposals
  labeled_derivations
  analysis_proposal

kernel:
  identity
  exact_schema_and_template
  workflow_state
  context_projection
  validation
  acceptance_binding
  freshness
  transition
  persistence
  refusal

gateway:
  bounded_effect
  observed_result
  effect_evidence

client_or_adapter:
  UX
  event_translation
  model_callback
  result_presentation
```

Agent-authored `status`, `result`, prose, or confidence never replaces operator
decision or kernel validation.

¶ 3 — Artifact and Runtime Status

Artifact source owns only content lifecycle:

```text
content_status:
  draft
  proposed
  superseded
```

The artifact envelope owns:

```text
acceptance_status:
  pending
  accepted
  rejected

freshness_status:
  fresh
  stale
  stale_derived
  invalid
```

Acceptance requires an authenticated external decision record. Freshness is
calculated by the kernel and is never agent-authored.

¶ 4 — Project and Feature Lifecycle

Project lifecycle:

```text
unmanaged
-> discovered
-> adoption_proposed
-> governed
```

Discovery is read-only. Adoption is explicit.

Feature lifecycle:

```text
proposed
-> provisional
-> active
-> planning_ready
-> pending_acceptance
-> complete
-> archived

any_nonterminal -> blocked
```

Activation:

```text
feature_proposed
  + project_governed
  + constitution_accepted_fresh
  -> feature_provisional

feature_provisional
  + operator_explicit_activation
  + no_other_active_feature
  -> feature_active
```

Only one feature holds execution authority per workflow unless a future
workflow explicitly defines concurrency.

¶ 5 — Artifact DAG and Staleness

```text
constitution -> spec
constitution -> plan
constitution -> analysis

spec -> plan
spec -> tasks
spec -> analysis

plan -> tasks
plan -> analysis

tasks -> analysis
```

Direct artifact or part references establish direct dependencies unless the
schema marks a reference informational-only.

```text
direct_semantic_change:
  direct_dependents -> stale
  transitive_dependents -> stale_derived

source_only_change_with_same_ir:
  revalidate_source_IR_pair
  regenerate_source-sensitive_publication_if_needed
  do_not_stale_semantic_dependents
```

Staleness uses predecessor semantic `ir_digest`, relevant acceptance decision,
and applicable policy revision. It never uses timestamps, file recency, branch
names, or unchecked boxes.

Part-level narrowing is valid only when the dependency basis records exact part
references and the changed parts cannot affect the dependent.

¶ 6 — Artifact-Part Identity

```text
@spec/<feature>#journey/<id>
@spec/<feature>#requirement/<id>
@spec/<feature>#criterion/<id>
@plan/<feature>#component/<id>
@plan/<feature>#boundary/<id>
@plan/<feature>#interface/<id>
@plan/<feature>#validation/<id>
@tasks/<feature>#task/<id>
@analysis/<feature>#finding/<id>
```

Part IDs are unique within artifact and kind. Renaming an ID is a semantic
change. Tasks trace to stable requirement, plan-part, and validation references.

¶ 7 — Canonical Dialect Family

The initial family is:

```text
constitution@1
spec@1
plan@1
tasks@1
analysis@1
phase_package@1
template@1
header_profile@1
```

Exact schemas and revisions are owned by:

```text
docs/architecture/tdsl/schemas/registry.json
docs/architecture/tdsl/schemas/*.schema.json
```

Prose in this document explains workflow meaning. Schema files own field types,
cardinality, value states, reference targets, accumulated blocks, object fields,
content statuses, invariants, renderers, and compatibility.

¶ 8 — Constitution

`constitution@1` is project policy, not a normal feature artifact.

```text
author:
  agent proposes
  operator decides
  kernel validates

accept:
  exact source + IR pair
  exact schema revision
  operator decision record
  constitution version
```

An amendment that changes meaning:

- creates a new version;
- requires operator acceptance;
- recalculates affected freshness through the DAG;
- cannot silently grant effect authority;
- records impact and semantic-version consequence.

Project branding and personal header signatures are not constitution semantics
unless the operator explicitly declares them as project policy.

¶ 9 — Specification and Clarification

`spec@1` owns feature intent, user journeys, requirements, criteria, edge cases,
decisions, unknowns, and evidence references.

```text
spec_proposal_valid
  + no_material_unknowns
  + operator_spec_acceptance
  -> spec_accepted_fresh
```

Clarify is a governed replacement operation:

```text
input:
  current_spec
  material_unknowns
  operator_dialogue

output:
  next_spec_version

prohibited:
  in_place_mutation
  competing_primary_clarify_artifact
  inferred_operator_answer
```

A semantic replacement invalidates downstream artifacts according to the DAG.
A source-only reformulation with identical semantic IR does not.

¶ 10 — Plan

`plan@1` resolves the technical approach under accepted policy and specification.
It uses identified parts:

```text
component <id>
boundary <id>
interface <id>
validation <id>
```

A valid plan:

- references accepted fresh constitution and spec;
- reflects repository reality;
- identifies components and responsibilities;
- declares boundaries and their contracts;
- binds material authority boundaries to decisions;
- identifies interfaces and owners;
- defines data and state behavior;
- defines stable validation parts referenced by tasks;
- separates architecture from task decomposition;
- preserves technical unknowns.

Acceptance:

```text
plan_proposed_valid
  + constitution_gate_pass
  + required_decisions_bound
  + operator_plan_acceptance
  -> plan_accepted_fresh
```

¶ 11 — Tasks

`tasks@1` is a set-level artifact. Each task item maps semantically to inherited
`task@1`; this is not schema subtyping.

```text
task@1.id:
  tasks@1 labeled block id

task@1.action:
  task.action

task@1.status:
  task.status

task@1.evidence_refs:
  task.evidence_refs
```

`tasks@1` additionally owns story, requirement, plan-part, file, validation,
dependency, parallelism, condition, and blocker references.

A valid task set:

- has unique task IDs;
- has an acyclic dependency graph;
- traces every task to at least one requirement, plan part, and validation part;
- uses exact file references when known and the permitted whole-field `unknown`
  state when legitimately deferred;
- declares validation before completion;
- requires evidence for completed tasks;
- does not introduce architecture or authority absent from accepted plan.

Acceptance:

```text
tasks_proposed_valid
  + DAG_acyclic
  + traceability_complete
  + operator_tasks_acceptance
  -> tasks_accepted_fresh
```

¶ 12 — Analysis

`analysis@1` is read-only with respect to inspected artifacts, implementation
files, and external effects. It may write only its own analysis artifact,
provenance, evidence, and transition candidate.

Severity:

```text
blocking
material
minor
observation
```

Result:

```text
pass
fail
inconclusive
```

`pass` requires complete required coverage and no unresolved blocking or
material finding. Zero findings are represented as `findings: []`. Every
finding cites canonical sources and routes to its owning artifact or to an
operator decision boundary.

Analysis is an agent-authored proposal validated by the kernel. It cannot grant
planning acceptance or mutate defects silently.

¶ 13 — Acceptance Records

Constitution, spec, plan, and tasks acceptance are external records:

```text
acceptance_record:
  decision_ref
  operator_identity
  artifact_ref
  source_digest
  ir_digest
  schema_revision
  accepted_at_operation_ref
  scope
```

The record binds one exact artifact candidate. A replacement version or semantic
digest change requires a new record. An agent cannot author an accepted source
state that bypasses this record.

¶ 14 — Assurance

Independent review is policy-selected:

```text
assurance_requirement selected_by:
  project_constitution
  affected_boundary
  explicit_operator_decision
```

It is not universal to every consumer. For development of LIMA, current project
policy may require it at material boundaries.

Assurance produces evidence and a disposition. It does not replace operator
acceptance.

¶ 15 — Planning-Ready Gate

`planning_ready` requires all of:

```text
feature:
  active

constitution:
  accepted
  fresh

spec:
  accepted
  fresh

plan:
  accepted
  fresh

tasks:
  accepted
  fresh

analysis:
  schema_valid
  references_valid
  coverage_complete
  result_pass
  no_unresolved_blocking_or_material_findings

assurance:
  passed_or_not_required

operator_planning_acceptance:
  recorded
```

No artifact self-promotes this transition.

¶ 16 — Controlled Returns

A controlled return records:

```text
finding_ref
from_phase
to_phase
owner_artifact_ref
affected_artifact_refs
stale_artifact_refs
authority_ref
reason
old_version_refs
replacement_version_ref?
```

Rules:

- return to the artifact owning the semantic defect;
- preserve current, rejected, and replacement versions;
- do not mutate unrelated predecessors;
- calculate stale derivatives through the DAG;
- require operator decision when changing product intent, architecture, public
  contract, persistence, dependency, security, data safety, risk, or acceptance;
- require renewed acceptance when accepted semantic meaning changes;
- allow bounded correction inside an authorized envelope;
- treat attempt count as telemetry, never authority.

¶ 17 — Concrete Phase Packages

The canonical proposed phase-package instances are:

```text
docs/architecture/tdsl/phase-packages/initialize-project.tdsl
docs/architecture/tdsl/phase-packages/constitution-author.tdsl
docs/architecture/tdsl/phase-packages/constitution-accept.tdsl
docs/architecture/tdsl/phase-packages/feature-propose.tdsl
docs/architecture/tdsl/phase-packages/feature-activate.tdsl
docs/architecture/tdsl/phase-packages/specify.tdsl
docs/architecture/tdsl/phase-packages/clarify.tdsl
docs/architecture/tdsl/phase-packages/plan.tdsl
docs/architecture/tdsl/phase-packages/tasks.tdsl
docs/architecture/tdsl/phase-packages/analyze.tdsl
docs/architecture/tdsl/phase-packages/planning-accept.tdsl
```

A phase package is host-neutral policy and orchestration data. It defines input
and output dialects, exact output revision, selected template, context,
questions, agent constraints, deterministic kernel actions, allowed references,
allowed capabilities, prerequisites, transitions, controlled returns, and
assurance requirement.

Phase packages do not live in consumer repositories as prompt authority.

¶ 18 — Template Family

```text
docs/architecture/tdsl/templates/constitution.tdsl
docs/architecture/tdsl/templates/spec.tdsl
docs/architecture/tdsl/templates/plan.tdsl
docs/architecture/tdsl/templates/tasks.tdsl
docs/architecture/tdsl/templates/analysis.tdsl
docs/architecture/tdsl/templates/phase-package.tdsl
```

Templates are `template@1` documents. They declare typed placeholders and exact
output revisions. Required zero-item accumulated containers use `when_empty` to
emit `container: []`; they never emit an empty indented block.

¶ 19 — Greenfield

```text
open_empty_project
-> read_only_discovery
-> free_conversation
-> explicit_initialize
-> constitution_author
-> operator_constitution_accept
-> project_governed
-> feature_propose
-> operator_feature_activate
-> specify
```

Discussion alone creates no project or feature authority.

¶ 20 — Brownfield

Discovery classifies without mutation:

```text
LIMA_managed_active
LIMA_managed_idle
Spec_Kit_existing
unmanaged
```

Minimal project anchor:

```text
lima:
  project_ref
  constitution_ref
  workflow_ref
  schema_lock_ref
```

The anchor contains no runtime session, secret, cache, prompt pack, or agent
memory.

Rules:

- code and executed evidence outrank documentation for observed state;
- Spec Kit artifacts enter as provenance and candidate semantics, not automatic
  runtime authority;
- exact revisions are recovered from tracked artifact headers and schema lock;
- ambiguous active feature or workflow position refuses;
- adoption does not rewrite repository history;
- newest file, branch, or unchecked task is never selected heuristically.

¶ 21 — Backbone Acceptance

A generic host-neutral harness must eventually demonstrate:

```text
greenfield:
  initialize
  accept_constitution
  activate_feature
  produce_and_accept_spec
  clarify_or_explicitly_skip
  produce_and_accept_plan
  produce_and_accept_tasks
  produce_validated_analysis
  satisfy_assurance
  record_planning_acceptance
  reach_planning_ready

brownfield:
  discover_without_mutation
  adopt_or_resume_explicitly
  recover_exact_schema_and_position
  preserve_history

control:
  refuse_invalid_transition
  refuse_stale_predecessor
  route_controlled_return
  distinguish_source_only_from_semantic_change
  persist_source_IR_envelope_publication_evidence
  recover_interrupted_publication
  operate_without_host_specific_semantics
```

This is a future implementation gate. No Codex, Claude Code, Cline, or
proprietary-client integration is required to define the backbone.
