---
name: debug
description: Structured diagnosis of a bug or unexpected behavior: symptom, scope, ranked hypotheses, evidence. Use when investigating an error, a divergence, or a surprising test result.
---

¶ - Structured debugging protocol for bug investigation

skill:
  id: @skill/debug

¶ 1 — Gatilho

condition(error_reported | divergent_behavior | unexpected_test_result) -> invoke

¶ 2 — Procedimento

1 capture symptom: what is happening, what was expected, under what conditions
2 isolate scope: identify where the problem manifests (file, function, approximate line)
3 generate ranked hypotheses ordered by probability, most likely to least
4 for each hypothesis, define a concrete and inexpensive verification test
5 execute verification in the defined order
6 report confirmed diagnosis and correction plan

¶ 3 — Critérios

hypotheses are testable, not speculative
order reflects actual probability, not guesswork
verifications start with the cheapest ones
diagnosis is confirmed by evidence, not inferred
correction addresses root cause, not symptom
