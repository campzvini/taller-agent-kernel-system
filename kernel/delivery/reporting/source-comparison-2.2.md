# TASK 2.2 — Source specification comparison

¶ - Compare the operator-supplied loop specification with the implemented kernel and validation evidence.

¶ 1 — Source and Scope

Source: `TASK_2_1_especificacao_reorganizacao_loops.md`, SHA-256
`8cec2ea8435d2098a98b9fb995a676c007f7be5c236a4e4b986d2fc0f1d6354b`.
The operator designated this work as version **2.2.0**, despite the source document's 2.1 title.
The working baseline is `3d0a1be`, which includes the explicit-entry correction following the
source document's reference `61040ea`. Those corrections remain in force: no implicit execute
skill invocation, structural reconciliation only on express request, and no automatic diagram task.
The operator separately authorized source and text diagram standardization for this update.

¶ 2 — Final Criteria Crosswalk

| Source criterion | Applied result | Evidence |
| --- | --- | --- |
| 1. Department and loop ownership | Nine departments, four architectural levels and L01–L08 ownership | `system/routing/departments.json`; `behavior/loops/catalog.tdsl` |
| 2. Reuse without duplicate authority | 27 authoritative Python implementations; public scripts are thin entrypoints | Manifest uniqueness and original-versus-departmental AST comparison |
| 3. L02 successive sufficiency | Delimited request, loaded-context reuse, minimum next source, dynamic-state checks, explicit absence/uncertainty | `behavior/loops/L02.tdsl`; policy; code-map and protocol entrypoints |
| 4. L04 warm/cold entry | Contextual recovery of missing instructions, anchor/features, configuration, constitution and relevant history; runtime checks retained | `behavior/loops/L04.tdsl`; compact session snapshot; runtime and installed tests |
| 5. L08 authorized commit | Validation and review precede commit; exact owned paths, no repeat confirmation for existing authority, explicit blocked delivery | `behavior/loops/L08.tdsl`; commit/review skills; real-Git scope tests |
| 6. Distribution consistency | Policies, skills, templates, adapter boundaries, INSTALL and README describe the same department layout | Installed clean layout, rendered contracts and upgrade-preservation tests |
| 7. Stable public entrypoints | Existing script filenames, skill IDs, sibling imports and resource lookup retained | Installed CLI tests, full installed suite and selftest |
| 8. Existing project data preserved | No schema changes, no new warm/cold configuration fields and no project record migration | Grammar diff unchanged; upgrade keeps configuration, personal skill, backups and journal bytes |
| 9. Required validation executed | 90-test baseline; final source and installed suites; installed selftest | `validation-2.2.json` |
| 10. Functional and structural changes distinguished | Three context/Git helper extensions; departmental relocation and comment-only normalization tracked separately | Sections 3–5 below |

¶ 3 — Behavioral Acceptance Coverage

| Source scenarios | Contract and executable coverage |
| --- | --- |
| General request with sufficient context; reuse; incremental acquisition | L02 explicitly terminates acquisition when sufficient and chooses only the next relevant source. Code-map remains read-only and optional. No deterministic semantic classifier was added. |
| Project-specific behavior and mutable evidence | L02 requires actual project sources, and L04 confirms necessary mutable state. SessionStart emits an observed compact snapshot rather than a warm/cold verdict. |
| Warm execution; cold recovery | L04 centralizes the branch and delegates insufficiency to L02. Execute, protocol, delegation and project templates reference that contract. |
| Missing authority/dependencies; interrupted units | Existing execution/runtime tests retain authority, DAG, ownership, attempts and recovery checks. No task/configuration schema changed. |
| Authorized code delivery; blocked authority | L08 and commit skill distinguish validation, completion, authorization, commit and delivery. The existing helper observes but never stages or grants authority. |
| New, modified, removed, renamed or untracked code | Real Git fixtures test clean/no-code paths, document-only changes, additions, deletion, Unicode/space rename, and exact-path selection. |
| Unrelated staged changes and interrupted delivery | Tests verify preexisting staged content remains intact. Handoff reports HEAD and outstanding changes; both helpers must produce their JSON without changing HEAD, index or worktree. |
| Clean installation and upgrade | Full rendered installed layout runs the same suite. Upgrade fixture preserves operator configuration, personal content, backups and consumer journal bytes. |
| Hooks and regression | Installed Codex and Claude gates retain write checks and emit no automatic PostToolUse reconciliation/commit. Existing journals, SDD, structural/scaffold and diagram suites remain active. |

Behavioral sufficiency and warm/cold are agent instruction contracts. Automated tests demonstrate
mechanical observations, wiring and runtime invariants; they do not claim universal compliance by
all models or harnesses. Harnesses without complete hooks use the same policy and skills.

¶ 4 — Physical Compatibility and Diagram Integrity

Implementations moved to departments once. `scripts/_entrypoint.py` executes each implementation
in its existing public module namespace. `__file__` remains the public script path for established
resource lookup; tracebacks and `__task_implementation__` identify the departmental source.
This preserves sibling imports and pinned schema lookup without parallel implementations.

Python headers and chapters were normalized through the existing renderer. AST comparison verified
that the formatting pass alone did not change executable code. Comment-safe Markdown, TDSL and
prompt templates have purpose and chapter anchors. The tree-only architecture template, machine
JSON/schema/configuration, VERSION and LICENSE retain their native formats; invalid comment markers
were not inserted. These boundaries are recorded in the department manifest.

Pinned schema JSON is copied byte-for-byte during installation. Rendering is confined to the
existing text/template contract; normalizing schema bytes would invalidate their revision pins.

¶ 5 — Result and Delivery Boundary

The source's scoped L02/L04/L08 changes, department migration, existing entrypoint compatibility,
installed validation and diagram standardization are represented in the applied result. The other
loop IDs locate existing responsibilities without introducing new behavioral algorithms.
No new dependency, operational journal, initializer, installer, task field or schema was introduced.
The live operator installation is distinct from the isolated installed-layout verification.
Git commit, merge and push are performed under the operator's explicit authorization for this update.
