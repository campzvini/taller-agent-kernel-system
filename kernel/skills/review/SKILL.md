---
name: review
description: Critical reading of code or a diff for consistency, edge cases and risk — reasoning, not linting. Use before a commit, or after an executor finishes.
---

¶ - Critical code analysis and diff review before commit

skill:
  id: @skill/review

¶ 1 — Gatilho

condition(pre_commit_checkpoint | operator_requests_explicitly | subagent_executor_completes) -> invoke

¶ 2 — Procedimento

1 receive code or diff to review. For pre-commit review, can execute `python {{KERNEL_HOME}}/scripts/commit_context.py` and read `.agent-cache/commit-context.md` as source material.
2 identify project patterns via AGENTS.md and ADRs
3 analyze consistency with existing conventions in the codebase
4 identify uncovered edge cases
5 identify risks: side effects, breaking changes, regressions in adjacent code
6 verify adherence to modularity and block division rules
7 compose classified report

¶ 3 — Critérios

analysis goes beyond syntax errors; addresses logic and architecture
each critique is specific and referenced to code (line or function)
suggestions are actionable, not abstract
classification is justified by identified points

¶ 4 — Context and Delivery

rule: before_commit_review_the_actual_owned_diff_including_additions_and_deletions
rule: separate_preexisting_and_third_party_changes_from_the_work
rule: review_and_commit_do_not_substitute_for_functional_validation
reference: {{KERNEL_HOME}}/behavior/loops/L08.tdsl
