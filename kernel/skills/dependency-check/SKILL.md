---
name: dependency-check
description: Audit project dependencies for versions, conflicts, vulnerabilities and removal candidates. Use for a periodic audit or before a release.
---

¶ - Audit project dependencies for versions and vulnerabilities

skill:
  id: @skill/dependency-check

¶ 1 — Gatilho

condition(periodic_audit | pre_release | operator_requests_after_stale) -> invoke

¶ 2 — Procedimento

1 identify the project's dependency manager
  Rust: `Cargo.toml`, `Cargo.lock`
  Python: `pyproject.toml`, `requirements.txt`, `poetry.lock`
  JavaScript/TypeScript: `package.json`, `package-lock.json`
2 list direct dependencies (not transitive)
3 for each dependency
  version in use
  latest available version
  gap (patch, minor, major)
4 verify known vulnerabilities via appropriate tool
  cargo audit, pip-audit, npm audit
5 identify unused dependencies via import analysis
6 compose prioritized report with recommendations

¶ 3 — Critérios

verifications are executed, not inferred
vulnerability severity is reported with source
recommendations respect impact of breaking changes in majors
removal candidates were confirmed by code search
