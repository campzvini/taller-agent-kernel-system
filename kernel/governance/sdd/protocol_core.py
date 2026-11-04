# ────────────────────────────────────────────
# TASK 2.2.0 — protocol_core.py
# § - Workflow-neutral machinery shared by every .task governance flow · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ── § 1 — CONFIG — layout constants every workflow shares ──

ROOT_DIR = ".task"
CACHE_DIR = ".agent-cache"

ANCHOR = "project.tdsl"
FEATURES = "features"
JOURNAL = "execution.journal.tdsl"
SCAFFOLD = ".scaffold"

# Skills and docs resolve from this file, never from ~/.codex: a copy under
# test must read its own templates.
HARNESS = Path(__file__).resolve().parent.parent

REF_RE = re.compile(
    r"^@[a-z][a-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_.~-]*"
    r"(?:/[A-Za-z0-9][A-Za-z0-9_.~-]*)*"
    r"(?:#[a-z_]+/[A-Za-z0-9][A-Za-z0-9_.~-]*)?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FEATURE_ID_RE = re.compile(r"^\d{3}-[a-z0-9][a-z0-9-]*$")

# Records this harness emits are local artifacts, not LIMA dialects. Saying so
# is honest; a string of zeros pretending to be a digest was not.
LOCAL_ANCHOR_REVISION = "local:protocol-anchor@1"

# Lifecycle is position in the cycle, never a judgement of quality. Acceptance
# stays in the conversation, where the operator is; position has to be written
# down, because the next agent enters cold and the repository is all it reads.
LIFECYCLE_STATES = ("active", "delivered", "heritage", "historical",
                    "superseded", "abandoned")
PLANNING_MODES = ("gradual", "integral")
ROUTING_STATE = "active"          # the only state from which a feature routes work
LIFECYCLE_DEFAULT = "active"      # an unregistered feature is assumed in progress
CLOSED_STATES = tuple(s for s in LIFECYCLE_STATES if s != ROUTING_STATE)
IDLE = "idle"                     # no governed work open; the next step is the operator's

OK, WARN, FAIL = "ok", "warn", "fail"
SEVERITY_ORDER = {"blocking": 0, "material": 1, "minor": 2, "observation": 3}


@dataclass(frozen=True)
class Workflow:
    """What makes one governance flow differ from another.

    Everything else in this module is domain-neutral: the grammar, the block
    parser, reference resolution, the journal, the state renderer. A workflow
    supplies only the names, the order, and the checks that know the domain.
    """

    name: str                                   # sdd | cad
    project_artifact: str                       # the one record that is not per-feature
    feature_artifacts: tuple[str, ...]          # written inside features/<id>/
    phases: dict[str, tuple[tuple[str, ...], str | None]]
    dialect_of: dict[str, str]
    next_phase_order: tuple[tuple[str, str], ...]   # (artifact, phase) in sequence
    terminal_phase: str
    skeleton_of: dict[str, str] = field(default_factory=dict)   # artifact -> skill owning its template
    dialect_checks: dict[str, Callable[[Path], list[tuple[str, str]]]] = field(default_factory=dict)
    project_files: dict[str, str] = field(default_factory=dict)

    @property
    def artifacts(self) -> tuple[str, ...]:
        return (self.project_artifact, *self.project_files, *self.feature_artifacts)


# ── § 2 — IO — locate, read, digest ──


def find_root(start: Path) -> Path | None:
    """Walk up from start looking for a .task directory."""
    for candidate in [start, *start.parents]:
        if (candidate / ROOT_DIR).is_dir():
            return candidate
    return None


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def digest(path: Path) -> str:
    """sha256 over LF-normalized UTF-8 bytes — source identity, not file identity."""
    return "sha256:" + hashlib.sha256(read_text(path).encode("utf-8")).hexdigest()


def parse_flat(text: str) -> dict[str, str]:
    """Top-level `key: value` pairs only. Enough for identity headers."""
    out: dict[str, str] = {}
    for line in text.split("\n"):
        if not line or line.startswith(" ") or line.lstrip().startswith("#"):
            continue
        if ": " in line:
            key, _, value = line.partition(": ")
            out.setdefault(key.strip(), value.strip())
        elif line.endswith(":"):
            out.setdefault(line[:-1].strip(), "")
    return out


def members(value: str) -> list[str]:
    """Parse a TDSL collection literal `[a b]` or legacy `[a, b]`."""
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    return [m for m in re.split(r"[,\s]+", inner) if m] if inner else []


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_blocks(text: str, container: str, key: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Parse one accumulated block. Indentation is derived, never assumed.

    tdsl-language ¶6: a container at indent N holds `key <label>:` at N+2 and
    that item's fields at N+4. Returns ({label: {field: raw_value}}, duplicates).
    """
    items: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    container_indent: int | None = None
    item_indent: int | None = None
    current: str | None = None
    # An `ln` body sits deeper than its own key. Dropping it made every check
    # over prose fields dead code, silently.
    ln_field: str | None = None
    ln_indent = 0
    ln_body: list[str] = []

    lines = text.split("\n")

    def flush_ln() -> None:
        nonlocal ln_field, ln_body
        if ln_field is not None and current is not None:
            items[current][ln_field] = "\n".join(ln_body).strip()
        ln_field, ln_body = None, []

    for line in lines:
        stripped = line.strip()
        indent = indent_of(line)

        if ln_field is not None:
            if not stripped or indent >= ln_indent:
                ln_body.append(stripped)
                continue
            flush_ln()

        if not stripped or stripped.startswith("#"):
            continue

        if container_indent is None:
            if stripped == f"{container}:":
                container_indent = indent
                item_indent = indent + 2
            continue

        if indent <= container_indent:
            break

        label = re.match(rf"^{key} ([A-Za-z0-9][A-Za-z0-9_.~-]*):$", stripped)
        if label and indent == item_indent:
            current = label.group(1)
            if current in items:
                duplicates.append(current)
            items.setdefault(current, {})
            continue

        if current is not None and indent == (item_indent or 0) + 2:
            body_start = re.match(r"^([a-z_]+) ln: \|$", stripped)
            if body_start:
                ln_field = body_start.group(1)
                ln_indent = indent + 2
                ln_body = []
                continue
            field_match = re.match(r"^([a-z_]+): ?(.*)$", stripped)
            if field_match:
                items[current][field_match.group(1)] = field_match.group(2)

    flush_ln()
    return items, duplicates


def top_level_value(text: str, name: str) -> str | None:
    for line in text.split("\n"):
        if line.startswith(f"{name}: "):
            return line.partition(": ")[2].strip()
    return None


def parse_reference(ref: str) -> tuple[str, str] | None:
    """`@spec/001-x#requirement/R001` -> ('requirement', 'R001')."""
    if "#" not in ref:
        return None
    _, _, part = ref.partition("#")
    kind, _, part_id = part.partition("/")
    return (kind, part_id) if kind and part_id else None


# ── § 3 — STATE — what exists, and what the anchor points at ──


class State:
    def __init__(self, root: Path, workflow: Workflow):
        self.root = root
        self.workflow = workflow
        self.base = root / ROOT_DIR
        anchor_path = self.base / ANCHOR
        source = read_text(anchor_path) if anchor_path.is_file() else ""
        self.anchor = parse_flat(source) if source else {}
        # Two slots, deliberately. `active_feature` is a cursor: which feature
        # this session is pointed at, one at most. `features:` is the register:
        # what each feature's position in the cycle is. One slot could not hold
        # both, so opening a feature used to erase the previous one from state.
        self.features, _ = parse_blocks(source, "features", "feature") if source else ({}, [])
        cursor = self.anchor.get("active_feature", "")
        cursor = "" if cursor in ("", "unknown") else cursor
        # A cursor left pointing at a closed feature routes nothing; closing is
        # what ends a cycle, and the cursor must not resurrect it.
        self.cursor = cursor
        self.feature = cursor if self.lifecycle_of(cursor) == ROUTING_STATE else ""
        # gradual: one feature walks its phases to execute before the next one opens.
        # integral: every active feature is planned (spec..analysis) before any execute.
        mode = (self.anchor.get("planning_mode", "") or "").strip()
        self.mode = mode if mode in PLANNING_MODES else "gradual"
        self.next_feature = ""

    def lifecycle_of(self, feature_id: str) -> str:
        """Position in the cycle. An unregistered feature is assumed in progress.

        Backward compatibility is not optional here: every anchor written before
        the register existed has no `features:` block, and must keep working.
        """
        if not feature_id:
            return ""
        state = (self.features.get(feature_id, {}).get("lifecycle", "") or "").strip()
        return state if state in LIFECYCLE_STATES else LIFECYCLE_DEFAULT

    def known_features(self) -> list[str]:
        """Every feature the project has, registered or merely present on disk."""
        found = set(self.features)
        directory = self.base / FEATURES
        if directory.is_dir():
            found |= {p.name for p in directory.iterdir() if p.is_dir()}
        return sorted(found)

    def path_of(self, artifact: str) -> Path | None:
        if artifact in self.workflow.project_files:
            return self.base / self.workflow.project_files[artifact]
        if artifact == self.workflow.project_artifact:
            return self.base / f"{artifact}.tdsl"
        if artifact in self.workflow.feature_artifacts:
            if not self.feature:
                return None
            return self.base / FEATURES / self.feature / f"{artifact}.tdsl"
        return None

    def exists(self, artifact: str) -> bool:
        path = self.path_of(artifact)
        return bool(path and path.is_file())

    def feature_has(self, feature_id: str, artifact: str) -> bool:
        return (self.base / FEATURES / feature_id / f"{artifact}.tdsl").is_file()

    def roadmap(self) -> list[dict]:
        """Planning position of every active feature, in id order."""
        rows = []
        for fid in self.known_features():
            if self.lifecycle_of(fid) != ROUTING_STATE:
                continue
            present = {a: self.feature_has(fid, a) for a, _ in self.workflow.next_phase_order}
            missing = next((ph for a, ph in self.workflow.next_phase_order if not present[a]), "")
            rows.append({"feature": fid, "present": present, "next": missing or self.workflow.terminal_phase})
        return rows

    def source_of(self, artifact: str) -> str | None:
        path = self.path_of(artifact)
        return read_text(path) if path and path.is_file() else None

    def snapshot(self) -> dict:
        artifacts = {}
        for artifact in self.workflow.artifacts:
            path = self.path_of(artifact)
            artifacts[artifact] = {
                "path": str(path.relative_to(self.root)) if path else None,
                "present": self.exists(artifact),
            }
        snapshot = {
            "root": str(self.root),
            "workflow": self.workflow.name,
            "project": self.anchor.get("id", "unknown"),
            "active_feature": self.feature or "unknown",
            "cursor": self.cursor or "unknown",
            "features": {
                fid: {
                    "lifecycle": self.lifecycle_of(fid),
                    "successor": self.features.get(fid, {}).get("successor", ""),
                    "closed_at": self.features.get(fid, {}).get("closed_at", ""),
                    "registered": fid in self.features,
                }
                for fid in self.known_features()
            },
            "artifacts": artifacts,
            "next_phase": self.next_phase(),
            "planning_mode": self.mode,
            "next_feature": self.next_feature or self.feature or "unknown",
        }
        if (self.base / "execution.config.tdsl").is_file():
            from execution_runtime import configuration, load_units
            snapshot["execution"] = configuration(self.root)
            snapshot["execution"]["units"] = load_units(self.root)
            snapshot["execution"]["scaffold_present"] = (self.base / "runtime/scaffold.json").is_file()
            snapshot["execution"]["tracking_present"] = (self.base / "tracking/registry.json").is_file()
        return snapshot

    def next_phase(self) -> str:
        """The next phase whose output does not exist yet. A suggestion, not an order.

        Existence alone used to decide this, so a delivered feature and a feature
        mid-flight were the same state: both answered `execute`. Position in the
        cycle is consulted first, and the answer is allowed to be `idle` — the
        flow had an entrance and a progression, and no exit.
        """
        if not (self.base / ANCHOR).is_file():
            return "initialize"
        if not self.exists(self.workflow.project_artifact):
            return self.workflow.project_artifact
        if (self.base / "execution.config.tdsl").is_file():
            from execution_runtime import configuration
            if configuration(self.root)["scaffold_required"] and not self.exists("architecture"):
                return "architecture"
        if self.mode == "integral":
            # Plan everything first: the first active feature still missing a
            # planning record is where work goes, wherever the cursor points.
            roadmap = self.roadmap()
            for row in roadmap:
                if row["next"] != self.workflow.terminal_phase:
                    self.next_feature = row["feature"]
                    return row["next"]
            if roadmap and (self.base / "execution.config.tdsl").is_file():
                self.next_feature = self.feature or roadmap[0]["feature"]
                return self.workflow.terminal_phase
        if not self.feature:
            # Nothing is pointed at. Whether that means "open the first feature"
            # or "nothing is pending" depends on whether this project ever had one.
            return IDLE if self.known_features() else "feature"
        for artifact, phase in self.workflow.next_phase_order:
            if not self.exists(artifact):
                return phase
        return self.workflow.terminal_phase


def journal_outcomes(state: State, include_runtime: bool = True) -> tuple[set[str], set[str]]:
    """Read the append-only execution journal: (completed, blocked) step ids."""
    if not state.feature:
        return set(), set()
    path = state.base / FEATURES / state.feature / JOURNAL
    done: set[str] = set()
    blocked: set[str] = set()
    # Legacy labels were task ids. Reduce each physical entry in order instead
    # of merging repeated labels and losing the outcome of a retry.
    text = read_text(path) if path.is_file() else ""
    chunks = re.split(r"(?m)^  entry ", text)[1:]
    for chunk in chunks:
        label, _, body = chunk.partition(":\n")
        entries, _ = parse_blocks("journal:\n  entry " + label + ":\n" + body, "journal", "entry")
        fields = entries.get(label, {})
        step_id = fields.get("task_ref", label).rsplit("/", 1)[-1]
        outcome = fields.get("outcome", "").strip()
        if outcome == "completed":
            done.add(step_id)
            blocked.discard(step_id)
        elif outcome in ("blocked", "failed", "interrupted", "started"):
            done.discard(step_id)
            blocked.add(step_id)
    if include_runtime:
        from runtime_journal import execution_state
        prefix = f"@tasks/{state.feature}#task/"
        for ref, fields in execution_state(state.root).items():
            if not ref.startswith(prefix):
                continue
            tid = ref[len(prefix):]
            done.discard(tid)
            blocked.discard(tid)
            if fields.get("outcome") == "completed":
                done.add(tid)
            elif fields.get("outcome") in ("blocked", "failed", "interrupted", "started"):
                blocked.add(tid)
    return done, blocked


# ── § 4 — CHECK — lexical and structural conformance, no dialect knowledge ──


def cycle_nodes(edges: dict[str, list[str]]) -> list[str]:
    """Every node that closes a cycle in a dependency map. Iterative, not recursive.

    Lived inline in the task check while the subtask check had none, so a cyclic
    decomposition passed conformance. One dependency model, one cycle detector.
    """
    color: dict[str, int] = {node: 0 for node in edges}
    found: list[str] = []
    for start in edges:
        if color[start]:
            continue
        color[start] = 1
        stack = [(start, iter(edges[start]))]
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if child not in edges:
                    continue
                if color[child] == 1:
                    found.append(child)
                    color[child] = 2
                elif color[child] == 0:
                    color[child] = 1
                    stack.append((child, iter(edges[child])))
                    advanced = True
                    break
            if not advanced:
                color[node] = 2
                stack.pop()
    return found


def check_source(path: Path) -> list[tuple[str, str]]:
    """Conformance shared by every tracked TDSL source, whatever its dialect."""
    findings: list[tuple[str, str]] = []
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        findings.append((FAIL, "TDSL-E102 BOM_forbidden"))
    text = read_text(path)
    if text and not text.endswith("\n"):
        findings.append((FAIL, "TDSL-E003 final_newline required"))
    for number, line in enumerate(text.split("\n"), start=1):
        if "\t" in line:
            findings.append((FAIL, f"TDSL-E104 tab at line {number}"))
        if line != line.rstrip():
            findings.append((FAIL, f"TDSL-E106 trailing_whitespace at line {number}"))
        if line.strip() and indent_of(line) % 2:
            findings.append((FAIL, f"TDSL-E105 invalid_indent at line {number}"))
        if re.search(r"\{[*#]?[a-z_][a-z0-9_.]*\}", line):
            findings.append((FAIL, f"TDSL-E504 unresolved placeholder at line {number}"))
        if re.match(r"^\s*(for|when|when_empty)\s+\S+.*:$", line):
            findings.append((FAIL, f"TDSL-E504 template directive in ordinary source at line {number}"))
        collection = re.search(r": \[(.*)\]$", line)
        if collection:
            body = collection.group(1).strip()
            if "," in body and re.search(r"[^,]\s", re.sub(r",\s", ",", body)):
                findings.append((WARN, f"TDSL-E203 mixed collection separators at line {number}"))

    header = parse_flat(text)
    for name in ("tdsl", "schema_revision", "id"):
        if name not in header:
            findings.append((FAIL, f"TDSL-E305 required identity field missing: {name}"))
    revision = header.get("schema_revision", "")
    if revision and not (DIGEST_RE.match(revision) or revision.startswith("local:")):
        findings.append((FAIL, "TDSL-E304 schema_revision is neither sha256:<64 hex> nor local:<id>"))
    if "id" in header and not REF_RE.match(header["id"]):
        findings.append((FAIL, f"TDSL-E401 malformed_reference: {header['id']}"))
    return findings


def emit(findings: list[tuple[str, str]], label: str) -> int:
    worst = OK
    for level, message in findings:
        print(f"  {level.upper():4} {message}")
        if level == FAIL:
            worst = FAIL
        elif worst == OK:
            worst = WARN
    print(f"{label}: {worst.upper()}")
    return 1 if worst == FAIL else 0


def build_payload(state: State, findings: list[tuple[str, str, str]]) -> dict:
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f[0], 9), f[1], f[2]))
    serious = sum(1 for severity, _, _ in findings if severity in ("blocking", "material"))
    return {
        "result": "fail" if serious else "pass",
        "workflow": state.workflow.name,
        "feature": state.feature,
        "counts": {s: sum(1 for x, _, _ in findings if x == s) for s in SEVERITY_ORDER},
        "findings": [{"severity": s, "code": c, "message": m} for s, c, m in findings],
    }


# ── § 5 — COMMANDS — the parts no workflow needs to reimplement ──


def resolve_state(args, workflow: Workflow) -> State:
    root = find_root(Path(args.cwd).resolve())
    if root is None:
        print(f"FAIL: no {ROOT_DIR}/ anchor found from {args.cwd}. Run `init` first.")
        sys.exit(2)
    state = State(root, workflow)
    scope = getattr(args, "feature_scope", None)
    if scope:
        if scope not in state.known_features():
            raise ValueError(f"unknown feature scope: {scope}")
        state.cursor = scope
        state.feature = scope if state.lifecycle_of(scope) == ROUTING_STATE else ""
    return state


def cmd_init(args, workflow: Workflow) -> int:
    root = Path(args.cwd).resolve()
    base = root / ROOT_DIR
    if (base / ANCHOR).is_file():
        print(f"FAIL: {base / ANCHOR} already exists, refusing to overwrite the anchor.")
        return 2
    (base / FEATURES).mkdir(parents=True, exist_ok=True)
    name = args.name or root.name
    (base / ANCHOR).write_text(
        "tdsl: project_anchor@1\n"
        f"schema_revision: {LOCAL_ANCHOR_REVISION}\n"
        f"id: @project/{name}\n"
        "version: 1\n"
        "status: proposed\n"
        f"purpose: protocol anchor for {name}\n"
        f"workflow: {workflow.name} # discovered from operator intent; a record, not a switch\n"
        "active_feature: unknown\n"
        f"planning_mode: {args.mode}\n",
        encoding="utf-8", newline="\n")
    placed = place_scaffold(base, workflow)
    from execution_runtime import migrate
    migrate(root)
    print(f"OK: initialized {base} for workflow `{workflow.name}`")
    if placed:
        print(f"OK: {len(placed)} authoring skeletons in {ROOT_DIR}/{SCAFFOLD}/ "
              f"({' '.join(sorted(placed))})")
    print(f"Next phase: {workflow.project_artifact}")
    return 0


def place_scaffold(base: Path, workflow: Workflow) -> list[str]:
    """Copy every authoring skeleton into the project, in one pass.

    Deliberately outside the paths `path_of` resolves. A skeleton dropped where
    an artifact belongs would satisfy the existence test `next_phase` runs, and
    a freshly initialized project would report itself ready to execute. It also
    carries placeholders and directives, which `check` refuses by design — the
    skeleton is what a phase fills in, never a record.
    """
    target = base / SCAFFOLD
    target.mkdir(parents=True, exist_ok=True)
    placed: list[str] = []
    for artifact, skill in workflow.skeleton_of.items():
        source = HARNESS / "skills" / skill / "template.tdsl"
        if not source.is_file():
            continue
        (target / f"{artifact}.tdsl").write_text(read_text(source), encoding="utf-8", newline="\n")
        placed.append(artifact)
    if placed:
        (target / "README.md").write_text(
            "# Authoring skeletons\n\n"
            "Shapes, not records. Every project's structure is the same; only the\n"
            "content differs. A phase skill reads the skeleton here and writes the\n"
            "artifact in its real location.\n\n"
            "These files carry placeholders and directives on purpose, so `check`\n"
            "refuses them. They are never a governed record, and nothing routes\n"
            "off their existence.\n\n"
            f"Refresh after a harness update: `{SCAFFOLD} <- scaffold` command.\n",
            encoding="utf-8", newline="\n")
    return placed


def cmd_scaffold(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    placed = place_scaffold(state.base, workflow)
    if not placed:
        print(f"WARN: no template found under {HARNESS / 'skills'}; nothing placed")
        return 1
    print(f"OK: {len(placed)} skeletons in {ROOT_DIR}/{SCAFFOLD}/: {' '.join(sorted(placed))}")
    return 0


def cmd_state(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    snapshot = state.snapshot()
    if getattr(args, "json", False):
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return 0
    lines = [
        "# protocol state", "",
        f"workflow: {snapshot['workflow']}",
        f"project: {snapshot['project']}",
        f"active_feature: {snapshot['active_feature']}",
        "", "| artefato | existe |", "| --- | --- |",
    ]
    for artifact, data in snapshot["artifacts"].items():
        lines.append(f"| {artifact} | {'sim' if data['present'] else '—'} |")
    if snapshot["features"]:
        lines += ["", "| feature | ciclo de vida | nota |", "| --- | --- | --- |"]
        for fid, data in snapshot["features"].items():
            note = data["successor"] and f"sucessora {data['successor']}" or data["closed_at"]
            lines.append(f"| {fid} | {data['lifecycle']} | {note or '—'} |")
    lines += ["", f"planning_mode: {snapshot['planning_mode']}",
              f"next_phase: {snapshot['next_phase']} (feature: {snapshot['next_feature']})"]
    if snapshot["next_phase"] == IDLE:
        lines.append("")
        lines.append("Nenhum trabalho governado aberto. O próximo passo é decisão do operador: "
                     "abrir uma feature, reabrir uma fechada, ou nada.")
    lines.append("")
    report = "\n".join(lines)
    print(report)
    cache = state.root / CACHE_DIR
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "protocol-state.md").write_text(report, encoding="utf-8", newline="\n")
    return 0


def cmd_gate(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    phase = args.phase
    if phase not in workflow.phases:
        print(f"FAIL: unknown phase {phase}. Known: {' '.join(workflow.phases)}")
        return 2
    required, _ = workflow.phases[phase]
    blocked: list[str] = []
    if phase not in {"initialize", workflow.project_artifact, "feature", *workflow.project_files} and not state.feature:
        if state.cursor:
            blocked.append(
                f"{state.cursor} is {state.lifecycle_of(state.cursor)}, not active; "
                f"a closed feature routes no work. Reopen it or activate another.")
        else:
            blocked.append(f"no active feature in {ROOT_DIR}/{ANCHOR}")
    for artifact in required:
        if not state.exists(artifact):
            blocked.append(f"{artifact} does not exist; `{phase}` references its parts")
    if phase == "execute" and (state.base / "execution.config.tdsl").is_file():
        from execution_runtime import execution_status, preserve_constitution
        blocked.extend(execution_status(state.root)["blockers"])
        if not blocked:
            preserve_constitution(state.root)
    if blocked:
        for item in blocked:
            print(f"  FAIL {item}")
        print(f"gate {phase}: FAIL")
        return 1
    print(f"gate {phase}: OK")
    return 0


def cmd_check(args, workflow: Workflow) -> int:
    path = Path(args.path).resolve()
    if not path.is_file():
        print(f"FAIL: {path} not found")
        return 2
    findings = check_source(path)
    artifact = path.name[:-len(".tdsl")] if path.name.endswith(".tdsl") else path.stem
    extra = workflow.dialect_checks.get(artifact)
    if extra:
        findings += extra(path)
    expected = workflow.dialect_of.get(artifact)
    actual = parse_flat(read_text(path)).get("tdsl")
    supported = {expected}
    if expected and expected.endswith("@1") and artifact in {"constitution", "spec", "plan", "tasks", "analysis"}:
        supported.add(expected[:-1] + "2")
    if expected and actual not in supported:
        findings.append((FAIL, f"TDSL-E701 dialect is {actual}, expected {expected}"))
    if actual and (actual.endswith("@2") or actual in {"project_execution@1", "execution_journal@1", "decision_journal@1", "failure_journal@1"}):
        from contract_check import check_contract
        findings.extend(check_contract(path))
    return emit(findings, f"check {path.name}")


def write_anchor(state: State, cursor: str | None = None,
                 register: dict[str, dict[str, str]] | None = None) -> None:
    """Rewrite the anchor's two mutable slots. The only writer of either.

    Text surgery rather than a re-emit: the anchor carries operator comments and
    field order that a naive serializer would silently discard.
    """
    path = state.base / ANCHOR
    text = read_text(path)

    if cursor is not None:
        value = cursor or "unknown"
        text, count = re.subn(r"^active_feature: .*$", f"active_feature: {value}",
                              text, flags=re.M)
        if count == 0:
            if not text.endswith("\n"):
                text += "\n"
            text += f"active_feature: {value}\n"
        elif count > 1:
            raise ValueError(f"{ANCHOR} declares active_feature {count} times")

    if register is not None:
        lines = text.split("\n")
        container = next((i for i, line in enumerate(lines)
                          if line.rstrip() == "features:"), None)
        if container is not None:
            # The block ends at the next column-zero statement. Walking from the
            # comment above it instead stopped on the container line itself, so
            # every write left the previous register behind it.
            end = container + 1
            while end < len(lines) and (not lines[end].strip() or lines[end].startswith(" ")):
                end += 1
            start = container
            while start and lines[start - 1].lstrip().startswith("#"):
                start -= 1
            del lines[start:end]
        else:
            start = len(lines)
            while start and not lines[start - 1].strip():
                start -= 1
        # tdsl-language: comments are full-line only. An inline one here made the
        # container unparseable, so the register read back empty and every
        # closed feature silently reverted to active.
        block = ["# register of position in the cycle; never a judgement of quality",
                 "features:"]
        for fid in sorted(register):
            block.append(f"  feature {fid}:")
            for name in ("lifecycle", "successor", "closed_at", "reason", "depends_on"):
                value = register[fid].get(name, "")
                if value:
                    block.append(f"    {name}: {value}")
        lines[start:start] = block + [""]
        text = "\n".join(lines)

    while text.endswith("\n\n"):
        text = text[:-1]
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def current_register(state: State) -> dict[str, dict[str, str]]:
    """The register as it stands, with anything only present on disk filled in."""
    register = {fid: dict(fields) for fid, fields in state.features.items()}
    for fid in state.known_features():
        entry = register.setdefault(fid, {})
        entry.setdefault("lifecycle", LIFECYCLE_DEFAULT)
    return register


def succession_problem(state: State, feature_id: str, successor: str) -> str:
    """Why this succession edge would be a claim with no evidence, or nothing at all.

    Requiring a successor to exist was not enough: a feature naming itself
    satisfies the letter and records no substitution, and a chain that closes on
    itself asserts that work was replaced by work that never shipped.
    """
    if successor == feature_id:
        return f"{feature_id} cannot succeed itself; that records no substitution"
    if successor not in state.known_features():
        return f"successor {successor} does not exist"
    if state.lifecycle_of(successor) == "abandoned":
        return (f"successor {successor} is abandoned; work cannot be superseded by "
                "work that was never delivered")

    # Walk the chain the new edge would create. Any return to a feature already
    # visited is a cycle, and a cycle says everything replaced everything.
    chain = [feature_id]
    node = successor
    while node:
        if node in chain:
            return f"succession cycle: {' -> '.join([*chain, node])} closes on itself"
        chain.append(node)
        node = (state.features.get(node, {}).get("successor", "") or "").strip()
    return ""


def cmd_close(args, workflow: Workflow) -> int:
    """End a feature's cycle. The operator directs it; this only records it.

    The flow had `feature` to open and nothing to close, and that asymmetry is
    the whole bias: every answer the router could give was an imperative.
    """
    state = resolve_state(args, workflow)
    if args.state == "delivered" and (state.base / "execution.config.tdsl").is_file():
        from execution_runtime import latest_outcomes
        task_path = state.base / FEATURES / args.id / "tasks.tdsl"
        if not task_path.is_file():
            print("FAIL: tasks missing; delivery cannot be established")
            return 1
        tasks, _ = parse_blocks(read_text(task_path), "tasks", "task")
        outcomes = latest_outcomes(state.root)
        if not tasks or any(outcomes.get(f"@tasks/{args.id}#task/{tid}", {}).get("outcome") != "completed" for tid in tasks):
            print("FAIL: delivery requires completed journal evidence for every task")
            return 1
    if args.state not in CLOSED_STATES:
        print(f"FAIL: --as must be one of {' '.join(CLOSED_STATES)}, got {args.state}")
        return 2
    if args.id not in state.known_features():
        print(f"FAIL: unknown feature {args.id}; nothing under {ROOT_DIR}/{FEATURES}/ by that name")
        return 2
    if state.lifecycle_of(args.id) != ROUTING_STATE and not args.reopen:
        print(f"FAIL: {args.id} is already {state.lifecycle_of(args.id)}; "
              "pass --reopen to reclassify it")
        return 1
    # `superseded` without a named successor is a claim with no evidence, and
    # `abandoned` without a reason is a fact nobody can audit later. The reverse
    # matters too: a `delivered` carrying a closing reason implies a
    # justification for ending that its own state says does not exist.
    if args.state == "superseded" and not args.successor:
        print("FAIL: --as superseded requires --successor <feature-id>")
        return 2
    if args.successor and args.state != "superseded":
        print(f"FAIL: --successor is meaningless for --as {args.state}; "
              "only a superseded feature has one")
        return 2
    if args.reason and args.state != "abandoned":
        print(f"FAIL: --reason is meaningless for --as {args.state}; "
              "only an abandoned feature records why it ended")
        return 2
    if args.state == "abandoned" and not args.reason:
        print("FAIL: --as abandoned requires --reason <text>")
        return 2

    if args.successor:
        problem = succession_problem(state, args.id, args.successor)
        if problem:
            print(f"FAIL: {problem}")
            return 2

    register = current_register(state)
    entry = register.setdefault(args.id, {})
    entry["lifecycle"] = args.state
    entry["closed_at"] = args.at or _today()
    if args.successor:
        entry["successor"] = args.successor
    if args.reason:
        entry["reason"] = args.reason.replace("\n", " ").strip()

    cursor = "" if state.cursor == args.id else None
    write_anchor(state, cursor=cursor, register=register)
    print(f"OK: {args.id} -> {args.state}")
    if cursor is not None:
        print("cursor cleared; no feature is active")
    print(f"next_phase: {State(state.root, workflow).next_phase()}")
    return 0


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def cmd_mode(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    if not args.value:
        print(f"planning_mode: {state.mode}")
        return 0
    anchor = state.base / ANCHOR
    text = anchor.read_text(encoding="utf-8")
    if re.search(r"^planning_mode:.*$", text, flags=re.M):
        text = re.sub(r"^planning_mode:.*$", f"planning_mode: {args.value}", text, flags=re.M)
    else:
        text = text.rstrip("\n") + f"\nplanning_mode: {args.value}\n"
    anchor.write_text(text, encoding="utf-8", newline="\n")
    print(f"planning_mode: {args.value}")
    return 0


def cmd_roadmap(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    rows = state.roadmap()
    if getattr(args, "json", False):
        print(json.dumps({"planning_mode": state.mode, "features": rows}, indent=2, ensure_ascii=False))
        return 0
    phases = [a for a, _ in workflow.next_phase_order]
    lines = [f"planning_mode: {state.mode}", "",
             "| feature | " + " | ".join(phases) + " | next |",
             "| --- |" + " --- |" * (len(phases) + 1)]
    for r in rows:
        lines.append(f"| {r['feature']} | " + " | ".join("x" if r["present"][a] else "—" for a in phases)
                     + f" | {r['next']} |")
    planned = all(r["next"] == workflow.terminal_phase for r in rows) and rows
    lines += ["", "all features planned; execution may start" if planned else "planning incomplete"]
    print("\n".join(lines))
    return 0


def cmd_feature(args, workflow: Workflow) -> int:
    state = resolve_state(args, workflow)
    if not FEATURE_ID_RE.match(args.id):
        print(f"FAIL: feature id must match NNN-kebab-case, got {args.id}")
        return 2
    if not state.exists(workflow.project_artifact):
        print(f"FAIL: {workflow.project_artifact} does not exist; write it first")
        return 1
    # A feature that was closed does not silently reopen because the cursor
    # moved onto it: reclassifying is an operator act, and it is spelled out.
    standing = state.lifecycle_of(args.id) if args.id in state.known_features() else ""
    if standing and standing != ROUTING_STATE and not args.reopen:
        print(f"FAIL: {args.id} is {standing}, not active. "
              "Pass --reopen to put it back in work, or pick another id.")
        return 1

    register = current_register(state)
    entry = register.setdefault(args.id, {})
    entry["lifecycle"] = ROUTING_STATE
    dependencies = getattr(args, "depends_on", None)
    if dependencies is not None:
        dependencies = [dep.removeprefix("@feature/") for dep in dependencies]
        if args.id in dependencies or any(dep not in state.known_features() for dep in dependencies):
            print("FAIL: feature dependencies must name existing other features")
            return 1
        entry["depends_on"] = "[" + " ".join(dependencies) + "]"
        graph = {fid: members(item.get("depends_on", "[]")) for fid, item in register.items()}
        if cycle_nodes(graph):
            print("FAIL: feature dependency cycle")
            return 1
    if args.reopen:
        # Reopening does not rewrite history; it drops the closing facts that no
        # longer hold, and keeps nothing that would now be false.
        for stale in ("closed_at", "successor", "reason"):
            entry.pop(stale, None)
    try:
        (state.base / FEATURES / args.id).mkdir(parents=True, exist_ok=True)
        write_anchor(state, cursor=args.id, register=register)
    except ValueError as error:
        print(f"FAIL: {error}; fix it by hand")
        return 1
    print(f"OK: active_feature = {args.id}")
    print(f"next_phase: {State(state.root, workflow).next_phase()}")
    return 0


def write_analysis_cache(state: State, payload: dict) -> None:
    cache = state.root / CACHE_DIR
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "protocol-analysis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


# ── § 6 — ENTRY — the argument surface every workflow gate shares ──


def build_parser(workflow: Workflow, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--cwd", default=".", help="directory to resolve the .task anchor from")
    parser.add_argument("--feature", dest="feature_scope", help="inspect the target feature without moving the shared cursor")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create the .task anchor")
    p.add_argument("--name", default=None)
    p.add_argument("--mode", choices=PLANNING_MODES, default="gradual",
                   help="gradual: one feature to execute at a time; integral: plan every feature first")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("state", help="report what exists and the next phase")
    p.add_argument("--json", action="store_true")
    p.add_argument("--if-present", action="store_true", dest="if_present",
                   help="hook mode: emit nothing and succeed when there is no anchor")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("gate", help="check that a phase's predecessors exist")
    p.add_argument("phase", choices=sorted(workflow.phases))
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("check", help="conformance-check one TDSL record")
    p.add_argument("path")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("mode", help="show or switch the planning mode")
    p.add_argument("value", nargs="?", choices=PLANNING_MODES)
    p.set_defaults(func=cmd_mode)

    p = sub.add_parser("roadmap", help="planning position of every active feature")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_roadmap)

    p = sub.add_parser("feature", help="activate a feature id")
    p.add_argument("id")
    p.add_argument("--depends-on", nargs="*", default=None, help="explicit predecessor feature ids")
    p.add_argument("--reopen", action="store_true",
                   help="put a closed feature back in work; drops its closing facts")
    p.set_defaults(func=cmd_feature)

    p = sub.add_parser("scaffold", help="re-place the authoring skeletons in this project")
    p.set_defaults(func=cmd_scaffold)

    p = sub.add_parser("close", help="record where a feature ended in its cycle")
    p.add_argument("id")
    p.add_argument("--as", dest="state", required=True, choices=sorted(CLOSED_STATES))
    p.add_argument("--successor", default="", help="required by --as superseded")
    p.add_argument("--reason", default="", help="required by --as abandoned")
    p.add_argument("--at", default="", help="closing date; defaults to today")
    p.add_argument("--reopen", action="store_true",
                   help="reclassify a feature that is already closed")
    p.set_defaults(func=cmd_close)

    return parser


def run(parser: argparse.ArgumentParser, workflow: Workflow) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = parser.parse_args()
    if getattr(args, "if_present", False) and find_root(Path(args.cwd).resolve()) is None:
        return 0
    return args.func(args, workflow)
