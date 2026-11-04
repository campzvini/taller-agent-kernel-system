---
name: commit
description: Commit validated owned changes when authorized, including normal code delivery. Reuse existing authorization; report an explicit uncommitted state when blocked.
---

¶ - Commit scoped validated changes through the existing Git context helper.

skill:
  id: @skill/commit
  loop: {{KERNEL_HOME}}/behavior/loops/L08.tdsl

¶ 1 — Suggested Commit Loop

suggested_loop:
  context: python {{KERNEL_HOME}}/scripts/commit_context.py
  ownership: compare_current_changes_with_work_scope_and_initial_state
  review: inspect_owned_diff_with_existing_review_skill
  validation: require_applicable_validation_before_commit
  no_remaining_owned_code_changes: skip_empty_or_duplicate_commit
  authorized_work_and_commit: stage_exact_owned_paths_and_commit_without_repeated_confirmation
  higher_confirmation_required: obtain_it_before_mutation
  forbidden_or_unknown_authority: preserve_work_and_report_uncommitted_paths_and_reason
  success: include_commit_identifier_in_delivery

¶ 2 — Boundaries

rule: helper_reports_changes_and_never_grants_authority_or_stages_files
rule: code_candidates_are_not_ownership_or_automatic_selection
rule: exclude_preexisting_third_party_and_unrelated_changes_even_if_already_staged
rule: mixed_staged_changes_require_scope_isolation_without_reverting_others
rule: use_atomic_conventional_commits_and_configured_authorship
rule: do_not_repeat_a_commit_for_already_committed_changes
rule: push_merge_release_and_feature_closure_require_their_own_authority
