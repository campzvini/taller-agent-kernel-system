---
name: execute
description: Execute authorized task units with reconciliation, independent validation and operational journals.
---

¶ - Run the persistent orchestrator loop within declared authority.

skill:
  id: @skill/execute
  phase: execute
  policy: {{KERNEL_HOME}}/docs/sdd.tdsl

¶ 1 — Recover the Package

recover:
  read: project_configuration_and_constitution_authority
  state: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root . status
  reconcile: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root . reconcile
  consult: task_sources_relevant_decisions_failures_and_interrupted_attempts
  legacy: missing_execution_configuration_means_interactive
  configuration: .task/execution.config.tdsl
  authorization: autonomous_authorized_true_only_after_explicit_grant
rule: existing_analysis_not_repeated_without_material_change
rule: missing_predecessor -> owning_phase; do_not_fabricate_record

¶ 2 — Execute Zero

condition: integral_package_ready_and_structure_not_scaffolded
command: python {{KERNEL_HOME}}/scripts/structure_scaffold.py --root . --apply
rules:
  inspect_existing_first: true
  overwrite_existing: false
  provisional: ◇_and_stable_anchor_ref
  unsupported_placeholder: pending_with_reason
  completion_claim: structural_only
  after: reconcile_and_record_evidence

¶ 3 — Select and Claim

selection:
  command: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root . next
  authority: task_and_feature_dependency_DAG
  difficulty: low_medium_high_guides_grouping
  unit: feature_task_group_or_task
  claim: exclusive_write_scope_before_spawn
  max_active_subagents: project_config_default_1
  claim_command: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root . claim <unit_ref> <task_refs> --owner <owner>
  conditional_task: judge_applicability_from_sources_then_add_--condition-satisfied_<task_ref>
  resolve_command: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root . resolve <task_ref>
  parallel: independent_units_disjoint_source_and_operational_destinations
rule: unresolved_or_ambiguous_ref -> reconcile_before_intervention
rule: planned_destination_exists_false_allows_create_after_source_reconciliation

¶ 4 — Reconcile and Delegate

per_unit:
  1: resolve_targets_and_governing_refs
  2: consult_constitution_planning_and_relevant_history
  3: inspect_actual_destinations
  4: decide_reuse_modify_create_or_no_action
  5: classify_validations_before_tests
  6: spawn_test_author_when_separate_test_author_true
  7: spawn_executor_with_minimal_context_and_exclusive_write_scope
  8: receive_changes_decisions_failures_and_evidence
rule: executor_never_runs_test_gate_or_contacts_operator
rule: test_criteria_independent_even_when_roles_share_agent
rule: necessary_new_structure_allowed_with_recorded_reason_and_updated_sources

¶ 5 — Verify and Record

verification:
  owner: orchestrator
  run: declared_build_and_required_validation_suite
  completion: required_validations_ran_and_passed
  absent_validation: blocked_with_reason
  contested_test: judge_against_spec_and_independent_reference
  known_failure: precise_feedback_to_executor
record:
  execution: unique_event_task_attempt_timestamp_outcome_evidence
  decision: material_question_choice_rationale_evidence_explicit_supersession
  failure: material_cause_effect_resolution_rationale_evidence_resolution_state
  trivial_error: omit
rule: journals_append_only; planning_has_no_runtime_status
rule: checklist_is_execution_journal_projection_only

¶ 6 — Update and Continue

after_unit:
  1: promote_implemented_◇_to_§_preserving_anchor_ref
  2: reconcile_indices
  3: record_validation_results
  4: release_claim_and_end_executor
  5: close_feature_when_validated_and_authorized
  6: select_next_eligible_unit
execution_mode:
  autonomous: continue_inside_declared_authority_without_questions
  interactive: material_undelegated_choice_goes_to_operator
halt_only: real_block_outside_authority_explicit_stop_or_dependency_confirmation
rule: no_scope_expansion_beyond_declared_package

¶ 7 — Report

report:
  initial: compact_unit_and_progress_projection
  progressive: material_changes_and_real_blocks
  detailed: targeted_evidence_on_request
  final: completed_pending_blocked_and_validation_evidence
ban: scaffold_promotion_or_executor_success_as_functional_proof
