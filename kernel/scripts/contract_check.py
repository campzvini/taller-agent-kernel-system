# ────────────────────────────────────────────
# TASK 2.0 — contract_check.py
# § - Validate bundled TDSL field contracts without policy inference · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── § 1 — SYNTAX — Parse fields and opaque text without losing duplicates ──
SCHEMAS = Path(__file__).resolve().parents[1] / "grammar" / "schemas"
LEGACY = {f"{family}@1" for family in ("constitution", "spec", "plan", "tasks", "analysis")}
FIELD = re.compile(r"^([a-z][a-z0-9_]*)(?: ([A-Za-z0-9][A-Za-z0-9_.~-]*))?(:)(?: (.*))?$")
REF = re.compile(r"^@([a-z][a-z0-9_-]*)/[A-Za-z0-9][A-Za-z0-9_.~/-]*(?:#([a-z][a-z0-9_-]*)/[A-Za-z0-9][A-Za-z0-9_.~-]*)?$")


@dataclass
class Node:
    """One lexical field, preserving source representation and repeated labels."""
    name: str
    value: str
    line: int
    label: str | None = None
    opaque: bool = False
    children: list[Node] = field(default_factory=list)


def parse_document(source: str) -> tuple[list[Node], list[str]]:
    """Parse a bounded indentation tree; ln bodies are never interpreted."""
    roots: list[Node] = []
    stack: list[tuple[int, list[Node]]] = [(-2, roots)]
    errors: list[str] = []
    lines = source.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        number = index + 1
        index += 1
        text = line.lstrip(" ")
        indent = len(line) - len(text)
        if not text or text.startswith("#") or text.startswith("¶"):
            continue
        if "\t" in line or indent % 2:
            errors.append(f"line {number}: invalid indentation")
            continue
        opaque = re.fullmatch(r"([a-z][a-z0-9_]*) ln: \|", text)
        match = FIELD.fullmatch(text)
        if not opaque and not match:
            errors.append(f"line {number}: malformed field")
            continue
        if opaque:
            node = Node(opaque.group(1), "", number, opaque=True)
            body: list[str] = []
            while index < len(lines):
                following = lines[index]
                if following.strip() and len(following) - len(following.lstrip(" ")) <= indent:
                    break
                if following.strip() and not following.startswith(" " * (indent + 2)):
                    errors.append(f"line {index + 1}: opaque body requires two-space nesting")
                body.append(following[indent + 2:] if following.strip() else "")
                index += 1
            node.value = "\n".join(body)
        else:
            assert match is not None
            node = Node(match.group(1), match.group(4) or "", number, match.group(2))
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        if indent != stack[-1][0] + 2:
            errors.append(f"line {number}: unexpected indentation")
        stack[-1][1].append(node)
        if not node.value and not node.opaque:
            stack.append((indent, node.children))
    return roots, errors


def scalar(value: str) -> str:
    """Decode a quoted string while retaining reserved bare value states."""
    if value.startswith('"'):
        decoded = json.loads(value)
        if not isinstance(decoded, str):
            raise ValueError("quoted scalar must be a string")
        return decoded
    if '"' in value or "#" in value and not value.startswith("@"):
        raise ValueError("invalid quoting or inline comment")
    return value


def collection(value: str) -> list[str]:
    """Read canonical whitespace collections, including quoted string members."""
    if not (value.startswith("[") and value.endswith("]")):
        raise ValueError("expected bracketed collection")
    body = value[1:-1]
    if re.search(r',(?=(?:[^"\\]*"[^"\\]*")*[^"\\]*$)', body):
        raise ValueError("commas are not canonical collection separators")
    lexer = shlex.shlex(body, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)

# ── § 2 — TYPES — Validate closed fields objects collections and references ──
class Validator:
    """Validate schema declarations without evaluating normative policy prose."""
    def __init__(self, schema: dict[str, Any], types: dict[str, Any]):
        self.schema = schema
        self.types = types
        self.errors: list[str] = []

    def fail(self, location: str, message: str) -> None:
        self.errors.append(f"{location}: {message}")

    def fields(self, nodes: list[Node], specs: list[dict[str, Any]], location: str) -> None:
        declared = {s["name"]: s for s in specs}
        seen: set[str] = set()
        for node in nodes:
            target = f"{location}.{node.name}"
            if node.label is not None:
                self.fail(target, "unexpected labeled field")
            if node.name in seen:
                self.fail(target, "duplicate field")
            seen.add(node.name)
            if node.name not in declared:
                self.fail(target, "unknown field")
            else:
                self.value(node, declared[node.name], target)
        for name, spec in declared.items():
            if spec.get("required") and name not in seen:
                self.fail(location, f"missing required field {name}")

    def reference(self, value: str, spec: dict[str, Any], location: str) -> None:
        match = REF.fullmatch(value)
        if not match:
            self.fail(location, "invalid typed reference")
            return
        contract = spec.get("references", {})
        if contract.get("namespaces") and match.group(1) not in contract["namespaces"]:
            self.fail(location, "reference namespace is not allowed")
        if contract.get("part_kinds") and match.group(2) not in contract["part_kinds"]:
            self.fail(location, "reference part kind is not allowed")

    def value(self, node: Node, spec: dict[str, Any], location: str) -> None:
        kind = spec["type"]
        raw = node.value
        if raw in {"unknown", "empty"}:
            if raw in spec.get("allowed_value_states", []):
                return
            # Enums explicitly containing unknown are ordinary enum values.
            if raw not in spec.get("enum", []):
                self.fail(location, f"value state {raw} is not allowed")
                return
        if kind.startswith("accumulated:"):
            key = kind.partition(":")[2]
            block = next((b for b in self.schema.get("accumulated_blocks", []) if b["key"] == key and b["container"] == node.name), None)
            if block is None:
                self.fail(location, f"missing accumulated contract {key}")
                return
            if raw not in {"", "[]"} or node.opaque:
                self.fail(location, "expected accumulated block or []")
            if len(node.children) < block.get("min_items", 0):
                self.fail(location, f"requires at least {block['min_items']} items")
            seen: set[str] = set()
            for item in node.children:
                if item.name != key or not item.label or item.value or item.opaque:
                    self.fail(location, "invalid accumulated item")
                    continue
                if item.label in seen:
                    self.fail(location, f"duplicate item {item.label}")
                seen.add(item.label)
                self.fields(item.children, block["fields"], f"{location}.{item.label}")
            return
        definition = self.types.get(kind, {})
        if kind.startswith("object:") or definition.get("kind") == "object":
            if node.value or node.opaque:
                self.fail(location, "expected object block")
                return
            fields = [{"name": k, **v} for k, v in definition.get("fields", {}).items()]
            if not definition:
                self.fail(location, f"unknown object contract {kind}")
            self.fields(node.children, fields, location)
            return
        if kind == "ln":
            if not node.opaque:
                self.fail(location, "expected opaque ln field")
            elif not raw.strip():
                self.fail(location, "opaque text must not be empty")
            return
        if node.children or node.opaque:
            self.fail(location, "expected scalar or collection")
            return
        if kind.endswith("_list") or definition.get("kind") == "collection":
            try:
                values = collection(raw)
            except ValueError as exc:
                self.fail(location, str(exc))
                return
            if spec.get("collection_semantics") == "set" and len(set(values)) != len(values):
                self.fail(location, "duplicate set member")
            cardinality = spec.get("references", {}).get("cardinality")
            exact = {"one": 1, "two": 2}.get(cardinality)
            minimum = {"one_or_more": 1, "two_or_more": 2}.get(cardinality, 0)
            if exact is not None and len(values) != exact or len(values) < minimum:
                self.fail(location, f"invalid cardinality {cardinality}")
            for item in values:
                if kind == "reference_list":
                    self.reference(item, spec, location)
                elif kind == "enum_list" and item not in spec.get("enum", []):
                    self.fail(location, f"invalid enum value {item}")
                elif kind not in {"string_list", "enum_list"}:
                    pattern = self.types.get(definition.get("item", ""), {}).get("pattern")
                    if pattern and not re.fullmatch(pattern, item):
                        self.fail(location, "invalid collection member")
            return
        if raw.startswith("["):
            self.fail(location, "expected scalar, found collection")
            return
        try:
            value = scalar(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            self.fail(location, str(exc))
            return
        if not raw:
            self.fail(location, "empty scalar")
        if kind == "reference":
            self.reference(value, spec, location)
        elif kind == "enum" or definition.get("target") == "enum":
            if value not in spec.get("enum", definition.get("enum", [])):
                self.fail(location, f"invalid enum value {value}")
        elif kind == "boolean":
            if raw not in {"true", "false"}:
                self.fail(location, "expected bare boolean")
        elif definition.get("pattern"):
            if not re.fullmatch(definition["pattern"], value):
                self.fail(location, f"invalid {kind}")
            if definition.get("source") == ["bare"] and raw.startswith('"'):
                self.fail(location, f"{kind} must be bare")
        elif kind != "string":
            self.fail(location, f"unsupported contract type {kind}")

# ── § 3 — CONTRACTS — Bind headers to exact registered schema bytes ──
def check_contract(path: Path) -> list[tuple[str, str]]:
    """Return deterministic fail findings for new bundled TDSL contracts."""
    path = Path(path)
    try:
        raw = path.read_bytes()
        source = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        return [("fail", f"contract: {exc}")]
    dialect_match = re.search(r"^tdsl: ([^\n\r]+)\r?$", source, re.MULTILINE)
    dialect = dialect_match.group(1) if dialect_match else ""
    if dialect in LEGACY:
        return []
    issues: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        issues.append("encoding must be UTF-8 without BOM, LF, final newline")
    for number, line in enumerate(source.splitlines(), 1):
        if "\t" in line or line.rstrip() != line:
            issues.append(f"line {number}: tab or trailing whitespace")
    try:
        registry = json.loads((SCHEMAS / "registry.json").read_text(encoding="utf-8"))
        entry = next((e for e in registry["entries"] if e["dialect"] == dialect), None)
        if entry is None:
            return [("fail", f"contract: unregistered dialect {dialect or 'missing'}")]
        schema_path = SCHEMAS / Path(entry["path"]).name
        schema_bytes = schema_path.read_bytes()
        if entry["schema_revision"] != "sha256:" + hashlib.sha256(schema_bytes).hexdigest():
            issues.append("registry schema pin does not match bundled bytes")
        schema = json.loads(schema_bytes)
        if schema.get("representation") == "json":
            return [("fail", "contract: JSON registry is not a TDSL document")]
        types = json.loads((SCHEMAS / "core-types@1.schema.json").read_text(encoding="utf-8"))["type_definitions"]
    except (OSError, ValueError, KeyError) as exc:
        return [("fail", f"contract: cannot load bundled schema: {exc}")]
    nodes, parse_errors = parse_document(source)
    issues.extend(parse_errors)
    names = [n.name for n in nodes[:6]]
    if names != ["tdsl", "schema_revision", "id", "version", "status", "purpose"]:
        issues.append("identity header must use canonical six-field order")
    revisions = [n.value for n in nodes if n.name == "schema_revision"]
    if revisions != [entry["schema_revision"]]:
        issues.append("schema_revision must match exact registered pin")
    validator = Validator(schema, types)
    validator.fields(nodes, schema["fields"], dialect)
    issues.extend(validator.errors)
    return [("fail", "contract: " + issue) for issue in issues]

# ── § 4 — ENTRY — Report mechanical contract findings as JSON ──
def main() -> int:
    parser = argparse.ArgumentParser(description="validate a new bundled TDSL contract")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    findings = check_contract(args.path)
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
