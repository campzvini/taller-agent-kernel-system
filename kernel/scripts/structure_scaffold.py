# ────────────────────────────────────────────
# TASK 2.0 — structure_scaffold.py
# § - Reconcile the intended architecture and create safe provisional structure · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from diagram_check import comment_cfg, render_header, wrap
from structure_tracker import atomic_write, safe_relative, scan_project

# ── § 1 — ARCHITECTURE — Parse a tree-only Markdown structure ──

UNSAFE_NAMES = {'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'Cargo.lock', 'poetry.lock',
                'uv.lock', 'Cargo.toml', 'package.json', 'pyproject.toml', 'go.mod', 'go.sum'}
PLAIN_TEXT = {'.md', '.txt', '.rst', '.tdsl'}


def parse_architecture(path: Path) -> list[dict[str, str]]:
    """Parse fenced or bare Unix trees; reject prose and ambiguous indentation."""
    entries: list[dict[str, str]] = []
    parents: dict[int, str] = {}
    seen: set[str] = set()
    for number, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith('```'):
            continue
        if line.strip() in ('.', './'):
            continue
        match = re.fullmatch(r'((?:(?:│   |    ))*)(?:├── |└── )(.+)', line)
        if match:
            depth = len(match[1]) // 4
            label = match[2]
        else:
            match = re.fullmatch(r'( *)([^\s].*)', line)
            if match is None or len(match[1]) % 2:
                raise ValueError(f'architecture line {number}: invalid tree indentation')
            depth, label = len(match[1]) // 2, match[2]
        if label != label.strip() or '\\' in label or any(token in label for token in (' #', ' →', ' —', '\t')):
            raise ValueError(f'architecture line {number}: tree entries contain paths only')
        is_directory = label.endswith('/')
        label = label.rstrip('/')
        if not label or Path(label).is_absolute() or '..' in Path(label).parts or label.startswith(('#', '¶')):
            raise ValueError(f'architecture line {number}: unsafe or non-tree entry')
        if depth and depth - 1 not in parents:
            raise ValueError(f'architecture line {number}: missing directory parent')
        relative = str(Path(parents[depth - 1]) / label).replace('\\', '/') if depth else label
        if relative in seen:
            raise ValueError(f'architecture line {number}: duplicate destination {relative}')
        seen.add(relative)
        entries.append({'path': relative, 'kind': 'dir' if is_directory else 'file'})
        for key in list(parents):
            if key >= depth:
                del parents[key]
        if is_directory:
            parents[depth] = relative
    return entries


# ── § 2 — RECONCILIATION — Inspect existing destinations before creating anything ──

def scaffold_content(path: Path, file_ref: str = '@file/Funassigned') -> str | None:
    """Return comment-only source scaffolds; never fabricate manifests or binaries."""
    if path.name in UNSAFE_NAMES or path.suffix == '.lock':
        return None
    config = comment_cfg(path)
    if config['kind'] in ('line', 'block'):
        identity = f'{file_ref}#section/S0001'
        header = render_header(config, 'PROJECT', '0', path.name,
                               'Reserved implementation destination', config['lang'] or 'Source')
        return header + '\n\n' + wrap(config, '◇ 1 — IMPLEMENTATION — Reserved implementation destination') + '\n' + wrap(config, f'anchor_ref: {identity}') + '\n'
    if path.suffix in PLAIN_TEXT:
        return f'¶ - Reserved document destination for {path.name}.\n\n¶ 1 — Content\n'
    return None


def scaffold_project(root: Path, apply: bool = False, architecture: Path | None = None) -> dict[str, Any]:
    """Plan or create missing safe structure without overwriting existing bytes."""
    root = root.resolve()
    architecture = architecture or root / '.task/Architecture.md'
    entries = parse_architecture(architecture)
    actions: list[dict[str, str]] = []
    for entry in entries:
        relative, kind = entry['path'], entry['kind']
        destination = safe_relative(root, relative)
        if relative == '.git' or relative.startswith('.git/') or relative.startswith('.task/tracking/'):
            raise ValueError(f'protected scaffold destination: {relative}')
        if destination.is_symlink():
            raise ValueError(f'scaffold does not write through symlink: {relative}')
        parent = destination.parent
        while parent != root:
            if parent.is_symlink():
                raise ValueError(f'scaffold does not write through symlink parent: {relative}')
            if parent.exists() and not parent.is_dir():
                raise ValueError(f'scaffold parent is not a directory: {relative}')
            parent = parent.parent
        if destination.exists():
            if (kind == 'dir') != destination.is_dir():
                raise ValueError(f'architecture conflicts with existing destination kind: {relative}')
            actions.append({**entry, 'action': 'reuse'})
            continue
        # Governance records are authored by their phase, never satisfied by a
        # comment-only placeholder that the existence router could mistake for a record.
        content = None if relative.startswith('.task/') and kind == 'file' else (scaffold_content(destination) if kind == 'file' else '')
        action = 'pending' if content is None else 'create'
        actions.append({**entry, 'action': action})
        # Inspect all destinations before performing any writes.
    if apply:
        intended = scan_project(root)
        planned_refs = {item['path']: reference for reference, item in intended['elements'].items()
                        if item['kind'] == 'file' and item['state'] in ('planned', 'present')}
        # An interrupted or newly incomplete scaffold cannot retain an old completion claim.
        (root / '.task/runtime/scaffold.json').unlink(missing_ok=True)
        (root / '.task/runtime/scaffold-preparation.json').unlink(missing_ok=True)
        for action in actions:
            destination = safe_relative(root, action['path'])
            if action['action'] != 'create':
                continue
            if action['kind'] == 'dir':
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                content = scaffold_content(destination, planned_refs[action['path']])
                if content is None:
                    raise ValueError(f'cannot scaffold destination safely: {destination}')
                with destination.open('x', encoding='utf-8', newline='\n') as handle:
                    handle.write(content)
        registry = scan_project(root)
        generation = registry['generation']
        preparation = {'format': 'task.scaffold-preparation@1', 'generation': generation,
                       'inventory': entries, 'deferred': [a['path'] for a in actions if a['action'] == 'pending'],
                       'functional_implementation': False}
        atomic_write(root / '.task/runtime/scaffold-preparation.json', json.dumps(preparation, ensure_ascii=False, indent=2) + '\n')
        if not any(action['action'] == 'pending' for action in actions):
            completion = {'format': 'task.structural-scaffold@1', 'generation': generation,
                          'architecture': architecture.relative_to(root).as_posix()
                          if architecture.is_relative_to(root) else str(architecture),
                          'inventory': entries, 'functional_implementation': False}
            atomic_write(root / '.task/runtime/scaffold.json', json.dumps(completion, ensure_ascii=False, indent=2) + '\n')
    else:
        generation = None
    return {'architecture': str(architecture), 'applied': apply, 'generation': generation,
            'complete': apply and not any(action['action'] == 'pending' for action in actions),
            'inventory': entries,
            'functional_implementation': False, 'actions': actions}


# ── § 3 — ENTRY — Expose dry-run and explicit structural creation ──

def main() -> int:
    """Report scaffold actions and preserve explicit failure feedback."""
    parser = argparse.ArgumentParser(description='Safe Execute 0 structural scaffold')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--architecture', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        result = scaffold_project(args.root, args.apply, args.architecture)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
