---
name: diagram
description: Apply or repair the § header and chapter markers in source files, via diagram_check.py. Use when delivering new code, or when code-map reports a file has no anchors.
---

¶ - Apply TDSL anchor diagramming with section markers to source files

skill:
  id: @skill/diagram

¶ 1 — Invariantes

NEVER write a banner by hand. Always generate via `diagram_check.py render`.
Run `diagram_check.py guard` for changes claimed to be comment-only. Functional edits use the normal declared validation and are never reverted merely because this guard detects code changes.
Top-level chapters remain module-level at column zero. A subsection may split one oversized item using its native indentation, as engineering ¶5 permits.
Header respects the language's anchor: shebang (`#!`) stays on line 1; Rust crate attributes (`#![...]`), `package`/`<?php`/pragmas come before the header. The header never pushes these lines down.
Do not invent a chapter where there is no logical boundary. Skip it and report; generic titles pollute the code-map.
Chapter titles declare a domain plus an observable responsibility or result. `UTILS`, `HELPERS`, `MISC`, `LOGIC`, and `METHODS` alone are invalid navigation context.
`※` semantic comments are optional and deliberate. Add one only for the closed vocabulary and authoring conditions in `{{KERNEL_HOME}}/docs/engineering.tdsl ¶6`; never promote ordinary narration.

¶ 2 — Procedimento

1 obtain session file list: `python {{KERNEL_HOME}}/scripts/diagram_check.py scan` (no args uses `git diff --name-only HEAD`). Read `.agent-cache/diagram-report.md`.
2 for each file with status `warn` (missing header or legacy style)
  a run `code-map` to discover structure cheaply, without rereading the entire file
  b decide chapter boundaries and titles (JUDGMENT). Level 1 in UPPERCASE, level 2 in TitleCase, numbering l1=integer, l2=integer.integer; every title names a domain and observable responsibility
  c generate each piece with `diagram_check.py render` (see examples below), passing `--file <path>` to infer delimiter and language
  d insert pieces via edit: header at top (respecting invariant 4), chapters immediately before each logical section
3 for diagram-only edits run `python {{KERNEL_HOME}}/scripts/diagram_check.py guard <file>`. A failure requires targeted diagnosis and correction; preserve functional and unrelated edits.
4 when a commit is authorized, keep diagram-only work traceable with `chore(diagram): apply section banners`; never fabricate a nonfunctional baseline for functional work.
5 report to operator: files diagrammed, skipped and why.

¶ 3 — Render Examples

Base command: `python {{KERNEL_HOME}}/scripts/diagram_check.py render <level> --file <path> [flags]`

Line style (// for Rust, C/C++, C#, JS/TS, Go, Java, Kotlin, Swift):

```text
// ────────────────────────────────────────────
// MYAPP 1.0 — OrganizeView.tsx
// § - Orchestrate the Organize tab · TypeScript
// <signature author, omitted when empty>
// VAI CORINTHIANS!
// ────────────────────────────────────────────

// ── § 1 — TYPES AND CONSTANTS — Tab contracts ──

// ── § 1.1 — Scope Defaults — Per-tab scope seed ──
```

Line style (# for Python, Ruby, Shell, PowerShell):

```text
# ────────────────────────────────────────────
# DNG_MV 0.4 — pipeline.py
# § - Convert RAW frames into DNG files · Python
# <signature author, omitted when empty>
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — INGEST — Frame intake and validation ──
```

Line style (-- for SQL, Lua, Haskell):

```text
-- ────────────────────────────────────────────
-- TLR 1.0 — schema.sql
-- § - Define the preservation database schema · SQL
-- <signature author, omitted when empty>
-- VAI CORINTHIANS!
-- ────────────────────────────────────────────

-- ── § 1 — TABLES — Core archival entities ──
```

Block style (/* */ for CSS, SCSS) — each line wrapped for guard recognition:

```text
/* ──────────────────────────────────────────── */
/* DARKROOM 0.2 — negatives.css */
/* § - Style the negative viewer · CSS */
/* <signature author, omitted when empty> */
/* VAI CORINTHIANS! */
/* ──────────────────────────────────────────── */

/* ── § 1 — LAYOUT — Viewer grid ── */
```

Block style (<!-- --> for HTML, XML, SVG):

```text
<!-- ──────────────────────────────────────────── -->
<!-- DARKROOM 0.2 — index.html -->
<!-- § - Host the Darkroom application shell · HTML -->
<!-- <signature author, omitted when empty> -->
<!-- VAI CORINTHIANS! -->
<!-- ──────────────────────────────────────────── -->

<!-- ── § 1 — HEAD — Metadata and assets ── -->
```

¶ 4 — Critérios

no banner written by hand; all via `render`
diagram-only guard green for diagram-only changes; functional work uses its declared validation
top-level chapters at module level; oversized-item subsections follow engineering ¶5
header respects shebang/attributes/pragmas of language
titles meaningful; file without clear boundary is skipped, not invented
semantic comments explain only non-local rationale, invariants, boundaries, decisions, effects, assumptions, relations or risks
code remains the source of truth; index and context comments are preliminary navigation context
block-comment language uses line-by-line wrapped banner

¶ 5 — Provisional Identity and Audit

provisional:
  marker: ◇
  identity: anchor_ref_preserved_on_executor_promotion_to_§
  validation: promotion_not_proof
coverage:
  safe_comments: physical_markers
  unsafe_formats: external_registry_only
audit:
  script: shape_duplicates_unresolved_refs_generic_title_patterns
  agent: title_and_boundary_usefulness_from_targeted_source
brownfield:
  opt_in: selected_files_only
  baseline: before_changes
  verification: comment_only_guard_for_diagram_only_edits
  preserve: origin_and_attribution
rule: functional_changes_use_normal_validation_not_comment_guard
rule: never_revert_unrelated_changes_on_guard_failure
