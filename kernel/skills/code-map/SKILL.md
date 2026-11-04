---
name: code-map
description: Return an available code map or report that it is unavailable. Read-only navigation; never triggers reconciliation, diagramming or task execution.
---

¶ - Supply existing code navigation without prescribing work.

skill:
  id: @skill/code-map
  role: read_only_navigation

¶ 1 — Suggested Consultation Loop

consult:
  locate: existing_project_map_context_map_or_registered_ranges
  available: return_relevant_map_with_coverage_and_provenance
  unavailable: report_map_unavailable
  partial: disclose_available_coverage_without_inferring_missing_behavior
  behavior_question: consult_relevant_source_when_needed
locations:
  structural: .agent-cache/project-map.md
  machine: .agent-cache/project-map.json
  semantic: .agent-cache/context-map.md
  identity: .task/tracking/registry.json
rule: map_is_navigation_not_behavioral_evidence_or_execution_authority
rule: do_not_rebuild_refresh_scan_or_reconcile_to_answer_a_map_request
rule: brownfield_without_available_map -> report_unavailable_without_requiring_anchors
rule: this_skill_never_instructs_creation_repair_diagramming_or_other_task_execution
rule: diagramming_is_relevant_only_when_an_open_feature_explicitly_assigns_it
rule: preserve_existing_files_and_history
