# ────────────────────────────────────────────
# TASK 2.2.0 — _entrypoint.py
# § - Load one departmental implementation through stable public script paths · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — COMPATIBILITY — Preserve module identity and legacy resource resolution ──
from pathlib import Path
from typing import Any


def load(namespace: dict[str, Any], implementation: str) -> None:
    """Execute one authoritative implementation in its public module namespace.

    Keep __file__ at the compatibility entrypoint so existing sibling imports,
    schema locations and fixture paths retain their established meaning. Python
    tracebacks use the departmental source path from compile().
    """
    legacy = Path(namespace["__file__"]).resolve()
    root = legacy.parent.parent
    target = (root / implementation).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise ImportError(f"TASK departmental implementation is unavailable: {implementation}")
    namespace["__task_implementation__"] = str(target)
    exec(compile(target.read_bytes(), str(target), "exec"), namespace)
