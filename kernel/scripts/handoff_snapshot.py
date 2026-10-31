# ────────────────────────────────────────────
# CODEX-ENV 1.0 — handoff_snapshot.py
# § - Collect mechanical snapshot for session handoff; LLM writes the narrative · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ── § 1 — GIT HELPERS ──

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


# ── § 2 — COLLECTORS ──

def collect_branch(root: Path) -> str:
    _, out = run_git(["branch", "--show-current"], root)
    return out.strip() or "(detached)"


def collect_status(root: Path) -> tuple[str, str]:
    _, full = run_git(["status"], root)
    _, short = run_git(["status", "--short"], root)
    return full, short


def collect_log(root: Path) -> list[str]:
    _, out = run_git(["log", "--oneline", "-10"], root)
    return [line for line in out.splitlines() if line.strip()]


def collect_diff_stat(root: Path) -> tuple[str, str]:
    _, unstaged = run_git(["diff", "--stat"], root)
    _, staged = run_git(["diff", "--staged", "--stat"], root)
    return unstaged, staged


def parse_modified_files(short_status: str) -> list[str]:
    files: list[str] = []
    for line in short_status.splitlines():
        if not line.strip():
            continue
        parts = line[3:].strip()
        if " -> " in parts:
            parts = parts.split(" -> ")[-1]
        files.append(parts.strip())
    return files


# ── § 3 — ACTIVE SPECS ──

def list_active_specs(root: Path) -> list[str]:
    specs_dir = root / "docs" / "specs" / "active"
    if not specs_dir.exists():
        return []
    return sorted(
        str(f.relative_to(root))
        for f in specs_dir.iterdir()
        if f.is_file() and f.suffix in {".md", ".txt", ".rst"}
    )


# ── § 4 — TODO/FIXME SCANNER ──

_TODO_RE = re.compile(r"\b(TODO|FIXME)\b.*", re.IGNORECASE)


def scan_todos(root: Path, files: list[str]) -> list[str]:
    """Scan modified files for TODO/FIXME lines using Python re (no external grep)."""
    findings: list[str] = []
    for rel_path in files:
        abs_path = root / rel_path
        if not abs_path.exists() or not abs_path.is_file():
            continue
        try:
            lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if _TODO_RE.search(line):
                excerpt = line.strip()
                if len(excerpt) > 120:
                    excerpt = excerpt[:117] + "..."
                findings.append(f"`{rel_path}:{lineno}` {excerpt}")
    return findings


# ── § 5 — AGENT CACHE INVENTORY ──

def list_cache_reports(root: Path) -> list[str]:
    cache_dir = root / ".agent-cache"
    if not cache_dir.exists():
        return []
    return sorted(
        f".agent-cache/{f.name}"
        for f in cache_dir.iterdir()
        if f.is_file() and f.suffix in {".md", ".json"}
    )


# ── § 6 — MECHANICAL OBSERVATIONS ──

def build_observations(
    short_status: str,
    active_specs: list[str],
    todos: list[str],
) -> list[str]:
    obs: list[str] = []
    if short_status.strip():
        obs.append("Working tree has uncommitted changes.")
    if active_specs:
        obs.append(f"{len(active_specs)} active spec(s) found.")
    if todos:
        obs.append(f"{len(todos)} TODO/FIXME marker(s) found in modified files.")
    if not obs:
        obs.append("Working tree is clean, no active specs, no TODO/FIXME markers.")
    return obs


# ── § 7 — REPORT GENERATION ──

def build_report(
    root: Path,
    branch: str,
    short_status: str,
    commits: list[str],
    files: list[str],
    unstaged_stat: str,
    staged_stat: str,
    active_specs: list[str],
    todos: list[str],
    cache_reports: list[str],
    observations: list[str],
) -> tuple[str, dict[str, Any]]:

    md_lines: list[str] = ["# Handoff Snapshot", "", "## Branch", f"`{branch}`", ""]

    md_lines += ["## Estado git", "```", short_status.strip() or "(clean)", "```", ""]

    if commits:
        md_lines.append("## Últimos commits")
        for c in commits:
            md_lines.append(f"- `{c}`")
        md_lines.append("")

    if files:
        md_lines.append("## Arquivos modificados")
        for f in files:
            md_lines.append(f"- `{f}`")
        md_lines.append("")

    if unstaged_stat.strip():
        md_lines += ["## Diff stat (unstaged)", "```",
                     unstaged_stat.strip(), "```", ""]

    if staged_stat.strip():
        md_lines += ["## Diff stat (staged)", "```",
                     staged_stat.strip(), "```", ""]

    if active_specs:
        md_lines.append("## Specs ativas")
        for s in active_specs:
            md_lines.append(f"- `{s}`")
        md_lines.append("")
    else:
        md_lines += ["## Specs ativas", "Nenhuma.", ""]

    md_lines.append("## TODO/FIXME em arquivos modificados")
    if todos:
        for t in todos:
            md_lines.append(f"- {t}")
    else:
        md_lines.append("- Nenhum encontrado.")
    md_lines.append("")

    md_lines.append("## Relatórios disponíveis")
    if cache_reports:
        for r in cache_reports:
            md_lines.append(f"- `{r}`")
    else:
        md_lines.append("- Nenhum em `.agent-cache/`.")
    md_lines.append("")

    md_lines.append("## Observações mecânicas")
    for o in observations:
        md_lines.append(f"- {o}")

    md = "\n".join(md_lines)

    data: dict[str, Any] = {
        "branch": branch,
        "is_clean": not short_status.strip(),
        "modified_files": files,
        "recent_commits": commits,
        "active_specs": active_specs,
        "todos": todos,
        "cache_reports": cache_reports,
        "observations": observations,
    }

    return md, data


# ── § 8 — MAIN ──

def main() -> int:
    cwd = Path.cwd()
    root = git_root(cwd)
    if root is None:
        print("ERROR: not inside a git repository.", file=sys.stderr)
        return 3

    branch = collect_branch(root)
    _full_status, short_status = collect_status(root)
    commits = collect_log(root)
    unstaged_stat, staged_stat = collect_diff_stat(root)
    files = parse_modified_files(short_status)
    active_specs = list_active_specs(root)
    todos = scan_todos(root, files)
    cache_reports = list_cache_reports(root)
    observations = build_observations(short_status, active_specs, todos)

    md, data = build_report(
        root, branch, short_status, commits, files,
        unstaged_stat, staged_stat,
        active_specs, todos, cache_reports, observations,
    )

    cache_dir = root / ".agent-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    md_path = cache_dir / "handoff-snapshot.md"
    json_path = cache_dir / "handoff-snapshot.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] handoff-snapshot written to {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
