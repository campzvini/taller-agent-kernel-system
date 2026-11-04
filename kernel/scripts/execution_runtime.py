# ────────────────────────────────────────────
# TASK 2.0 — execution_runtime.py
# § - Resolve eligible execution units, authority and exclusive write ownership · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from protocol_core import State, cycle_nodes, members, parse_blocks, parse_flat, read_text

# § 1 — CONFIGURATION — Resolve explicit authority without upgrading legacy projects

DEFAULTS = {"execution_mode": "interactive", "max_active_subagents": 1,
            "separate_test_author": True, "autonomous_authorized": False,
            "scaffold_required": False}


def configuration(root: Path) -> dict:
    """Read explicit runtime settings; absence preserves legacy behavior."""
    path = root / ".task/execution.config.tdsl"
    if path.is_file():
        from contract_check import check_contract
        errors = check_contract(path)
        if errors:
            raise ValueError("invalid execution configuration: " + "; ".join(message for _, message in errors))
    raw = parse_flat(read_text(path)) if path.is_file() else {}
    result = dict(DEFAULTS)
    for key in result:
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(result[key], bool):
            if value not in ("true", "false"):
                raise ValueError(f"{key}: expected true or false")
            result[key] = value == "true"
        elif isinstance(result[key], int):
            result[key] = int(value)
        else:
            result[key] = value
    if result["execution_mode"] not in ("interactive", "autonomous"):
        raise ValueError("unknown execution_mode")
    if result["max_active_subagents"] < 1:
        raise ValueError("max_active_subagents must be positive")
    result["legacy"] = not path.is_file()
    return result


def migrate(root: Path) -> dict:
    """Opt into structural contracts without silently granting autonomous authority."""
    from structure_tracker import scan_project
    base = root / ".task"
    if not (base / "project.tdsl").is_file():
        raise ValueError("project anchor is required")
    path = base / "execution.config.tdsl"
    if not path.exists():
        from runtime_journal import schema_revision
        text = ("tdsl: project_execution@1\n"
                f"schema_revision: {schema_revision('project_execution@1')}\n"
                "id: @execution/project\nversion: 1\nstatus: proposed\n"
                "purpose: explicit execution authority and topology\n"
                "execution_mode: interactive\nmax_active_subagents: 1\n"
                "separate_test_author: true\nautonomous_authorized: false\n"
                "scaffold_required: true\n")
        path.write_text(text, encoding="utf-8", newline="\n")
    if (base / "constitution.tdsl").is_file():
        preserve_constitution(root)
    scan_project(root)
    return configuration(root)


# § 2 — ELIGIBILITY — Resolve cross-feature dependencies and task destinations

def task_catalog(root: Path) -> tuple[dict, dict]:
    """Return declared task fields and dependencies without inferring work."""
    from sdd_gate import SDD
    state = State(root, SDD)
    tasks, feature_dependencies = {}, {}
    for feature in state.known_features():
        if state.lifecycle_of(feature) != "active":
            continue
        feature_dependencies[feature] = members(state.features.get(feature, {}).get("depends_on", "[]"))
        path = root / ".task/features" / feature / "tasks.tdsl"
        if not path.is_file():
            continue
        parsed, duplicates = parse_blocks(read_text(path), "tasks", "task")
        if duplicates:
            raise ValueError(f"duplicate tasks: {duplicates}")
        for tid, fields in parsed.items():
            ref = f"@tasks/{feature}#task/{tid}"
            tasks[ref] = dict(fields, feature=feature, task_id=tid)
    graph = {f: [r.removeprefix("@feature/") for r in ds] for f, ds in feature_dependencies.items()}
    if cycle_nodes(graph):
        raise ValueError("cross-feature dependency cycle")
    known = set(state.known_features())
    for feature, dependencies in graph.items():
        for dep in dependencies:
            if dep not in known:
                raise ValueError(f"{feature}: unknown feature dependency {dep}")
    return tasks, graph


def latest_outcomes(root: Path) -> dict:
    """Combine legacy journals with the new event journal, newest contract wins."""
    from sdd_gate import SDD
    from protocol_core import journal_outcomes
    from runtime_journal import execution_state
    state = State(root, SDD)
    result = {}
    for feature in state.known_features():
        state.feature = feature
        done, blocked = journal_outcomes(state, include_runtime=False)
        result.update({f"@tasks/{feature}#task/{tid}": {"outcome": "completed"} for tid in done})
        result.update({f"@tasks/{feature}#task/{tid}": {"outcome": "blocked"} for tid in blocked})
    result.update(execution_state(root))
    return result


def normalized_scope(root: Path, raw: str) -> str:
    """Canonicalize a write destination and refuse escape through links or parents."""
    if any(char in raw for char in "*?[]"):
        raise ValueError("write scopes must be concrete paths, not patterns")
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"write scope escapes project: {raw}")
    return os.path.normcase(str(path))


def scopes_for(root: Path, fields: dict) -> list[str]:
    """Prefer explicit write scopes; old file_refs remain accepted."""
    raw = fields.get("write_scope", fields.get("write_refs", fields.get("file_refs", "[]")))
    paths = members(raw)
    if not paths or raw == "unknown":
        raise ValueError("task has no concrete write scope")
    return [normalized_scope(root, p) for p in paths]


def overlaps(left: list[str], right: list[str]) -> bool:
    """Directory ownership covers every descendant, including temporary outputs."""
    return any(Path(a) == Path(b) or Path(a) in Path(b).parents or Path(b) in Path(a).parents
               for a in left for b in right)


def eligible_tasks(root: Path, grouped: set[str] | None = None) -> list[dict]:
    """List tasks whose declared predecessors are complete; never judge implementation."""
    from sdd_gate import SDD
    tasks, feature_graph = task_catalog(root)
    outcomes = latest_outcomes(root)
    state = State(root, SDD)
    active = load_units(root)
    claimed = {ref for unit in active.values() for ref in unit["task_refs"]}
    result = []
    for ref, fields in tasks.items():
        if state.mode == "gradual" and fields["feature"] != state.feature:
            continue
        if outcomes.get(ref, {}).get("outcome") == "completed" or ref in claimed:
            continue
        dependencies = [dep if dep.startswith("@") else f'@tasks/{fields["feature"]}#task/{dep}'
                        for dep in members(fields.get("depends_on", "[]"))]
        if any(dep not in tasks and outcomes.get(dep, {}).get("outcome") != "completed" for dep in dependencies):
            raise ValueError(f"{ref}: unresolved task dependency")
        if any(outcomes.get(dep, {}).get("outcome") != "completed" and dep not in (grouped or set()) for dep in dependencies):
            continue
        if any(state.lifecycle_of(dep) != "delivered" for dep in feature_graph[fields["feature"]]):
            continue
        result.append({"task_ref": ref, "difficulty": fields.get("difficulty", "medium"),
                       "target_refs": members(fields.get("target_refs", "[]")),
                       "condition": fields.get("condition", ""),
                       "write_scope": scopes_for(root, fields)})
    dependency_graph = {ref: [dep if dep.startswith("@") else f'@tasks/{fields["feature"]}#task/{dep}'
                              for dep in members(fields.get("depends_on", "[]"))] for ref, fields in tasks.items()}
    if cycle_nodes(dependency_graph):
        raise ValueError("task dependency cycle")
    return result


# § 3 — OWNERSHIP — Serialize claims and preserve interrupted units for explicit recovery

@contextmanager
def runtime_lock(root: Path):
    """Reject overlapping mutations instead of overwriting another orchestrator."""
    base = root / ".task/runtime"
    base.mkdir(parents=True, exist_ok=True)
    path = base / "execution.lock"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def load_units(root: Path) -> dict:
    """Read active reservations; session boundaries never imply success."""
    path = root / ".task/runtime/units.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def save_units(root: Path, units: dict) -> None:
    """Publish reservations atomically while holding runtime_lock."""
    path = root / ".task/runtime/units.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(units, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temp.replace(path)


def claim(root: Path, unit_ref: str, task_refs: list[str], owner: str,
          conditions_satisfied: list[str] | None = None) -> dict:
    """Reserve independent eligible tasks and their complete write boundaries."""
    if not unit_ref.startswith("@unit/") or not owner or not task_refs:
        raise ValueError("unit reference, owner and task refs required")
    with runtime_lock(root):
        units = load_units(root)
        if unit_ref in units:
            raise ValueError("unit already active")
        from runtime_journal import read_entries
        if any(event.get("unit_ref") == unit_ref for event in read_entries(root, "execution")):
            raise ValueError("unit identity was already used; allocate a new identity")
        config = configuration(root)
        if len(units) >= config["max_active_subagents"]:
            raise ValueError("max_active_subagents reached")
        status = execution_status(root)
        if status["blockers"]:
            raise ValueError("; ".join(status["blockers"]))
        preserve_constitution(root)
        eligible = {item["task_ref"]: item for item in eligible_tasks(root, set(task_refs))}
        if len(task_refs) != len(set(task_refs)) or any(ref not in eligible for ref in task_refs):
            raise ValueError("unit contains duplicate or ineligible tasks")
        for ref in task_refs:
            if eligible[ref]["condition"] and ref not in (conditions_satisfied or []):
                raise ValueError(f"conditional task requires explicit applicability judgment: {ref}")
        scopes = sorted({p for ref in task_refs for p in eligible[ref]["write_scope"]})
        for unit in units.values():
            if overlaps(scopes, unit["write_scope"]):
                raise ValueError("write ownership conflict")
        unit = {"owner": owner, "task_refs": task_refs, "write_scope": scopes,
                "conditions_satisfied": conditions_satisfied or [],
                "started_at": datetime.now(timezone.utc).isoformat(), "state": "active"}
        units[unit_ref] = unit
        save_units(root, units)
        from runtime_journal import append_entry
        for ref in task_refs:
            append_entry(root, "execution", {"task_ref": ref, "outcome": "started",
                         "evidence_refs": [], "unit_ref": unit_ref,
                         "evidence": f"write ownership reserved for {owner}"})
        return unit


def release(root: Path, unit_ref: str, owner: str, interrupted: bool = False) -> dict:
    """Release after validated delivery, or explicitly record interrupted work."""
    from runtime_journal import append_entry
    with runtime_lock(root):
        units = load_units(root)
        unit = units.get(unit_ref)
        if not unit or unit["owner"] != owner:
            raise ValueError("unit not owned by caller")
        outcomes = latest_outcomes(root)
        if not interrupted and any(outcomes.get(ref, {}).get("outcome") != "completed" for ref in unit["task_refs"]):
            raise ValueError("unit has incomplete tasks; use explicit interruption")
        if interrupted:
            for ref in unit["task_refs"]:
                if outcomes.get(ref, {}).get("outcome") != "completed":
                    append_entry(root, "execution", {"task_ref": ref, "outcome": "interrupted",
                                 "validation_refs": [], "evidence_refs": [],
                                 "evidence": f"unit {unit_ref} interrupted by {owner}"})
        del units[unit_ref]
        save_units(root, units)
        return unit


# § 4 — RECONCILIATION — Report required reads and preserve constitutional revisions

def preserve_constitution(root: Path) -> str:
    """Preserve each version; refuse changed content under an existing version."""
    source = root / ".task/constitution.tdsl"
    if not source.is_file():
        raise ValueError("constitution is missing")
    text = read_text(source)
    version = parse_flat(text).get("version", "")
    if not version.isdigit() or int(version) < 1:
        raise ValueError("constitution version must be a positive integer")
    directory = root / ".task/history/constitution"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{version}.tdsl"
    if target.exists() and read_text(target) != text:
        raise ValueError("constitution version is immutable; explicit revision required")
    if not target.exists():
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    return str(target.relative_to(root))


def execution_status(root: Path) -> dict:
    """Report mechanical prerequisites and explicit authority, never approval by silence."""
    from sdd_gate import SDD
    state = State(root, SDD)
    config = configuration(root)
    blockers = []
    if config["execution_mode"] == "autonomous" and not config["autonomous_authorized"]:
        blockers.append("autonomous execution lacks explicit authorization")
    if not state.exists("constitution"):
        blockers.append("constitution missing")
    else:
        text = read_text(root / ".task/constitution.tdsl")
        version = parse_flat(text).get("version", "")
        if not version.isdigit() or int(version) < 1:
            blockers.append("constitution version must be a positive integer")
        else:
            snapshot = root / ".task/history/constitution" / f"{version}.tdsl"
            if snapshot.exists() and read_text(snapshot) != text:
                blockers.append("constitution version is immutable; explicit revision required")
    if config["scaffold_required"] and not (root / ".task/Architecture.md").is_file():
        blockers.append("Architecture.md missing")
    features = state.known_features() if state.mode == "integral" else ([state.feature] if state.feature else [])
    for fid in features:
        if state.lifecycle_of(fid) != "active":
            continue
        for artifact in ("spec", "plan", "tasks", "analysis"):
            if not state.feature_has(fid, artifact):
                blockers.append(f"{fid}: {artifact} missing")
    return {"configuration": config, "planning_mode": state.mode, "blockers": blockers,
            "units": load_units(root), "next_phase": state.next_phase()}


def reconcile(root: Path) -> dict:
    """Refresh structural evidence and return history needed for a bounded intervention."""
    from structure_tracker import scan_project
    version = preserve_constitution(root)
    tracking = scan_project(root)
    return {"constitution_snapshot": version, "tracking": tracking,
            "status": execution_status(root)}


def resolve_intervention(root: Path, task_ref: str) -> dict:
    """Locate normative sources, exact destinations and relevant operational history."""
    from structure_tracker import query_registry
    from runtime_journal import read_entries
    tasks, _ = task_catalog(root)
    if task_ref not in tasks:
        raise ValueError("unknown task reference")
    fields = tasks[task_ref]
    feature = fields["feature"]
    targets = []
    for ref in members(fields.get("target_refs", "[]")):
        try:
            resolved = query_registry(root, ref)
            targets.append({"reference": ref, "exists": resolved.get("exists", resolved["element"]["state"] == "present"), "resolution": resolved})
        except ValueError as error:
            targets.append({"reference": ref, "exists": False, "unresolved": str(error),
                            "prospective_destinations": scopes_for(root, fields)})
    return {"task_ref": task_ref,
            "sources": [".task/constitution.tdsl", ".task/Architecture.md",
                        *[f".task/features/{feature}/{name}.tdsl" for name in ("spec", "plan", "tasks", "analysis")]],
            "targets": targets, "write_scope": scopes_for(root, fields),
            "history": {kind: [entry for entry in read_entries(root, kind) if entry.get("task_ref") == task_ref]
                        for kind in ("execution", "decision", "failure")},
            "required_judgment": "read applicable sources and observed destinations; choose reuse, modify, create or no_action"}


# § 5 — ENTRY — Expose orchestration primitives without selecting technical trajectory

def main() -> int:
    """Run bounded runtime commands; agents retain judgment and test responsibility."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "next", "reconcile", "migrate"):
        sub.add_parser(name)
    p = sub.add_parser("resolve")
    p.add_argument("task_ref")
    p = sub.add_parser("claim")
    p.add_argument("unit_ref")
    p.add_argument("task_refs", nargs="+")
    p.add_argument("--owner", required=True)
    p.add_argument("--condition-satisfied", action="append", default=[])
    p = sub.add_parser("release")
    p.add_argument("unit_ref")
    p.add_argument("--owner", required=True)
    p.add_argument("--interrupted", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "status":
            result = execution_status(root)
        elif args.command == "next":
            result = execution_status(root)
            result["eligible"] = eligible_tasks(root) if not result["blockers"] else []
        elif args.command == "claim":
            result = claim(root, args.unit_ref, args.task_refs, args.owner, args.condition_satisfied)
        elif args.command == "resolve":
            result = resolve_intervention(root, args.task_ref)
        elif args.command == "release":
            result = release(root, args.unit_ref, args.owner, args.interrupted)
        else:
            result = {"migrate": migrate, "reconcile": reconcile}[args.command](root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
