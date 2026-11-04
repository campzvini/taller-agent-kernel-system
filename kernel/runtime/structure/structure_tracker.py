# ────────────────────────────────────────────
# TASK 2.2.0 — structure_tracker.py
# § - Maintain stable structural identities and reconstructible navigation indexes · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterator
import uuid

# ── § 1 — IDENTITY — Persist identity independently of paths and visual numbers ──

REGISTRY = Path('.task/tracking/registry.json')
PROJECTION = Path('.agent-cache/tracking')
EXCLUDED = {'.git', '.hg', '.svn', '.agent-cache', '__pycache__'}
REF_RE = re.compile(r'@[a-z][a-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_.~/-]*(?:#[a-z_]+/[A-Za-z0-9][A-Za-z0-9_.~-]*)?')
MARKER_RE = re.compile(r'^\s*(?:(?://|#|--|/\*|<!--|\*)\s*)?(?:[─━═]\s*)*([§¶◇])\s+(\d+(?:\.\d+)*)\s*[—:-]\s*(.*?)\s*(?:─+|\*/|-->)?\s*$')
ANCHOR_REF_RE = re.compile(r'^\s*(?:(?://|#|--|/\*|<!--|\*)\s*)?anchor_ref:\s*(' + REF_RE.pattern + r')')
DOC_ID_RE = re.compile(r'^id:\s*(' + REF_RE.pattern + r')\s*$', re.MULTILINE)


def atomic_write(path: Path, text: str) -> None:
    """Publish a UTF-8 file atomically without exposing a partial document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(text, encoding='utf-8', newline='\n')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def registry_lock(root: Path) -> Iterator[None]:
    """Refuse concurrent writers; a stale lock requires explicit recovery."""
    lock = root / '.task/tracking/write.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise ValueError(f'tracking writer is active or interrupted: {lock}; inspect before removing the lock') from error
    try:
        os.write(descriptor, str(os.getpid()).encode('ascii'))
        os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def load_registry(root: Path) -> dict[str, Any]:
    """Read persistent identities; never silently replace corrupt state."""
    path = root / REGISTRY
    if not path.exists():
        return {'format': 'task.structural-registry@1', 'generation': 0, 'next_id': 1,
                'elements': {}, 'relationships': [], 'issues': []}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('format') != 'task.structural-registry@1' or not isinstance(data.get('elements'), dict):
        raise ValueError(f'unsupported structural registry: {path}')
    if type(data.get('generation')) is not int or data['generation'] < 0 or type(data.get('next_id')) is not int or data['next_id'] < 1:
        raise ValueError('corrupt structural generation or identity counter')
    for reference, element in data['elements'].items():
        if not REF_RE.fullmatch(reference) or not isinstance(element, dict) or element.get('state') not in {'present', 'planned', 'removed', 'unresolved'}:
            raise ValueError(f'corrupt structural identity: {reference}')
        if element.get('kind') not in {'file', 'dir', 'link', 'section'} or not isinstance(element.get('path'), str):
            raise ValueError(f'corrupt structural element: {reference}')
    return data


def allocate_ref(registry: dict[str, Any], kind: str) -> str:
    """Allocate a never-reused identity without hashing source content."""
    while True:
        number = registry['next_id']
        registry['next_id'] += 1
        reference = f'@{kind}/{kind[0].upper()}{number:06d}'
        if reference not in registry['elements']:
            return reference


def safe_relative(root: Path, value: str) -> Path:
    """Resolve an in-project path and refuse traversal or symlink escapes."""
    candidate = root / value
    if not value or value in ('.', './') or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError(f'path must be project relative: {value}')
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f'path leaves project: {value}')
    return candidate


# ── § 2 — INVENTORY — Enumerate every bounded filesystem element without following links ──

def inventory(root: Path) -> list[tuple[str, str]]:
    """Inventory directories, files and symlinks independently of suffix."""
    result: list[tuple[str, str]] = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        kept = []
        for name in sorted(dirs):
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if name in EXCLUDED or relative == '.task/tracking':
                continue
            result.append((relative, 'link' if path.is_symlink() else 'dir'))
            if not path.is_symlink():
                kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            path = parent / name
            result.append((path.relative_to(root).as_posix(), 'link' if path.is_symlink() else 'file'))
    return sorted(result)


def read_text_if_safe(path: Path) -> str | None:
    """Read UTF-8 text only; binaries and links remain externally addressable."""
    if path.is_symlink():
        return None
    try:
        raw = path.read_bytes()
        return None if b'\x00' in raw else raw.decode('utf-8')
    except UnicodeDecodeError:
        return None


# ── § 3 — ANCHORS — Bind explicit identities while retaining legacy navigation ──

def extract_sections(text: str) -> list[dict[str, Any]]:
    """Extract declared chapters; identity comments bind to the preceding chapter."""
    sections: list[dict[str, Any]] = []
    lines = text.splitlines()
    for line_number, line in enumerate(lines, 1):
        marker = MARKER_RE.match(line)
        if marker:
            sections.append({'marker': marker[1], 'number': marker[2],
                             'title': marker[3].rstrip('─ */->!'), 'line': line_number,
                             'identity': None})
        identity = ANCHOR_REF_RE.match(line)
        if identity and sections and line_number <= sections[-1]['line'] + 2:
            sections[-1]['identity'] = identity[1]
    for index, section in enumerate(sections):
        end = sections[index + 1]['line'] - 1 if index + 1 < len(sections) else len(lines)
        section['limit'] = end - section['line'] + 1
    return sections


def register_sections(registry: dict[str, Any], file_ref: str, path: str, text: str,
                      previous: dict[str, Any], seen: set[str]) -> None:
    """Promote markers only when identity is explicit; never match by title or bytes."""
    elements = registry['elements']
    sections = extract_sections(text)
    former_legacy = [item for item in previous.values()
                     if item.get('file_ref') == file_ref and item.get('identity_quality') == 'legacy_locator'
                     and item['state'] != 'removed']
    former_legacy.sort(key=lambda item: item['line'])
    current_legacy = [item for item in sections if item['identity'] is None]
    changed = bool(former_legacy) and [(item['number'], item['title']) for item in former_legacy] != [
        (item['number'], item['title']) for item in current_legacy]
    legacy_unresolved = bool(current_legacy) and (changed or any(item['state'] == 'unresolved' for item in former_legacy))
    if legacy_unresolved:
        registry['issues'].append({'code': 'unresolved_legacy_identity', 'path': path,
                                   'reference': file_ref,
                                   'resolution': 'reconcile explicit section identities; numbers and titles are locators only'})
    lines = text.splitlines()
    for section in sections:
        reference = section.pop('identity')
        state = 'present'
        if reference is None:
            # Legacy numbers are locators, not stable identity evidence after movement.
            reference = f'{file_ref}#section/legacy-{section["number"]}'
            section['identity_quality'] = 'legacy_locator'
            if legacy_unresolved:
                state = 'unresolved'
        elif not reference.startswith('@file/') or '#section/' not in reference:
            registry['issues'].append({'code': 'invalid_section_identity', 'path': path, 'reference': reference})
            continue
        if reference in seen:
            registry['issues'].append({'code': 'duplicate_identity', 'path': path, 'reference': reference})
            continue
        seen.add(reference)
        former = previous.get(reference, {})
        elements[reference] = {'kind': 'section', 'path': path, 'file_ref': file_ref,
                               'state': state, **section}
        if former.get('marker') == '◇' and section['marker'] == '§':
            elements[reference]['promotion_generation'] = registry['generation']
        registry['relationships'].append({'source': file_ref, 'relation': 'contains', 'target': reference})
        if section.get('identity_quality') != 'legacy_locator':
            body = '\n'.join(lines[section['line'] - 1:section['line'] - 1 + section['limit']])
            registry['relationships'].extend({'source': reference, 'relation': 'references', 'target': target}
                                             for target in sorted(set(REF_RE.findall(body))) if target != reference)


# ── § 4 — REFERENCES — Resolve typed relationships without judging implementation ──

def collect_references(registry: dict[str, Any], file_ref: str, text: str,
                       aliases: dict[str, str]) -> None:
    """Index references and tracked document identities without inventing semantics."""
    document = DOC_ID_RE.search(text)
    source = document[1] if document else file_ref
    snapshot = re.fullmatch(r'\.task/history/constitution/([1-9][0-9]*)\.tdsl', registry['elements'][file_ref]['path'])
    if snapshot and document:
        declared_version = re.search(r'^version:\s*([1-9][0-9]*)\s*$', text, re.MULTILINE)
        if declared_version is None or declared_version[1] != snapshot[1]:
            registry['issues'].append({'code': 'invalid_snapshot_version', 'path': registry['elements'][file_ref]['path']})
        source += f'~v{snapshot[1]}'
    if document:
        if source in aliases and aliases[source] != file_ref:
            registry['issues'].append({'code': 'duplicate_document_identity', 'reference': source})
        aliases[source] = file_ref
    # A part ends at its next sibling or enclosing block, not at the file boundary.
    lines = text.splitlines()
    part_pattern = re.compile(r'^( +)([a-z][a-z0-9_]*)\s+([A-Za-z0-9_.~-]+):\s*$')
    details = registry.setdefault('alias_details', {})

    def add_part_edges(part_ref: str, body: str) -> None:
        for target in sorted(set(REF_RE.findall(body))):
            if snapshot and document and target.startswith(document[1] + '#'):
                target = source + target[len(document[1]):]
            if target != part_ref:
                registry['relationships'].append({'source': part_ref, 'relation': 'references', 'target': target})

    for index, line in enumerate(lines):
        match = part_pattern.match(line)
        if not match:
            continue
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= len(match[1]):
                break
            end += 1
        if document:
            reference = f'{source}#{match[2]}/{match[3]}'
            if reference in aliases:
                registry['issues'].append({'code': 'duplicate_part_identity', 'reference': reference})
            aliases[reference] = file_ref
            details[reference] = {'line': index + 1, 'limit': end - index, 'kind': match[2]}
            add_part_edges(reference, '\n'.join(lines[index:end]))
        for nested in lines[index + 1:end]:
            identity = re.match(r'^\s+(event_id|decision_id|failure_id):\s*(' + REF_RE.pattern + r')\s*$', nested)
            if identity:
                if identity[2] in aliases:
                    registry['issues'].append({'code': 'duplicate_event_identity', 'reference': identity[2]})
                aliases[identity[2]] = file_ref
                details[identity[2]] = {'line': index + 1, 'limit': end - index, 'kind': identity[1].removesuffix('_id')}
                add_part_edges(identity[2], '\n'.join(lines[index:end]))
    for reference in sorted(set(REF_RE.findall(text))):
        if document and reference == document[1]:
            continue
        if snapshot and document and reference.startswith(document[1] + '#'):
            reference = source + reference[len(document[1]):]
        if reference != source:
            registry['relationships'].append({'source': source, 'relation': 'references', 'target': reference})


def resolve_reference(registry: dict[str, Any], reference: str) -> dict[str, Any] | None:
    """Resolve structural identities and declared document aliases."""
    target = registry.get('aliases', {}).get(reference, reference)
    return registry['elements'].get(target)


def check_registry(root: Path) -> list[dict[str, Any]]:
    """Return structural integrity findings from the last published registry."""
    registry = load_registry(root)
    return registry.get('issues', [])


def register_intended(root: Path, registry: dict[str, Any], by_path: dict[str, str], seen: set[str]) -> None:
    """Identify declared architecture destinations before they physically exist."""
    architecture = root / '.task/Architecture.md'
    if not architecture.is_file():
        return
    if architecture.is_symlink():
        registry['issues'].append({'code': 'invalid_architecture', 'path': '.task/Architecture.md',
                                   'reason': 'architecture cannot be read through a symbolic link'})
        return
    from structure_scaffold import parse_architecture
    try:
        entries = parse_architecture(architecture)
        for entry in entries:
            safe_relative(root, entry['path'])
            if any(part in EXCLUDED for part in Path(entry['path']).parts) or entry['path'].startswith('.task/tracking'):
                raise ValueError(f'architecture targets an excluded boundary: {entry["path"]}')
    except (OSError, ValueError) as error:
        registry['issues'].append({'code': 'invalid_architecture', 'path': '.task/Architecture.md', 'reason': str(error)})
        return
    elements = registry['elements']
    current_paths = {item['path']: ref for ref, item in elements.items() if ref in seen and item['kind'] != 'section'}
    for entry in entries:
        path, kind = entry['path'], entry['kind']
        reference = current_paths.get(path) or by_path.get(path)
        if reference and elements[reference]['kind'] != kind:
            registry['issues'].append({'code': 'architecture_kind_conflict', 'path': path, 'reference': reference})
            continue
        if reference is None:
            reference = allocate_ref(registry, 'dir' if kind == 'dir' else 'file')
        if reference not in seen:
            elements[reference] = {'kind': kind, 'path': path, 'state': 'planned'}
        elements[reference]['intended'] = True
        seen.add(reference)
        registry['relationships'].append({'source': '@arch/project', 'relation': 'plans', 'target': reference})


# ── § 5 — RECONCILIATION — Publish a consistent scan and preserve removed identities ──

def _scan_locked(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    previous = {key: dict(value) for key, value in registry['elements'].items()}
    previous_aliases = dict(registry.get('aliases', {}))
    previous_details = dict(registry.get('alias_details', {}))
    registry['generation'] += 1
    registry['relationships'], registry['issues'] = [], []
    registry['alias_details'] = {}
    aliases: dict[str, str] = {}
    by_path = {item['path']: reference for reference, item in previous.items()
               if item['kind'] != 'section' and item['state'] in ('present', 'planned')}
    seen: set[str] = set()
    texts: list[tuple[str, str]] = []
    for path, kind in inventory(root):
        text = read_text_if_safe(root / path) if kind == 'file' else None
        reference = by_path.get(path)
        if reference and previous[reference]['kind'] != kind:
            reference = None
        owners = {section['identity'].split('#', 1)[0] for section in extract_sections(text or '')
                  if section['identity'] and section['identity'].startswith('@file/')}
        if len(owners) > 1:
            registry['issues'].append({'code': 'ambiguous_file_identity', 'path': path})
        elif owners:
            declared = next(iter(owners))
            former = previous.get(declared)
            original_exists = former and (root / former['path']).exists() and former['path'] != path
            if declared in seen or original_exists:
                registry['issues'].append({'code': 'duplicate_file_identity', 'path': path, 'reference': declared})
            elif reference and reference != declared and previous.get(reference, {}).get('identity_quality') == 'explicit':
                registry['issues'].append({'code': 'conflicting_file_identity', 'path': path, 'reference': declared})
            else:
                reference = declared
        if reference is None:
            reference = allocate_ref(registry, 'dir' if kind == 'dir' else 'file')
        registry['elements'][reference] = {'kind': kind, 'path': path, 'state': 'present'}
        if owners and reference in owners:
            registry['elements'][reference]['identity_quality'] = 'explicit'
        seen.add(reference)
        if kind == 'file':
            if text is not None:
                register_sections(registry, reference, path, text, previous, seen)
                texts.append((reference, text))
    register_intended(root, registry, by_path, seen)
    # Removed elements retain their old identity and remain valid historical targets.
    for reference, element in list(registry['elements'].items()):
        if reference not in seen:
            element['state'] = 'removed'
    removed = [reference for reference, item in previous.items()
               if item['kind'] != 'section' and item['state'] == 'present' and reference not in seen]
    added = [reference for reference in seen if reference not in previous
             and registry['elements'][reference]['kind'] != 'section'
             and registry['elements'][reference].get('identity_quality') != 'explicit']
    if removed and added:
        registry['issues'].append({'code': 'unresolved_identity', 'removed': sorted(removed),
                                   'added': sorted(added), 'resolution': 'declare moves explicitly; no correspondence inferred'})
    for reference, text in texts:
        collect_references(registry, reference, text, aliases)
        path = registry['elements'][reference]['path']
        if path == '.task/Architecture.md':
            aliases['@arch/project'] = reference
        if path == '.task/project.tdsl':
            for match in re.finditer(r'^  feature ([A-Za-z0-9_.~-]+):\s*$', text, re.MULTILINE):
                alias = f'@feature/{match[1]}'
                aliases[alias] = reference
                document = DOC_ID_RE.search(text)
                part = f'{document[1]}#feature/{match[1]}' if document else ''
                if part in registry['alias_details']:
                    registry['alias_details'][alias] = dict(registry['alias_details'][part])
    # Retain historical aliases when their defining file has been removed.
    for alias, reference in previous_aliases.items():
        if alias not in aliases and reference in registry['elements'] and registry['elements'][reference]['state'] == 'removed':
            aliases[alias] = reference
            if alias in previous_details:
                registry['alias_details'][alias] = previous_details[alias]
    registry['aliases'] = aliases
    paths = {item['path']: reference for reference, item in registry['elements'].items()
             if item['kind'] != 'section' and item['state'] in ('present', 'planned')}
    for path, reference in paths.items():
        parent = Path(path).parent.as_posix()
        if parent in paths:
            registry['relationships'].append({'source': paths[parent], 'relation': 'contains', 'target': reference})
    for edge in registry['relationships']:
        if edge['relation'] != 'references':
            continue
        target = resolve_reference(registry, edge['target'])
        if target is None or target['state'] not in ('present', 'planned'):
            registry['issues'].append({'code': 'unresolved_reference', **edge})
    atomic_write(root / REGISTRY, json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    write_projections(root, registry)
    return registry


def scan_project(root: Path) -> dict[str, Any]:
    """Reconcile a project and atomically publish registry before derived indexes."""
    root = root.resolve()
    with registry_lock(root):
        return _scan_locked(root, load_registry(root))


def move_element(root: Path, reference: str, destination: str) -> dict[str, Any]:
    """Declare identity-preserving movement after an external filesystem move."""
    root = root.resolve()
    destination = Path(destination).as_posix()
    target = safe_relative(root, destination)
    with registry_lock(root):
        registry = load_registry(root)
        element = registry['elements'].get(reference)
        if element is None or element['kind'] == 'section':
            raise ValueError(f'unknown filesystem identity: {reference}')
        old = element['path']
        if (root / old).exists() or (root / old).is_symlink():
            raise ValueError('original path still exists; copied elements cannot inherit identity')
        if not target.exists() and not target.is_symlink():
            raise ValueError(f'move destination does not exist: {destination}')
        for other_ref, other in registry['elements'].items():
            if other_ref != reference and other['path'] == destination and other['state'] == 'present':
                raise ValueError('destination already owns a distinct identity; reconcile before declaring move')
        for item in registry['elements'].values():
            if item['path'] == old or item['path'].startswith(old + '/'):
                item['path'] = destination + item['path'][len(old):]
                item['state'] = 'present'
        return _scan_locked(root, registry)


# ── § 6 — QUERIES — Return bounded context by identity or path ──

def query_registry(root: Path, reference: str) -> dict[str, Any]:
    """Return one element, its incoming/outgoing relations and relevant issues."""
    registry = load_registry(root)
    element = resolve_reference(registry, reference)
    if element is None:
        matches = [(key, value) for key, value in registry['elements'].items()
                   if value['path'] == reference and value['kind'] != 'section' and value['state'] in ('present', 'planned')]
        if len(matches) == 1:
            reference, element = matches[0]
    if element is None:
        raise ValueError(f'unresolved structural target: {reference}')
    detail = registry.get('alias_details', {}).get(reference, {})
    exists = element['state'] == 'present'
    return {'reference': reference, 'generation': registry['generation'], 'exists': exists,
            'element': {**element, **detail, 'exists': exists},
            'relationships': [edge for edge in registry['relationships'] if reference in (edge['source'], edge['target'])],
            'issues': [issue for issue in registry['issues'] if reference in issue.values()]}


# ── § 7 — PROJECTIONS — Rebuild Markdown navigation without creating authority ──

def write_projections(root: Path, registry: dict[str, Any]) -> None:
    """Render directory and project navigation from the persistent registry."""
    projection = root / PROJECTION
    rows = ['# Structural index', '', '¶ - Reconstructible structural navigation; not normative authority.', '',
            f'Generation: {registry["generation"]}', '', '| Identity | Kind | State | Path |', '|---|---|---|---|']
    for reference, item in sorted(registry['elements'].items()):
        rows.append(f'| `{reference}` | {item["kind"]} | {item["state"]} | `{item["path"]}` |')
    atomic_write(projection / 'index.md', '\n'.join(rows) + '\n')
    atomic_write(projection / 'index.json', json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    directories: dict[str, list[tuple[str, dict[str, Any]]]] = {'.': []}
    directory_refs = {item['path']: reference for reference, item in registry['elements'].items() if item['kind'] == 'dir'}
    for directory in directory_refs:
        directories[directory] = []
    for reference, item in registry['elements'].items():
        if item['state'] in ('present', 'planned') and item['kind'] != 'section':
            directories.setdefault(Path(item['path']).parent.as_posix(), []).append((reference, item))
    for directory, items in directories.items():
        name = 'project-root' if directory == '.' else directory_refs[directory].split('/', 1)[1]
        lines = [f'# Directory — {directory}', '', '¶ - Derived direct-child inventory.', '']
        lines.extend(f'`{ref}` → `{item["path"]}` ({item["kind"]})' for ref, item in sorted(items))
        atomic_write(projection / 'directories' / f'{name}.md', '\n\n'.join(lines) + '\n')


def main() -> int:
    """Dispatch structural commands and report explicit errors to callers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('scan')
    commands.add_parser('check')
    query = commands.add_parser('query')
    query.add_argument('reference')
    move = commands.add_parser('move')
    move.add_argument('reference')
    move.add_argument('destination')
    args = parser.parse_args()
    try:
        if args.command == 'scan':
            registry = scan_project(args.root)
            result = {'generation': registry['generation'], 'elements': len(registry['elements']), 'issues': registry['issues']}
        elif args.command == 'query':
            result = query_registry(args.root, args.reference)
        elif args.command == 'move':
            registry = move_element(args.root, args.reference, args.destination)
            result = {'generation': registry['generation'], 'issues': registry['issues']}
        else:
            result = check_registry(args.root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.command == 'check' and result else 0
    except (OSError, ValueError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
