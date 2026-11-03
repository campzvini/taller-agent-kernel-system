# ────────────────────────────────────────────
# TASK 2.0 — runtime_journal.py
# § - Append operational events and derive runtime projections · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import tempfile

from protocol_core import parse_blocks

# ── § 1 — CONTRACTS — Define typed immutable operational records ──
KINDS = {"execution": "event", "decision": "decision", "failure": "failure"}
OUTCOMES = {"started", "completed", "blocked", "failed", "interrupted"}
REF = re.compile(r"^@[a-z][a-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_.~/-]*(?:#[a-z][a-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_.~-]*)?$")
REQUIRED = {
    "execution": {"task_ref", "outcome", "evidence_refs"},
    "decision": {"task_ref", "question", "choice", "rationale", "evidence_refs"},
    "failure": {"task_ref", "cause", "effect", "resolution", "rationale", "evidence_refs", "resolution_state", "materiality"},
}
TEXT_FIELDS = {"question", "choice", "rationale", "cause", "effect", "resolution", "evidence", "reason"}


def schema_revision(dialect: str) -> str:
    """Resolve the exact bundled revision; never infer a schema identity."""
    from tdsl_lock import DEFAULT_KERNEL
    registry = json.loads((DEFAULT_KERNEL / "schemas" / "registry.json").read_text(encoding="utf-8"))
    for entry in registry["entries"]:
        if entry["dialect"] == dialect:
            return str(entry["schema_revision"])
    raise ValueError(f"unregistered dialect: {dialect}")


def journal_path(root: Path, kind: str) -> Path:
    """Return the canonical journal path for a supported record kind."""
    if kind not in KINDS:
        raise ValueError(f"unknown journal kind: {kind}")
    return Path(root).resolve() / ".task" / "journals" / f"{kind}.journal.tdsl"


def validate_entry(kind: str, payload: dict[str, Any]) -> None:
    """Reject incomplete records and ambiguous supersession before writing."""
    allowed = {"task_ref", "evidence_refs"}
    allowed |= {"execution": {"outcome", "attempt", "validation_refs", "evidence", "reason", "unit_ref"}, "decision": {"question", "choice", "rationale", "supersedes_ref", "supersession_scope", "affected_refs"}, "failure": {"cause", "effect", "resolution", "rationale", "resolution_state", "materiality", "decision_ref", "supersedes_ref"}}[kind]
    if payload.keys() - allowed:
        raise ValueError(f"unknown {kind} fields: {sorted(payload.keys() - allowed)}")
    missing = REQUIRED[kind] - payload.keys()
    if missing:
        raise ValueError(f"missing {kind} fields: {sorted(missing)}")
    if not REF.fullmatch(str(payload["task_ref"])):
        raise ValueError("task_ref must be a typed reference")
    for field, value in payload.items():
        if field in TEXT_FIELDS and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{field} must be nonempty text")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", field):
            raise ValueError(f"invalid field: {field}")
        if field.endswith("_refs"):
            if not isinstance(value, list) or any(not REF.fullmatch(str(v)) for v in value):
                raise ValueError(f"{field} must contain typed references")
        if field.endswith("_ref") and value and not REF.fullmatch(str(value)):
            raise ValueError(f"invalid reference in {field}")
    if kind == "execution":
        if payload["outcome"] not in OUTCOMES:
            raise ValueError("invalid execution outcome")
        if payload["outcome"] == "completed" and not payload["evidence_refs"]:
            raise ValueError("completion requires evidence_refs")
        if "attempt" in payload and (type(payload["attempt"]) is not int or payload["attempt"] < 1):
            raise ValueError("attempt must be a positive integer")
    if kind == "decision" and payload.get("supersedes_ref"):
        if payload.get("supersession_scope") not in {"full", "partial"}:
            raise ValueError("supersession requires explicit full or partial scope")
        if payload["supersession_scope"] == "partial" and not payload.get("affected_refs"):
            raise ValueError("partial supersession requires affected_refs")
    if kind == "failure":
        if payload["materiality"] not in {"material", "recurring", "architectural", "contract", "consequential"}:
            raise ValueError("trivial failures do not belong in the failure journal")
        if payload["resolution_state"] not in {"open", "investigating", "resolved", "superseded"}:
            raise ValueError("invalid resolution_state")

# ── § 2 — STORAGE — Serialize append-only TDSL under exclusive ownership ──
@contextmanager
def journal_lock(path: Path) -> Iterator[None]:
    """Hold a non-stealable lock; an interrupted writer requires reconciliation."""
    lock = path.with_suffix(path.suffix + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def read_entries(root: Path, kind: str) -> list[dict[str, Any]]:
    """Read unique immutable events; reject corruption rather than merge it."""
    path = journal_path(root, kind)
    if not path.exists():
        return []
    from contract_check import check_contract
    findings = check_contract(path)
    if findings:
        raise ValueError("invalid journal contract: " + "; ".join(message for _, message in findings))
    source = path.read_text(encoding="utf-8")
    if not source.endswith("\n"):
        raise ValueError("incomplete journal: final newline missing")
    blocks, duplicates = parse_blocks(source, "journal", "entry")
    if duplicates:
        raise ValueError(f"duplicate event identities: {duplicates}")
    records = []
    for identity, raw in blocks.items():
        event: dict[str, Any] = {"id": identity}
        for key, value in raw.items():
            if key.endswith("_refs"):
                if not (value.startswith("[") and value.endswith("]")):
                    raise ValueError(f"malformed reference list in {identity}.{key}")
                event[key] = value[1:-1].split()
            elif key == "attempt":
                event[key] = int(value)
            else:
                event[key] = value
        validate_entry(kind, {k: v for k, v in event.items() if k not in {"id", f"{KINDS[kind]}_id", "timestamp"}})
        if not REF.fullmatch(str(event.get(f"{KINDS[kind]}_id", ""))):
            raise ValueError(f"missing typed identity in {identity}")
        if not event[f"{KINDS[kind]}_id"].startswith(f"@{KINDS[kind]}/"):
            raise ValueError(f"wrong identity namespace in {identity}")
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
            raise ValueError(f"timestamp is not UTC in {identity}")
        records.append(event)
    return records


def _entry_text(identity: str, payload: dict[str, Any]) -> str:
    lines = [f"  entry {identity}:"]
    for field, value in payload.items():
        if isinstance(value, list):
            lines.append(f"    {field}: [{' '.join(str(v) for v in value)}]")
        elif field in TEXT_FIELDS or "\n" in str(value):
            lines.append(f"    {field} ln: |")
            lines.extend("      " + line for line in str(value).splitlines() or [""])
        else:
            text = str(value)
            if "\r" in text or not text.strip():
                raise ValueError(f"invalid scalar in {field}")
            lines.append(f"    {field}: {text}")
    return "\n".join(lines) + "\n"


def append_entry(root: Path, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Append one validated event and return its immutable identity."""
    path = journal_path(root, kind)
    payload = dict(payload)
    reserved = {"id", "event_id", "decision_id", "failure_id", "timestamp"} & payload.keys()
    if reserved:
        raise ValueError(f"writer owns identity and timestamp: {sorted(reserved)}")
    validate_entry(kind, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with journal_lock(path):
        records = read_entries(root, kind)
        number = len(records) + 1
        identity = f"{KINDS[kind][0].upper()}{number:06d}"
        ref = f"@{KINDS[kind]}/{identity}"
        if kind == "execution":
            prior = [e for e in records if e.get("task_ref") == payload["task_ref"]]
            previous_attempt = prior[-1].get("attempt", 1) if prior else 0
            continuing = bool(prior and prior[-1].get("outcome") == "started" and payload["outcome"] != "started")
            payload.setdefault("attempt", previous_attempt if continuing else previous_attempt + 1)
        if payload.get("supersedes_ref"):
            if not any(e.get(f"{KINDS[kind]}_id") == payload["supersedes_ref"] for e in records):
                raise ValueError("supersedes_ref must identify an existing event in this journal")
        event = {f"{KINDS[kind]}_id": ref, "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), **payload}
        if not path.exists():
            dialect = f"{kind}_journal@1"
            revision = schema_revision(dialect)
            header = f"tdsl: {dialect}\nschema_revision: {revision}\nid: @journal/{kind}\nversion: 1\nstatus: proposed\npurpose: immutable {kind} history\n\njournal:\n"
        else:
            header = ""
        previous = path.read_text(encoding="utf-8") if path.exists() else header
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(previous + _entry_text(identity, event))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return {"id": identity, **event}

# ── § 3 — PROJECTIONS — Derive latest execution and checklist without duplication ──
def execution_state(root: Path) -> dict[str, dict[str, Any]]:
    """Project the latest event per task, including reopenings after completion."""
    result: dict[str, dict[str, Any]] = {}
    for event in read_entries(root, "execution"):
        result[event["task_ref"]] = event
    return result


def render_checklist(root: Path, task_refs: list[str]) -> str:
    """Render disposable Markdown checkboxes from journal evidence only."""
    states = execution_state(root)
    return "\n".join(f"- [{'x' if states.get(ref, {}).get('outcome') == 'completed' else ' '}] {ref}" for ref in task_refs) + "\n"

# ── § 4 — ENTRY — Expose append queries and derived checklists ──
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    append = commands.add_parser("append")
    append.add_argument("kind", choices=KINDS)
    append.add_argument("--data", required=True, help="JSON object or @JSON-file")
    query = commands.add_parser("query")
    query.add_argument("kind", nargs="?", choices=KINDS)
    query.add_argument("--task-ref", help="return only events belonging to this task")
    query.add_argument("--ref", help="return an event identity and explicit references to it")
    checklist = commands.add_parser("checklist")
    checklist.add_argument("task_refs", nargs="*")
    args = parser.parse_args()
    try:
        if args.command == "append":
            raw = Path(args.data[1:]).read_text(encoding="utf-8") if args.data.startswith("@") else args.data
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("--data must be an object")
            result = append_entry(args.root, args.kind, data)
        elif args.command == "query":
            def select(kind: str) -> list[dict[str, Any]]:
                entries = read_entries(args.root, kind)
                if args.task_ref:
                    entries = [e for e in entries if e.get("task_ref") == args.task_ref]
                if args.ref:
                    entries = [e for e in entries if any(args.ref == v or (isinstance(v, list) and args.ref in v) for v in e.values())]
                return entries
            result = select(args.kind) if args.kind else {k: select(k) for k in KINDS}
        else:
            refs = args.task_refs or sorted(execution_state(args.root))
            print(render_checklist(args.root, refs), end="")
            return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, StopIteration) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
