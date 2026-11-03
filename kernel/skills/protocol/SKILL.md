---
name: protocol
description: Route governed work from state and declared planning and execution authority.
---

¶ - Recover workflow state and dispatch one phase without inventing authority.

skill:
  id: @skill/protocol
  role: workflow_router
  policy: {{KERNEL_HOME}}/docs/sdd.tdsl

¶ 1 — Determine the Workflow

workflow:
  existing: local_instructions_and_artifacts_declare_it
  absent: operator_intent_declares_it
  ambiguous: ask_operator
  ban: selecting_by_directory_name
rule: load_only_dispatched_phase_skill_and_template

¶ 2 — Recover State and Authority

commands:
  state: python {{KERNEL_HOME}}/scripts/sdd_gate.py state
  runtime: python {{KERNEL_HOME}}/scripts/execution_runtime.py --root . status
configuration:
  planning_mode: gradual_or_integral
  execution_mode: interactive_or_autonomous
  max_active_subagents: positive_integer_default_1
  separate_test_author: boolean_default_true
rule: absent_new_config_preserves_legacy_interactive_behavior
rule: autonomous_requires_explicit_authority_and_complete_integral_planning

¶ 3 — Dispatch

routing:
  initialize: initialize_when_authorized
  constitution: skill(constitution)
  architecture: skill(architecture)
  feature: register_declared_feature_and_dependencies
  specify: skill(specify)
  clarify: skill(clarify)
  plan: skill(plan)
  tasks: skill(tasks)
  analyze: skill(analyze)
  execute_zero: skill(execute)
  execute: skill(execute)
  idle: report_and_stop
rule: broken_reference -> owning_phase
rule: available_technical_answer -> resolve_within_authority
rule: material_undelegated_choice -> operator

¶ 4 — Modes and Closure

planning:
  gradual: active_feature_cycles_before_next_feature
  integral: complete_declared_features_then_cross_feature_analysis
execution:
  autonomous: ready_package_proceeds_to_execute_zero_and_loop_in_same_session
  interactive: proceed_with_existing_or_new_execution_authority
closure:
  delegated: validated_feature_may_close_and_next_eligible_unit_routes
  undelegated: propose_for_operator_direction
  exhausted: idle_without_new_scope
rule: feature_ids_tie_break_not_define_dependencies
scope:
  gate: python {{KERNEL_HOME}}/scripts/sdd_gate.py --feature <id> gate <phase>
  parallel_context: inspect_target_feature_without_mutating_shared_cursor

¶ 5 — Reporting

report:
  compact: planning_position_progress_next_unit_and_real_blocks
  checklist: derived_from_execution_journal
  detail: query_specific_refs_on_request
ban: tracker_or_router_judging_implementation_quality
