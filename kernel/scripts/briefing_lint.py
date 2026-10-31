# ────────────────────────────────────────────
# CODEX-ENV 1.0 — briefing_lint.py
# § - Validate a briefing markdown before handing it to a subagent executor · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ── § 1 — CONFIG ──

REQUIRED_FIELDS: dict[str, list[str]] = {
    "objetivo": ["objetivo", "goal"],
    "arquivos_alvo": ["arquivos alvo", "arquivos-alvo", "arquivos",
                      "target files", "alvos"],
    "contexto_minimo": ["contexto mínimo", "contexto minimo", "contexto",
                        "background"],
    "escopo_positivo": ["escopo positivo", "escopo", "in scope"],
    "escopo_negativo": ["escopo negativo", "fora do escopo", "out of scope",
                        "não fazer", "nao fazer"],
    "restricoes": ["restrições", "restricoes", "constraints", "limites"],
    "criterio_validacao": ["critério de validação", "criterio de validacao",
                           "validação", "validacao", "como validar",
                           "acceptance"],
    "output_esperado": ["output esperado", "saída esperada", "saida esperada",
                        "entregável", "entregavel", "expected output"],
}

BLOCKING_FIELDS = {"objetivo", "arquivos_alvo", "escopo_negativo",
                   "criterio_validacao"}

VAGUE_TERMS = [
    "ajuste o necessário",
    "ajuste o necessario",
    "melhore",
    "faça direito",
    "faca direito",
    "refatore se precisar",
    "decida a melhor abordagem",
]


# ── § 2 — PARSING ──

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def parse_headings(text: str) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for idx, line in enumerate(text.splitlines()):
        m = HEADING_RE.match(line)
        if m:
            out.append((idx, len(m.group(1)), m.group(2).strip().lower()))
    return out


def match_field(title: str, keywords: list[str]) -> bool:
    return any(kw in title for kw in keywords)


def section_content(text: str, headings: list[tuple[int, int, str]],
                    idx: int) -> str:
    lines = text.splitlines()
    start = headings[idx][0] + 1
    end = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
    return "\n".join(lines[start:end]).strip()


# ── § 3 — EXTRA CHECKS ──

def extract_target_files(content: str) -> list[str]:
    files: list[str] = []
    for line in content.splitlines():
        s = line.strip()
        if s.startswith(("-", "*", "+")):
            s = s[1:].strip()
        # take first backtick token or first word that looks like a path
        m = re.search(r"`([^`]+)`", s)
        if m:
            files.append(m.group(1).strip())
            continue
        token = s.split()[0] if s else ""
        if token and ("/" in token or "\\" in token or "." in token):
            files.append(token)
    return files


def verify_files_exist(files: list[str], base: Path) -> list[str]:
    missing: list[str] = []
    for f in files:
        if (base / f).exists():
            continue
        if Path(f).exists():
            continue
        missing.append(f)
    return missing


# ── § 4 — LINT ──

def lint_briefing(text: str, base: Path) -> dict[str, Any]:
    headings = parse_headings(text)
    found: dict[str, bool] = {k: False for k in REQUIRED_FIELDS}
    empty: dict[str, bool] = {k: False for k in REQUIRED_FIELDS}
    contents: dict[str, str] = {}
    for key, kws in REQUIRED_FIELDS.items():
        for i, (_, _, title) in enumerate(headings):
            if match_field(title, kws):
                found[key] = True
                c = section_content(text, headings, i)
                contents[key] = c
                if not c:
                    empty[key] = True
                break
    missing = [k for k, v in found.items() if not v]
    blockers = [k for k in missing if k in BLOCKING_FIELDS]
    if "escopo_negativo" in empty:
        blockers.append("escopo_negativo")
    if "criterio_validacao" in empty:
        blockers.append("criterio_validacao")
    blockers = sorted(set(blockers))
    text_low = text.lower()
    vague_hits = [t for t in VAGUE_TERMS if t in text_low]
    target_files = extract_target_files(contents.get("arquivos_alvo", ""))
    missing_files = verify_files_exist(target_files, base)
    if blockers:
        status = "FAIL"
        code = 2
    elif missing or vague_hits or missing_files or any(empty.values()):
        status = "WARN"
        code = 1
    else:
        status = "OK"
        code = 0
    return {
        "status": status,
        "code": code,
        "found": found,
        "missing": missing,
        "empty": [k for k, v in empty.items() if v],
        "blockers": blockers,
        "vague_terms": vague_hits,
        "target_files": target_files,
        "missing_target_files": missing_files,
    }


# ── § 5 — RENDER ──

LABELS = {
    "objetivo": "Objetivo",
    "arquivos_alvo": "Arquivos alvo",
    "contexto_minimo": "Contexto mínimo",
    "escopo_positivo": "Escopo positivo",
    "escopo_negativo": "Escopo negativo",
    "restricoes": "Restrições",
    "criterio_validacao": "Critério de validação",
    "output_esperado": "Output esperado",
}


def render_markdown(target: Path, result: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# Briefing Lint")
    L.append("")
    L.append(f"Arquivo: `{target}`")
    L.append("")
    L.append("## Status")
    L.append(result["status"])
    L.append("")
    L.append("## Checklist")
    for key in REQUIRED_FIELDS:
        mark = "x" if result["found"][key] else " "
        L.append(f"- [{mark}] {LABELS[key]}")
    L.append("")
    L.append("## Bloqueios")
    if result["blockers"]:
        for k in result["blockers"]:
            L.append(f"- {LABELS.get(k, k)} ausente ou vazio.")
    else:
        L.append("- Nenhum.")
    L.append("")
    L.append("## Avisos")
    warn_lines: list[str] = []
    for k in result["missing"]:
        if k not in result["blockers"]:
            warn_lines.append(f"- {LABELS[k]} ausente.")
    for k in result["empty"]:
        if k not in result["blockers"]:
            warn_lines.append(f"- {LABELS[k]} presente mas sem conteúdo.")
    for t in result["vague_terms"]:
        warn_lines.append(f"- Termo vago encontrado: \"{t}\".")
    for f in result["missing_target_files"]:
        warn_lines.append(f"- Arquivo alvo não encontrado no disco: `{f}`.")
    if warn_lines:
        L.extend(warn_lines)
    else:
        L.append("- Nenhum.")
    L.append("")
    L.append("## Recomendação")
    if result["status"] == "FAIL":
        L.append("Completar briefing antes de enviar para subagent.")
    elif result["status"] == "WARN":
        L.append("Briefing utilizável, mas revisar avisos antes do spawn.")
    else:
        L.append("Briefing pronto para envio ao subagent.")
    L.append("")
    return "\n".join(L)


# ── § 6 — ENTRYPOINT ──

def find_git_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return start.resolve()


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("Uso: python briefing_lint.py <arquivo>", file=sys.stderr)
        return 3
    target = Path(argv[0])
    if not target.exists() or not target.is_file():
        print(f"ERRO: arquivo não existe: {argv[0]}", file=sys.stderr)
        return 3
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"ERRO: falha ao ler arquivo: {e}", file=sys.stderr)
        return 3
    cwd = Path.cwd()
    root = find_git_root(cwd)
    result = lint_briefing(text, base=root)
    cache = root / ".agent-cache"
    try:
        cache.mkdir(exist_ok=True)
    except OSError as e:
        print(f"ERRO: não foi possível criar .agent-cache/: {e}",
              file=sys.stderr)
        return 3
    md = render_markdown(target, result)
    payload = {
        "status": result["status"].lower(),
        "file": str(target),
        "found": result["found"],
        "missing": result["missing"],
        "empty": result["empty"],
        "blockers": result["blockers"],
        "vague_terms": result["vague_terms"],
        "target_files": result["target_files"],
        "missing_target_files": result["missing_target_files"],
    }
    try:
        (cache / "briefing-lint.md").write_text(md, encoding="utf-8")
        (cache / "briefing-lint.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8")
    except OSError as e:
        print(f"ERRO: falha ao escrever relatório: {e}", file=sys.stderr)
        return 3
    print(f"briefing_lint: {result['status']} — "
          f"{len(result['blockers'])} bloqueio(s)")
    print("Relatório: .agent-cache/briefing-lint.md")
    return result["code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
