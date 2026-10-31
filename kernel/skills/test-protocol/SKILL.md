---
name: test-protocol
description: Define or apply the project's test method: strategy, order, criteria, report format. Use when establishing a protocol or running a test session.
---

¶ - Define or apply project testing methodology and protocols

skill:
  id: @skill/test-protocol

¶ 1 — Gatilho

condition(new_project_protocol | apply_existing_protocol | operator_requests_review) -> invoke

¶ 2 — Procedimento — Definition

1 execute `python {{KERNEL_HOME}}/scripts/detect_project.py` to identify language and available frameworks
2 read `.agent-cache/project-detect.md`
3 define testing strategy
  unit: what is tested in isolation
  integration: what is tested together
  manual: what requires human verification
4 define execution order (unit before integration before manual)
5 define approval criteria: minimum coverage, mandatory cases
6 define report format
7 save as `docs/test-protocol.md` in project

¶ 2.A — Procedimento — Application

1 execute `python {{KERNEL_HOME}}/scripts/detect_project.py` to confirm stack and available commands
2 read existing project protocol and `.agent-cache/project-detect.md`
3 execute tests in defined order
4 capture results
5 compose report in defined format

¶ 3 — Critérios

protocol respects language characteristics (Rust differs from Python)
approval criteria are verifiable, not subjective
execution report includes evidence (command output)
failures reported with sufficient context for diagnosis
