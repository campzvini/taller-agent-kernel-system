# ────────────────────────────────────────────
# TASK 2.0 — post_write.py
# § - Reconcile structural indexes after writes without judging implementation · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
from pathlib import Path

from protocol_core import find_root

# § 1 — RECONCILIATION — Refresh derived navigation after intercepted writes


def post_write(cwd: Path) -> dict:
    """Reconcile structure independently of tool name; hooks never claim validation."""
    from structure_tracker import scan_project
    from diagram_check import scan_file
    root = find_root(cwd.resolve())
    if root is None:
        return {"governed": False}
    if (root / ".task/execution.config.tdsl").is_file() and (root / ".task/constitution.tdsl").is_file():
        from execution_runtime import preserve_constitution
        preserve_constitution(root)
    registry = scan_project(root)
    records = []
    for item in registry["elements"].values():
        if item["kind"] == "file" and item["state"] == "present":
            path = root / item["path"]
            record = scan_file(path)
            if record["status"] not in ("skip", "ok"):
                records.append(record)
    directory = root / ".agent-cache/tracking"
    (directory / "diagram.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    return {"governed": True, "generation": registry["generation"],
            "structural_issues": len(registry["issues"]), "diagram_issues": len(records),
            "details": ".agent-cache/tracking"}


# § 2 — ENTRY — Report compact mechanical feedback without blocking a harness

def main() -> int:
    """Allow adapters and manual callers to invoke the same reconciliation path."""
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
