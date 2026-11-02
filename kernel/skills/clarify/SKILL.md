---
name: clarify
description: Resolve material unknowns in an existing spec by asking the operator targeted questions, then emit the next spec version. Use when the spec carries explicit_unknowns, when analyze routes a defect back to the specification, or when the operator says the spec is vague, ambiguous, or underspecified. Governed replacement — never an in-place edit.
---

¶ - Resolve explicit unknowns in spec through targeted questions, emit next version.

skill:
  id: @skill/clarify
  phase clarify
  output_dialect spec@1
  output_path .task/features/<feature_id>/spec.tdsl
  skeleton {{KERNEL_HOME}}/skills/specify/template.tdsl # clarify emits a spec, it owns no shape of its own

¶ 1 — What this is

A governed replacement operation, not an annotation pass.

```text
input current_spec, material_unknowns, operator_dialogue
output next_spec_version

ban in_place_mutation without a version bump
ban a parallel clarifications artifact competing with the spec
ban inferring the operator answer from context, precedent, or plausibility
```

The difference from a Spec Kit clarify: there, answers are appended to the same
file as a Clarifications log. Here the spec is replaced, the version increments,
and whatever the change makes incoherent downstream is reported by analyze as
content, not as a status. Nothing accumulates as sediment inside the record.

¶ 2 — Preconditions

```text
1 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py state
2 spec absent -> this is not clarify; invoke_skill(specify)
3 read the current spec and its explicit_unknowns
4 read the constitution: an unknown the constitution already answers is not an unknown
```

¶ 3 — Find what is actually unresolved

Scan the current spec for material uncertainty. Material means: two competent
readers would build different systems, or a downstream artifact cannot be
authored without guessing.

```text
sources:
  explicit_unknowns declared by the spec
  requirement whose statement admits more than one behavior
  journey whose acceptance references no requirement
  criterion with no measure, or a measure with no unit or threshold
  term used normatively but never fixed as an entity
  non_goal absent where scope is visibly contested

not_material:
  wording preference
  anything the constitution already decides
  implementation choice # belongs to plan, not spec
  a question whose answer changes no requirement
```

¶ 4 — Ask

```text
batch ask in one round; never drip one question per turn
limit at most 5 questions per round, highest impact first
form each question states what is unresolved, why it blocks, and the options with their consequence
default offer a recommended option only when one is genuinely better, and say why
ban leading questions, compound questions, and questions whose answer you already hold

operator_declines_to_decide -> the unknown stays an explicit_unknown; say what it blocks downstream
operator_answers_partially -> resolve what was answered, keep the rest unresolved
```

Use the AskUserQuestion tool when the options are enumerable; use plain prose
when the answer is open-ended.

¶ 5 — Emit

```text
1 version+1; status: proposed
2 fold each answer into the requirement, criterion, entity or non_goal it belongs to
3 remove every explicit_unknown the operator resolved; keep the rest verbatim
4 an answer that creates required behavior becomes a requirement, never a note
5 an answer that bounds scope becomes a non_goal
6 an answer that fixes a term becomes an entity
ban appending a "clarifications" section; the answer lives where the meaning lives
```

Read the shape at {{KERNEL_HOME}}/skills/specify/template.tdsl and the revision at
{{KERNEL_HOME}}/skills/_shared/schema-lock.tdsl.

¶ 6 — Close

```text
1 write the spec
2 run: python {{KERNEL_HOME}}/scripts/sdd_gate.py check <path>
3 report per answer: which requirement or field now carries it
4 run analyze and show what the change made incoherent, if anything
5 stop. O registro está escrito. Se ele precisa mudar, o operador diz o que muda;
  silêncio é concordância. Não existe passo de aceitação.
```

A source-only reformulation with identical meaning is not a clarify. If nothing
material changed, say so and leave the version alone.
