# Changelog

## 1.0.0 — 2026-10-31

First public release.

- Global policy template rendered by an agent-run installer interview (signature, profile, language, style, attribution, planning mode, test stance).
- Spec-driven workflow with `gradual` and `integral` planning modes (`sdd_gate.py mode`, `sdd_gate.py roadmap`).
- `§` anchor index profile, `diagram_check.py` (render, scan, guard) with configurable signature; guard reads git output as UTF-8.
- Bundled TDSL v3 grammar and schemas; schema lock regenerated from the bundled copy.
- Adapters for Claude Code, Codex, Antigravity and Cline.
