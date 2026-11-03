# ────────────────────────────────────────────
# CODEX-ENV 1.0 — diagram_check.py
# § - Diagram validator, renderer and code-safety guard for Taller source files · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ── § 1 — CONVENTION — annex_b diagramming constants ──

RULE_WIDTH = 44
RULE = "─" * RULE_WIDTH
def _signature() -> tuple[str, str]:
    """Header signature lines from <KERNEL_HOME>/kernel.config.json; empty strings omit the line."""
    import json as _json
    cfg_path = Path(__file__).resolve().parent.parent / "kernel.config.json"
    try:
        sig = _json.loads(cfg_path.read_text(encoding="utf-8")).get("signature", {})
    except (OSError, ValueError):
        sig = {}
    return sig.get("author", ""), sig.get("tagline", "VAI CORINTHIANS!")


YEAR, SIGNATURE = _signature()

# Line-comment delimiters (single source of truth for annex_b).
LINE_DELIMS: dict[str, set[str]] = {
    "//": {
        ".rs", ".c", ".h", ".cpp", ".cxx", ".cc", ".hpp", ".hh",
        ".cs", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        ".go", ".java", ".kt", ".kts", ".swift",
    },
    "#": {".py", ".rb", ".sh", ".bash", ".zsh", ".ps1", ".psm1"},
    "--": {".sql", ".lua", ".hs"},
}

# Block-comment languages: banners are rendered line-by-line wrapped so the
# guard can recognize each banner line as a self-closed comment safely.
BLOCK_DELIMS: dict[tuple[str, str], set[str]] = {
    ("/*", "*/"): {".css", ".scss"},
    ("<!--", "-->"): {".html", ".htm", ".xml", ".svg"},
}

# annex_b skip list — never carry headers/chapters.
SKIP_EXT: set[str] = {".json", ".yaml", ".yml", ".toml", ".md", ".env", ".lock"}

SPECIAL_FILENAMES: dict[str, str] = {"Makefile": "#", "Dockerfile": "#"}

LANG_LABEL: dict[str, str] = {
    ".rs": "Rust", ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++",
    ".cs": "C#", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".go": "Go", ".java": "Java", ".kt": "Kotlin",
    ".swift": "Swift", ".py": "Python", ".rb": "Ruby", ".sh": "Shell",
    ".bash": "Shell", ".ps1": "PowerShell", ".sql": "SQL", ".lua": "Lua",
    ".hs": "Haskell", ".css": "CSS", ".scss": "SCSS", ".html": "HTML",
    ".xml": "XML", ".svg": "SVG",
}

# § marker parser: number (1 or 1.1), optional separator, title.
CHAPTER_RE = re.compile(r"§\s*([0-9]+(?:\.[0-9]+)*)?\s*[—\-:]?\s*(.*?)\s*$")

# Legacy rule detection: a banner rule made of '=' (any comment style, incl.
# block-wrapped /* === */) or the old box-drawing '═'. Strips surrounding
# comment tokens before checking, so it catches // ===, # ===, and bare ===.
_LEAD_TOKENS = ("<!--", "/*", "//", "--", "#", "*")
_TRAIL_TOKENS = ("-->", "*/")


def is_legacy_rule(line: str) -> bool:
    s = line.strip()
    for t in _LEAD_TOKENS:
        if s.startswith(t):
            s = s[len(t):].strip()
            break
    for t in _TRAIL_TOKENS:
        if s.endswith(t):
            s = s[: -len(t)].strip()
            break
    # A legacy banner is a line that is ENTIRELY the rule glyph ('=' old ascii
    # rule, or '═' old box-drawing). Whole-line test (not substring) so prose
    # that merely mentions the glyph is not falsely flagged.
    return len(s) >= 5 and set(s) in ({"="}, {"═"})


# ── § 2 — CLASSIFY — language and comment-style resolution ──

def comment_cfg(path: Path) -> dict[str, Any]:
    """Resolve comment style for a file. Recognizes any known language.

    Returns kind = line | block | skip | unknown, with the delimiter
    payload needed by render and guard.
    """
    name = path.name
    ext = path.suffix.lower()
    if name in SPECIAL_FILENAMES:
        return {"kind": "line", "delim": SPECIAL_FILENAMES[name],
                "block": None, "lang": name}
    if ext in SKIP_EXT:
        return {"kind": "skip", "delim": None, "block": None, "lang": None}
    for delim, exts in LINE_DELIMS.items():
        if ext in exts:
            return {"kind": "line", "delim": delim, "block": None,
                    "lang": LANG_LABEL.get(ext, ext.lstrip("."))}
    for pair, exts in BLOCK_DELIMS.items():
        if ext in exts:
            return {"kind": "block", "delim": None, "block": pair,
                    "lang": LANG_LABEL.get(ext, ext.lstrip("."))}
    return {"kind": "unknown", "delim": None, "block": None, "lang": None}


def find_git_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return start.resolve()


# ── § 3 — RENDER — deterministic banner generation ──

def wrap(cfg: dict[str, Any], text: str) -> str:
    if cfg["kind"] == "line":
        return f"{cfg['delim']} {text}"
    if cfg["kind"] == "block":
        op, cl = cfg["block"]
        return f"{op} {text} {cl}"
    raise ValueError(f"cannot render for kind={cfg['kind']}")


def render_header(cfg: dict[str, Any], project: str, version: str,
                  filename: str, purpose: str, lang: str) -> str:
    rows = [
        RULE,
        f"{project} {version} — {filename}",
        f"§ - {purpose} · {lang}",
        YEAR,
        SIGNATURE,
        RULE,
    ]
    rows = [r for r in rows if r]
    return "\n".join(wrap(cfg, r) for r in rows)


def render_chapter(cfg: dict[str, Any], num: str, title: str, desc: str,
                   upper: bool) -> str:
    t = title.strip().upper() if upper else title.strip()
    body = f"§ {num} — {t}"
    if desc.strip():
        body += f" — {desc.strip()}"
    return wrap(cfg, f"── {body} ──")


# ── § 4 — GUARD — code-only-unchanged safety invariant ──

def is_pure_comment(line: str, cfg: dict[str, Any], first: bool) -> bool:
    """True only if the whole line is a self-contained comment.

    Line langs: stripped line starts with the delimiter.
    Block langs: stripped line starts with the opener AND ends with the
    closer (this is exactly how banners are rendered), so no code-bearing
    line is ever misread as a comment. Shebang is never a comment.
    """
    s = line.strip()
    if not s:
        return False
    if first and s.startswith("#!"):
        return False
    if cfg["kind"] == "line":
        return s.startswith(cfg["delim"])
    if cfg["kind"] == "block":
        op, cl = cfg["block"]
        return s.startswith(op) and s.endswith(cl)
    return False


def _strip_leading_block_comment(lines: list[str], cfg: dict[str, Any]) -> list[str]:
    """Drop a leading /* ... */ header from a line-comment file.

    A legacy header is block-wrapped even in // languages. Migrating it to a
    // header would otherwise look like deleting code lines (the block's inner
    text does not start with //). A /* at the very top — before any statement —
    is unambiguously a comment by language rules, so stripping it is safe.
    """
    if cfg["kind"] != "line":
        return lines
    i = 0
    n = len(lines)
    while i < n and (not lines[i].strip()
                     or (i == 0 and lines[i].lstrip().startswith("#!"))):
        i += 1
    if i < n and lines[i].lstrip().startswith("/*"):
        j = i
        while j < n and "*/" not in lines[j]:
            j += 1
        if j < n:
            return lines[:i] + lines[j + 1:]
    return lines


def significant_lines(text: str, cfg: dict[str, Any]) -> list[str]:
    """Lines that carry code: non-blank and not full-line comments.

    Banner insertion/removal only touches full-line comments, so the
    significant subsequence must stay byte-identical across a valid edit. A
    leading block-comment header is stripped first so legacy migration passes.
    """
    raw_lines = _strip_leading_block_comment(text.splitlines(), cfg)
    out: list[str] = []
    for i, raw in enumerate(raw_lines):
        if not raw.strip():
            continue
        if is_pure_comment(raw, cfg, first=(i == 0)):
            continue
        out.append(raw)
    return out


def guard_file(path: Path, against: str) -> dict[str, Any]:
    cfg = comment_cfg(path)
    if cfg["kind"] not in ("line", "block"):
        return {"file": str(path), "result": "skip",
                "reason": f"kind={cfg['kind']}"}
    root = find_git_root(path.parent)
    try:
        rel = path.resolve().relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    try:
        before = subprocess.run(
            ["git", "show", f"{against}:{rel}"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
    except (subprocess.CalledProcessError, OSError) as e:
        return {"file": str(path), "result": "error",
                "reason": f"sem versão base em {against}: {e}"}
    after = path.read_text(encoding="utf-8", errors="replace")

    sig_before = significant_lines(before, cfg)
    sig_after = significant_lines(after, cfg)
    if sig_before == sig_after:
        return {"file": str(path), "result": "pass",
                "code_lines": len(sig_after)}
    diff_at = None
    for idx, (a, b) in enumerate(zip(sig_before, sig_after)):
        if a != b:
            diff_at = {"index": idx, "before": a, "after": b}
            break
    return {"file": str(path), "result": "fail",
            "reason": "linha de código alterada — apenas comentários são permitidos",
            "first_divergence": diff_at,
            "len_before": len(sig_before), "len_after": len(sig_after)}


# ── § 5 — SCAN — detect headers, chapters and legacy style ──

def scan_file(path: Path) -> dict[str, Any]:
    from code_map import opens_line
    cfg = comment_cfg(path)
    rec: dict[str, Any] = {
        "file": str(path), "kind": cfg["kind"], "lang": cfg["lang"],
        "has_header": False, "legacy_header": False,
        "chapters": [], "subchapters": 0, "legacy_banners": 0,
        "status": "ok", "warnings": [],
    }
    if cfg["kind"] == "skip":
        rec["status"] = "skip"
        return rec
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        rec["status"] = "error"
        rec["warnings"].append(f"falha ao ler: {e}")
        return rec

    head_zone = lines[:14]
    has_signature = any("§ - " in ln for ln in head_zone)
    has_new_rule = any("─" in ln for ln in head_zone)
    # Conforming header = signature + new ── rule. Signature without the new
    # rule means a legacy header that needs migration.
    rec["has_header"] = has_signature and has_new_rule
    rec["legacy_header"] = has_signature and not has_new_rule

    for lineno, ln in enumerate(lines, start=1):
        if lineno > 14 and is_legacy_rule(ln):
            rec["legacy_banners"] += 1
        marker = "◇" if "◇" in ln else "§"
        if marker not in ln or not opens_line(ln, marker):
            continue
        tail = ln[ln.index(marker):].replace("◇", "§", 1)
        m = CHAPTER_RE.match(tail)
        number = (m.group(1) or "").strip() if m else ""
        if not number:
            if not tail.startswith("§ - "):
                rec["warnings"].append(f"line {lineno}: malformed chapter marker")
            continue
        title = (m.group(2) or "").strip() if m else tail.strip()
        title = title.rstrip("─*/->! ").strip()
        rec["chapters"].append({"line": lineno, "number": number,
                                 "title": title, "provisional": marker == "◇"})
        if number.count(".") >= 1:
            rec["subchapters"] += 1
        if title.upper() in {"UTILS", "HELPERS", "MISC", "LOGIC", "METHODS"} or not title.strip():
            rec["warnings"].append(f"line {lineno}: title has no navigational responsibility")

    if cfg["kind"] == "unknown":
        rec["status"] = "warn"
        rec["warnings"].append(
            "linguagem desconhecida; scan read-only, render exige --delim")
    else:
        if not rec["has_header"] and not rec["legacy_header"]:
            rec["status"] = "warn"
            rec["warnings"].append("header ausente")
        elif rec["legacy_header"]:
            rec["status"] = "warn"
            rec["warnings"].append(
                "header em estilo legado; migrar para ── + VAI CORINTHIANS!")
        if rec["legacy_banners"]:
            rec["status"] = "warn"
            rec["warnings"].append(
                "capítulos em estilo legado (===); migrar para § + ──")
    if rec["warnings"] and rec["status"] == "ok":
        rec["status"] = "warn"
    return rec


def git_changed_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
    except (subprocess.CalledProcessError, OSError):
        return []
    return [root / line.strip() for line in out.splitlines() if line.strip()]


# ── § 6 — REPORT — markdown rendering of scan ──

def render_report(records: list[dict[str, Any]]) -> str:
    L = ["# Diagram Check", ""]
    warn = [r for r in records if r["status"] == "warn"]
    L.append(f"Arquivos: {len(records)} · pendências: {len(warn)}")
    L.append("")
    L.append("| Arquivo | Status | Header | Capítulos | Avisos |")
    L.append("|---------|--------|--------|-----------|--------|")
    for r in records:
        L.append(
            f"| {r['file']} | {r['status']} | "
            f"{'sim' if r['has_header'] else 'não'} | "
            f"{len(r['chapters'])} | {'; '.join(r['warnings']) or '—'} |")
    return "\n".join(L) + "\n"


# ── § 7 — ENTRYPOINT — subcommand dispatch ──

def cmd_scan(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    root = find_git_root(cwd)
    if args.files:
        targets = [Path(f) for f in args.files]
    else:
        targets = git_changed_files(root)
    targets = [p for p in targets if p.exists() and p.is_file()]
    records = [scan_file(p) for p in targets]
    cache = root / ".agent-cache"
    cache.mkdir(exist_ok=True)
    payload = {"root": str(root), "records": records}
    (cache / "diagram-report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (cache / "diagram-report.md").write_text(
        render_report(records), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        warn = sum(1 for r in records if r["status"] == "warn")
        print(f"diagram_check scan: {len(records)} arquivos, {warn} pendências")
        print(f"Relatório: {(cache / 'diagram-report.md').relative_to(root)}")
    return 1 if any(r["status"] == "warn" for r in records) else 0


def cfg_for_render(args: argparse.Namespace) -> dict[str, Any]:
    if args.file:
        cfg = comment_cfg(Path(args.file))
        if cfg["kind"] in ("line", "block"):
            return cfg
    if args.block:
        op, cl = args.block.split(",", 1)
        return {"kind": "block", "delim": None, "block": (op, cl),
                "lang": args.lang or ""}
    return {"kind": "line", "delim": args.delim or "//", "block": None,
            "lang": args.lang or ""}


def cmd_render(args: argparse.Namespace) -> int:
    cfg = cfg_for_render(args)
    lang = args.lang or cfg.get("lang") or ""
    if args.level == "header":
        fname = args.file_name or (Path(args.file).name if args.file else "FILE")
        print(render_header(cfg, args.project, args.version, fname,
                            args.purpose or "", lang))
    elif args.level == "l1":
        print(render_chapter(cfg, args.num, args.title, args.desc or "",
                             upper=True))
    elif args.level == "l2":
        print(render_chapter(cfg, args.num, args.title, args.desc or "",
                             upper=False))
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    results = [guard_file(Path(f), args.against) for f in args.files]
    root = find_git_root(Path.cwd())
    cache = root / ".agent-cache"
    cache.mkdir(exist_ok=True)
    (cache / "diagram-guard.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    failed = [r for r in results if r["result"] in ("fail", "error")]
    for r in results:
        print(f"guard {r['result']}: {r['file']}"
              + (f" — {r.get('reason')}" if r.get("reason") else ""))
    return 2 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="diagram_check.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="detecta header/capítulos/legado")
    s.add_argument("files", nargs="*", help="vazio = git diff HEAD")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)

    r = sub.add_parser("render", help="gera moldura determinística")
    r.add_argument("level", choices=["header", "l1", "l2"])
    r.add_argument("--file", help="infere delim/lang/nome pela extensão")
    r.add_argument("--delim", help="delimitador de linha explícito (ex: //)")
    r.add_argument("--block", help="par de bloco explícito (ex: /*,*/)")
    r.add_argument("--lang")
    r.add_argument("--file-name", dest="file_name")
    r.add_argument("--project", default="PROJECT")
    r.add_argument("--version", default="1.0")
    r.add_argument("--purpose", default="")
    r.add_argument("--num", default="1")
    r.add_argument("--title", default="")
    r.add_argument("--desc", default="")
    r.set_defaults(func=cmd_render)

    g = sub.add_parser("guard", help="rejeita mudança em linha de código")
    g.add_argument("files", nargs="+")
    g.add_argument("--against", default="HEAD")
    g.set_defaults(func=cmd_guard)
    return p


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
