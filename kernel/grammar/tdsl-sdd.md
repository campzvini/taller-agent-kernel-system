# TASK Development Contracts

¶ - Bundled development dialect interpretation, authority boundaries and runtime separation.

document:
  id: @arch/tdsl-sdd
  version: 2
  status: proposed
  purpose: define_TASK_development_contracts_without_a_second_approval_system
  grammar: @arch/tdsl-language
  field_authority: schemas/registry.json
  lifecycle_authority: @task/sdd-policy

¶ 1 — Backbone

backbone: constitution_architecture_features_specs_plans_tasks_analysis_execute_zero_execution
rule: execute_zero_required_for_integral_mode
rule: gradual_mode_may_create_structure_as_needed
rule: dependencies_not_directory_names_select_order

¶ 2 — Actor Authority

authority:
  operator: intent_constitution_material_undelegated_choices_and_authority_grants
  agent: resolve_known_technical_choices_within_authority
  orchestrator: recover_select_delegate_verify_record_update
  executor: implement_assigned_unit_with_exclusive_write_scope
  test_author: independent_when_configured
  script: mechanical_parsing_integrity_indexing_and_projection
rule: constitution_highest_project_normative_authority
rule: code_material_truth_of_existing_behavior
rule: neither_existing_code_nor_script_result_grants_authority

¶ 3 — Artifact and Runtime Status

planning:
  content_status: draft_proposed_superseded
  runtime_progress: excluded
runtime:
  source: append_only_execution_journal
  attempts: unique_event_identity_plus_task_ref
  completion: required_validation_pass_with_evidence
  checklist: derived_only
rule: no_per_task_runtime_status_in_tasks@2
rule: legacy_tasks@1_remain_readable

¶ 4 — Project and Feature Lifecycle

project:
  planning_mode: gradual_integral
  execution_mode: interactive_autonomous
  legacy_default: interactive
feature:
  lifecycle: active_delivered_heritage_historical_superseded_abandoned
  depends_on: explicit_feature_DAG
  cursor: navigation_only
  closure: operator_direction_or_explicit_delegation
rule: autonomous_requires_explicit_scope_and_stop_conditions
rule: mode_name_never_grants_authority

¶ 5 — Artifact DAG and Change

dag:
  constitution -> architecture, spec, plan, tasks, analysis
  architecture -> structural_destinations
  spec -> plan, tasks, analysis
  plan -> tasks, analysis
  tasks -> analysis, execution_events
change:
  semantic: preserve_relevant_history_update_owning_sources_reconcile_refs
  cosmetic: no_invented_semantic_staleness
  decision_precedence: explicit_supersession_not_date
rule: no_content_hash_structural_identity
rule: schema_revision_hashes_remain_required

¶ 6 — Artifact and Structural Identity

identity:
  project: @project/<id>
  directory: @dir/<id>
  file: @file/<id>
  section: @file/<id>#section/<id>
  task: @tasks/<feature>#task/<id>
  execution: @event/<id>
  decision: @decision/<id>
  failure: @failure/<id>
  evidence: @ev/<id>
  unit: @unit/<id>
rule: position_title_line_and_path_are_not_stable_identity
rule: duplicates_or_ambiguous_moves_are_unresolved_not_merged

¶ 7 — Dialect Family

schemas:
  authority: schemas/registry.json
  revision: explicit_schema_revision_in_each_tracked_artifact
  legacy: old_major_contracts_remain_readable
  successor: major_for_changed_authority_required_fields_or_semantics
rule: never_infer_dialect_or_revision_from_filename
rule: schema_lock_and_field_contracts_generated_by_tdsl_lock.py

¶ 8 — Constitution

constitution:
  scope: principles_authority_quality_safety_evidence_amendment
  each_version: immutable
  amendment: explicit_revision_authority_and_preserved_predecessor
  current: .task/constitution.tdsl
  history: .task/history/constitution/<version>.tdsl
rule: normative_conflict_requires_reconciliation_even_if_code_exists

¶ 9 — Specification

specification:
  owns: objective_journeys_atomic_requirements_measurable_criteria_unknowns
  references: applicable_constitution_and_feature
  excludes: technical_design_and_duplicate_architecture_tree
  clarification: governed_next_version
rule: known_source_answer_is_resolved_before_operator_question
rule: genuine_material_unknown_remains_explicit

¶ 10 — Plan

plan:
  owns: components_boundaries_interfaces_data_state_and_validation_map
  structural_targets: stable_refs_into_intended_architecture
  validation: each_required_behavior_has_observable_proof
  decisions: refs_to_material_decision_records
  new_structure: justified_and_reconciled_with_sources
rule: no_silent_architecture_or_authority_expansion

¶ 11 — Tasks

tasks:
  dialect: tasks@2
  owns: action_requirement_refs_plan_refs_target_refs_validation_refs_dependencies_difficulty_write_scope
  difficulty: low_medium_high
  dependency: acyclic_DAG
  execution_order: deterministic_linearization_not_second_graph
  runtime_status: absent
  evidence: journal_only
rule: difficulty_guides_unit_selection_not_automatic_model_choice
rule: legacy_file_refs_and_tasks@1_are_supported_at_read_boundary

¶ 12 — Analysis

analysis:
  mechanical: references_coverage_dependency_cycles_identity_and_write_conflicts
  judgment: policy_alignment_material_scope_decision_precedence_navigation_value
  method: index_triage_targeted_read_then_full_only_when_necessary
  outcome: findings_routed_to_owning_source
rule: no_additional_approval_layer
rule: real_blocks_and_integrity_failures_are_not_silently_ignored

¶ 13 — Operational Records

execution:
  required: event_id_task_ref_attempt_timestamp_outcome_validation_and_evidence
decision:
  required: decision_id_task_ref_timestamp_question_choice_rationale_evidence_refs
  supersedes: explicit_target_and_scope
failure:
  required: failure_id_task_ref_cause_effect_resolution_rationale_evidence_refs_resolution_state
  inclusion: material_recurring_architectural_contract_or_consequential
rule: append_only_corrections_retries_and_resolutions
rule: trivial_immediate_errors_omitted
rule: failure_triggering_decision_cross_references_it

¶ 14 — Assurance and Test Authorship

validation:
  policy: constitution_then_test_protocol
  gate: orchestrator
  separate_test_author: configurable_default_true
  criteria: independent_even_with_combined_authorship
  missing_required_validation: blocked
  completion: evidence_of_required_validation_pass
tracker: never_runs_tests_or_judges_implementation

¶ 15 — Planning Readiness

readiness:
  gradual: current_feature_records_resolve
  integral: all_declared_features_planned_and_cross_feature_analysis_done
  execution: authority_present_dependencies_satisfied_destinations_resolved
  scaffold: integral_before_functional_execution
rule: readiness_is_not_quality_acceptance_or_new_authority

¶ 16 — Controlled Return

return:
  defect -> owning_record
  known_answer -> agent_resolves_within_authority
  new_material_choice -> decision_journal_and_affected_source_update
  real_unknown_or_outside_authority -> operator
rule: never_modify_unrelated_predecessor_to_make_check_pass

¶ 17 — Execution Units

unit:
  may_be: feature_task_group_or_task
  selection: difficulty_dependencies_context_and_write_scope
  max_active_subagents: default_1
  parallel: independent_units_exclusive_paths
  write_scope: includes_source_tests_reports_journals_indices_temporaries
  lifecycle: claim_implement_return_validate_record_release
rule: interruption_recovered_explicitly_before_retry

¶ 18 — Authoring Shapes

templates:
  phase_owned: load_only_when_dispatched
  skeleton: shape_not_record
  placeholder: never_in_emitted_record
  generated_contracts: schema_lock_and_field_contracts
architecture:
  format: tree_only_Markdown
  metadata: external_registry

¶ 19 — Greenfield

greenfield:
  order: constitution_then_architecture_then_feature_planning
  execute_zero: create_only_safe_missing_structure
  provisional: ◇_with_stable_anchor_ref
  promotion: executor_changes_to_§_without_identity_change
rule: scaffold_does_not_prove_behavior
rule: no_fake_binary_manifest_or_lockfile

¶ 20 — Brownfield

brownfield:
  inspect_existing: before_any_creation
  identity: register_without_mutating_original_sources
  ambiguity: unresolved_explicit_reconciliation
  rediagramming: optional_scoped_baseline_and_nonfunctional_guard
  provenance: preserve_origin_license_attribution_and_adaptation_classes
rule: absent_index_entry_never_proves_absent_behavior

¶ 21 — Migration and Boundaries

migration:
  explicit: preserve_old_records_and_history
  default_authority: interactive
  new_autonomy: explicit_opt_in
  legacy_journals: remain_readable
  runtime_progress: derive_without_rewriting_planning
boundaries:
  tracker: identity_location_relationship_and_index_only
  index: reconstructible_projection
  registry: persistent_identity_binding
  hooks: assistance_not_complete_interception
  reconciliation: independently_available
ban: second_Git_or_content_hash_identity
