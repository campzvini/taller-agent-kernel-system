# ────────────────────────────────────────────
# TASK 2.2.0 — test_loops_delivery.py
# § - Verify delivery scope and compact context through real Git state · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — DELIVERY — Observe code changes without staging unrelated work ──

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from commit_context import collect_delivery_state

class DeliveryScopeTests(unittest.TestCase):
    """Exercise new, modified, removed and unrelated files in independent repositories."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.root / ".gitignore").write_text(".agent-cache/\n")
        (self.root / "owned.py").write_text("value = 1\n")
        (self.root / "other.py").write_text("value = 2\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def git(self, *args):
        """Execute a bounded Git operation in this test's private repository."""
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def test_clean_delivery_has_no_candidate_or_empty_commit(self):
        head = self.git("rev-parse", "HEAD")
        state = collect_delivery_state(self.root)
        self.assertEqual(state["code_candidates"], [])
        self.assertEqual(self.git("rev-parse", "HEAD"), head)

    def test_real_additions_deletions_and_unrelated_staged_work_are_separate(self):
        (self.root / "owned.py").unlink()
        (self.root / "new file.py").write_text("value = 3\n")
        (self.root / "other.py").write_text("value = 4\n")
        self.git("add", "other.py")
        staged = self.git("diff", "--cached")
        state = collect_delivery_state(self.root, ["owned.py", "new file.py"])
        self.assertCountEqual(state["code_candidates"], ["owned.py", "new file.py", "other.py"])
        self.assertCountEqual(state["selected_paths"], ["owned.py", "new file.py"])
        self.assertEqual(state["excluded_paths"], ["other.py"])
        self.assertEqual(state["authority"], "not_inferred")
        self.assertEqual(self.git("diff", "--cached"), staged)

    def test_document_only_change_does_not_require_code_commit(self):
        (self.root / "README.md").write_text("Notes\n")
        self.assertEqual(collect_delivery_state(self.root)["code_candidates"], [])

    def test_rename_preserves_original_path_without_quoted_status_parsing(self):
        self.git("mv", "owned.py", 'renamed café file.py')
        changes = collect_delivery_state(self.root)["changes"]
        self.assertEqual(changes[0]["original_path"], "owned.py")
        self.assertEqual(changes[0]["path"], 'renamed café file.py')

    def test_commit_context_and_handoff_leave_git_state_unchanged(self):
        scripts = Path(__file__).resolve().parent
        (self.root / "owned.py").write_text("value = 5\n")
        before = self.git("status", "--porcelain=v1")
        for helper in ("commit_context.py", "handoff_snapshot.py"):
            result = subprocess.run([sys.executable, str(scripts / helper)], cwd=self.root,
                                    text=True, capture_output=True, encoding="utf-8")
            self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            filename = "commit-context.json" if helper == "commit_context.py" else "handoff-snapshot.json"
            self.assertTrue((self.root / ".agent-cache" / filename).is_file(), result.stdout + result.stderr)
        commit = json.loads((self.root / ".agent-cache/commit-context.json").read_text())
        self.assertEqual(commit["delivery"]["code_candidates"], ["owned.py"])
        snapshot = json.loads((self.root / ".agent-cache/handoff-snapshot.json").read_text())
        self.assertEqual(snapshot["git_delivery"]["code_candidates"], ["owned.py"])
        self.assertEqual(snapshot["git_delivery"]["head"], self.git("rev-parse", "HEAD").strip())
        self.assertEqual(self.git("diff", "--cached"), "")
        self.assertIn("owned.py", before)
        self.assertEqual(self.git("status", "--porcelain=v1"), before)

if __name__ == "__main__":
    unittest.main()
