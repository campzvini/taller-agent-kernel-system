# Contributing

¶ - How to propose changes to the Taller Agent System Kernel.

```text
scope policy, skills, scripts, grammar, adapters for more harnesses
language English for files, identifiers and comments; TDSL for agent-facing documents
anchors every source file keeps its § header and chapters; run diagram_check.py scan before a PR
verify python kernel/scripts/selftest.py prints "selftest: OK"
versioning semantic: MAJOR policy or record-format break | MINOR new skill, mode or adapter | PATCH fix
changelog add an entry to CHANGELOG.md under Unreleased
personal_content keep names, paths and private projects out of the kernel; they belong in the installer interview
```

¶ 1 — Runtime and Contract Changes

Preserve legacy project behavior unless migration explicitly adopts a successor contract. Changes to
required fields, authority or reference meaning require a major dialect revision. Regenerate schema
locks and field contracts from the bundled registry; do not hand-edit their generated outputs.

Validate structural identity independently of paths, retries independently of task IDs, and derived
progress independently of planning records. The tracker must remain mechanical. Demonstrate safe
scaffolding, unresolved ambiguous moves and conservative migration with executable evidence.

Keep this release on its review branch until the operator evaluates it. Updating the repository does
not authorize installation into the live kernel or merging the branch.
