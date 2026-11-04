# SPDX-License-Identifier: LicenseRef-Taller-Personal-Noncommercial-1.0
# ────────────────────────────────────────────
# TASK 2.2.0 — test_diagram_project.py
# § - Verify diagram adoption migration and immediate snapshot integrity · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

"""Verify independent diagram operations and preservation of brownfield source."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from diagram_project import run, verify_snapshot
from diagram_python import equivalent


# ── § 1 — OPERATIONS — Exercise preservation recovery and independent operation ──

class DiagramProjectTests(unittest.TestCase):
    """Exercise real files without Git, constitution or project configuration."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def source(self, text, name='module.py'):
        """Create a disposable exact-byte input."""
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode('utf-8'))
        return path

    def test_preview_does_not_write_anything(self):
        path = self.source('def run():\n    return 42\n')
        before = path.read_bytes()
        result = run(self.root, 'adopt')
        self.assertEqual(result['counts']['ready'], 1)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.root / '.task').exists())
        self.assertFalse((self.root / '.agent-cache').exists())

    def test_adopt_preserves_decorators_docstrings_directives_and_crlf(self):
        text = '#!/usr/bin/python\r\n# coding: utf-8\r\n"""Module purpose."""\r\n# type: ignore\r\n@decorator\r\ndef run():\r\n    """Execute conversion."""\r\n    return 42\r\n'
        path = self.source(text)
        result = run(self.root, 'adopt', True)
        after = path.read_bytes().decode('utf-8')
        self.assertTrue(equivalent(text, after))
        self.assertTrue(after.startswith('#!/usr/bin/python\r\n# coding: utf-8\r\n'))
        self.assertIn('@decorator\r\ndef run()', after)
        self.assertIn('# type: ignore\r\n', after)
        self.assertNotIn(b'\n', path.read_bytes().replace(b'\r\n', b''))
        self.assertTrue(verify_snapshot(self.root, Path(result['snapshot']))['integrity'])

    def test_markers_inside_strings_are_not_upgraded(self):
        path = self.source('value = """\n# § 1 — FALSE\n# § - false header\n"""\n')
        before = path.read_bytes()
        self.assertEqual(run(self.root, 'upgrade', True)['counts']['pending'], 1)
        self.assertEqual(path.read_bytes(), before)

    def test_upgrade_preserves_numbers_titles_provisional_and_refs(self):
        path = self.source('# =====\n# § - Existing purpose · Python\n# Author copyright\n# =====\n# ◇ 4 — ENGINE — Reserved work\nvalue = 1\n')
        run(self.root, 'upgrade', True, True)
        after = path.read_text(encoding='utf-8')
        self.assertIn('◇ 4 — ENGINE — Reserved work', after)
        self.assertIn('#section/legacy-4', after)
        self.assertIn('# Author copyright', after)
        before = path.read_bytes()
        self.assertFalse(run(self.root, 'upgrade', True)['applied'])
        self.assertEqual(before, path.read_bytes())
        registry = json.loads((self.root / '.task/tracking/registry.json').read_text())
        self.assertFalse(any(i['code'] == 'unresolved_legacy_identity' for i in registry['issues']))

    def test_unsupported_and_generated_sources_are_untouched(self):
        paths = [self.source('fn main() {}\n', 'engine.rs'),
                 self.source('# @generated\ndef run(): pass\n')]
        originals = [p.read_bytes() for p in paths]
        self.assertEqual(run(self.root, 'adopt', True)['counts']['pending'], 2)
        self.assertEqual(originals, [p.read_bytes() for p in paths])

    def test_build_and_dependency_trees_are_excluded(self):
        self.source('def run(): pass\n', 'node_modules/dep.py')
        self.source('def run(): pass\n', 'target/build.py')
        self.assertEqual(run(self.root, 'adopt')['files'], [])

    def test_malformed_nested_and_duplicate_markers_are_pending(self):
        for text in ('# § 1 — A\n# § 1 — B\nx = 1\n',
                     'def run():\n    # § 1 — A\n    pass\n',
                     '# § 1 ???\nx = 1\n'):
            with self.subTest(text=text):
                path = self.source(text)
                self.assertEqual(run(self.root, 'upgrade', True)['counts']['pending'], 1)
                self.assertEqual(path.read_text(encoding='utf-8'), text)

    def test_adopt_is_idempotent_and_tracking_is_optional(self):
        path = self.source('def run():\n    """Run conversion."""\n    pass\n')
        run(self.root, 'adopt', True)
        before = path.read_bytes()
        self.assertFalse((self.root / '.task/tracking/registry.json').exists())
        self.assertFalse((self.root / '.task').exists())
        self.assertFalse(run(self.root, 'adopt', True)['applied'])
        self.assertEqual(before, path.read_bytes())

    def test_snapshot_detects_functional_change_and_corruption(self):
        path = self.source('def run(): return 42\n')
        result = run(self.root, 'adopt', True)
        snapshot = Path(result['snapshot'])
        path.write_text(path.read_text(encoding='utf-8').replace('42', '43'), encoding='utf-8')
        self.assertFalse(verify_snapshot(self.root, snapshot)['integrity'])
        (snapshot / 'module.py').write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            verify_snapshot(self.root, snapshot)

    def test_failed_publication_restores_only_own_changes(self):
        paths = [self.source('def a(): pass\n', 'a.py'), self.source('def b(): pass\n', 'b.py')]
        originals = [p.read_bytes() for p in paths]
        import os
        replace = os.replace
        calls = []
        def fail_second(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError('simulated publication failure')
            replace(source, destination)
        with patch('diagram_project.os.replace', side_effect=fail_second):
            with self.assertRaises(OSError):
                run(self.root, 'adopt', True)
        self.assertEqual(originals, [p.read_bytes() for p in paths])

    def test_invalid_python_and_bom_are_pending(self):
        for text in ('def broken(:\n', '\ufeffx = 1\n'):
            self.source(text)
            self.assertEqual(run(self.root, 'adopt', True)['counts']['pending'], 1)

    def test_verify_does_not_claim_integrity_without_baseline(self):
        self.source('x = 1\n')
        result = run(self.root, 'verify')
        self.assertIn('not established', result['integrity'])
        self.assertFalse((self.root / '.task').exists())

    def test_duplicate_explicit_identities_never_publish(self):
        text = '# § 1 — ENGINE — Convert input\n# anchor_ref: @file/Fsame#section/Ssame\nx = 1\n'
        paths = [self.source(text, 'a.py'), self.source(text, 'b.py')]
        result = run(self.root, 'upgrade', True)
        self.assertFalse(result['applied'])
        self.assertEqual(result['counts']['pending'], 2)
        self.assertEqual([p.read_text(encoding='utf-8') for p in paths], [text, text])

    def test_registered_legacy_reference_survives_upgrade(self):
        from structure_tracker import scan_project, query_registry
        self.source('# § 3 — ENGINE — Convert input\nx = 1\n')
        registry = scan_project(self.root)
        reference = next(ref for ref, item in registry['elements'].items() if item['kind'] == 'section')
        run(self.root, 'upgrade', True)
        self.assertTrue(query_registry(self.root, reference)['exists'])

    def test_source_changed_after_proposal_is_rejected(self):
        import diagram_project
        path = self.source('def run(): pass\n')
        original_propose = diagram_project.propose
        def changing_propose(*args):
            result = original_propose(*args)
            path.write_bytes(b'def run(): return 7\n')
            return result
        with patch('diagram_project.propose', side_effect=changing_propose):
            with self.assertRaisesRegex(ValueError, 'changed since proposal'):
                run(self.root, 'adopt', True)
        self.assertEqual(path.read_bytes(), b'def run(): return 7\n')

    def test_tracking_can_register_unsupported_source_externally(self):
        self.source('fn main() {}\n', 'engine.rs')
        result = run(self.root, 'adopt', True, True)
        self.assertTrue(result['tracking_initialized'])
        registry = json.loads((self.root / '.task/tracking/registry.json').read_text(encoding='utf-8'))
        self.assertTrue(any(item['path'] == 'engine.rs' for item in registry['elements'].values()))


if __name__ == '__main__':
    unittest.main()
