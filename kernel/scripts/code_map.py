# ────────────────────────────────────────────
# CODEX-ENV 3.0 — code_map.py
# § - Build structural and semantic context indexes without exposing source bodies · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ── § 1 — CONFIG — Define anchors vocabularies and eligible project files ──

SECTION = "§"   # § source code
PILCROW = "¶"   # ¶ TDSL documents and agent-facing markdown
CONTEXT = "※"   # typed semantic source comment
PROVISIONAL = "◇"

DOC_SUFFIXES = {".md", ".tdsl", ".txt", ".rst"}
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html",
    ".java", ".js", ".jsx", ".kt", ".lua", ".mjs", ".php", ".ps1",
    ".py", ".rb", ".rs", ".scss", ".sh", ".sql", ".swift", ".svg",
    ".ts", ".tsx", ".xml",
}
MAP_SUFFIXES = DOC_SUFFIXES | SOURCE_SUFFIXES
SKIP_DIRS = {
    ".agent-cache", ".codex", ".git", ".hg", ".next", ".svn", ".tricot", ".venv",
    "__pycache__", "backups", "build", "cache", "coverage", "dist", "logs", "memories",
    "node_modules", "out", "sessions", "target", "vendor", "vendor_imports", "venv", "venvs",
}
CONTEXT_KINDS = {
    "assumption", "boundary", "decision", "effect", "invariant", "rationale",
    "relation", "risk",
}

# `<anchor> - purpose` is the file header: descriptive, deliberately unnumbered.
HEADER_RE = re.compile(r"^\s*[-—:]\s*(?P<title>.+?)\s*$")
# `<anchor> 1 — TITLE` or `<anchor> 1.2 — Title` is a chapter.
CHAPTER_RE = re.compile(r"^\s*(?P<number>\d+(?:\.\d+)*)\s*[-—:]\s*(?P<title>.*?)\s*$")
CONTEXT_RE = re.compile(
    r"^\s*(?P<kind>[a-z][a-z-]*)\s*[-—:]\s*(?P<statement>.+?)\s*$")

# O banner de código fecha a linha com decoração (`── § 1 — NOME ──`). Ela não é
# título; deixá-la entrar polui o índice e carrega glifos que um console legado
# não sabe imprimir.
TRAILING_DECOR = re.compile(r"[\s─━═\-—=*/#<>!]+$")
CONTEXT_TRAILING_DECOR = re.compile(r"(?:\s+─+|\s*\*/|\s*-->)?\s*$")

# A chapter marker opens its line. Everything that may legally precede it is
# indentation, a comment delimiter, or box drawing. Anything else means the
# anchor is being cited inside prose (`see tdsl-language ¶6`), not declared.
LEAD_CHARS = frozenset(" \t/#-<!*;%\"'|=─━═")

OK, WARN = "OK", "WARN"


def anchor_for(path: Path, override: str | None) -> str:
    if override:
        return SECTION if override == "section" else PILCROW
    return PILCROW if path.suffix.lower() in DOC_SUFFIXES else SECTION


# ── § 2 — PARSING — Extract structural ranges and typed semantic comments ──


def opens_line(line: str, anchor: str) -> bool:
    """True when the anchor declares a marker rather than being cited in prose."""
    index = 0
    while index < len(line) and line[index] in LEAD_CHARS:
        index += 1
    return index < len(line) and line[index] == anchor


def parse_entries(path: Path, anchor: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int]:
    header: dict[str, Any] | None = None
    chapters: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for lineno, line in enumerate(handle, start=1):
            total = lineno
            marker = PROVISIONAL if PROVISIONAL in line and opens_line(line, PROVISIONAL) else anchor
            if marker not in line or not opens_line(line, marker):
                continue
            tail = line[line.index(marker) + 1:].rstrip("\n")
            chapter = CHAPTER_RE.match(tail)
            if chapter:
                chapters.append({
                    "line": lineno,
                    "number": chapter.group("number"),
                    "title": TRAILING_DECOR.sub("", chapter.group("title")),
                    "level": chapter.group("number").count(".") + 1,
                    "implementation_state": "provisional" if marker == PROVISIONAL else "implemented_marker",
                })
                continue
            header_match = HEADER_RE.match(tail)
            if header_match and header is None:
                header = {"line": lineno,
                          "title": TRAILING_DECOR.sub("", header_match.group("title"))}
    return header, chapters, total


def attach_ranges(chapters: list[dict[str, Any]], total: int) -> None:
    """Give each chapter the exact Read(offset, limit) pair that covers it."""
    for index, chapter in enumerate(chapters):
        end = chapters[index + 1]["line"] - 1 if index + 1 < len(chapters) else total
        chapter["offset"] = chapter["line"]
        chapter["limit"] = max(1, end - chapter["line"] + 1)


def parse_context(path: Path, anchor: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract deliberate semantic comments and bind each to its current chapter."""
    if anchor != SECTION:
        return [], []
    annotations: list[dict[str, Any]] = []
    issues: list[str] = []
    current: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for lineno, line in enumerate(handle, start=1):
            if SECTION in line and opens_line(line, SECTION):
                tail = line[line.index(SECTION) + 1:].rstrip("\n")
                chapter = CHAPTER_RE.match(tail)
                if chapter:
                    current = {
                        "number": chapter.group("number"),
                        "title": TRAILING_DECOR.sub("", chapter.group("title")),
                    }
            if CONTEXT not in line or not opens_line(line, CONTEXT):
                continue
            tail = line[line.index(CONTEXT) + 1:].rstrip("\n")
            match = CONTEXT_RE.match(tail)
            if not match:
                issues.append(
                    f"Linha {lineno}: comentário contextual inválido; use "
                    f"`{CONTEXT} <tipo> — <afirmação>`."
                )
                continue
            kind = match.group("kind")
            if kind not in CONTEXT_KINDS:
                issues.append(
                    f"Linha {lineno}: tipo contextual `{kind}` não pertence ao vocabulário fechado."
                )
                continue
            if current is None:
                issues.append(
                    f"Linha {lineno}: comentário contextual não pertence a um capítulo `§`."
                )
            annotations.append({
                "line": lineno,
                "kind": kind,
                "statement": CONTEXT_TRAILING_DECOR.sub("", match.group("statement")),
                "chapter": current,
            })
    return annotations, issues


# ── § 3 — VALIDATION — Report structural defects without inventing anatomy ──


def has_frontmatter_purpose(path: Path) -> bool:
    """A SKILL.md states its purpose in the frontmatter `description`.

    Demanding a `¶ - <purpose>` line on top of it would state one proposition
    in two places, which is the duplication this whole convention exists to
    avoid. The frontmatter IS the header for such a file.
    """
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            if handle.readline().rstrip("\n") != "---":
                return False
            for _ in range(20):
                line = handle.readline()
                if not line or line.rstrip("\n") == "---":
                    return False
                if line.startswith("description:") and line[12:].strip():
                    return True
    except OSError:
        return False
    return False


def detect_issues(header: dict[str, Any] | None, chapters: list[dict[str, Any]],
                  anchor: str, path: Path) -> list[str]:
    issues: list[str] = []
    if header is None and not has_frontmatter_purpose(path):
        issues.append(f"Header ausente: falta a linha `{anchor} - <propósito>`.")
    elif header is not None and not header["title"]:
        issues.append(f"Linha {header['line']}: header sem propósito.")
    elif anchor == SECTION and header is not None and " · " not in header["title"]:
        issues.append(
            f"Linha {header['line']}: header de código deve declarar propósito e linguagem com ` · `."
        )

    seen: dict[str, int] = {}
    for chapter in chapters:
        if not chapter["title"]:
            issues.append(f"Linha {chapter['line']}: capítulo {chapter['number']} sem título.")
        elif anchor == SECTION and " — " not in chapter["title"]:
            issues.append(
                f"Linha {chapter['line']}: capítulo deve declarar domínio e responsabilidade "
                "observável separados por ` — `."
            )
        first = seen.get(chapter["number"])
        if first is not None:
            issues.append(
                f"Linha {chapter['line']}: numeração `{chapter['number']}` "
                f"duplicada (primeira em {first}).")
        else:
            seen[chapter["number"]] = chapter["line"]

    previous = 0
    for chapter in (c for c in chapters if c["level"] == 1):
        current = int(chapter["number"])
        if current != previous + 1:
            issues.append(
                f"Linha {chapter['line']}: capítulo {current} quebra a sequência "
                f"(esperado {previous + 1}).")
        previous = current
    return issues


# ── § 4 — RENDER — Emit file project and semantic context projections ──


def render_markdown(target: Path, anchor: str, header: dict[str, Any] | None,
                    chapters: list[dict[str, Any]], issues: list[str], status: str) -> str:
    lines = [
        f"# Map — {target.name}",
        "",
        f"Arquivo: `{target}`",
        f"Âncora: `{anchor}`",
        f"Status: {status}",
        "",
    ]
    if header:
        lines += [f"Propósito: {header['title']}", ""]
    lines.append("## Índice")
    if chapters:
        lines += ["| Cap. | Título | Read(offset, limit) |", "|---|---|---|"]
        for chapter in chapters:
            indent = "&nbsp;&nbsp;" * (chapter["level"] - 1)
            lines.append(
                f"| {indent}{chapter['number']} | {chapter['title'] or '—'} | "
                f"`offset={chapter['offset']}, limit={chapter['limit']}` |")
    else:
        lines.append(f"- Nenhum capítulo `{anchor}` encontrado.")
    lines += ["", "## Inconsistências"]
    lines += [f"- {issue}" for issue in issues] or ["- Nenhuma."]
    lines.append("")
    return "\n".join(lines)


def render_project_markdown(root: Path, results: list[dict[str, Any]]) -> str:
    """Render the whole-project structural index as initial context, never truth."""
    mapped = [result for result in results if result["header"] or result["chapters"]]
    lines = [
        "# Project Code Map",
        "",
        f"Root: `{root}`",
        "Authority: initial structural context only; source code remains the source of truth.",
        f"Coverage: {len(mapped)}/{len(results)} eligible files carry an index.",
        "",
        "## Structural index",
        "",
    ]
    if not mapped:
        lines += ["No indexed files found.", ""]
    for result in mapped:
        relative = Path(result["file"]).relative_to(root).as_posix()
        purpose = result["header"]["title"] if result["header"] else "header missing"
        lines.append(f"`{relative}` — {purpose}")
        for chapter in result["chapters"]:
            indent = "  " * chapter["level"]
            lines.append(
                f"{indent}{result['anchor']} {chapter['number']} — {chapter['title']} "
                f"[offset={chapter['offset']}, limit={chapter['limit']}]"
            )
        lines.append("")
    unmapped = [Path(result["file"]).relative_to(root).as_posix()
                for result in results if not result["header"] and not result["chapters"]]
    lines += ["## Coverage gaps", ""]
    lines += [f"- `{name}`" for name in unmapped] or ["- None."]
    lines.append("")
    return "\n".join(lines)


def render_context_markdown(root: Path, results: list[dict[str, Any]]) -> str:
    """Render only typed semantic comments; ordinary comments remain source-local."""
    annotated = [result for result in results if result.get("context")]
    lines = [
        "# Project Context Map",
        "",
        f"Root: `{root}`",
        "Authority: declared preliminary context; verify every behavioral claim in source code.",
        f"Coverage: {sum(len(result.get('context', [])) for result in results)} annotations "
        f"across {len(annotated)} file(s).",
        "",
    ]
    if not annotated:
        return "\n".join(lines + ["No typed context comments found.", ""])
    for result in annotated:
        relative = Path(result["file"]).relative_to(root).as_posix()
        lines.append(f"`{relative}`")
        for item in result["context"]:
            chapter = item.get("chapter")
            owner = f"{SECTION} {chapter['number']}" if chapter else "file"
            lines.append(
                f"  {owner} · line {item['line']} · {CONTEXT} {item['kind']} — "
                f"{item['statement']}"
            )
        lines.append("")
    return "\n".join(lines)


def discover_project(root: Path) -> list[Path]:
    """Return eligible files deterministically while pruning generated and external trees."""
    found: list[Path] = []
    for current, directories, filenames in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS)
        base = Path(current)
        for name in sorted(filenames):
            path = base / name
            if path.suffix.lower() in MAP_SUFFIXES:
                found.append(path)
    return sorted(found, key=lambda item: item.relative_to(root).as_posix().lower())


def find_root(start: Path) -> Path:
    for parent in [start.resolve(), *start.resolve().parents]:
        if (parent / ".git").exists():
            return parent
    return start.resolve()


# ── § 5 — ENTRY — Route file and project modes to cache artifacts ──


def map_one(target: Path, override: str | None, include_context: bool = False) -> dict[str, Any]:
    anchor = anchor_for(target, override)
    header, chapters, total = parse_entries(target, anchor)
    attach_ranges(chapters, total)
    issues = detect_issues(header, chapters, anchor, target)
    context, context_issues = parse_context(target, anchor) if include_context else ([], [])
    issues.extend(context_issues)
    status = OK if chapters and not issues else WARN
    return {
        "status": status.lower(),
        "file": str(target),
        "anchor": anchor,
        "lines": total,
        "header": header,
        "chapters": chapters,
        "context": context,
        "issues": issues,
    }


def main() -> int:
    # Um console legado não pode derrubar a ferramenta de índice.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(
        description="Build structural and semantic context indexes without exposing source bodies")
    parser.add_argument("targets", nargs="*", help="files to map")
    parser.add_argument("--project", nargs="?", const=".", metavar="ROOT",
                        help="recursively map every eligible file below ROOT")
    parser.add_argument("--context", action="store_true",
                        help=f"also extract typed `{CONTEXT}` source comments")
    parser.add_argument("--anchor", choices=["section", "pilcrow"], default=None,
                        help="force an anchor instead of deriving it from the suffix")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--query", help="resolve an identity from structural indexes")
    args = parser.parse_args()
    if args.query:
        from structure_tracker import query_registry
        root = Path(args.project or ".").resolve()
        print(json.dumps(query_registry(root, args.query), ensure_ascii=False, indent=2))
        return 0

    if args.project is not None and args.targets:
        parser.error("use file targets or --project, not both")
    if args.project is None and not args.targets:
        parser.error("provide file targets or --project [ROOT]")

    project_root = Path(args.project).resolve() if args.project is not None else None
    if project_root is not None and not project_root.is_dir():
        print(f"ERRO: não é diretório: {project_root}", file=sys.stderr)
        return 3
    raw_targets = discover_project(project_root) if project_root else [Path(raw) for raw in args.targets]

    results: list[dict[str, Any]] = []
    worst = 0
    for raw in raw_targets:
        target = Path(raw)
        if not target.is_file():
            print(f"ERRO: não é arquivo: {raw}", file=sys.stderr)
            return 3
        result = map_one(target, args.anchor, include_context=args.context)
        results.append(result)
        if result["status"] == "warn":
            worst = 1

    root = project_root or find_root(Path.cwd())
    cache = root / ".agent-cache"
    try:
        cache.mkdir(exist_ok=True)
    except OSError as error:
        print(f"ERRO: não foi possível criar .agent-cache/: {error}", file=sys.stderr)
        return 3

    for result in results:
        target = Path(result["file"])
        report = render_markdown(target, result["anchor"], result["header"],
                                 result["chapters"], result["issues"],
                                 result["status"].upper())
        # o stem sozinho colide (dezoito SKILL.md viram um relatório só);
        # o caminho inteiro, achatado, é único por construção
        slug = re.sub(r"[^A-Za-z0-9]+", "-", str(target)).strip("-").lower()[-80:]
        (cache / f"map-{slug}.md").write_text(report, encoding="utf-8", newline="\n")

    payload = results[0] if len(results) == 1 else {"maps": results}
    (cache / "map.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    if project_root is not None:
        if (project_root / ".task/project.tdsl").is_file():
            from structure_tracker import scan_project
            registry = scan_project(project_root)
            for result in results:
                relative = Path(result["file"]).relative_to(project_root).as_posix()
                result["identities"] = [ref for ref, item in registry["elements"].items()
                                        if item["path"] == relative and item["state"] == "present"]
        project_payload = {
            "schema": "taller.project-code-map/1",
            "authority": "initial_context_only",
            "source_of_truth": "source_code",
            "root": str(project_root),
            "maps": results,
        }
        (cache / "project-map.json").write_text(
            json.dumps(project_payload, indent=2, ensure_ascii=False),
            encoding="utf-8", newline="\n")
        (cache / "project-map.md").write_text(
            render_project_markdown(project_root, results), encoding="utf-8", newline="\n")
        if args.context:
            context_payload = {
                "schema": "taller.project-context-map/1",
                "authority": "declared_preliminary_context",
                "source_of_truth": "source_code",
                "root": str(project_root),
                "files": [
                    {"file": str(Path(result["file"]).relative_to(project_root)),
                     "context": result["context"]}
                    for result in results if result["context"]
                ],
            }
            (cache / "context-map.json").write_text(
                json.dumps(context_payload, indent=2, ensure_ascii=False),
                encoding="utf-8", newline="\n")
            (cache / "context-map.md").write_text(
                render_context_markdown(project_root, results), encoding="utf-8", newline="\n")

    if args.json:
        if project_root is not None:
            payload = project_payload
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif project_root is not None:
        mapped = sum(1 for result in results if result["header"] or result["chapters"])
        annotations = sum(len(result["context"]) for result in results)
        print(f"project-map: {mapped}/{len(results)} arquivos indexados")
        if args.context:
            print(f"context-map: {annotations} comentários contextuais tipados")
        print("Autoridade: contexto inicial; código-fonte permanece a fonte de verdade")
        print(f"Relatórios: {cache / 'project-map.md'}"
              + (f", {cache / 'context-map.md'}" if args.context else ""))
    else:
        for result in results:
            target = Path(result["file"])
            # SKILL.md, mod.rs, __init__.py: o nome sozinho não identifica nada
            name = f"{target.parent.name}/{target.name}" if target.name in {
                "SKILL.md", "mod.rs", "__init__.py", "index.ts", "index.js"
            } else target.name
            print(f"{name}: {result['status'].upper()} — anchor {result['anchor']}, "
                  f"{len(result['chapters'])} capítulos, {len(result['issues'])} inconsistências")
            for issue in result["issues"]:
                print(f"    {issue}")
        # When a single target is mapped and --json is absent, print the chapter table
        if len(results) == 1:
            result = results[0]
            if result["chapters"]:
                print()
                for chapter in result["chapters"]:
                    print(f"  {chapter['number']}  {chapter['title']}  offset={chapter['offset']} limit={chapter['limit']}")
        print(f"Relatórios: {cache.relative_to(root) if cache.is_relative_to(root) else cache}/map-*.md")
    return 0 if project_root is not None else worst


if __name__ == "__main__":
    sys.exit(main())
