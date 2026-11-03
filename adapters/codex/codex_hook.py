# ────────────────────────────────────────────
# TASK 1.1.0 — codex_hook.py
# § - PreToolUse router: enforce the .task gate, force-load routed policy once · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ── § 1 — CONFIG — routed documents and their trigger ──

# Resolve siblings from this file, never from ~/.codex: a copy under test must
# call its own gates and load its own policy.
HARNESS = Path(__file__).resolve().parent.parent
DOCS = HARNESS / "docs"
# Cada workflow tem seu gate e seus registros. O hook descobre qual pela âncora,
# porque escrever um part.tdsl contra o gate de desenvolvimento não gateia nada.
GATES = {
    "sdd": HARNESS / "scripts/sdd_gate.py",
}

DELEGATION = DOCS / "delegation.tdsl"
ENGINEERING = DOCS / "engineering.tdsl"
POLICY = {"sdd": DOCS / "sdd.tdsl"}

# workflow -> artifact filename -> gate phase that must pass before it may be written
ARTIFACT_PHASE = {
    "sdd": {
        "constitution": "constitution",
        "Architecture": "architecture",
        "spec": "specify",
        "plan": "plan",
        "tasks": "tasks",
        "analysis": "analyze",
        "decomposition": "decompose",
    },
}

# writes inside .task that the gate itself owns; never intercepted
# Skeletons are shapes, not records: gating them as if they were an artifact
# would refuse a write that authors nothing.
SOURCE_SUFFIXES = {
    ".rs", ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".kt", ".swift",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".rb", ".sh", ".ps1", ".lua", ".sql",
}


# ── § 2 — SESSION MARKERS — a routed document is force-loaded once per session ──


def marker(session_id: str, name: str) -> Path:
    directory = Path(tempfile.gettempdir()) / "codex-hook-markers"
    directory.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "nosession")
    return directory / f"{safe}.{name}"


def already_loaded(session_id: str, name: str) -> bool:
    path = marker(session_id, name)
    if path.exists():
        return True
    path.write_text("1", encoding="utf-8")
    return False


# ── § 3 — RESPONSES ──


def respond(payload: dict) -> None:
    print(json.dumps(payload))
    sys.exit(0)


def allow_silently() -> None:
    sys.exit(0)


def deny(reason: str) -> None:
    respond({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def inject(context: str, message: str | None = None,
           event_name: str = "PreToolUse") -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }
    if message:
        payload["systemMessage"] = message
    respond(payload)


def read_doc(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ── § 4 — HANDLERS ──


def handle_subagent_start() -> None:
    """Inject the briefing contract into every Codex subagent context."""
    body = read_doc(DELEGATION)
    if not body:
        allow_silently()
    inject(body, "delegation contract loaded for this subagent", "SubagentStart")


def patch_paths(command: str) -> list[str]:
    """Extract target paths from Codex apply_patch input."""
    return re.findall(
        r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+?)\s*$",
        command,
        flags=re.MULTILINE,
    )


def protocol_target(file_path: str) -> tuple[str, str, str] | None:
    """Return (workflow, artifact, phase) when the write targets a governed record."""
    normalized = file_path.replace("\\", "/")
    if "/.task/" not in normalized and not normalized.startswith(".task/"):
        return None
    parts = tuple(part for part in normalized.split("/") if part)
    protocol_index = parts.index(".task")
    governed_parts = parts[protocol_index + 1:]
    if (not governed_parts or governed_parts[0] in ("decisions", ".scaffold")
            or governed_parts == ("project.tdsl",)):
        return None
    name = Path(normalized).name
    if name == "Architecture.md":
        return "sdd", "Architecture", "architecture"
    if not name.endswith(".tdsl"):
        return None  # só artefatos TDSL são governados
    artifact = name[: -len(".tdsl")]
    workflow = workflow_of(file_path, artifact)
    if workflow is None:
        return "unknown", artifact, "unknown"
    phase = ARTIFACT_PHASE[workflow].get(artifact)
    if phase is None:
        return None
    return workflow, artifact, phase


def anchor_fields(file_path: str) -> dict[str, str]:
    """Read the anchor directly: cheaper than a subprocess, and the hook is hot."""
    for parent in Path(file_path).resolve().parents:
        anchor = parent / ".task" / "project.tdsl"
        if anchor.is_file():
            out: dict[str, str] = {}
            for line in anchor.read_text(encoding="utf-8", errors="replace").split("\n"):
                if ": " in line and not line.startswith(" "):
                    key, _, value = line.partition(": ")
                    out[key.strip()] = value.partition(" #")[0].strip()
            return out
    return {}


def active_feature(file_path: str) -> str | None:
    value = anchor_fields(file_path).get("active_feature", "")
    return None if value in ("", "unknown") else value


def workflow_of(file_path: str, artifact: str | None = None) -> str | None:
    """Resolve the owning tree without silently turning ambiguity into SDD."""
    declared = anchor_fields(file_path).get("workflow", "")
    if declared in ARTIFACT_PHASE:
        return declared
    if artifact:
        owners = [name for name, phases in ARTIFACT_PHASE.items() if artifact in phases]
        if len(owners) == 1:
            return owners[0]
    return None


def feature_of(file_path: str) -> str | None:
    parts = file_path.replace("\\", "/").split("/")
    if "features" in parts:
        index = parts.index("features")
        if index + 1 < len(parts):
            return parts[index + 1]
    return None


def handle_protocol_write(session_id: str, file_path: str,
                          workflow: str, artifact: str, phase: str) -> None:
    """The gate decides. A failing prerequisite blocks the write outright."""
    if workflow == "unknown":
        deny(
            f"The workflow owning {file_path} is ambiguous. Declare `workflow: sdd` "
            "or `workflow: cad` in .task/project.tdsl before writing this shared record."
        )
    directory = str(Path(file_path).parent)
    target_feature = feature_of(file_path)
    scope = ["--feature", target_feature] if target_feature else []
    try:
        proc = subprocess.run(
            [sys.executable, str(GATES[workflow]), "--cwd", directory, *scope, "gate", phase],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        allow_silently()  # fail open: a broken gate must not wedge the session
        return

    if proc.returncode == 2:
        deny(
            f"{file_path} sits under .task/ but the project has no anchor, so no "
            "phase can be gated. Ask the operator to authorize:\n"
            f"  python ~/.codex/scripts/{GATES[workflow].name} init --name <project>"
        )

    # Targeted gates never mutate the cursor shared by concurrent units.
    if proc.returncode != 0:
        deny(
            f"The `{phase}` gate refuses this write to {artifact}.tdsl.\n\n"
            f"{proc.stdout.strip()}\n\n"
            "Resolve the prerequisite, or tell the operator what is blocked. "
            "Do not mutate a predecessor to make this pass."
        )

    marker_name = f"policy-{workflow}"
    if not already_loaded(session_id, marker_name):
        inject(read_doc(POLICY[workflow]),
               f"protocol/{workflow}: {phase} gate OK, lifecycle policy loaded")
    allow_silently()


def handle_source_write(session_id: str, file_path: str) -> None:
    if Path(file_path).suffix.lower() not in SOURCE_SUFFIXES:
        allow_silently()
    if already_loaded(session_id, "engineering"):
        allow_silently()
    body = read_doc(ENGINEERING)
    if not body:
        allow_silently()
    inject(body, "engineering standards loaded for this session")


# ── § 5 — ENTRY ──


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    if event.get("hook_event_name") == "PostToolUse":
        proc = subprocess.run(
            [sys.executable, str(HARNESS / "scripts/post_write.py"),
             "--cwd", event.get("cwd") or os.getcwd()],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.stdout.strip():
            inject(proc.stdout.strip(), "structural reconciliation", event_name="PostToolUse")
        return 0

    session_id = event.get("session_id", "")
    event_name = event.get("hook_event_name", "")
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if event_name == "SubagentStart":
        handle_subagent_start()
        return 0

    if event_name == "PreToolUse" and tool == "apply_patch":
        paths = patch_paths(tool_input.get("command", ""))
        if not paths:
            return 0
        governed = [(path, protocol_target(path)) for path in paths]
        governed = [(path, target) for path, target in governed if target]
        if len(governed) > 1:
            deny(
                "One apply_patch call targets multiple governed records. "
                "Write one .task record per patch so each phase gate is explicit."
            )
        if governed:
            file_path, target = governed[0]
            handle_protocol_write(session_id, file_path, *target)
            return 0
        for file_path in paths:
            if Path(file_path).suffix.lower() in SOURCE_SUFFIXES:
                handle_source_write(session_id, file_path)
                return 0
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # a hook must never wedge the session
