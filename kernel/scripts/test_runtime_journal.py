# ────────────────────────────────────────────
# TASK 2.0 — test_runtime_journal.py
# § - Verify immutable operational history and evidence-derived projections · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────
from __future__ import annotations

import tempfile
import hashlib
import json
import unittest
from pathlib import Path
from datetime import datetime

import runtime_journal as journal

# ── § 1 — FIXTURE — Isolate operational history in disposable projects ──
class JournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.task = "@tasks/sample#task/T001"

    def execution(self, outcome: str, **extra: object) -> dict:
        return {"task_ref": self.task, "outcome": outcome, "evidence_refs": ["@ev/V001"] if outcome == "completed" else [], **extra}

    def decision(self, **extra: object) -> dict:
        return {"task_ref": self.task, "question": "Which representation?", "choice": "Typed references", "rationale": "Preserve identity across movement", "evidence_refs": [], **extra}

# ── § 2 — HISTORY — Preserve attempts and explicit decision precedence ──
    def test_append_preserves_prefix_and_retry_identity(self) -> None:
        first = journal.append_entry(self.root, "execution", self.execution("failed", attempt=1))
        path = journal.journal_path(self.root, "execution")
        prefix = path.read_bytes()
        second = journal.append_entry(self.root, "execution", self.execution("completed", attempt=2))
        self.assertTrue(path.read_bytes().startswith(prefix))
        self.assertNotEqual(first["event_id"], second["event_id"])
        records = journal.read_entries(self.root, "execution")
        self.assertEqual([1, 2], [e["attempt"] for e in records])
        self.assertIsInstance(records[-1]["attempt"], int)
        self.assertEqual("completed", journal.execution_state(self.root)[self.task]["outcome"])

    def test_started_and_completion_share_attempt(self) -> None:
        start = journal.append_entry(self.root, "execution", self.execution("started"))
        complete = journal.append_entry(self.root, "execution", self.execution("completed"))
        self.assertEqual(start["attempt"], complete["attempt"])

    def test_reopen_changes_derived_checklist_without_editing_plan(self) -> None:
        journal.append_entry(self.root, "execution", self.execution("completed"))
        self.assertIn("[x]", journal.render_checklist(self.root, [self.task]))
        journal.append_entry(self.root, "execution", self.execution("started"))
        self.assertIn("[ ]", journal.render_checklist(self.root, [self.task]))
        self.assertFalse((self.root / ".task/features/sample/tasks.tdsl").exists())

    def test_partial_supersession_has_explicit_affected_scope(self) -> None:
        original = journal.append_entry(self.root, "decision", self.decision())
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "decision", self.decision(supersedes_ref=original["decision_id"], supersession_scope="partial"))
        replacement = journal.append_entry(self.root, "decision", self.decision(supersedes_ref=original["decision_id"], supersession_scope="partial", affected_refs=["@file/F001#section/S001"]))
        self.assertEqual(original["decision_id"], replacement["supersedes_ref"])
        self.assertEqual(2, len(journal.read_entries(self.root, "decision")))

    def test_unknown_superseded_decision_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "decision", self.decision(supersedes_ref="@decision/D999", supersession_scope="full"))

# ── § 3 — INTEGRITY — Refuse invalid evidence materiality and competing writers ──
    def test_reference_and_evidence_requirements(self) -> None:
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "execution", self.execution("started", task_ref="path/to/task"))
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "execution", self.execution("completed", evidence_refs=[]))
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "execution", self.execution("completed", evidence_refs=["broken"]))

    def test_timestamp_is_generated_as_utc(self) -> None:
        entry = journal.append_entry(self.root, "execution", self.execution("started"))
        self.assertTrue(entry["timestamp"].endswith("Z"))
        self.assertEqual(0, datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).utcoffset().total_seconds())
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "execution", self.execution("started", timestamp="yesterday"))

    def test_trivial_failure_not_recorded(self) -> None:
        failure = {"task_ref": self.task, "cause": "Contract mismatch", "effect": "Cannot resume", "resolution": "Pending", "rationale": "Material runtime effect", "evidence_refs": [], "resolution_state": "open", "materiality": "trivial"}
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "failure", failure)
        failure["materiality"] = "contract"
        journal.append_entry(self.root, "failure", failure)
        self.assertEqual(1, len(journal.read_entries(self.root, "failure")))

    def test_existing_writer_lock_is_not_stolen(self) -> None:
        path = journal.journal_path(self.root, "execution")
        path.parent.mkdir(parents=True)
        lock = path.with_suffix(path.suffix + ".lock")
        lock.write_text("another writer", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            journal.append_entry(self.root, "execution", self.execution("started"))
        self.assertTrue(lock.exists())
        self.assertFalse(path.exists())

    def test_incomplete_history_is_not_silently_repaired(self) -> None:
        journal.append_entry(self.root, "execution", self.execution("started"))
        path = journal.journal_path(self.root, "execution")
        path.write_bytes(path.read_bytes().rstrip(b"\n"))
        with self.assertRaises(ValueError):
            journal.read_entries(self.root, "execution")

    def test_duplicate_fields_in_persisted_event_are_rejected(self) -> None:
        journal.append_entry(self.root, "execution", self.execution("started"))
        path = journal.journal_path(self.root, "execution")
        source = path.read_text(encoding="utf-8")
        path.write_text(source.replace("    outcome: started", "    outcome: started\n    outcome: failed"), encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(ValueError, "duplicate field"):
            journal.read_entries(self.root, "execution")

    def test_fields_from_other_journal_kinds_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "execution", self.execution("started", affected_refs=["@file/F001"]))
        with self.assertRaises(ValueError):
            journal.append_entry(self.root, "execution", self.execution("started", supersedes_ref="@event/E001"))

    def test_registry_pins_match_exact_bundled_bytes(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        registry = repository / "kernel/grammar/schemas/registry.json"
        for entry in json.loads(registry.read_text(encoding="utf-8"))["entries"]:
            with self.subTest(dialect=entry["dialect"]):
                path = repository / entry["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(entry["schema_revision"], "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
