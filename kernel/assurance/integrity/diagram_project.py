# SPDX-License-Identifier: LicenseRef-Taller-Personal-Noncommercial-1.0
# ────────────────────────────────────────────
# TASK 2.2.0 — diagram_project.py
# § - Adopt and upgrade structural diagrams independently of governance · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

"""Independent, snapshot-backed structural diagram adoption and migration."""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

import code_map
import diagram_check as banners
from diagram_python import equivalent, header_position, inspect_source, symbols
from structure_tracker import (MARKER_RE, allocate_ref, extract_sections, load_registry, registry_lock,
                               _scan_locked)


# ── § 1 — DISCOVERY — Bound source inventory and fingerprint original bytes ──

def digest(data: bytes) -> str:
    """Fingerprint exact source bytes, including local uncommitted changes."""
    return hashlib.sha256(data).hexdigest()


def discover(root: Path):
    """Enumerate source candidates without following links or entering build trees."""
    for directory, dirs, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        dirs[:] = sorted(name for name in dirs if name not in code_map.SKIP_DIRS
                         and name != '.task' and not (parent / name).is_symlink())
        for name in sorted(files):
            path = parent / name
            if not path.is_symlink() and banners.comment_cfg(path)['kind'] in ('line', 'block'):
                yield path


# ── § 2 — PROPOSALS — Prepare conservative comment transformations ──

def propose(path: Path, mode: str, registry: dict, relative: str) -> tuple[dict, bytes | None]:
    """Build a deterministic Python proposal; unsupported inputs remain external."""
    raw = path.read_bytes()
    record = {'path': relative, 'before_sha256': digest(raw), 'status': 'pending',
              'reasons': [], 'changes': [], 'review': []}
    if path.suffix != '.py':
        record['reasons'] = ['no safe syntax adapter; external identity only']
        return record, None
    try:
        text = raw.decode('utf-8')
        if text.startswith('\ufeff'):
            raise ValueError('UTF-8 BOM requires explicit migration')
        tree, comments = inspect_source(text)
    except (UnicodeError, SyntaxError, ValueError, IndentationError) as error:
        record['reasons'] = [str(error)]
        return record, None
    if any(re.search(r'(?i)(@generated|auto[- ]generated|do not edit)', value)
           for line, value in comments.items() if line <= 20):
        record['reasons'] = ['generated source excluded']
        return record, None
    lines = text.splitlines(keepends=True)
    sections = []
    headers = []
    for number, comment in comments.items():
        marker = MARKER_RE.match(comment)
        if marker:
            if lines[number - 1].startswith((' ', '\t')):
                record['reasons'] = ['nested marker requires review']
                return record, None
            sections.append((number, marker))
        elif re.match(r'^#\s*§ - ', comment):
            headers.append(number)
        elif re.search(r'[§◇]\s*\d', comment):
            record['reasons'] = ['malformed marker requires review']
            return record, None
    if len(headers) > 1 or len({m[2] for _, m in sections}) != len(sections):
        record['reasons'] = ['duplicate header or chapter number']
        return record, None
    if mode == 'adopt' and (sections or headers):
        record['status'] = 'existing'
        record['reasons'] = ['use upgrade for existing diagrams']
        return record, None
    if mode == 'upgrade' and not (sections or headers):
        record['reasons'] = ['no recognized diagram; use adopt']
        return record, None
    file_ref = next((ref for ref, item in registry['elements'].items()
                     if item['path'] == relative and item['kind'] == 'file'
                     and item['state'] == 'present'), None)
    owners = {m[1].split('#')[0] for comment in comments.values()
              if (m := re.fullmatch(r'#\s*anchor_ref:\s*(@file/\S+#section/\S+)\s*', comment))}
    if len(owners) > 1 or (owners and file_ref and file_ref not in owners):
        record['reasons'] = ['conflicting explicit file identities']
        return record, None
    if owners:
        owner = next(iter(owners))
        former = registry['elements'].get(owner)
        if former and former['path'] != relative and (path.parents[len(Path(relative).parts) - 1] / former['path']).exists():
            record['reasons'] = ['explicit file identity already belongs to another path']
            return record, None
    file_ref = file_ref or (next(iter(owners)) if owners else allocate_ref(registry, 'file'))
    cfg = banners.comment_cfg(path)
    edits = {}
    insertions = {}
    newline = '\r\n' if b'\r\n' in raw else '\n'
    def insert(position, value):
        insertions.setdefault(position, []).append(value.replace('\n', newline) + newline)
    if not headers:
        purpose = (ast_doc(tree) or path.stem.replace('_', ' '))
        insert(header_position(lines), banners.render_header(cfg, 'SOURCE', '', path.name,
                                                           purpose, 'Python'))
        record['changes'].append('insert header')
        if not ast_doc(tree):
            record['review'].append('file purpose derived from filename; review semantics')
    else:
        # Normalize only recognized diagram delimiters, preserving attribution and prose.
        header_line = headers[0]
        if header_line > 14:
            record['reasons'] = ['header outside recognized leading zone']
            return record, None
        for number, comment in comments.items():
            if number <= 14 and banners.is_legacy_rule(comment):
                edits[number - 1] = banners.wrap(cfg, banners.RULE) + newline
        if not any('─' in c for n, c in comments.items() if n <= 14):
            insert(header_line - 1, banners.wrap(cfg, banners.RULE))
            insert(header_line, banners.wrap(cfg, banners.RULE))
    if mode == 'adopt':
        for index, symbol in enumerate(symbols(tree), 1):
            title = symbol['name'].upper()
            description = symbol['description']
            if not description:
                record['review'].append({'line': symbol['line'], 'symbol': symbol['name'],
                                         'reason': 'responsibility requires semantic review'})
            identity = f'{file_ref}#section/S{index:04d}'
            insert(symbol['line'] - 1, banners.render_chapter(cfg, str(index), title, description, True)
                   + '\n' + banners.wrap(cfg, 'anchor_ref: ' + identity))
            record['changes'].append({'symbol': symbol['name'], 'line': symbol['line']})
        if not symbols(tree):
            record['review'].append('no module-level declarations; no artificial chapter inserted')
    else:
        for number, marker in sections:
            title = re.sub(r'\s+─+\s*$', '', marker[3]).strip()
            if not title:
                record['reasons'] = ['empty chapter title']
                return record, None
            rendered = banners.render_chapter(cfg, marker[2], title, '', False)
            if marker[1] == '◇':
                rendered = rendered.replace('§', '◇', 1)
            edits[number - 1] = rendered + newline
            identities = [comments[n] for n in (number + 1, number + 2)
                          if n in comments and re.match(r'^#\s*anchor_ref:', comments[n])]
            if identities and (len(identities) != 1 or not re.fullmatch(
                    r'#\s*anchor_ref:\s*@file/[A-Za-z0-9_.~-]+#section/[A-Za-z0-9_.~-]+\s*', identities[0])):
                record['reasons'] = ['invalid or duplicate explicit section identity']
                return record, None
            if not identities:
                # Preserve the existing locator as explicit identity; references keep working.
                insert(number, banners.wrap(cfg, f'anchor_ref: {file_ref}#section/legacy-{marker[2]}'))
            record['changes'].append({'chapter': marker[2], 'line': number})
        for number, comment in comments.items():
            if number > 14 and banners.is_legacy_rule(comment):
                edits[number - 1] = banners.wrap(cfg, banners.RULE) + newline
    output = []
    for index in range(len(lines) + 1):
        output.extend(insertions.get(index, []))
        if index < len(lines):
            output.append(edits.get(index, lines[index]))
    candidate = ''.join(output)
    if not equivalent(text, candidate):
        raise ValueError(f'Python safety invariant failed: {relative}')
    encoded = candidate.encode('utf-8')
    record['after_sha256'] = digest(encoded)
    record['status'] = 'unchanged' if raw == encoded else 'ready'
    return record, encoded if raw != encoded else None


def ast_doc(tree) -> str:
    """Return the first line of an existing module description."""
    import ast
    return (ast.get_docstring(tree) or '').split('\n')[0].strip()


# ── § 3 — VERIFICATION — Compare current source with immediate snapshots ──

def verify_snapshot(root: Path, snapshot: Path) -> dict:
    """Compare current executable structure with the exact pre-operation bytes."""
    snapshot = snapshot.resolve(strict=True)
    manifest = json.loads((snapshot / 'manifest.json').read_text(encoding='utf-8'))
    results = []
    for rec in manifest['files']:
        if rec['status'] != 'ready':
            continue
        relative = Path(rec['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('unsafe snapshot path')
        source, backup = root / relative, snapshot / relative
        if not source.resolve().is_relative_to(root) or not backup.resolve().is_relative_to(snapshot):
            raise ValueError('snapshot path leaves declared root')
        before = backup.read_bytes()
        if digest(before) != rec['before_sha256']:
            raise ValueError('snapshot bytes do not match manifest')
        after = source.read_bytes()
        try:
            valid = equivalent(before.decode('utf-8'), after.decode('utf-8'))
        except (UnicodeError, SyntaxError, ValueError):
            valid = False
        results.append({'path': rec['path'], 'functional_integrity': valid,
                        'exact_result': digest(after) == rec['after_sha256']})
    return {'mode': 'verify', 'snapshot': str(snapshot), 'files': results,
            'integrity': all(item['functional_integrity'] for item in results)}


# ── § 4 — PUBLICATION — Apply recoverable transformations and optional tracking ──

@contextmanager
def operation_lock(root: Path):
    """Serialize diagram writers without creating an optional tracking registry."""
    lock = root / '.agent-cache/diagram/write.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise ValueError(f'diagram writer active or interrupted: {lock}; inspect before recovery') from error
    try:
        os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def run(root: Path, mode: str, apply: bool = False, tracking: bool = False) -> dict:
    """Plan or apply an isolated operation with recoverable immediate snapshots."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('root must be a directory')
    if mode == 'verify':
        records = []
        for path in discover(root):
            rec = banners.scan_file(path)
            rec['path'] = path.relative_to(root).as_posix()
            if path.suffix == '.py':
                try:
                    _, comments = inspect_source(path.read_bytes().decode('utf-8'))
                    rec['chapters'] = [{'line': n, 'number': m[2], 'title': m[3],
                                        'level': m[2].count('.') + 1}
                                       for n, c in comments.items() if (m := MARKER_RE.match(c))]
                    header = next(({'line': n, 'title': c.split('§ - ', 1)[1]}
                                   for n, c in comments.items()
                                   if n <= 14 and re.match(r'^#\s*§ - ', c)), None)
                    rec['has_header'] = bool(header)
                    rec['warnings'].extend(code_map.detect_issues(header, rec['chapters'], '§', path))
                    if rec['warnings'] or not rec['chapters']:
                        rec['status'] = 'warn'
                except (UnicodeError, SyntaxError, ValueError) as error:
                    rec.update(status='error', warnings=[str(error)])
            records.append(rec)
        return {'mode': mode, 'files': records,
                'integrity': 'not established without an operation snapshot'}
    registry = load_registry(root)
    generation = registry['generation']
    # Reserve explicit owner names before allocating any new file identity.
    for path in discover(root):
        if path.suffix != '.py':
            try:
                sections = extract_sections(path.read_bytes().decode('utf-8'))
            except UnicodeError:
                continue
            for section in sections:
                reference = section['identity']
                if reference and reference.startswith('@file/'):
                    owner = reference.split('#', 1)[0]
                    registry['elements'].setdefault(owner, {'kind': 'file', 'state': 'present',
                                                           'path': path.relative_to(root).as_posix()})
            continue
        try:
            _, comments = inspect_source(path.read_bytes().decode('utf-8'))
        except (UnicodeError, SyntaxError, ValueError):
            continue
        for comment in comments.values():
            match = re.fullmatch(r'#\s*anchor_ref:\s*(@file/\S+)#section/\S+\s*', comment)
            if match and match[1] not in registry['elements']:
                registry['elements'][match[1]] = {'kind': 'file', 'state': 'present',
                                                'path': path.relative_to(root).as_posix()}
    records, candidates = [], []
    for path in discover(root):
        relative = path.relative_to(root).as_posix()
        rec, candidate = propose(path, mode, registry, relative)
        records.append(rec)
        if candidate is not None:
            candidates.append((path, rec, candidate))
    declared = {}
    for path in discover(root):
        if path.suffix != '.py':
            continue
        try:
            _, comments = inspect_source(path.read_bytes().decode('utf-8'))
        except (UnicodeError, SyntaxError, ValueError):
            continue
        for comment in comments.values():
            match = re.fullmatch(r'#\s*anchor_ref:\s*(@file/\S+#section/\S+)\s*', comment)
            if match:
                declared.setdefault(match[1], []).append(path.relative_to(root).as_posix())
    duplicate_paths = {path for paths in declared.values() if len(paths) > 1 for path in paths}
    owners = {}
    for ref, paths in declared.items():
        owners.setdefault(ref.split('#')[0], set()).update(paths)
    duplicate_paths.update(path for paths in owners.values() if len(paths) > 1 for path in paths)
    for rec in records:
        if rec['path'] in duplicate_paths:
            rec.update(status='pending', reasons=['duplicate explicit identity'])
    candidates = [item for item in candidates if item[1]['status'] == 'ready']
    result = {'mode': mode, 'applied': False, 'files': records,
              'counts': {status: sum(r['status'] == status for r in records)
                         for status in ('ready', 'unchanged', 'existing', 'pending')}}
    if not apply:
        return result
    if not candidates:
        if tracking:
            with registry_lock(root):
                _scan_locked(root, load_registry(root))
            result['tracking_initialized'] = True
        return result
    with operation_lock(root), (registry_lock(root) if tracking or
                               (root / '.task/tracking/registry.json').exists() else nullcontext()):
        if load_registry(root)['generation'] != generation:
            raise ValueError('structural registry changed since proposal')
        snapshot = root / '.agent-cache/diagram' / uuid.uuid4().hex
        snapshot.mkdir(parents=True)
        originals = []
        for path, rec, candidate in candidates:
            raw = path.read_bytes()
            if (digest(raw) != rec['before_sha256'] or path.is_symlink()
                    or not path.resolve().is_relative_to(root)):
                raise ValueError(f'source changed since proposal: {rec["path"]}')
            backup = snapshot / rec['path']
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(raw)
            originals.append((path, raw, candidate))
        (snapshot / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                                               encoding='utf-8', newline='\n')
        written = []
        try:
            for path, original, candidate in originals:
                if (path.is_symlink() or not path.resolve().is_relative_to(root)
                        or path.read_bytes() != original):
                    raise ValueError(f'source changed before publication: {path}')
                temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
                try:
                    temporary.write_bytes(candidate)
                    os.chmod(temporary, path.stat().st_mode)
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
                written.append((path, original, candidate))
                if path.read_bytes() != candidate:
                    raise ValueError(f'publication verification failed: {path}')
            result['indexes'] = [code_map.map_one(path, None) for path, _, _ in originals]
            if tracking or (root / '.task/tracking/registry.json').exists():
                _scan_locked(root, load_registry(root))
        except Exception:
            for path, original, candidate in reversed(written):
                if not path.is_symlink() and path.read_bytes() == candidate:
                    path.write_bytes(original)
            raise
        result.update(applied=True, snapshot=str(snapshot), integrity='tokens and AST preserved')
        (snapshot / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                                             encoding='utf-8', newline='\n')
    return result


# ── § 5 — ENTRY — Expose preview application and verification commands ──

def main() -> int:
    """Expose independent dry-run, explicit application and coverage inspection."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['adopt', 'upgrade', 'verify'])
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--tracking', action='store_true', help='initialize optional structural tracking')
    parser.add_argument('--snapshot', type=Path, help='verify against an operation snapshot')
    args = parser.parse_args()
    if args.mode == 'verify' and (args.apply or args.tracking):
        parser.error('verify is read-only')
    if args.snapshot and args.mode != 'verify':
        parser.error('--snapshot requires verify')
    try:
        result = (verify_snapshot(args.root.resolve(strict=True), args.snapshot) if args.snapshot
                  else run(args.root, args.mode, args.apply, args.tracking))
    except (OSError, ValueError, SyntaxError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.mode == 'verify':
        if args.snapshot:
            return int(not result['integrity'])
        return int(any(r['status'] not in ('ok', 'skip') for r in result['files']))
    return int(bool(result['counts']['pending']))


if __name__ == '__main__':
    raise SystemExit(main())
