---
name: pr-description
description: Compose a PR title and description from the branch commits. Use when a branch is ready for human review.
---

¶ - Generate PR title and description from branch commits

skill:
  id: @skill/pr-description

¶ 1 — Gatilho

condition(operator_requests_pr_prep | feature_ready_for_review | commit_sequence_completes_unit) -> invoke

¶ 2 — Procedimento

1 identify current branch and base branch (usually main)
2 execute `git log <base>..<current>` to list branch commits
3 execute `git diff <base>..<current> --stat` to understand scope
4 synthesize changes by theme (not just list commits)
5 compose concise title following conventional commits
6 compose description with sections
  motivation: why this change
  main changes: what was altered
  breaking changes: if any
  test notes: how to verify
7 present for confirmation before any push

¶ 3 — Critérios

title is informative without being long
description groups by theme, does not repeat commit log
breaking changes highlighted if they exist
test notes are actionable by human reviewer
does not invent content: everything referenced to branch commits
