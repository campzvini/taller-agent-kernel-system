---
name: test-protocol
description: Define or apply the project's test method: test-triage classes, order, criteria, report format. Use when establishing a protocol, classifying validations before tests are written, or running a test session.
---

¶ - Define or apply project testing methodology and protocols

skill:
  id: @skill/test-protocol

¶ 1 — Gatilho

condition(new_project_protocol | apply_existing_protocol | classify_validations | operator_requests_review) -> invoke

¶ 2 — Procedimento — Definition

1 execute `python {{KERNEL_HOME}}/scripts/detect_project.py` to identify language and available frameworks
2 read `.agent-cache/project-detect.md`
3 define testing strategy by the test-triage classes of ¶3, never by test kind alone
4 define execution order (build check before suite; whole suite once per unit of work)
5 define approval criteria: every validation has a stated class; mandatory cases from irreversible risk
6 define report format
7 save as `docs/test-protocol.md` in project

¶ 2.A — Procedimento — Application

1 execute `python {{KERNEL_HOME}}/scripts/detect_project.py` to confirm stack and available commands
2 read existing project protocol and `.agent-cache/project-detect.md`
3 execute the build check, then the whole suite once
4 capture results
5 compose report in defined format

¶ 3 — Test Triage

A test exists to turn uncertainty into evidence. Before a validation becomes a
test its class is stated; a constitution principle, when present, overrides this.

```text
guaranteed_by_construction (types, compiler) -> no test; the build check suffices
reused_from_tested_upstream (SDK, own engines) -> test only the seam, once
uncertain_and_mechanically_observable -> automated test against an independent reference
  (fixture, SDK output, spec number); stays as a permanent guard
uncertain_and_perceptual (look, smoothness) -> measurement with metric and threshold, never agent opinion
uncertain_and_not_observable_by_the_agent (hardware, taste, domain) -> operator, with what cannot be verified and why

override irreversible risk (originals, destructive writes) -> always tested
ban tautological test: expected value derived from the code under test
ban a test per requirement by habit; hollow traceability is not evidence
```

¶ 4 — Critérios

protocol respects language characteristics (Rust differs from Python)
approval criteria are verifiable, not subjective
execution report includes evidence (command output)
failures reported with sufficient context for diagnosis
