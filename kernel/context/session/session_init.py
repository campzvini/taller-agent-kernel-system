# ────────────────────────────────────────────
# TASK 2.2.0 — session_init.py
# § - Capture repository state at session start: branch, status, log, specs, diff · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Sibling scripts resolve from this file, not from ~/.codex: a copy under
# test must call its own gates, never the installed ones.
SCRIPTS = Path(__file__).resolve().parent

# ── § 1 — GIT HELPERS — Query repository state without modifying it ──

def run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace")
        return proc.returncode, proc.stdout
    except FileNotFoundError:
        return 127, ""


def git_root(cwd: Path) -> Path | None:
    code, out = run_git(["rev-parse", "--show-toplevel"], cwd)
    if code != 0:
        return None
    return Path(out.strip())


# ── § 2 — COLLECTORS — Collect bounded observations from existing sources ──

def collect_branch(root: Path) -> str:
    _, out = run_git(["branch", "--show-current"], root)
    return out.strip() or "(detached)"


def collect_status(root: Path) -> tuple[str, list[str]]:
    _, short = run_git(["status", "--short"], root)
    modified = [line[3:].strip() for line in short.splitlines() if line.strip()]
    return short, modified


def collect_log(root: Path) -> list[str]:
    _, out = run_git(["log", "--oneline", "-10"], root)
    return [l for l in out.splitlines() if l.strip()]


def collect_diff(root: Path, staged: bool) -> tuple[str, str]:
    args_stat = ["diff", "--stat"]
    args_full = ["diff"]
    if staged:
        args_stat.insert(1, "--staged")
        args_full.insert(1, "--staged")
    _, stat = run_git(args_stat, root)
    _, full = run_git(args_full, root)
    return stat, full


def collect_specs(root: Path) -> list[dict[str, Any]]:
    specs_dir = root / "docs" / "specs" / "active"
    if not specs_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(specs_dir.iterdir()):
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        first_para = ""
        for line in content.splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                first_para = s
                break
        out.append({
            "path": str(p.relative_to(root)),
            "name": p.name,
            "first_paragraph": first_para,
            "size_bytes": len(content.encode("utf-8")),
        })
    return out


GATE_OF_WORKFLOW = {"sdd": "sdd_gate.py"}


def governed_workflow(root: Path) -> str | None:
    """Which tree governs this project. The anchor's record first, then evidence.

    Hardcoding the sdd gate here reported every CAD project against the wrong
    workflow: its records read as absent and next_phase pointed at a phase the
    project had already passed.
    """
    anchor = root / ".task" / "project.tdsl"
    if anchor.is_file():
        for line in anchor.read_text(encoding="utf-8", errors="replace").split("\n"):
            if line.startswith("workflow: "):
                declared = line.partition(": ")[2].partition(" #")[0].strip()
                if declared in GATE_OF_WORKFLOW:
                    return declared
    features = root / ".task" / "features"
    if features.is_dir() and any(features.glob("*/part.tdsl")):
        return "cad"
    return None


def collect_protocol(root: Path) -> dict[str, Any] | None:
    """Governance state, when the project is governed. The gate owns the truth."""
    if not (root / ".task").is_dir():
        return None
    workflow = governed_workflow(root)
    if workflow is None:
        anchor = root / ".task" / "project.tdsl"
        fields: dict[str, str] = {}
        if anchor.is_file():
            for line in anchor.read_text(encoding="utf-8", errors="replace").split("\n"):
                if ": " in line and not line.startswith(" "):
                    key, _, value = line.partition(": ")
                    fields[key.strip()] = value.partition(" #")[0].strip()
        return {
            "project": fields.get("id", "unknown"),
            "workflow": "unknown",
            "active_feature": fields.get("active_feature", "unknown"),
            "artifacts": {},
            "next_phase": "unknown",
            "routing_error": "workflow ausente ou ambiguo",
        }
    gate = SCRIPTS / GATE_OF_WORKFLOW[workflow]
    if not gate.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(gate), "--cwd", str(root), "state", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout)
    except (OSError, json.JSONDecodeError):
        return None
    return None


def collect_staged_files(root: Path) -> list[str]:
    _, out = run_git(["diff", "--staged", "--name-only"], root)
    return [l for l in out.splitlines() if l.strip()]


# ── § 3 — STACK DETECTION (DELEGATED) — Locate stack detection (delegated) responsibilities ──

def collect_stack(root: Path) -> dict[str, Any] | None:
    detect_script = SCRIPTS / "detect_project.py"
    if not detect_script.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(detect_script), "--json"],
            cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        if proc.returncode in (0, 1) and proc.stdout.strip():
            return json.loads(proc.stdout)
    except (OSError, json.JSONDecodeError):
        return None
    return None


# ── § 4 — REPORT — Render observed context without granting authority ──

def build_report(root: Path, diff_mode: str) -> dict[str, Any]:
    branch = collect_branch(root)
    status_short, modified = collect_status(root)
    log = collect_log(root)
    specs = collect_specs(root)
    staged_files = collect_staged_files(root)
    is_clean = not status_short.strip()
    diff_stat, diff_full = "", ""
    staged_stat, staged_full = "", ""
    if not is_clean and diff_mode != "none":
        diff_stat, diff_full = collect_diff(root, staged=False)
        if staged_files:
            staged_stat, staged_full = collect_diff(root, staged=True)
    stack = collect_stack(root)
    protocol = collect_protocol(root)
    risks: list[str] = []
    if not is_clean:
        risks.append("Working tree não está limpo.")
    if staged_files:
        risks.append("Existem mudanças staged não commitadas.")
    if specs:
        risks.append(f"{len(specs)} spec(s) ativa(s) em docs/specs/active/.")
    overall_status = "WARN" if not is_clean else "OK"
    return {
        "status": overall_status.lower(),
        "repo_root": str(root),
        "branch": branch,
        "is_clean": is_clean,
        "status_short": status_short,
        "modified_files": modified,
        "staged_files": staged_files,
        "recent_commits": log,
        "active_specs": specs,
        "diff_mode": diff_mode,
        "diff_stat": diff_stat,
        "diff_full": diff_full if diff_mode == "full" else "",
        "staged_stat": staged_stat,
        "staged_full": staged_full if diff_mode == "full" else "",
        "stack": stack,
        "protocol": protocol,
        "risks": risks,
    }


def render_markdown(r: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# Session Report")
    L.append("")
    L.append("## Status")
    L.append(r["status"].upper())
    L.append("")
    L.append("## Repositório")
    L.append(f"- Root: `{r['repo_root']}`")
    L.append(f"- Branch: `{r['branch']}`")
    L.append("")
    L.append("## Working tree")
    L.append(f"- Clean: {'sim' if r['is_clean'] else 'não'}")
    if r["modified_files"]:
        L.append("- Arquivos modificados:")
        for f in r["modified_files"]:
            L.append(f"  - `{f}`")
    L.append("")
    L.append("## Últimos commits")
    if r["recent_commits"]:
        for c in r["recent_commits"]:
            parts = c.split(" ", 1)
            h = parts[0]
            m = parts[1] if len(parts) > 1 else ""
            L.append(f"- `{h}` {m}")
    else:
        L.append("- (sem histórico)")
    L.append("")
    L.append("## Specs ativas")
    if r["active_specs"]:
        for s in r["active_specs"]:
            L.append(f"### `{s['path']}`")
            if s["first_paragraph"]:
                L.append(f"- Propósito: {s['first_paragraph']}")
            L.append(f"- Tamanho: {s['size_bytes']} bytes")
            L.append("")
    else:
        L.append("- Nenhuma.")
        L.append("")
    if r["diff_mode"] != "none" and not r["is_clean"]:
        L.append("## Diff pendente")
        L.append("### Stat")
        L.append("```")
        L.append(r["diff_stat"].rstrip() or "(vazio)")
        L.append("```")
        if r["diff_full"]:
            L.append("### Diff")
            L.append("```diff")
            L.append(r["diff_full"].rstrip())
            L.append("```")
        L.append("")
    if r["staged_files"]:
        L.append("## Staged changes")
        L.append("### Stat")
        L.append("```")
        L.append(r["staged_stat"].rstrip() or "(vazio)")
        L.append("```")
        if r["staged_full"]:
            L.append("### Diff")
            L.append("```diff")
            L.append(r["staged_full"].rstrip())
            L.append("```")
        L.append("")
    L.append("## Stack detectada")
    stack = r.get("stack")
    if stack and stack.get("detections"):
        for d in stack["detections"]:
            L.append(f"- {d['stack']}")
    else:
        L.append("- (não detectada ou script ausente)")
    L.append("")
    protocol = r.get("protocol")
    if protocol:
        L.append("## Governança (.task)")
        L.append(f"- Projeto: `{protocol.get('project')}`")
        L.append(f"- Workflow: `{protocol.get('workflow')}`")
        L.append(f"- Feature ativa: `{protocol.get('active_feature')}`")
        # The snapshot reports existence, nothing else. Acceptance and freshness
        # were removed from the model; rendering them raised KeyError and took
        # the whole boot report down with it.
        for artifact, data in (protocol.get("artifacts") or {}).items():
            L.append(f"- {artifact}: {'presente' if data.get('present') else '—'}")
        L.append(f"- Próxima fase: `{protocol.get('next_phase')}`")
        execution = protocol.get("execution")
        if execution:
            L.append(f"- Execução: `{execution['execution_mode']}`; concorrência: {execution['max_active_subagents']}")
            L.append(f"- Scaffold registrado: {execution.get('scaffold_present', False)}")
            L.append(f"- Unidades para retomada: {len(execution.get('units', {}))}")
        if protocol.get("routing_error"):
            L.append(f"- Bloqueio de roteamento: {protocol['routing_error']}")
        L.append("")
    L.append("## Riscos imediatos")
    if r["risks"]:
        for risk in r["risks"]:
            L.append(f"- {risk}")
    else:
        L.append("- Nenhum.")
    L.append("")
    # Nenhum "próximo passo sugerido": um script não elege trajetória por heurística.
    # A próxima fase, quando existe, vem do gate; caso contrário o operador decide.
    return "\n".join(L)


# ── § 5 — ARGS + ENTRYPOINT — Parse arguments and dispatch the requested command ──

def parse_args(argv: list[str]) -> tuple[str, bool, bool]:
    diff_mode = "stat"
    json_mode = False
    hook_mode = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--diff" and i + 1 < len(argv):
            v = argv[i + 1]
            if v in ("full", "stat", "none"):
                diff_mode = v
            else:
                print(f"ERRO: --diff inválido: {v}", file=sys.stderr)
                sys.exit(3)
            i += 2
            continue
        if a == "--json":
            json_mode = True
            i += 1
            continue
        if a == "--hook":
            hook_mode = True
            diff_mode = "stat"
            i += 1
            continue
        print(f"ERRO: argumento desconhecido: {a}", file=sys.stderr)
        sys.exit(3)
    return diff_mode, json_mode, hook_mode


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    diff_mode, json_mode, hook_mode = parse_args(argv)
    cwd = Path.cwd()
    root = git_root(cwd)
    if root is None:
        if hook_mode:
            return 0  # projeto sem git não é erro de boot; siga em silêncio
        print("ERRO: diretório não é repositório git.", file=sys.stderr)
        return 3
    cache = root / ".agent-cache"
    try:
        cache.mkdir(exist_ok=True)
    except OSError as e:
        print(f"ERRO: não foi possível criar .agent-cache/: {e}",
              file=sys.stderr)
        return 3
    report = build_report(root, diff_mode)
    context = {"repo_root": report["repo_root"], "branch": report["branch"],
               "is_clean": report["is_clean"], "protocol": report["protocol"],
               "sources": {"instructions": "AGENTS.md", "anchor": ".task/project.tdsl",
                           "configuration": ".task/execution.config.tdsl", "constitution": ".task/constitution.tdsl"},
               "authority": "observed_state_only", "semantic_sufficiency": "agent_judgment",
               "detail": ".agent-cache/session-report.json"}
    report["context_snapshot"] = ".agent-cache/session-context.json"
    md = render_markdown(report)
    try:
        (cache / "session-context.json").write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (cache / "session-report.md").write_text(md, encoding="utf-8")
        (cache / "session-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8")
    except OSError as e:
        print(f"ERRO: falha ao escrever relatório: {e}", file=sys.stderr)
        return 3
    # árvore suja é estado normal, não falha: em modo hook nunca sinalize erro
    code = 0 if hook_mode else (1 if not report["is_clean"] else 0)
    if json_mode:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"session_init: {report['status'].upper()} — branch "
              f"{report['branch']} — clean={report['is_clean']}")
        print(f"Specs ativas: {len(report['active_specs'])}")
        protocol = report.get("protocol")
        if protocol:
            print(f"Workflow: {protocol.get('workflow')}")
            print(f"Feature ativa: {protocol.get('active_feature')}")
            print(f"Próxima fase: {protocol.get('next_phase')}")
            if protocol.get("routing_error"):
                print(f"Bloqueio de roteamento: {protocol['routing_error']}")
        print("Contexto compacto: .agent-cache/session-context.json; consulte detalhes somente se necessários")
        print("Relatório: .agent-cache/session-report.md")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
