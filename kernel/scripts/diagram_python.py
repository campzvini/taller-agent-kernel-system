# SPDX-License-Identifier: LicenseRef-Taller-Personal-Noncommercial-1.0
# ────────────────────────────────────────────
# TASK 2.1 — diagram_python.py
# § - Identify safe Python boundaries and verify executable equivalence · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

"""Conservative Python adapter for structural comment transformations."""
from __future__ import annotations

import ast
import io
import re
import tokenize


# ── § 1 — PARSING — Locate real comments and module declarations ──

def inspect_source(text: str) -> tuple[ast.Module, dict[int, str]]:
    """Parse Python and locate full-line comments outside strings."""
    tree = ast.parse(text)
    comments = {}
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT and not token.line[:token.start[1]].strip():
            comments[token.start[0]] = token.string
    return tree, comments


# ── § 2 — INTEGRITY — Compare executable tokens and syntax trees ──

def equivalent(before: str, after: str) -> bool:
    """Require identical executable tokens, AST and non-diagram comments."""
    def signature(text):
        ignored = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER,
                   tokenize.ENCODING}
        return [(t.type, t.string) for t in tokenize.generate_tokens(io.StringIO(text).readline)
                if t.type not in ignored]
    return (signature(before) == signature(after)
            and ast.dump(ast.parse(before), include_attributes=False)
            == ast.dump(ast.parse(after), include_attributes=False))


# ── § 3 — BOUNDARIES — Keep decorators attached and preserve source preambles ──

def symbols(tree: ast.Module) -> list[dict]:
    """Return module-level declarations with decorators attached to their symbol."""
    result = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            line = min([node.lineno] + [item.lineno for item in node.decorator_list])
            result.append({'line': line, 'name': node.name,
                           'kind': 'class' if isinstance(node, ast.ClassDef) else 'function',
                           'description': (ast.get_docstring(node) or '').split('\n')[0].strip()})
    return result


def header_position(lines: list[str]) -> int:
    """Keep shebang and Python encoding declarations at their original positions."""
    position = 1 if lines and lines[0].startswith('#!') else 0
    for index, line in enumerate(lines[:2]):
        if re.match(r'^\s*#.*?coding[:=]\s*[-\w.]+', line):
            position = index + 1
    return position
