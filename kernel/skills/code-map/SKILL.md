---
name: code-map
description: Build a project-wide structural index from § and ¶ anchors, optionally enriched by typed ※ context comments, or map named files to exact Read ranges. Use at the start of repository work when ownership is unknown and before reading, delegating, reviewing, or refactoring large code.
---

¶ - Build cheap preliminary repository context and exact ranges for targeted source reads.

skill:
  id: @skill/code-map
  role project_context_then_targeted_read
  script {{KERNEL_HOME}}/scripts/code_map.py

¶ 1 — Authority

```text
source_code sole source of truth for current behavior
project_map initial structural context, may be incomplete or stale
context_map declared preliminary context, may be incomplete or stale
ban cite an index or comment map as proof of behavior
rule every behavioral claim that affects a decision requires a targeted source read

principle map the project, triage ownership, then read only the target range
cost a full read of a long file is the most common avoidable context expense
```

¶ 2 — Contracts

One mechanism, two glyphs. The script derives the anchor from the suffix.

```text
§ source_code            .rs .py .ts .go .java .c .rb .sh ...
¶ TDSL_and_agent_markdown .md .tdsl .txt .rst

header `<anchor> - <purpose>` one line, no number
chapter `<anchor> <n> — <TITLE>` and `<anchor> <n>.<m> — <Title>`
override --anchor section | pilcrow # for a file whose suffix lies about its content

※ source semantic context comment
  form `※ <kind> — <statement>`
  kinds [assumption boundary decision effect invariant rationale relation risk]
  associated with the nearest preceding § chapter
  ordinary comments are never promoted into the context map
```

¶ 3 — Modes

```text
project_orientation:
  run `python {{KERNEL_HOME}}/scripts/code_map.py --project .`
  read `.agent-cache/project-map.md`
  generated, dependency, cache and agent-private directories are pruned mechanically
  use when repository ownership or architecture is not already known this session

preliminary_semantics:
  run `python {{KERNEL_HOME}}/scripts/code_map.py --project . --context`
  read `.agent-cache/context-map.md` after the structural map
  use for cross-cutting changes, architecture, risk, authority or non-obvious constraints

targeted_file:
  run `python {{KERNEL_HOME}}/scripts/code_map.py <file> [<file> ...]`
  report lands in .agent-cache/map-<stem>.md, machine form in .agent-cache/map.json

machine_forms:
  project `.agent-cache/project-map.json`
  context `.agent-cache/context-map.json`

then:
  triage the index; name the files and chapters that can hold the answer
  Read(file, offset=<offset>, limit=<limit>) using the pair the map hands you
  verify comment-map claims in those source ranges before relying on them

ban reading the whole file once the map gave you a range
ban re-running the map on a file already mapped this session
```

Several files map in one call. Batch them; never one invocation per file.

¶ 4 — Reading the result

```text
OK   chapters found, no inconsistency
WARN no chapter found | header missing | duplicate number | broken sequence

no_chapter_found -> the file is not diagrammed
  consulting_only -> read it normally, do NOT stop to diagram
  editing_it -> invoke skill(diagram) for a source file
inconsistency_found -> report it; repair only if you are already editing the file
coverage_gap -> absent from preliminary context, never evidence that the file is irrelevant
context_conflict -> code wins; report divergence; repair only within authorized scope
```

¶ 5 — Boundaries

```text
read_only this skill never edits the mapped file
ban inventing a chapter boundary that the file does not mark
ban treating structure, titles or typed comments as current behavior without source verification
ban extracting ordinary comments into preliminary context
diagram_repair belongs to skill(diagram); ¶-anchored documents have no automated renderer
```
