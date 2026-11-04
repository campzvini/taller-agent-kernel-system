# ────────────────────────────────────────────
# TASK 2.2.0 — test_contract_check.py
# § - Verify deterministic closed TDSL contract validation · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contract_check import check_contract
from runtime_journal import schema_revision

# ── § 1 — FIXTURES — Construct minimal registered configuration and task records ──
class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def header(self, dialect: str) -> str:
        return f"tdsl: {dialect}\nschema_revision: {schema_revision(dialect)}\nid: @test/fixture\nversion: 1\nstatus: proposed\npurpose: deterministic contract fixture\n"

    def config(self) -> str:
        return self.header("project_execution@1") + "execution_mode: interactive\nmax_active_subagents: 1\nseparate_test_author: true\nautonomous_authorized: false\nscaffold_required: true\n"

    def tasks(self) -> str:
        return self.header("tasks@2") + """spec_ref: @spec/sample
plan_ref: @plan/sample
tasks:
  task T001:
    action ln: |
      Implement the declared target.
    difficulty: medium
    requirement_refs: [@spec/sample#requirement/R001]
    plan_refs: [@plan/sample#component/C001]
    file_refs: [src/main.py]
    target_refs: [@file/F001#section/S001]
    write_scope: [src/main.py]
    validation_refs: [@plan/sample#validation/V001]
    depends_on: []
execution_order: [@tasks/sample#task/T001]
validation:
  completion_rule: all_required_validation_pass
  required_refs: [@plan/sample#validation/V001]
completion:
  evidence_required: true
  authority_ref: @project/constitution
"""

    def check(self, source: str) -> list[tuple[str, str]]:
        path = self.root / "record.tdsl"
        path.write_text(source, encoding="utf-8", newline="\n")
        return check_contract(path)

# ── § 2 — FIELDS — Reject missing unknown mistyped and unpinned configuration ──
    def test_valid_new_config(self) -> None:
        self.assertEqual([], self.check(self.config()))

    def test_invalid_enum(self) -> None:
        findings = self.check(self.config().replace("interactive", "unbounded"))
        self.assertTrue(any("invalid enum" in message for _, message in findings))

    def test_missing_required_field(self) -> None:
        findings = self.check(self.config().replace("separate_test_author: true\n", ""))
        self.assertTrue(any("missing required field separate_test_author" in message for _, message in findings))

    def test_unknown_field(self) -> None:
        findings = self.check(self.config() + "invented: true\n")
        self.assertTrue(any("unknown field" in message for _, message in findings))

    def test_pin_mismatch(self) -> None:
        findings = self.check(self.config().replace(schema_revision("project_execution@1"), "sha256:" + "0" * 64))
        self.assertTrue(any("exact registered pin" in message for _, message in findings))

    def test_boolean_and_positive_integer(self) -> None:
        findings = self.check(self.config().replace("max_active_subagents: 1", "max_active_subagents: 0").replace("separate_test_author: true", "separate_test_author: yes"))
        self.assertTrue(any("positive_integer" in message for _, message in findings))
        self.assertTrue(any("boolean" in message for _, message in findings))

    def test_duplicate_field_and_header_order(self) -> None:
        findings = self.check(self.config() + "execution_mode: interactive\n")
        self.assertTrue(any("duplicate field" in message for _, message in findings))
        source = self.config().replace("version: 1\nstatus: proposed", "status: proposed\nversion: 1")
        self.assertTrue(any("canonical six-field order" in message for _, message in self.check(source)))

# ── § 3 — STRUCTURE — Validate accumulated records objects and typed references ──
    def test_valid_v2_tasks_with_core_objects(self) -> None:
        self.assertEqual([], self.check(self.tasks()))

    def test_reference_namespace_and_part_kind(self) -> None:
        source = self.tasks().replace("@spec/sample#requirement/R001", "@plan/sample#component/C001")
        findings = self.check(source)
        self.assertTrue(any("namespace" in message for _, message in findings))
        self.assertTrue(any("part kind" in message for _, message in findings))

    def test_accumulated_duplicates_and_required_minimum(self) -> None:
        source = self.tasks()
        start = source.index("  task T001:")
        end = source.index("execution_order:")
        duplicated = source[:end] + source[start:end] + source[end:]
        self.assertTrue(any("duplicate item" in message for _, message in self.check(duplicated)))
        empty = source[:start].replace("tasks:\n", "tasks: []\n") + source[end:]
        self.assertTrue(any("at least 1" in message for _, message in self.check(empty)))

    def test_core_object_closed_fields(self) -> None:
        source = self.tasks().replace("  evidence_required: true", "  evidence_required: true\n  invented: true")
        self.assertTrue(any("unknown field" in message for _, message in self.check(source)))

    def test_ln_is_opaque_and_not_parsed_as_fields(self) -> None:
        source = self.tasks().replace("      Implement the declared target.", "      unknown_field: allowed inside prose\n      # opaque text\n      § 3 is prose")
        self.assertEqual([], self.check(source))

    def test_legacy_planning_fixtures_are_unchanged(self) -> None:
        self.assertEqual([], self.check("tdsl: tasks@1\nschema_revision: local:fixture\n"))


if __name__ == "__main__":
    unittest.main()
