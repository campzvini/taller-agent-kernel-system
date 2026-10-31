---
name: commit
description: Compose a conventional commit from the current repository state. Use when the operator authorizes a commit or a logical unit of work is finished.
---

¶ - Generate conventional commits from repository state

skill:
  id: @skill/commit

¶ 1 — Gatilho

condition(operator_authorized | end_of_approved_unit) -> invoke

¶ 2 — Procedimento

1 execute `python {{KERNEL_HOME}}/scripts/commit_context.py`
2 read `.agent-cache/commit-context.md` to understand state and file grouping
3 classify commit type
  feat: nova funcionalidade
  fix: correção de bug
  docs: alteração apenas em documentação
  refactor: reorganização sem mudança de comportamento
  test: adição ou ajuste de testes
  chore: configuração, build, dependências
4 identify scope from file grouping in the report
5 compose description: imperative, present tense, short
6 assemble message: `type(scope): description`
7 present message to operator for confirmation
8 after confirmation, execute `git add` (if needed) and `git commit`

¶ 3 — Critérios

message reflects what effectively changed
scope is specific (module) not generic (entire project)
description fits within 50 characters when possible
commit is atomic: one logical unit per commit
