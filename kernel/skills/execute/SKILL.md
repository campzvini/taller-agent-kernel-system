---
name: execute
description: Enter execution only when the operator explicitly invokes $execute or /execute. Read AGENTS.md, the constitution and open features, then perform the authorized work.
---

¶ - Enter authorized feature execution without defining a second execution procedure.

skill:
  id: @skill/execute
  invocation: explicit_operator_command_only

¶ 1 — Entry

entry:
  read_order: [project_AGENTS.md governing_constitution open_features]
  next: execute_authorized_feature_work
  reuse: existing_mapping_sources_decisions_and_evidence
  consult_sources: when_needed_for_the_actual_task
rule: phase_reports_router_dispatch_and_general_requests_do_not_invoke_this_skill
rule: absent_explicit_command -> do_not_load_or_run_this_skill

¶ 2 — Boundary

ownership:
  task_behavior: open_feature_contracts_and_operator_scope
  source_evaluation_and_decision_loop: existing_kernel_mechanisms
  skill: entry_only_not_an_execution_engine
rule: this_skill_adds_no_scaffold_claim_delegation_test_or_closure_sequence
rule: reconciliation_only_on_express_operator_request
rule: diagramming_is_relevant_only_when_an_open_feature_explicitly_assigns_it
rule: unavailable_map_does_not_create_a_diagramming_task
rule: preserve_history_and_report_only_observed_results
