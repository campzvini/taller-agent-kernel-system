# Taller Agent Kernel System

A pre-harness governance kernel for AI coding agents: one global policy, a spec-driven workflow,
a navigation index for source code, and a set of skills and deterministic scripts — installed by
your own agent, into whichever harness you use.

Version 1.0.0 · [Taller Personal Noncommercial License 1.0](LICENSE) · contributions welcome.

## What you get

- **Global policy** in TDSL, a compact language written for agents to read: how the agent talks to you,
  routes work, spends tokens, treats code as the source of truth and asks before destructive actions.
- **Spec-driven development** (`protocol` skill): constitution → spec → plan → tasks → analysis → execute,
  with a gate that checks each record's predecessors. Two planning modes: *gradual* (one feature at a time)
  and *integral* (plan every feature before writing any code).
- **Code anchors**: a comment-only `§` index in every source file (header plus numbered chapters), so any
  agent can find the right section with one search instead of reading whole files.
- **Session skills**: commit, review, debug, handoff, refactor-plan, code-map, diagram, doc-update and more.
- **Scripts** (Python 3.10+) that do the mechanical work — gates, index rendering, code-safety guard, self-test.

## Supported harnesses

| Harness | Global rules | Skills | Hooks (mechanical enforcement) |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` | yes | yes |
| Codex | `~/.codex/AGENTS.md` | yes | yes |
| Antigravity | `~/.gemini/GEMINI.md` | yes | no — the agent runs the scripts itself |
| Cline | `~/Documents/Cline/Rules/` | yes | no — the agent runs the scripts itself |

Other harnesses that read a global instruction file can host it too; see `adapters/ADAPTERS.tdsl`.

## Install

1. Download the zip or clone this repository.
2. Open your agent (any harness above) and tell it:
   > Install the kernel from `<path to this folder>` following `INSTALL.md`.
3. Answer its questions. It explains each option (signature, language, response style, planning mode…)
   and backs up anything it changes.

Requirements: Python 3.10+ and git.

## Layout

```
INSTALL.md                  instructions for the installing agent
kernel/policy.tdsl.md       global policy template
kernel/docs/                routed policies: engineering, sdd, delegation
kernel/skills/              skills (SKILL.md folders)
kernel/scripts/             deterministic Python tooling
kernel/grammar/             canonical TDSL grammar and schemas
kernel/templates/           AGENTS.md, briefing and prompt templates
adapters/                   per-harness placement and hook configuration
kernel.config.example.json  the installer's answers end up here
```

## A note on the signature

Indexed source files carry a small header banner. Its last line defaults to `VAI CORINTHIANS!` —
a harmless joke and a reminder that whoever ships the code signs it. Change or remove it at install
time or later in `kernel.config.json`.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).
