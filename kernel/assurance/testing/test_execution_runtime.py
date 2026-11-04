# ────────────────────────────────────────────
# TASK 2.2.0 — test_execution_runtime.py
# § - Verify execution authority, dependency evidence and interrupted ownership · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from execution_runtime import (claim, configuration, eligible_tasks, latest_outcomes,
                               migrate, preserve_constitution, release, execution_status)
from runtime_journal import append_entry
from protocol_core import State, journal_outcomes
from sdd_gate import SDD
from protocol_core import build_parser, resolve_state

# ── § 1 — FIXTURE — Describe independent tasks and explicit project authority ──


class ExecutionTests(unittest.TestCase):
    """Exercise authority, ownership and recovery without running an agent harness."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write(".task/project.tdsl", "id: @project/test\nworkflow: sdd\nactive_feature: 001-one\nplanning_mode: gradual\nfeatures:\n  feature 001-one:\n    lifecycle: active\n")
        self.write(".task/constitution.tdsl", "tdsl: constitution@1\nversion: 1\nid: @constitution/test\n")
        for name in ("spec", "plan", "analysis"):
            self.write(f".task/features/001-one/{name}.tdsl", f"id: @{name}/001-one\n")
        self.tasks = "tasks:\n  task T1:\n    file_refs: [src/a.py]\n    depends_on: []\n  task T2:\n    file_refs: [src/b.py]\n    depends_on: []\n"
        self.write(".task/features/001-one/tasks.tdsl", self.tasks)

    def write(self, name, text):
        if name == ".task/execution.config.tdsl":
            from runtime_journal import schema_revision
            settings = {"execution_mode": "interactive", "max_active_subagents": "1",
                        "separate_test_author": "true", "autonomous_authorized": "false", "scaffold_required": "false"}
            settings.update(dict(line.split(": ", 1) for line in text.splitlines()))
            text = ("tdsl: project_execution@1\n" + f"schema_revision: {schema_revision('project_execution@1')}\n"
                    "id: @execution/project\nversion: 1\nstatus: proposed\npurpose: test explicit authority\n" +
                    "".join(f"{key}: {value}\n" for key, value in settings.items()))
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def finish(self, tid):
        append_entry(self.root, "execution", {"task_ref": f"@tasks/001-one#task/{tid}",
                     "outcome": "completed", "evidence_refs": ["@ev/test"]})

# ── § 2 — AUTHORITY — Preserve legacy operation and refuse implicit autonomy ──

    def test_legacy_never_gains_autonomy(self):
        self.assertTrue(configuration(self.root)["legacy"])
        migrate(self.root)
        config = configuration(self.root)
        self.assertEqual(config["execution_mode"], "interactive")
        self.assertFalse(config["autonomous_authorized"])
        self.assertIn("Architecture.md missing", execution_status(self.root)["blockers"])

    def test_unauthorized_autonomy_blocks_claim(self):
        self.write(".task/execution.config.tdsl", "execution_mode: autonomous\nautonomous_authorized: false\n")
        with self.assertRaisesRegex(ValueError, "authorization"):
            claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "worker")

    def test_constitution_version_is_immutable(self):
        preserve_constitution(self.root)
        self.write(".task/constitution.tdsl", "version: 1\nid: @constitution/test\nchanged: true\n")
        with self.assertRaisesRegex(ValueError, "immutable"):
            preserve_constitution(self.root)
        self.write(".task/constitution.tdsl", "version: 2\nid: @constitution/test\nchanged: true\n")
        preserve_constitution(self.root)
        self.assertTrue((self.root / ".task/history/constitution/1.tdsl").exists())

# ── § 3 — OWNERSHIP — Respect concurrency, path boundaries and interrupted units ──

    def test_default_concurrency_is_one(self):
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        with self.assertRaisesRegex(ValueError, "max_active"):
            claim(self.root, "@unit/U2", ["@tasks/001-one#task/T2"], "b")

    def test_parallel_directory_overlap_is_refused(self):
        self.write(".task/execution.config.tdsl", "max_active_subagents: 2\n")
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("src/a.py", "src"))
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        with self.assertRaisesRegex(ValueError, "ownership"):
            claim(self.root, "@unit/U2", ["@tasks/001-one#task/T2"], "b")

    def test_disjoint_parallel_units_are_allowed(self):
        self.write(".task/execution.config.tdsl", "max_active_subagents: 2\n")
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        claim(self.root, "@unit/U2", ["@tasks/001-one#task/T2"], "b")

    def test_path_escape_is_refused(self):
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("src/a.py", "../escape.py"))
        with self.assertRaisesRegex(ValueError, "escapes"):
            eligible_tasks(self.root)

    def test_release_requires_completion_or_explicit_interruption(self):
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            release(self.root, "@unit/U1", "a")
        release(self.root, "@unit/U1", "a", interrupted=True)
        self.assertEqual(latest_outcomes(self.root)["@tasks/001-one#task/T1"]["outcome"], "interrupted")
        claim(self.root, "@unit/U2", ["@tasks/001-one#task/T1"], "b")

    def test_release_checks_owner(self):
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        with self.assertRaisesRegex(ValueError, "owned"):
            release(self.root, "@unit/U1", "b", interrupted=True)

# ── § 4 — HISTORY — Reduce attempts and obey dependency evidence ──

    def test_completed_task_reopened_by_new_event(self):
        self.finish("T1")
        append_entry(self.root, "execution", {"task_ref": "@tasks/001-one#task/T1", "outcome": "started", "evidence_refs": []})
        done, blocked = journal_outcomes(State(self.root, SDD))
        self.assertNotIn("T1", done)
        self.assertIn("T1", blocked)

    def test_legacy_retry_uses_latest_outcome(self):
        self.write(".task/features/001-one/execution.journal.tdsl", "journal:\n  entry T1:\n    outcome: completed\n  entry T1:\n    outcome: failed\n")
        done, blocked = journal_outcomes(State(self.root, SDD))
        self.assertNotIn("T1", done)
        self.assertIn("T1", blocked)

    def test_dependency_waits_for_completed_journal(self):
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("task T2:\n    file_refs: [src/b.py]\n    depends_on: []", "task T2:\n    file_refs: [src/b.py]\n    depends_on: [@tasks/001-one#task/T1]"))
        self.assertEqual(len(eligible_tasks(self.root)), 1)
        self.finish("T1")
        self.assertEqual(eligible_tasks(self.root)[0]["task_ref"], "@tasks/001-one#task/T2")

    def test_gradual_claim_cannot_escape_cursor_feature(self):
        self.write(".task/features/002-two/tasks.tdsl", self.tasks)
        self.assertTrue(all("001-one" in task["task_ref"] for task in eligible_tasks(self.root)))
        with self.assertRaisesRegex(ValueError, "ineligible"):
            claim(self.root, "@unit/U1", ["@tasks/002-two#task/T1"], "a")

    def test_claim_detects_constitution_mutation(self):
        preserve_constitution(self.root)
        self.write(".task/constitution.tdsl", "version: 1\nid: @constitution/test\nchanged: true\n")
        with self.assertRaisesRegex(ValueError, "immutable"):
            claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")

    def test_conditional_task_needs_explicit_judgment(self):
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("task T1:\n", "task T1:\n    condition: only_when_migration_needed\n"))
        with self.assertRaisesRegex(ValueError, "applicability"):
            claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a", ["@tasks/001-one#task/T1"])

    def test_unit_can_cover_dependency_ordered_task_group(self):
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("task T2:\n    file_refs: [src/b.py]\n    depends_on: []", "task T2:\n    file_refs: [src/b.py]\n    depends_on: [@tasks/001-one#task/T1]"))
        unit = claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1", "@tasks/001-one#task/T2"], "a")
        self.assertEqual(len(unit["task_refs"]), 2)

    def test_cycle_refuses_unit_group(self):
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("task T1:\n    file_refs: [src/a.py]\n    depends_on: []", "task T1:\n    file_refs: [src/a.py]\n    depends_on: [@tasks/001-one#task/T2]").replace("task T2:\n    file_refs: [src/b.py]\n    depends_on: []", "task T2:\n    file_refs: [src/b.py]\n    depends_on: [@tasks/001-one#task/T1]"))
        with self.assertRaisesRegex(ValueError, "cycle"):
            claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1", "@tasks/001-one#task/T2"], "a")

    def test_targeted_gate_does_not_mutate_shared_cursor(self):
        self.write(".task/features/002-two/spec.tdsl", "id: @spec/002-two\n")
        anchor = (self.root / ".task/project.tdsl").read_bytes()
        args = build_parser(SDD, "test").parse_args(["--cwd", str(self.root), "--feature", "002-two", "state"])
        state = resolve_state(args, SDD)
        self.assertEqual(state.feature, "002-two")
        self.assertEqual((self.root / ".task/project.tdsl").read_bytes(), anchor)

    def test_interrupted_release_keeps_started_attempt(self):
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        before = latest_outcomes(self.root)["@tasks/001-one#task/T1"]["attempt"]
        release(self.root, "@unit/U1", "a", interrupted=True)
        after = latest_outcomes(self.root)["@tasks/001-one#task/T1"]["attempt"]
        self.assertEqual(before, after)

    def test_deferred_manifest_does_not_block_its_declared_owner(self):
        from structure_scaffold import scaffold_project
        anchor = self.root / ".task/project.tdsl"
        anchor.write_text(anchor.read_text().replace("gradual", "integral"), encoding="utf-8")
        self.write(".task/Architecture.md", "package.json\n")
        self.write(".task/features/001-one/tasks.tdsl", self.tasks.replace("src/a.py", "package.json"))
        migrate(self.root)
        result = scaffold_project(self.root, apply=True)
        self.assertFalse(result["complete"])
        self.assertFalse((self.root / "package.json").exists())
        self.assertEqual(execution_status(self.root)["blockers"], [])
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")

    def test_status_does_not_reconcile_deferred_structure(self):
        from structure_scaffold import scaffold_project
        anchor = self.root / ".task/project.tdsl"
        anchor.write_text(anchor.read_text().replace("gradual", "integral"), encoding="utf-8")
        self.write(".task/Architecture.md", "package.json\n")
        migrate(self.root)
        scaffold_project(self.root, apply=True)
        before = (self.root / ".task/tracking/registry.json").read_bytes()
        self.assertEqual(execution_status(self.root)["blockers"], [])
        self.assertEqual((self.root / ".task/tracking/registry.json").read_bytes(), before)

    def test_stale_scaffold_inventory_does_not_block_existing_work(self):
        anchor = self.root / ".task/project.tdsl"
        anchor.write_text(anchor.read_text().replace("gradual", "integral"), encoding="utf-8")
        self.write(".task/Architecture.md", "src/\n  a.py\n")
        self.write("src/a.py", "value = 1\n")
        migrate(self.root)
        self.write(".task/runtime/scaffold-preparation.json", '{"inventory": []}\n')
        before = (self.root / ".task/tracking/registry.json").read_bytes()
        claim(self.root, "@unit/existing", ["@tasks/001-one#task/T1"], "a")
        self.assertEqual((self.root / ".task/tracking/registry.json").read_bytes(), before)
        self.assertEqual((self.root / "src/a.py").read_text(), "value = 1\n")

    def test_unit_identity_is_not_reused_after_interruption(self):
        claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "a")
        release(self.root, "@unit/U1", "a", interrupted=True)
        with self.assertRaisesRegex(ValueError, "already used"):
            claim(self.root, "@unit/U1", ["@tasks/001-one#task/T1"], "b")

    def test_integral_recovery_routes_ready_work_without_shared_cursor(self):
        anchor = self.root / ".task/project.tdsl"
        anchor.write_text(anchor.read_text().replace("gradual", "integral").replace("active_feature: 001-one", "active_feature: unknown"), encoding="utf-8")
        self.write(".task/Architecture.md", "src/\n")
        migrate(self.root)
        state = State(self.root, SDD)
        self.assertEqual(state.next_phase(), "execute")
        self.assertEqual(state.next_feature, "001-one")


if __name__ == "__main__":
    unittest.main()
