# ────────────────────────────────────────────
# TASK 2.2.0 — spec_lint.py
# § - Validate a spec markdown for structural completeness before execution · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ── § 1 — CONFIG — Required sections and matching keywords ──

# section_key -> list of lowercase keywords/synonyms
REQUIRED_SECTIONS: dict[str, list[str]] = {
    "instrucao_execucao": ["instrução de execução", "instrucao de execucao",
                           "instruções de execução"],
    "contexto": ["contexto", "background", "motivação", "motivacao"],
    "objetivo": ["objetivo", "goal", "objetivos"],
    "escopo_positivo": ["escopo positivo", "escopo", "in scope", "dentro do escopo"],
    "escopo_negativo": ["escopo negativo", "fora do escopo", "out of scope",
                        "não-objetivos", "nao-objetivos", "non-goals"],
    "decisoes": ["decisões tomadas", "decisoes tomadas", "decisões", "decisoes",
                 "decisões de design", "decisions"],
    "arquitetura": ["arquitetura proposta", "arquitetura", "design",
                    "proposta arquitetural"],
    "sequencia": ["sequência de implementação", "sequencia de implementacao",
                  "plano de implementação", "plano de implementacao",
                  "etapas", "passos"],
    "criterios_aceitacao": ["critérios de aceitação", "criterios de aceitacao",
                            "acceptance criteria", "critérios de aceite"],
    "validacao": ["validação", "validacao", "como validar", "testes",
                  "verificação", "verificacao"],
    "pontos_atencao": ["pontos de atenção", "pontos de atencao", "riscos",
                       "edge cases", "atenção", "atencao", "cuidados"],
}

BLOCKING_KEYS = {"instrucao_execucao", "objetivo", "criterios_aceitacao",
                 "validacao"}

PROBLEMATIC_TERMS = [
    "implementar tudo",
    "melhorar geral",
    "refatorar se necessário",
    "refatorar se necessario",
    "decidir depois",
    "o agente escolhe",
]

# Taller-DSL specs use a fenced yaml block with line-start keys instead of
# markdown section headings. section_key -> list of DSL key tokens (line-start).
DSL_SECTIONS: dict[str, list[str]] = {
    "instrucao_execucao": ["instruction_to_executor", "completion_protocol"],
    "contexto": ["context"],
    "objetivo": ["objective"],
    "escopo_positivo": ["positive_scope"],
    "escopo_negativo": ["negative_scope"],
    "decisoes": ["decision", "context"],
    "arquitetura": ["architecture", "context"],
    "sequencia": ["implementation", "sub_specs"],
    "criterios_aceitacao": ["acceptance", "done_when"],
    "validacao": ["validation", "validation_gate"],
    "pontos_atencao": ["stop_rules", "risks"],
}


def is_taller_dsl(text: str) -> bool:
    """A taller-DSL spec declares spec_id at a line start (inside a yaml fence)."""
    return re.search(r"^\s*spec_id\b", text, re.MULTILINE) is not None


def dsl_found(text: str) -> dict[str, bool]:
    found: dict[str, bool] = {}
    for key, toks in DSL_SECTIONS.items():
        found[key] = any(
            re.search(rf"^\s*{re.escape(tok)}\b", text, re.MULTILINE)
            for tok in toks
        )
    return found


# ── § 2 — PARSING — Locate parsing responsibilities ──

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def parse_headings(text: str) -> list[tuple[int, int, str]]:
    """Return list of (line_index, level, title_lower)."""
    out: list[tuple[int, int, str]] = []
    for idx, line in enumerate(text.splitlines()):
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip().lower()
            out.append((idx, level, title))
    return out


def match_section(title: str, keywords: list[str]) -> bool:
    for kw in keywords:
        if kw in title:
            return True
    return False


def section_has_content(text: str, headings: list[tuple[int, int, str]],
                        idx: int) -> bool:
    lines = text.splitlines()
    start = headings[idx][0] + 1
    end = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
    for line in lines[start:end]:
        if line.strip():
            return True
    return False


# ── § 3 — LINT — Locate lint responsibilities ──

def lint_spec(text: str) -> dict[str, Any]:
    empty: dict[str, bool] = {k: False for k in REQUIRED_SECTIONS}
    if is_taller_dsl(text):
        # DSL mode: validate yaml-block keys, not markdown headings.
        found = dsl_found(text)
    else:
        headings = parse_headings(text)
        found = {k: False for k in REQUIRED_SECTIONS}
        for key, kws in REQUIRED_SECTIONS.items():
            for i, (_, _, title) in enumerate(headings):
                if match_section(title, kws):
                    found[key] = True
                    if not section_has_content(text, headings, i):
                        empty[key] = True
                    break
    missing = [k for k, v in found.items() if not v]
    blockers = [k for k in missing if k in BLOCKING_KEYS]
    warnings = [k for k in missing if k not in BLOCKING_KEYS]
    empty_sections = [k for k, v in empty.items() if v]
    text_low = text.lower()
    flagged_terms = [t for t in PROBLEMATIC_TERMS if t in text_low]
    if blockers:
        status = "FAIL"
        code = 2
    elif warnings or empty_sections or flagged_terms:
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
        "blockers": blockers,
        "warnings_missing": warnings,
        "empty_sections": empty_sections,
        "flagged_terms": flagged_terms,
    }


# ── § 4 — RENDER — Locate render responsibilities ──

LABELS = {
    "instrucao_execucao": "Instrução de execução",
    "contexto": "Contexto",
    "objetivo": "Objetivo",
    "escopo_positivo": "Escopo positivo",
    "escopo_negativo": "Escopo negativo",
    "decisoes": "Decisões tomadas",
    "arquitetura": "Arquitetura proposta",
    "sequencia": "Sequência de implementação",
    "criterios_aceitacao": "Critérios de aceitação",
    "validacao": "Validação",
    "pontos_atencao": "Pontos de atenção",
}


def render_markdown(target: Path, result: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# Spec Lint")
    L.append("")
    L.append(f"Arquivo: `{target}`")
    L.append("")
    L.append("## Status")
    L.append(result["status"])
    L.append("")
    L.append("## Seções obrigatórias")
    for key in REQUIRED_SECTIONS:
        mark = "x" if result["found"][key] else " "
        L.append(f"- [{mark}] {LABELS[key]}")
    L.append("")
    L.append("## Problemas")
    L.append("### Bloqueantes")
    if result["blockers"]:
        for k in result["blockers"]:
            L.append(f"- Ausência de seção: {LABELS[k]}.")
    else:
        L.append("- Nenhum.")
    L.append("")
    L.append("### Avisos")
    if (result["warnings_missing"] or result["empty_sections"]
            or result["flagged_terms"]):
        for k in result["warnings_missing"]:
            L.append(f"- {LABELS[k]} ausente.")
        for k in result["empty_sections"]:
            L.append(f"- {LABELS[k]} presente mas sem conteúdo.")
        for t in result["flagged_terms"]:
            L.append(f"- Termo problemático encontrado: \"{t}\".")
    else:
        L.append("- Nenhum.")
    L.append("")
    L.append("## Recomendação")
    if result["status"] == "FAIL":
        L.append("Não iniciar implementação até resolver os bloqueios.")
    elif result["status"] == "WARN":
        L.append("Spec utilizável, mas há lacunas que merecem revisão antes "
                 "de delegar a executores.")
    else:
        L.append("Spec pronta para execução.")
    L.append("")
    return "\n".join(L)


# ── § 5 — ENTRYPOINT — Locate entrypoint responsibilities ──

def find_git_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return start.resolve()


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("Uso: python spec_lint.py <arquivo>", file=sys.stderr)
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
    result = lint_spec(text)
    root = find_git_root(Path.cwd())
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
        "blockers": result["blockers"],
        "warnings_missing": result["warnings_missing"],
        "empty_sections": result["empty_sections"],
        "flagged_terms": result["flagged_terms"],
    }
    try:
        (cache / "spec-lint.md").write_text(md, encoding="utf-8")
        (cache / "spec-lint.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8")
    except OSError as e:
        print(f"ERRO: falha ao escrever relatório: {e}", file=sys.stderr)
        return 3
    print(f"spec_lint: {result['status']} — "
          f"{len(result['blockers'])} bloqueio(s), "
          f"{len(result['warnings_missing']) + len(result['empty_sections']) + len(result['flagged_terms'])} aviso(s)")
    print("Relatório: .agent-cache/spec-lint.md")
    return result["code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
