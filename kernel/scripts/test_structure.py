# ────────────────────────────────────────────
# TASK 2.0 — test_structure.py
# § - Verify identity reconciliation and safe structural scaffolding · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from structure_scaffold import parse_architecture, scaffold_project
from structure_tracker import load_registry, move_element, query_registry, scan_project

# ── § 1 — FIXTURES — Isolate every structural operation in a temporary project ──

class StructureTests(unittest.TestCase):
    """Verify approved structural contracts without depending on the repository."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')
        return path

    def architecture(self, text: str) -> Path:
        return self.write('.task/Architecture.md', text)

    def file_reference(self, registry: dict, path: str) -> str:
        return next(reference for reference, item in registry['elements'].items()
                    if item['path'] == path and item['kind'] == 'file' and item['state'] == 'present')

    # ── § 1.1 — Identity — Preserve explicit references and report uncertain movement ──

    def test_inventory_preserves_ids_and_covers_binary_and_directory(self) -> None:
        self.write('assets/example.dat', 'text')
        (self.root / 'assets/example.dat').write_bytes(b'\x00\xff\x01')
        first = scan_project(self.root)
        second = scan_project(self.root)
        self.assertEqual(first['elements'], second['elements'])
        kinds = {item['kind'] for item in second['elements'].values()}
        self.assertEqual({'dir', 'file'}, kinds)
        self.assertFalse(any('.task/tracking/' in item['path'] for item in second['elements'].values()))

    def test_promotion_and_explicit_movement_keep_identity(self) -> None:
        source = self.write('old.py', '# ◇ 1 — DOMAIN — Reserved destination\n# anchor_ref: @file/Fexplicit#section/Sone\n')
        scan_project(self.root)
        source.write_text(source.read_text(encoding='utf-8').replace('◇', '§'), encoding='utf-8')
        source.rename(self.root / 'new.py')
        registry = scan_project(self.root)
        self.assertEqual('new.py', registry['elements']['@file/Fexplicit']['path'])
        section = registry['elements']['@file/Fexplicit#section/Sone']
        self.assertEqual('§', section['marker'])
        self.assertEqual(registry['generation'], section['promotion_generation'])

    def test_external_move_can_be_declared_before_rescan(self) -> None:
        source = self.write('old.bin', 'opaque')
        registry = scan_project(self.root)
        reference = self.file_reference(registry, 'old.bin')
        source.rename(self.root / 'new.bin')
        moved = move_element(self.root, reference, 'new.bin')
        self.assertEqual('new.bin', moved['elements'][reference]['path'])

    def test_unmarked_move_is_not_guessed(self) -> None:
        source = self.write('old.bin', 'identical bytes are not identity')
        registry = scan_project(self.root)
        reference = self.file_reference(registry, 'old.bin')
        source.rename(self.root / 'new.bin')
        updated = scan_project(self.root)
        self.assertEqual('removed', updated['elements'][reference]['state'])
        self.assertNotEqual(reference, self.file_reference(updated, 'new.bin'))
        self.assertIn('unresolved_identity', [issue['code'] for issue in updated['issues']])

    def test_copy_does_not_inherit_duplicate_explicit_identity(self) -> None:
        content = '# § 1 — DOMAIN — Own responsibility\n# anchor_ref: @file/Fsame#section/Ssame\n'
        self.write('first.py', content)
        self.write('second.py', content)
        registry = scan_project(self.root)
        codes = [issue['code'] for issue in registry['issues']]
        self.assertIn('duplicate_file_identity', codes)
        self.assertIn('duplicate_identity', codes)

    def test_document_part_queries_return_bounded_ranges(self) -> None:
        self.write('spec.tdsl', 'id: @spec/demo\nrequirements:\n  requirement R1:\n    text: example\n  requirement R2:\n    text: other\n')
        scan_project(self.root)
        result = query_registry(self.root, '@spec/demo#requirement/R1')
        self.assertEqual(3, result['element']['line'])
        self.assertEqual(2, result['element']['limit'])

    def test_runtime_event_aliases_and_dangling_references(self) -> None:
        self.write('execution.tdsl', 'id: @journal/execution\njournal:\n  entry E1:\n    event_id: @event/E1\n    task_ref: @tasks/absent#task/T1\n')
        registry = scan_project(self.root)
        self.assertEqual(3, query_registry(self.root, '@event/E1')['element']['line'])
        self.assertTrue(any(issue.get('target') == '@tasks/absent#task/T1' for issue in registry['issues']))

    # ── § 1.2 — Scaffold — Create only safe missing destinations after complete inspection ──

    def test_scaffold_is_dry_run_then_idempotent_and_records_completion(self) -> None:
        self.architecture('```text\n.\n├── src/\n│   └── engine.py\n└── notes.md\n```\n')
        planned = scaffold_project(self.root)
        self.assertFalse(planned['applied'])
        self.assertFalse((self.root / 'src').exists())
        applied = scaffold_project(self.root, apply=True)
        self.assertTrue(applied['complete'])
        original = (self.root / 'src/engine.py').read_bytes()
        self.assertIn('◇'.encode(), original)
        self.assertIn(b'anchor_ref:', original)
        repeated = scaffold_project(self.root, apply=True)
        self.assertTrue(all(action['action'] == 'reuse' for action in repeated['actions']))
        self.assertEqual(original, (self.root / 'src/engine.py').read_bytes())
        marker = json.loads((self.root / '.task/runtime/scaffold.json').read_text(encoding='utf-8'))
        self.assertEqual(repeated['inventory'], marker['inventory'])

    def test_existing_source_bytes_are_never_overwritten(self) -> None:
        source = self.write('engine.py', 'print("existing implementation")\n')
        self.architecture('engine.py\n')
        before = source.read_bytes()
        scaffold_project(self.root, apply=True)
        self.assertEqual(before, source.read_bytes())

    def test_unsupported_binary_and_manifest_remain_pending(self) -> None:
        self.architecture('package.json\nimage.png\n')
        result = scaffold_project(self.root, apply=True)
        self.assertTrue(all(action['action'] == 'pending' for action in result['actions']))
        self.assertFalse(result['complete'])
        self.assertFalse((self.root / 'package.json').exists())
        self.assertFalse((self.root / '.task/runtime/scaffold.json').exists())

    def test_conflict_is_found_before_any_creation(self) -> None:
        self.write('blocked', 'not a directory')
        self.architecture('new.py\nblocked/\n  child.py\n')
        with self.assertRaises(ValueError):
            scaffold_project(self.root, apply=True)
        self.assertFalse((self.root / 'new.py').exists())

    def test_traversal_and_non_tree_prose_are_rejected(self) -> None:
        for content in ('../escape.py\n', '# Architecture\n', 'src/ # description\n'):
            with self.subTest(content=content):
                architecture = self.architecture(content)
                with self.assertRaises(ValueError):
                    parse_architecture(architecture)

    def test_symlink_parent_is_never_written_through(self) -> None:
        target = self.root / 'actual'
        target.mkdir()
        try:
            (self.root / 'linked').symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('platform does not permit symlink creation')
        self.architecture('linked/\n  engine.py\n')
        with self.assertRaises(ValueError):
            scaffold_project(self.root, apply=True)
        self.assertFalse((target / 'engine.py').exists())

    # ── § 1.3 — Intended state — Reconcile planned identities with observed destinations ──

    def test_planned_identity_survives_scan_scaffold_and_promotion(self) -> None:
        self.architecture('src/\n  engine.py\n')
        initial = scan_project(self.root)
        planned = query_registry(self.root, 'src/engine.py')
        reference = planned['reference']
        self.assertEqual('planned', planned['element']['state'])
        self.assertFalse(planned['exists'])
        scan_project(self.root)
        self.assertEqual(reference, query_registry(self.root, 'src/engine.py')['reference'])
        scaffold_project(self.root, apply=True)
        source = self.root / 'src/engine.py'
        self.assertIn(f'anchor_ref: {reference}#section/S0001', source.read_text(encoding='utf-8'))
        materialized = query_registry(self.root, reference)
        self.assertTrue(materialized['exists'])
        source.write_text(source.read_text(encoding='utf-8').replace('◇', '§'), encoding='utf-8')
        updated = scan_project(self.root)
        self.assertEqual('§', updated['elements'][reference + '#section/S0001']['marker'])
        self.assertEqual(reference, query_registry(self.root, 'src/engine.py')['reference'])

    def test_architecture_and_feature_aliases_are_externally_addressable(self) -> None:
        self.architecture('src/\n')
        self.write('.task/project.tdsl', 'id: @project/demo\nfeatures:\n  feature 001-engine:\n    lifecycle: active\n')
        scan_project(self.root)
        self.assertEqual('.task/Architecture.md', query_registry(self.root, '@arch/project')['element']['path'])
        feature = query_registry(self.root, '@feature/001-engine')
        self.assertEqual('.task/project.tdsl', feature['element']['path'])
        self.assertEqual(3, feature['element']['line'])

    def test_removed_document_keeps_historical_alias(self) -> None:
        source = self.write('spec.tdsl', 'id: @spec/deleted\nrequirements:\n  requirement R1:\n    text: preserved identity\n')
        scan_project(self.root)
        source.unlink()
        scan_project(self.root)
        result = query_registry(self.root, '@spec/deleted#requirement/R1')
        self.assertEqual('removed', result['element']['state'])
        self.assertFalse(result['exists'])

    def test_invalid_architecture_reports_issue_without_unsafe_creation(self) -> None:
        self.architecture('../outside.py\n')
        result = scan_project(self.root)
        self.assertIn('invalid_architecture', [issue['code'] for issue in result['issues']])
        self.assertFalse(any(item['state'] == 'planned' for item in result['elements'].values()))

    def test_legacy_renumbering_requires_explicit_identity_reconciliation(self) -> None:
        source = self.write('legacy.py', '# § 1 — READ — Read input\nvalue = 1\n# § 2 — WRITE — Write output\nvalue = 2\n')
        initial = scan_project(self.root)
        reference = self.file_reference(initial, 'legacy.py')
        source.write_text('# § 1 — WRITE — Write output\nvalue = 2\n# § 2 — READ — Read input\nvalue = 1\n', encoding='utf-8')
        updated = scan_project(self.root)
        self.assertIn('unresolved_legacy_identity', [issue['code'] for issue in updated['issues']])
        self.assertEqual('unresolved', updated['elements'][reference + '#section/legacy-1']['state'])
        self.assertFalse(query_registry(self.root, reference + '#section/legacy-1')['exists'])
        repeated = scan_project(self.root)
        self.assertIn('unresolved_legacy_identity', [issue['code'] for issue in repeated['issues']])
        source.write_text('# § 1 — WRITE — Write output\n# anchor_ref: ' + reference + '#section/write\nvalue = 2\n# § 2 — READ — Read input\n# anchor_ref: ' + reference + '#section/read\nvalue = 1\n', encoding='utf-8')
        reconciled = scan_project(self.root)
        self.assertNotIn('unresolved_legacy_identity', [issue['code'] for issue in reconciled['issues']])
        self.assertEqual('present', reconciled['elements'][reference + '#section/read']['state'])

    def test_constitution_snapshots_have_versioned_aliases_without_duplicates(self) -> None:
        first = 'id: @project/constitution\nversion: 1\nprinciples:\n  principle P1:\n    rule: original\n'
        active = self.write('.task/constitution.tdsl', first)
        self.write('.task/history/constitution/1.tdsl', first)
        registry = scan_project(self.root)
        self.assertNotIn('duplicate_document_identity', [issue['code'] for issue in registry['issues']])
        self.assertEqual('.task/constitution.tdsl', query_registry(self.root, '@project/constitution')['element']['path'])

        prior = query_registry(self.root, '@project/constitution~v1#principle/P1')
        self.assertEqual('.task/history/constitution/1.tdsl', prior['element']['path'])
        self.assertEqual(4, prior['element']['line'])
        second = first.replace('version: 1', 'version: 2').replace('original', 'revised')
        active.write_text(second, encoding='utf-8')
        self.write('.task/history/constitution/2.tdsl', second)
        updated = scan_project(self.root)
        self.assertNotIn('duplicate_document_identity', [issue['code'] for issue in updated['issues']])
        self.assertEqual('.task/history/constitution/1.tdsl', query_registry(self.root, '@project/constitution~v1')['element']['path'])
        self.assertEqual('.task/history/constitution/2.tdsl', query_registry(self.root, '@project/constitution~v2')['element']['path'])
        self.assertEqual('.task/constitution.tdsl', query_registry(self.root, '@project/constitution')['element']['path'])

    def test_part_and_explicit_section_queries_include_direct_relationships(self) -> None:
        self.write('engine.py', '# § 1 — ENGINE — Execute conversion\n# anchor_ref: @file/Fengine#section/Srun\n# ※ relation — Implements @tasks/engine#task/T1\n')
        self.write('tasks.tdsl', 'id: @tasks/engine\ntasks:\n  task T1:\n    target_refs: [@file/Fengine#section/Srun]\n')
        scan_project(self.root)
        task = query_registry(self.root, '@tasks/engine#task/T1')
        self.assertIn({'source': '@tasks/engine#task/T1', 'relation': 'references', 'target': '@file/Fengine#section/Srun'}, task['relationships'])
        section = query_registry(self.root, '@file/Fengine#section/Srun')
        self.assertIn({'source': '@file/Fengine#section/Srun', 'relation': 'references', 'target': '@tasks/engine#task/T1'}, section['relationships'])


# ── § 2 — ENTRY — Allow the orchestrator to run the complete test module ──

if __name__ == '__main__':
    unittest.main()
