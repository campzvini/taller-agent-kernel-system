# ────────────────────────────────────────────
# CODEX-ENV 2.0 — sdd_gate.py
# § - The development workflow: phases, dialect checks and coherence over spec, plan and tasks · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import sys
from pathlib import Path

from protocol_core import (
    FAIL, Workflow, State, cycle_nodes, build_payload, build_parser, journal_outcomes, members,
    parse_blocks, parse_reference, read_text, resolve_state, run, top_level_value,
    write_analysis_cache,
)

# ── § 1 — WORKFLOW — what makes development differ from any other flow ──

# A phase needs its predecessors because it references their parts. Referential
# integrity, not permission: records carry no status and grant nothing.
SDD = Workflow(
    name="sdd",
    project_artifact="constitution",
    feature_artifacts=("spec", "plan", "tasks", "analysis"),
    phases={
        "initialize": ((), None),
        "constitution": ((), "constitution"),
        "feature": (("constitution",), None),
        "specify": (("constitution",), "spec"),
        "clarify": (("constitution", "spec"), "spec"),
        "plan": (("constitution", "spec"), "plan"),
        "tasks": (("constitution", "spec", "plan"), "tasks"),
        "analyze": (("constitution", "spec", "plan", "tasks"), "analysis"),
        "decompose": (("constitution", "spec", "plan", "tasks"), "decomposition"),
        "execute": (("constitution", "spec", "plan", "tasks"), None),
    },
    dialect_of={
        "constitution": "constitution@1",
        "spec": "spec@1",
        "plan": "plan@1",
        "tasks": "tasks@1",
        "analysis": "analysis@1",
        "decomposition": "local:decomposition@1",
    },
    next_phase_order=(("spec", "specify"), ("plan", "plan"),
                      ("tasks", "tasks"), ("analysis", "analyze")),
    terminal_phase="execute",
    skeleton_of={"constitution": "constitution", "spec": "specify", "plan": "plan",
                 "tasks": "tasks", "analysis": "analyze",
                 "decomposition": "decompose"},
)


# ── § 2 — DIALECT CHECKS — invariants only this workflow's records have ──


def check_tasks(path: Path) -> list[tuple[str, str]]:
    """tasks@1 invariants: unique ids, acyclic DAG, complete traceability."""
    findings: list[tuple[str, str]] = []
    text = read_text(path)
    raw, duplicates = parse_blocks(text, "tasks", "task")
    for duplicate in duplicates:
        findings.append((FAIL, f"duplicate task id: {duplicate}"))
    tasks = {tid: {f: members(v) for f, v in fields.items()} for tid, fields in raw.items()}

    if not tasks:
        findings.append((FAIL, "no task blocks parsed; expected `task <id>:` two spaces inside `tasks:`"))
        return findings

    for task_id, fields in tasks.items():
        for required in ("requirement_refs", "plan_refs", "validation_refs"):
            if not fields.get(required):
                findings.append((FAIL, f"task {task_id}: traceability incomplete, {required} empty"))
        for edge in fields.get("depends_on", []):
            if edge not in tasks:
                findings.append((FAIL, f"task {task_id}: depends_on unknown task {edge}"))

    for node in cycle_nodes({t: f.get("depends_on", []) for t, f in tasks.items()}):
        findings.append((FAIL, f"dependency cycle through task {node}"))

    order = members(top_level_value(text, "execution_order") or "")
    if order:
        position = {t: i for i, t in enumerate(order)}
        for task_id in tasks:
            if task_id not in position:
                findings.append((FAIL, f"execution_order omits task {task_id}"))
        for task_id, fields in tasks.items():
            for edge in fields.get("depends_on", []):
                if edge in position and task_id in position and position[edge] > position[task_id]:
                    findings.append((FAIL, f"execution_order contradicts DAG: {edge} after {task_id}"))
    return findings


def check_analysis(path: Path) -> list[tuple[str, str]]:
    from protocol_core import parse_flat
    result = parse_flat(read_text(path)).get("result")
    if result not in {"pass", "fail", "inconclusive"}:
        return [(FAIL, "analysis result must be one of pass|fail|inconclusive")]
    return []


def check_decomposition(path: Path) -> list[tuple[str, str]]:
    """local:decomposition@1: every subtask names a parent that exists, acyclic.

    A sibling container, not a nested one. The shared block parser reads fields
    at exactly one level below an item, so a `subtask` block nested inside a
    `task` would be dropped without a word — the worst possible outcome.
    """
    findings: list[tuple[str, str]] = []
    text = read_text(path)
    raw, duplicates = parse_blocks(text, "subtasks", "subtask")
    for duplicate in duplicates:
        findings.append((FAIL, f"duplicate subtask id: {duplicate}"))
    if not raw:
        findings.append((FAIL, "no subtask blocks parsed; expected `subtask <id>:` two spaces inside `subtasks:`"))
        return findings

    parent_path = path.parent / "tasks.tdsl"
    parents: set[str] = set()
    if parent_path.is_file():
        parents = set(parse_blocks(read_text(parent_path), "tasks", "task")[0])
    else:
        findings.append((FAIL, "tasks.tdsl does not exist; a decomposition with no task set decomposes nothing"))

    for subtask_id, fields in raw.items():
        parent = fields.get("parent", "").strip()
        if not parent:
            findings.append((FAIL, f"subtask {subtask_id}: parent is required"))
        elif parents and parent not in parents:
            findings.append((FAIL, f"subtask {subtask_id}: parent {parent} is not a task in tasks.tdsl"))
        for edge in members(fields.get("depends_on", "")):
            if edge not in raw:
                findings.append((FAIL, f"subtask {subtask_id}: depends_on unknown subtask {edge}"))
            elif raw[edge].get("parent", "").strip() != fields.get("parent", "").strip():
                findings.append((FAIL, f"subtask {subtask_id}: depends_on {edge} crosses parents; "
                                       "ordering between tasks belongs to the task DAG"))
    for node in cycle_nodes({sid: members(f.get("depends_on", "")) for sid, f in raw.items()}):
        findings.append((FAIL, f"dependency cycle through subtask {node}"))
    return findings


object.__setattr__(SDD, "dialect_checks", {"tasks": check_tasks, "analysis": check_analysis,
                                           "decomposition": check_decomposition})


# ── § 3 — COHERENCE — what the records must say about each other ──


def analyze_payload(state: State) -> dict:
    """Deterministic cross-record pass. Judgment stays with the agent.

    Advisory by construction: the result is reported, never used to withhold a
    phase. Drift is detected here by content, which is why no digest-based
    freshness exists anywhere in this package.
    """
    findings: list[tuple[str, str, str]] = []

    def add(severity: str, code: str, message: str) -> None:
        findings.append((severity, code, message))

    sources: dict[str, str] = {}
    for artifact in ("constitution", "spec", "plan", "tasks"):
        source = state.source_of(artifact)
        if source is None:
            add("blocking", "artifact_absent", f"{artifact} does not exist")
        else:
            sources[artifact] = source

    if not {"spec", "plan", "tasks"} <= sources.keys():
        return build_payload(state, findings)

    requirements, _ = parse_blocks(sources["spec"], "requirements", "requirement")
    criteria, _ = parse_blocks(sources["spec"], "success_criteria", "criterion")
    journeys, _ = parse_blocks(sources["spec"], "user_journeys", "journey")
    components, _ = parse_blocks(sources["plan"], "components", "component")
    boundaries, _ = parse_blocks(sources["plan"], "boundaries", "boundary")
    interfaces, _ = parse_blocks(sources["plan"], "interfaces", "interface")
    validations, _ = parse_blocks(sources["plan"], "validations", "validation")
    tasks, _ = parse_blocks(sources["tasks"], "tasks", "task")

    known = {
        "requirement": set(requirements), "criterion": set(criteria),
        "journey": set(journeys), "component": set(components),
        "boundary": set(boundaries), "interface": set(interfaces),
        "validation": set(validations),
    }

    # every requirement is proved by at least one validation
    proved: set[str] = set()
    for validation_id, fields in validations.items():
        for ref in members(fields.get("proves", "")):
            parsed = parse_reference(ref)
            if parsed is None:
                add("material", "malformed_reference",
                    f"plan validation {validation_id}: `proves` member {ref} is not a part reference")
                continue
            kind, part_id = parsed
            if part_id not in known.get(kind, set()):
                add("material", "unresolved_reference",
                    f"plan validation {validation_id}: proves {kind}/{part_id}, which does not exist")
            elif kind == "requirement":
                proved.add(part_id)
    for requirement_id in sorted(set(requirements) - proved):
        add("material", "requirement_unproved",
            f"spec requirement {requirement_id} is proved by no plan validation")

    # every task reference resolves, per reference kind
    exercised: set[str] = set()
    for task_id, fields in tasks.items():
        for field_name in ("requirement_refs", "plan_refs", "validation_refs"):
            for ref in members(fields.get(field_name, "")):
                parsed = parse_reference(ref)
                if parsed is None:
                    add("material", "malformed_reference",
                        f"task {task_id}: {field_name} member {ref} is not a part reference")
                    continue
                kind, part_id = parsed
                if part_id not in known.get(kind, set()):
                    add("blocking", "unresolved_reference",
                        f"task {task_id}: {field_name} points at {kind}/{part_id}, which does not exist")
                elif kind == "component":
                    exercised.add(part_id)

    for component_id in sorted(set(components) - exercised):
        add("minor", "component_unexercised",
            f"plan component {component_id} is referenced by no task")

    measured = {
        parsed[1]
        for fields in validations.values()
        for ref in members(fields.get("proves", ""))
        if (parsed := parse_reference(ref)) and parsed[0] == "criterion"
    }
    for criterion_id in sorted(set(criteria) - measured):
        add("observation", "criterion_unmeasured",
            f"spec criterion {criterion_id} is measured by no plan validation")

    for artifact in ("spec", "plan"):
        for unknown in members(top_level_value(sources[artifact], "explicit_unknowns") or ""):
            add("minor", "explicit_unknown",
                f"{artifact} carries an unresolved explicit_unknown: {unknown}")

    return build_payload(state, findings)


# ── § 4 — COMMANDS — the two this workflow adds to the shared surface ──


def cmd_analyze(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    payload = analyze_payload(state)
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if not payload["findings"]:
            print("  (no deterministic finding)")
        for finding in payload["findings"]:
            print(f"  {finding['severity'].upper():11} {finding['code']:24} {finding['message']}")
        print(f"deterministic analysis: {payload['result'].upper()}")
        print("This pass checks references and coverage only. Duplication, policy "
              "alignment and intent drift remain agent judgment.")
    write_analysis_cache(state, payload)
    return 1 if payload["result"] == "fail" else 0


def cmd_trail(args, workflow: Workflow) -> int:
    """What exists, what coherence says about it, and where execution stands.

    Advisory by construction: nothing here withholds permission, because the
    operator is in the conversation and never needed a file to speak for them.
    """
    state = resolve_state(args, workflow)
    print(f"feature: {state.feature or 'unknown'}")
    print("")
    print("| artefato | existe |")
    print("| --- | --- |")
    missing = []
    for artifact in workflow.artifacts:
        present = state.exists(artifact)
        print(f"| {artifact} | {'sim' if present else '—'} |")
        if not present and artifact != "analysis":
            missing.append(artifact)

    payload = analyze_payload(state)
    counts = payload["counts"]
    print("")
    print(f"coerência: {payload['result'].upper()} "
          f"({counts['blocking']} blocking, {counts['material']} material, {counts['minor']} minor)")
    for finding in payload["findings"]:
        if finding["severity"] in ("blocking", "material"):
            print(f"  {finding['severity'].upper():9} {finding['message']}")

    source = state.source_of("tasks")
    if source:
        tasks, _ = parse_blocks(source, "tasks", "task")
        order = members(top_level_value(source, "execution_order") or "")
        done, blocked = journal_outcomes(state)
        pending = [t for t in tasks if t not in done]
        print("")
        print(f"tasks: {len(tasks)} total, {len(done)} concluídas, "
              f"{len(blocked)} bloqueadas, {len(pending)} pendentes")
        if blocked:
            print(f"bloqueadas: {' '.join(sorted(blocked))}")
        if order:
            remaining = [t for t in order if t not in done]
            print(f"próximas: {' -> '.join(remaining) if remaining else '(nenhuma)'}")

    print("")
    if missing:
        print(f"falta escrever: {' '.join(missing)}")
    elif counts["blocking"] or counts["material"]:
        print("coerência tem achados abertos — decida se importam antes de executar")
    else:
        print("registro completo e coerente")
    return 0


# ── § 5 — ENTRY ──


def main() -> int:
    parser = build_parser(SDD, "protocol development workflow gate")
    sub = parser._subparsers._group_actions[0]  # noqa: SLF001 — argparse exposes no public accessor

    p = sub.add_parser("trail", help="what exists, what coherence found, what remains")
    p.set_defaults(func=cmd_trail)

    p = sub.add_parser("analyze", help="deterministic cross-record coherence pass")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_analyze)

    return run(parser, SDD)


if __name__ == "__main__":
    sys.exit(main())
