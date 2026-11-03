# ────────────────────────────────────────────
# TASK 2.0 — test_delivery_integration.py
# § - Verify installed CLI composition and harness reconciliation · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# ── § 1 — HARNESS — Exercise the installed layout rather than repository-only imports ──

SOURCE = Path(__file__).resolve().parents[1]
REPOSITORY = SOURCE.parent


class InstalledIntegrationTests(unittest.TestCase):
    """Verify the distributed CLI and both harness adapters against real files."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.install = self.base / "kernel"
        shutil.copytree(SOURCE, self.install, ignore=shutil.ignore_patterns("__pycache__"))
        self.project = self.base / "project"
        self.project.mkdir()
        for harness in ("codex", "claude"):
            shutil.copyfile(REPOSITORY / f"adapters/{harness}/{harness}_hook.py",
                            self.install / f"scripts/{harness}_hook.py")

    def command(self, script, *args, event=None):
        return subprocess.run([sys.executable, str(self.install / "scripts" / script), *args],
                              cwd=self.project, input=json.dumps(event) if event else None,
                              capture_output=True, text=True, encoding="utf-8")

    def initialize(self):
        result = self.command("sdd_gate.py", "--cwd", str(self.project), "init", "--mode", "integral")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (self.project / ".task/constitution.tdsl").write_text("tdsl: constitution@1\nversion: 1\nid: @project/constitution\n", encoding="utf-8", newline="\n")
        (self.project / ".task/Architecture.md").write_text("src/\n  engine.py\n", encoding="utf-8", newline="\n")

# ── § 2 — DELIVERY — Prove initialization, scaffold and post-write reconciliation compose ──

    def test_new_project_scaffolds_and_queries_planned_identity(self):
        self.initialize()
        result = self.command("sdd_gate.py", "--cwd", str(self.project), "state", "--json")
        self.assertEqual(json.loads(result.stdout)["next_phase"], "feature")
        result = self.command("structure_tracker.py", "--root", str(self.project), "scan")
        self.assertEqual(result.returncode, 0, result.stderr)
        registry = json.loads((self.project / ".task/tracking/registry.json").read_text())
        ref = next(ref for ref, item in registry["elements"].items() if item["path"] == "src/engine.py")
        self.assertEqual(registry["elements"][ref]["state"], "planned")
        result = self.command("sdd_gate.py", "--cwd", str(self.project), "execute0", "--apply")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(ref, (self.project / "src/engine.py").read_text(encoding="utf-8"))
        result = self.command("structure_tracker.py", "--root", str(self.project), "query", ref)
        self.assertTrue(json.loads(result.stdout)["exists"])

    def test_both_installed_hooks_reconcile_after_external_write(self):
        self.initialize()
        (self.project / "photo.bin").write_bytes(bytes(range(256)))
        for harness in ("codex", "claude"):
            result = self.command(harness + "_hook.py", event={"hook_event_name": "PostToolUse",
                                  "cwd": str(self.project), "tool_name": "apply_patch"})
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PostToolUse")
            registry = json.loads((self.project / ".task/tracking/registry.json").read_text())
            self.assertTrue(any(item["path"] == "photo.bin" for item in registry["elements"].values()))

    def test_architecture_write_gate_works_without_active_feature(self):
        self.initialize()
        for harness in ("codex", "claude"):
            tool_input = {"command": "*** Begin Patch\n*** Update File: .task/Architecture.md\n*** End Patch"} if harness == "codex" else {"file_path": str(self.project / ".task/Architecture.md")}
            result = self.command(harness + "_hook.py", event={"hook_event_name": "PreToolUse", "session_id": harness,
                                  "cwd": str(self.project), "tool_name": "apply_patch" if harness == "codex" else "Write",
                                  "tool_input": tool_input})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if result.stdout.strip():
                self.assertNotEqual(json.loads(result.stdout).get("hookSpecificOutput", {}).get("permissionDecision"), "deny")


if __name__ == "__main__":
    unittest.main()
