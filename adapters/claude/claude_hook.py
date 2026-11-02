# ────────────────────────────────────────────
# TASK 1.1.0 — claude_hook.py
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

# Resolve siblings from this file, never from ~/.claude: a copy under test must
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
GATE_OWNED = ("/.task/decisions/", "/.task/project.tdsl", "/.task/.scaffold/")

SOURCE_SUFFIXES = {
    ".rs", ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".kt", ".swift",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".rb", ".sh", ".ps1", ".lua", ".sql",
}


# ── § 2 — SESSION MARKERS — a routed document is force-loaded once per session ──


def marker(session_id: str, name: str) -> Path:
    directory = Path(tempfile.gettempdir()) / "claude-hook-markers"
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


def inject(context: str, message: str | None = None) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
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


def handle_task(session_id: str) -> None:
    """First spawn of a session: refuse until the briefing contract is in context."""
    if already_loaded(session_id, "delegation"):
        allow_silently()
    body = read_doc(DELEGATION)
    if not body:
        allow_silently()
    deny(
        "Delegation policy was not in context for this session's first spawn.\n"
        "It is loaded below. Re-issue the Task call with a briefing that satisfies "
        "the contract (pure TDSL, points to the artifact, <~400 tokens).\n"
        "This block fires once per session; the next Task call passes.\n\n"
        + body
    )


def protocol_target(file_path: str) -> tuple[str, str, str] | None:
    """Return (workflow, artifact, phase) when the write targets a governed record."""
    normalized = file_path.replace("\\", "/")
    if "/.task/" not in normalized and not normalized.startswith(".task/"):
        return None
    if any(owned in normalized for owned in GATE_OWNED):
        return None
    name = Path(normalized).name
    if not name.endswith(".tdsl"):
        return None  # só artefatos TDSL são governados
    artifact = name[: -len(".tdsl")]
    workflow = workflow_of(file_path)
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


def workflow_of(file_path: str) -> str:
    """Which tree owns this write. The anchor's record first, then the evidence."""
    declared = anchor_fields(file_path).get("workflow", "")
    if declared in ARTIFACT_PHASE:
        return declared
    return "sdd"


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
    directory = str(Path(file_path).parent)
    try:
        proc = subprocess.run(
            [sys.executable, str(GATES[workflow]), "--cwd", directory, "gate", phase],
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
            f"  python ~/.claude/scripts/{GATES[workflow].name} init --name <project>"
        )

    # The gate reasons about the active feature; a write aimed at a different
    # feature directory would be validated against the wrong chain.
    target = feature_of(file_path)
    if target is not None:
        current = active_feature(file_path)
        if current != target:
            deny(
                f"This write targets feature `{target}` but the active feature is "
                f"`{current or 'none'}`. The gate validates the active chain, so the "
                "prerequisites it checked do not describe this file.\n"
                f"Activate it first, with operator authorization:\n"
                f"  python ~/.claude/scripts/{GATES[workflow_of(file_path)].name} feature {target}"
            )

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

    session_id = event.get("session_id", "")
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool == "Task":
        handle_task(session_id)
        return 0


    if tool in ("Write", "Edit", "NotebookEdit"):
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if not file_path:
            return 0
        target = protocol_target(file_path)
        if target:
            handle_protocol_write(session_id, file_path, *target)
            return 0
        handle_source_write(session_id, file_path)
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # a hook must never wedge the session
