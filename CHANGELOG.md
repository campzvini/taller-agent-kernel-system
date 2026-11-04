# Changelog

¶ - Release changes and migration boundaries.

## Unreleased

Fix explicit execution entry and reuse of prepared structure. Code-map and tool hooks no longer
trigger reconciliation; stale scaffold inventory no longer blocks claims. Diagramming is limited
to explicit feature tasks. Keep the current version unchanged.

¶ 1 — Version 2.1.0

## 2.1.0 — 2026-11-03

Adds an independent diagram CLI with preview-first adopt, conservative upgrade and snapshot-backed
verification. Python transformations use standard-library syntax and token parsing, preserve
existing identities and provisional markers, and record immediate pre-application originals.
Other languages remain pending rather than receiving unsafe automatic transformations. Structural
tracking is optional and no governed project or new hook is required. Includes installed-layout
integration coverage and documents adapter, semantic-review and full-scan limits.

Uses the Taller Personal Noncommercial License 1.0 for original material: free personal
noncommercial use, separate paid business licensing, and explicit identification of unofficial
adaptations.
Records the official Taller distribution and contribution terms for future commercial licensing.

¶ 2 — Version 2.0.0

## 2.0.0 — 2026-11-03

Adds intended/observed/historical state, immutable constitutional revisions, tree-only architecture,
stable structural identity and provisional sections. Introduces deterministic reconciliation and
safe integral scaffolding, adaptive execution units, explicit autonomy, configurable test authorship,
and execution/decision/failure journals with derived progress. Legacy projects retain interactive
authority; adopting new contracts requires migration. Completed after operator review and merged into master.

## 1.1.0 — 2026-11-02

Renamed to TASK — Taller Agent System Kernel. Delivery model reworked.

- Rename: TAKS -> TASK. `kernel_home` default `~/.taks` -> `~/.task`; rules-file markers `taks:begin/end` -> `task:begin/end`; document ids `taks.*` -> `task.*`. Upgrading from 1.0.0: move `~/.taks` to `~/.task` and replace the old marker block.
- Global policy ¶10 gains `problem_triage`: training -> web documentation -> only then the operator; no spikes or extra validation rounds when a known answer exists.
- `test-protocol` ¶3 Test Triage: every validation is classified before it becomes a test; tautological tests banned.
- `sdd` ¶13: integral mode ends with one analysis subagent over the whole package, then fixes, then a ready package.
- `sdd` ¶14 Delivery Session: no initial analysis or test run; orchestrator / test_author / executor roles; tests written before code; executor never edits tests nor escalates to the operator; one feature in flight; close without asking when the constitution pre-directs it.
- `execute`, `protocol`, `analyze`, `constitution`, `delegation`, briefing template aligned with the above.
- Governed project directory renamed `.protocol/` -> `.task/`. Upgrading: rename the directory in each governed project.
- `ADAPTERS.tdsl`: Codex, Antigravity and Cline paths re-verified against current official docs.

## 1.0.0 — 2026-10-31

First public release.

- Global policy template rendered by an agent-run installer interview (signature, profile, language, style, attribution, planning mode, test stance).
- Spec-driven workflow with `gradual` and `integral` planning modes (`sdd_gate.py mode`, `sdd_gate.py roadmap`).
- `§` anchor index profile, `diagram_check.py` (render, scan, guard) with configurable signature; guard reads git output as UTF-8.
- Bundled TDSL v3 grammar and schemas; schema lock regenerated from the bundled copy.
- Adapters for Claude Code, Codex, Antigravity and Cline.
