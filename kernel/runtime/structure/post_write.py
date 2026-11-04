# ────────────────────────────────────────────
# TASK 2.2.0 — post_write.py
# § - Reconcile structural indexes only on explicit invocation · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
from pathlib import Path

from protocol_core import find_root

# ── § 1 — RECONCILIATION — Refresh derived navigation on explicit request ──


def post_write(cwd: Path) -> dict:
    """Reconcile structure independently of tool name; hooks never claim validation."""
    from structure_tracker import scan_project
    root = find_root(cwd.resolve())
    if root is None:
        return {"governed": False}
    if (root / ".task/execution.config.tdsl").is_file() and (root / ".task/constitution.tdsl").is_file():
        from execution_runtime import preserve_constitution
        preserve_constitution(root)
    registry = scan_project(root)
    return {"governed": True, "generation": registry["generation"],
            "structural_issues": len(registry["issues"]),
            "details": ".agent-cache/tracking"}


# ── § 2 — ENTRY — Report compact mechanical feedback without blocking a harness ──

def main() -> int:
    """Run reconciliation when explicitly invoked by the operator."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = post_write(args.cwd)
        if result["governed"]:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"reconciliation_required": True, "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
