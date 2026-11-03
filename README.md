# TASK — Taller Agent System Kernel

¶ - Governance, structural navigation and evidence across coding-agent harnesses.

**A governance kernel for AI coding agents, installed before any harness and shared by all of them.**

Version 2.0.0 · [Taller Personal Noncommercial License 1.0](LICENSE) · created by Vinícius Campos ([Taller](https://github.com/campzvini))

The Taller Agent System Kernel (TASK) is the operating layer I built to work with AI agents every day:
a global policy, a language written for agents to read, a spec-driven workflow, a navigation index for
source code, and the skills and scripts that hold it together. It is not a product. It is a method,
released so anyone can use it, change it, and build on it.

This README explains what each part is and, above all, **why** it exists.

---

## Contents

1. [The problem it solves](#1-the-problem-it-solves)
2. [The idea: a kernel before the harness](#2-the-idea-a-kernel-before-the-harness)
3. [TDSL — a language for agents](#3-tdsl--a-language-for-agents)
4. [Who reads it decides the form](#4-who-reads-it-decides-the-form)
5. [Code anchors — `§`, `¶` and `※`](#5-code-anchors----and-)
6. [Spec-driven development — records, not bureaucracy](#6-spec-driven-development--records-not-bureaucracy)
7. [Scripts gather, agents judge](#7-scripts-gather-agents-judge)
8. [Economy, truth and limits](#8-economy-truth-and-limits)
9. [Skills](#9-skills)
10. [Supported harnesses](#10-supported-harnesses)
11. [Installation](#11-installation)
12. [Repository layout](#12-repository-layout)
13. [Contributing](#13-contributing)

---

## 1. The problem it solves

¶ 1 — The problem it solves

Working with an agent is communication over a noisy channel. Every instruction, briefing, spec and
handoff is a message, and each one can be read more than one way. Prose is the noisiest encoding
available: a sentence a human finds clear can be read three ways by a model, the same word means
different things in different files, and every ambiguity is a place where the agent fills the gap by
inventing. That invention is entropy, and in a long session it compounds.

TASK treats this as an information problem. Shannon's insight is that a message is useful in proportion
to how much uncertainty it removes, and that noise is what the channel adds that the sender did not
mean. Wittgenstein's is that the limits of a language are the limits of what can be said clearly in it,
and that meaning is fixed by use within a defined practice. Put together, the problem is this:

**how do you communicate with an agent so that each token carries the most information and the least
noise, and the agent's next step is determined by the message rather than guessed from it?**

TASK's answer is to make the communication model as deterministic as it can be:

- **A closed language.** TDSL gives every instruction one reading. Its grammar limits what can be said,
  so that what is said cannot drift.
- **A recipient rule.** Who reads a text decides its form; agents always receive TDSL, humans always
  receive natural language. No channel mixes the two.
- **A procedure, not advice.** The spec-driven flow (constitution, spec, plan, tasks, analysis,
  execution) turns intent into records, and records into a fixed order of steps. Each phase reads
  only what its predecessors wrote.
- **A map the agent walks.** Records, phase gates, routed policies and code anchors together form a
  map of where the agent is, what it may read, what comes next and when to stop. The agent does not
  re-derive the path each session; it follows it.

The practical symptoms this removes are familiar: four harnesses with four drifting copies of the same
rules, prose instructions paid for on every turn, whole files read to find one function, architecture
re-derived by every session, and delegation that loses or invents detail between agents. Each is a
form of the same noise, and each is answered by one deliberate choice described below.

## 2. The idea: a kernel before the harness

¶ 2 — The idea: a kernel before the harness

TASK sits **underneath** the harness, the way an operating-system kernel sits under applications.
There is one copy of the kernel on the machine (`~/.task`): scripts, policies, grammar, skills and your
configuration. Each harness receives only a thin adapter — its rules file and its skill folder — that
points back to that single kernel.

**Why this matters**

- **One source of truth.** Change a rule once; every harness follows it.
- **Model and vendor independence.** The same prompt works in Claude, Codex, Gemini, DeepSeek or a local
  model, because the method lives in the kernel, not in a vendor's feature set.
- **Portability of your way of working.** Switch harness, add a new one, or give your setup to a partner:
  the behaviour comes with you.
- **Graceful degradation.** Where a harness has hooks (Claude Code, Codex), rules are enforced
  mechanically. Where it does not (Antigravity, Cline), the same rules are followed by instruction,
  because the policy tells the agent which script to run and when.

## 3. TDSL — a language for agents

¶ 3 — TDSL — a language for agents

TDSL (Transformer Deterministic Semantic Language) is a small, line-oriented notation for writing instructions and
records that agents read. A fragment:

```text
delegation:
  default inline
  delegate_only_if large_or_multi_file | parallelizable | would_pollute_main_context
  doubt -> inline
```

Its principles are **maximum information per token, minimum invention, semantics over syntax**.

**Why a new language instead of prose, JSON or YAML**

- **Prose is ambiguous.** Natural language invites interpretation; agents fill gaps with plausible
  invention. TDSL states keys, values, collections and conditions (`condition -> action`) explicitly, so
  there is less to interpret and less to invent.
- **Prose is expensive.** Instructions are re-sent every turn. A rule that takes three sentences in
  English takes one line in TDSL, and that saving is multiplied by every turn of every session.
- **JSON and YAML are for machines, not for reasoning.** They carry syntax that adds tokens without
  meaning (quotes, braces, strict nesting) and they cannot express "if this, then that" naturally.
  TDSL keeps the structure a parser needs and the readability a model needs.
- **Deterministic shape.** Two-space indentation, full-line comments, one property per line, a fixed
  header for tracked records. Records written by different agents look the same, so they can be
  validated, diffed and compared by scripts.
- **Versioned and governed.** The canonical grammar and its JSON schemas ship with the kernel
  (`kernel/grammar/`). Records declare their dialect and schema revision, so a change of grammar is
  explicit, never silent.

**The gain:** shorter context, fewer misreadings, and instructions that mean the same thing to every
model that reads them.

## 4. Who reads it decides the form

¶ 4 — Who reads it decides the form

Every document or message has one primary reader, and the reader decides its form:

| Reader | Form | Examples |
| --- | --- | --- |
| A person | natural language, in the operator's chosen language | chat replies, README, changelog, PR descriptions, commit messages |
| An agent | TDSL, pure | policy, rules files, skills, briefings, handoffs, specs, plans, tasks, agent-to-agent messages |

The agent classifies the reader **before** writing, never mixes forms in one artifact, asks when a
surface is not listed, and writes two linked artifacts when both audiences need the same content.
Every message one agent sends to another is TDSL — whatever the harness, model or vendor on the
other side — and the orchestrating agent translates for the human.

**Why:** humans and agents read differently. Prose aimed at a model wastes tokens and invites
interpretation; TDSL aimed at a human is hard to read. Deciding by reader, deterministically, removes
the guesswork and keeps delegation lossless.

## 5. Code anchors — `§`, `¶` and `※`

¶ 5 — Code anchors — `§`, `¶` and `※`

Every source file gets a comment-only index: a header with its purpose, and numbered chapters at
module level.

```rust
// ────────────────────────────────────────────
// myapp 1.0.0 — parser.rs
// § - Parse configuration files into typed settings · Rust
// <your signature>
// VAI CORINTHIANS!
// ────────────────────────────────────────────

// ── § 1 — TYPES — Settings model and parse errors ──
// ── § 2 — LEXER — Tokens from raw text ──
// ── § 3 — PUBLIC API — parse and validate ──
```

- `§` indexes source code (header `§ -` plus numbered chapters `§ n — DOMAIN — responsibility`).
- `¶` indexes TDSL and agent-facing markdown the same way.
- `◇` marks a provisional section; promotion to `§` preserves its stable `anchor_ref`.
- Stable typed references identify directories, files and sections independently of paths and numbers.
  Binary files and unsafe comment formats receive identities only in the external registry.
- `※` marks an optional typed comment — `invariant`, `boundary`, `decision`, `risk`… — for context that
  cannot be read from the code itself.

**Why**

- **One search returns the map of a file.** Searching for `§` gives the purpose and every chapter with
  its line number, without reading the body. The agent then reads only the range it needs.
- **Review becomes staged and cheap:** pull the index of everything in scope, reason over the index,
  read only the chapters that can hold the answer, and read whole files only when proven necessary.
- **Comment-only, so it is safe on any code, including third-party code.** The `diagram_check.py guard`
  command verifies that an edit touched nothing but comments; behaviour cannot change.
- **The banner is rendered by a script**, so every file in every project looks the same no matter which
  agent wrote it.

The persistent identity registry is `.task/tracking/registry.json`; Markdown and machine projections
under `.agent-cache/tracking/` are rebuildable. The tracker locates elements and references, reports
ambiguity and records removals. It never runs tests, judges quality or declares tasks complete.

Before an intervention: resolve the destination, consult governing sources and relevant history,
inspect what exists, then reuse, modify, create or do nothing. Record material changes and reconcile
the index afterwards. Hooks assist this process; explicit reconciliation covers changes they miss.

## 6. Spec-driven development — records, not bureaucracy

¶ 6 — Spec-driven development — records, not bureaucracy

Each planning phase produces its owned artifact in `.task/`; Architecture.md contains only the intended tree:

```
constitution → Architecture.md → features → spec → (clarify) → plan → tasks → analysis
                                                                     ↓
                                      Execute 0 (integral) → execution loop
```

A single entry skill, `protocol`, reads the project state and routes to the right phase; the agent
never picks a phase on its own. A gate script checks that a phase's predecessors exist before its
record is written.

**Design choices and their reasons**

- **Constitutional authority.** The constitution is the highest project policy and each version is
  preserved. Code establishes existing behavior; differences must be reconciled against policy.
  Planning, observed structure and operational history remain distinct.
- **The gate checks structure, never permission.** It refuses a broken reference (a plan without a
  spec), not a decision. Judgement stays with the operator; consistency is mechanical.
- **One proposition, one location.** Downstream records reference upstream ids instead of restating
  them, so a decision changes in one place.
- **Unknowns are explicit.** Material uncertainty is written down as unknown, never silently assumed.
- **Planning and runtime are separate.** Progress lives in an execution journal, never inside the plan.

**Two planning modes**

| Mode | How it works | When to choose it |
| --- | --- | --- |
| `gradual` | one feature goes from spec to execution before the next opens | you want feedback from real code early |
| `integral` | every feature is specified, planned, tasked and analysed before any code is written | you want the whole architecture settled and reviewable up front |

Switch at any time with `sdd_gate.py mode <gradual|integral>`; `sdd_gate.py roadmap` shows the
planning position of every feature.

Planning mode and execution authority are independent. `interactive` is the default, including for
existing projects. Explicitly authorized `autonomous` execution continues through the declared package
until completion or a real block; choosing `integral` alone never grants that authority.

`Architecture.md` contains only the intended directory and file tree. Integral execution starts with
Execute 0: inspect existing destinations, create safe missing structure, add provisional `◇` sections
and reconcile indices. Scaffold presence is never functional completion.

The orchestrator selects a whole feature, task group or single task from dependencies, difficulty and
write scope. `max_active_subagents` defaults to one. Parallel units require exclusive destinations,
including reports and temporary files. Test-author separation is configurable; independent validation
criteria and the orchestrator's test gate remain required.

Execution, decisions and material failures have separate append-only journals. Completion checkboxes
are projections of execution history, never a second mutable status inside the task plan.

## 7. Scripts gather, agents judge

¶ 7 — Scripts gather, agents judge

Everything mechanical is done by deterministic Python scripts: reading project state, rendering
anchors, checking that an edit was comment-only, validating records, preparing commit context,
running the self-test. Everything that needs judgement — what a chapter is about, whether a plan is
sound — is left to the agent.

**Why:** a model asked to count, format or validate does it slightly differently each time and spends
tokens doing it. A script does it the same way every time, for free. Splitting the work this way makes
results reproducible across models and keeps the agent's attention on decisions.

## 8. Economy, truth and limits

¶ 8 — Economy, truth and limits

The global policy also fixes how the agent spends effort and what it trusts:

- **Cost is turns × context.** Batch reads, chain commands, never re-read what is already in context.
  The aim is fewer round trips, not smaller reads.
- **Inline first.** Spawning another agent costs a cold start that re-derives everything; the policy
  delegates only when work is large, parallel, would pollute the context, or needs a different model
  tier — and then with a TDSL briefing contract.
- **Authority and observation are distinct.** The constitution governs what is permitted; code
  establishes what exists. Indices locate both without judging them. Build and test claims require
  the relevant command to have run.
- **Hard limits.** Destructive or outward-facing actions are confirmed first; production dependencies
  need the operator's approval; original source files are not rewritten without instruction.

**The gain:** predictable cost, fewer confident-but-wrong statements, and no surprises in your
repository.

## 9. Skills

¶ 9 — Skills

Skills are folders with a `SKILL.md` that the agent loads only when a task needs them, so they cost
nothing until used.

| Group | Skills |
| --- | --- |
| Governed workflow | `protocol` (entry and router), `constitution`, `specify`, `clarify`, `plan`, `tasks`, `decompose`, `analyze`, `execute`, `architecture` |
| Code navigation | `diagram` (apply the anchors), `code-map` (index a file or a whole project) |
| Session work | `commit`, `review`, `debug`, `handoff`, `refactor-plan`, `pr-description`, `dependency-check`, `doc-update`, `test-protocol`, `provenance` |

Phase skills are deliberately reached only through `protocol`, so the order of the workflow is never
skipped by accident.

## 10. Supported harnesses

¶ 10 — Supported harnesses

| Harness | Global rules | Skills | Mechanical enforcement (hooks) |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | yes | yes |
| Codex | `~/.codex/AGENTS.md` | yes | yes |
| Antigravity | `~/.gemini/GEMINI.md` | yes | no — the agent runs the scripts itself |
| Cline | `~/Documents/Cline/Rules/` | yes | no — the agent runs the scripts itself |

Any harness that reads a global instruction file can host the kernel; see `adapters/ADAPTERS.tdsl`.

## 11. Installation

¶ 11 — Installation

The installer is your own agent.

1. Download the [latest release](https://github.com/campzvini/taller-agent-system-kernel/releases) or
   clone this repository.
2. Open your agent and say:
   > Install the kernel from `<path to this folder>` following `INSTALL.md`.
3. Answer its questions.

Requirements: Python 3.10+ and git.

**Why an agent installs it:** the right placement depends on your harness, your operating system and
what you already have configured. An agent can detect all of that, explain each option, back up what
it changes, and verify the result — something a static script cannot do across four harnesses.

During installation the agent explains, with pros and cons, and records your choices:

- the signature on indexed files (or none)
- your profile and the language it should talk to you in
- its posture (thought partner or executor) and response style (dense or balanced)
- whether commits may carry an AI co-author trailer
- whether it may edit documentation without being asked
- the default planning mode (`gradual` or `integral`)
- your stance on tests

Everything is stored in `~/.task/kernel.config.json` and in your rules file, between
`<!-- task:begin -->` and `<!-- task:end -->`, so your own content is kept and upgrades replace only
that block.

## 12. Repository layout

¶ 12 — Repository layout

```
INSTALL.md                  instructions executed by the installing agent (TDSL)
kernel/policy.tdsl.md       the global policy template
kernel/docs/                routed policies: engineering, sdd, delegation
kernel/skills/              skills (SKILL.md folders)
kernel/scripts/             deterministic Python tooling and self-test
kernel/grammar/             canonical TDSL grammar and JSON schemas
kernel/templates/           AGENTS.md, briefing and cross-model prompt templates
adapters/                   per-harness placement and hook configuration
kernel.config.example.json  shape of the installer's answers
```

## 13. Contributing

¶ 13 — Contributing

This is a contribution, not a product: issues, ideas and pull requests are welcome.
See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and versioning.

## 14. Upgrade from 1.x

¶ 14 — Upgrade from 1.x

Keep a reviewable checkout before upgrading the installed kernel. Legacy planning records and
feature journals remain readable; migration is explicit and preserves the existing interactive
authority. New task contracts separate runtime state from planning. Do not rename a dialect header
to migrate: use the matching schema and preserve predecessor versions. Schema revision hashes remain
in use; structural identities do not depend on content hashes.

Use `execution_runtime.py --root <project> migrate` for project adoption and inspect its output before
enabling autonomy. Reconcile with `structure_tracker.py --root <project> scan`; resolve ambiguous
movements explicitly. Source-provenance review and batch brownfield rediagramming are optional, scoped
operations with attribution and a nonfunctional baseline preserved.
