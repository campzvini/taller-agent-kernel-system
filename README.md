# TASK — Taller Agent System Kernel

**A governance kernel for AI coding agents, installed before any harness and shared by all of them.**

Version 1.1.0 · [Taller Personal Noncommercial License 1.0](LICENSE) · created by Vinícius Campos ([Taller](https://github.com/campzvini))

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

Agents are extremely capable, but capability without method turns into noise:

- **Every harness has its own rules format.** Claude Code reads `CLAUDE.md`, Codex reads `AGENTS.md`,
  Antigravity reads `GEMINI.md`, Cline reads a rules folder. Keep four copies by hand and they drift
  apart within weeks — the same instruction ends up meaning four different things.
- **Prose instructions are ambiguous and expensive.** A paragraph that a human finds clear can be read
  three ways by a model, and it is re-sent on every turn, paying tokens each time.
- **Agents read whole files to find one function.** On a large codebase that is most of the cost of a
  session, and most of the context window filled with things that did not matter.
- **"Just write the code" does not scale.** Without written decisions, each session re-derives the
  architecture, and two agents working in parallel make incompatible choices.
- **Delegation without a contract is lossy.** When one agent hands work to another in free prose, detail
  is dropped, invented or misread.

TASK answers each of these with one deliberate choice, described below.

## 2. The idea: a kernel before the harness

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

TDSL (Taller Domain-Specific Language) is a small, line-oriented notation for writing instructions and
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

**The gain:** large codebases become navigable at a fraction of the reading cost, and an index made
by one agent is immediately usable by any other.

## 6. Spec-driven development — records, not bureaucracy

Governed work moves through phases, each producing one TDSL record in `.protocol/`:

```
constitution → spec → (clarify) → plan → tasks → analysis → execute
```

A single entry skill, `protocol`, reads the project state and routes to the right phase; the agent
never picks a phase on its own. A gate script checks that a phase's predecessors exist before its
record is written.

**Design choices and their reasons**

- **Records, not authorities.** A record states decisions; it never carries "approved" or "passed".
  The operator is in the room and decides. This avoids a ceremony of sign-offs that would attest
  nothing the conversation does not already show.
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

**The gain:** decisions survive across sessions and agents, parallel agents work against the same
plan, and code is written against something that can be checked.

## 7. Scripts gather, agents judge

Everything mechanical is done by deterministic Python scripts: reading project state, rendering
anchors, checking that an edit was comment-only, validating records, preparing commit context,
running the self-test. Everything that needs judgement — what a chapter is about, whether a plan is
sound — is left to the agent.

**Why:** a model asked to count, format or validate does it slightly differently each time and spends
tokens doing it. A script does it the same way every time, for free. Splitting the work this way makes
results reproducible across models and keeps the agent's attention on decisions.

## 8. Economy, truth and limits

The global policy also fixes how the agent spends effort and what it trusts:

- **Cost is turns × context.** Batch reads, chain commands, never re-read what is already in context.
  The aim is fewer round trips, not smaller reads.
- **Inline first.** Spawning another agent costs a cold start that re-derives everything; the policy
  delegates only when work is large, parallel, would pollute the context, or needs a different model
  tier — and then with a TDSL briefing contract.
- **Code is the truth.** Documents describe intent and may be out of date; when they disagree with the
  code, the code wins and the divergence is reported. A build or test status is never asserted
  without running the command.
- **Hard limits.** Destructive or outward-facing actions are confirmed first; production dependencies
  need the operator's approval; original source files are not rewritten without instruction.

**The gain:** predictable cost, fewer confident-but-wrong statements, and no surprises in your
repository.

## 9. Skills

Skills are folders with a `SKILL.md` that the agent loads only when a task needs them, so they cost
nothing until used.

| Group | Skills |
| --- | --- |
| Governed workflow | `protocol` (entry and router), `constitution`, `specify`, `clarify`, `plan`, `tasks`, `decompose`, `analyze`, `execute` |
| Code navigation | `diagram` (apply the anchors), `code-map` (index a file or a whole project) |
| Session work | `commit`, `review`, `debug`, `handoff`, `refactor-plan`, `pr-description`, `dependency-check`, `doc-update`, `test-protocol` |

Phase skills are deliberately reached only through `protocol`, so the order of the workflow is never
skipped by accident.

## 10. Supported harnesses

| Harness | Global rules | Skills | Mechanical enforcement (hooks) |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | yes | yes |
| Codex | `~/.codex/AGENTS.md` | yes | yes |
| Antigravity | `~/.gemini/GEMINI.md` | yes | no — the agent runs the scripts itself |
| Cline | `~/Documents/Cline/Rules/` | yes | no — the agent runs the scripts itself |

Any harness that reads a global instruction file can host the kernel; see `adapters/ADAPTERS.tdsl`.

## 11. Installation

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

This is a contribution, not a product: issues, ideas and pull requests are welcome.
See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and versioning.
