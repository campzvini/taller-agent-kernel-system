---
name: architecture
description: Author the intended project tree before feature planning; reached through protocol.
---

¶ - Establish intended directories and files without duplicating behavior contracts.

skill:
  id: @skill/architecture
  phase: architecture
  output_path: .task/Architecture.md
  template: {{KERNEL_HOME}}/skills/architecture/template.md

¶ 1 — Inputs

inputs:
  normative: immutable_constitution_version
  observed: tracker_inventory_then_targeted_existing_structure
  intent: declared_project_scope
rule: inspect_existing_before_proposing_destinations

¶ 2 — Author

output:
  content: directory_and_file_tree_only
  paths: project_relative_no_escape_no_absolute_paths
  descriptions: excluded
  requirements: remain_in_specs
  strategy: remains_in_plans
  metadata_and_identity: external_registry
rule: tree_contains_existing_relevant_and_declared_new_destinations
rule: binary_manifest_generated_destination_need_not_receive_empty_file

¶ 3 — Reconcile

change:
  reason: record_material_structural_decision
  sources: update_affected_plan_task_and_refs
  registry: reconcile_without_guessing_ambiguous_identity
  validate: parse_tree_and_check_destinations
return: protocol_routes_feature_planning_or_execute_zero
