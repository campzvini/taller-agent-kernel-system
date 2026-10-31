---
name: doc-update
description: Update or generate technical documentation from current code. Use after behavior changes, or when docs and code have diverged.
---

¶ - Update or generate technical documentation from current code

skill:
  id: @skill/doc-update

¶ 1 — Gatilho

condition(implementation_alters_docs | operator_requests_update | reviewer_flags_divergence) -> invoke

¶ 2 — Procedimento

1 identify scope: file, module, API, or project README
2 read current code and existing documentation
3 identify divergences and omissions
4 for existing documentation: compose targeted edits via str_replace. Regenerate entire file only when restructuring justifies it.
5 for new documentation: generate following operator formatting rules (headers, numbered sections, chapters)
6 apply § separator for headers per standard
7 save and present diff or generated file
8 if editing operational environment documents (AGENTS.md, skills, subagents, specs, methodology or scripts), execute `python {{KERNEL_HOME}}/scripts/doc_lint.py` to verify mechanical coherence

¶ 3 — Critérios

targeted edits when possible; regenerating entire file is exception
documentation reflects current code, not intended future state
operator formatting conventions respected
headers follow pattern `§ N.M. Name` defined in project
does not document unimplemented functionality as if ready
