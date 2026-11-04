# ────────────────────────────────────────────
# TASK 2.2.0 — detect_project.py
# § - Detect project stacks, manifests, lockfiles and suggested commands · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ── § 1 — CONSTANTS — Files to detect per stack ──

RUST_FILES = ["Cargo.toml", "Cargo.lock"]
NODE_MANIFESTS = ["package.json", "tsconfig.json", "vite.config.js",
                  "vite.config.ts", "next.config.js", "next.config.ts",
                  "next.config.mjs"]
NODE_LOCKS = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock"]
PYTHON_FILES = ["pyproject.toml", "requirements.txt", "poetry.lock",
                "Pipfile", "pytest.ini"]
TASK_RUNNERS = ["Makefile", "justfile"]


# ── § 2 — DETECTION — Per stack ──

def detect_rust(root: Path) -> dict[str, Any] | None:
    present = [f for f in RUST_FILES if (root / f).exists()]
    if not present:
        return None
    return {
        "stack": "Rust",
        "manifests": [f for f in present if f == "Cargo.toml"],
        "lockfiles": [f for f in present if f == "Cargo.lock"],
        "suggested": {
            "min": ["cargo check"],
            "full": ["cargo test", "cargo build"],
            "extra": ["cargo clippy", "cargo fmt --check"],
        },
    }


def detect_node(root: Path) -> dict[str, Any] | None:
    manifests = [f for f in NODE_MANIFESTS if (root / f).exists()]
    locks = [f for f in NODE_LOCKS if (root / f).exists()]
    if not manifests and not locks:
        return None
    scripts: dict[str, str] = {}
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {}) or {}
        except (OSError, json.JSONDecodeError):
            scripts = {}
    runner = "npm"
    if "pnpm-lock.yaml" in locks:
        runner = "pnpm"
    elif "yarn.lock" in locks:
        runner = "yarn"
    suggested_min: list[str] = []
    suggested_full: list[str] = []
    for key in ("typecheck", "lint"):
        if key in scripts:
            suggested_min.append(f"{runner} run {key}")
    for key in ("test", "build"):
        if key in scripts:
            suggested_full.append(f"{runner} run {key}")
    is_ts = (root / "tsconfig.json").exists()
    return {
        "stack": "TypeScript" if is_ts else "Node",
        "manifests": manifests,
        "lockfiles": locks,
        "package_scripts": scripts,
        "runner": runner,
        "suggested": {
            "min": suggested_min,
            "full": suggested_full,
            "extra": [],
        },
    }


def detect_python(root: Path) -> dict[str, Any] | None:
    present = [f for f in PYTHON_FILES if (root / f).exists()]
    if not present:
        return None
    suggested_min: list[str] = []
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists():
        suggested_min.append("pytest")
    return {
        "stack": "Python",
        "manifests": [f for f in present
                      if f in ("pyproject.toml", "requirements.txt",
                               "Pipfile", "pytest.ini")],
        "lockfiles": [f for f in present if f in ("poetry.lock",)],
        "suggested": {
            "min": suggested_min or ["pytest"],
            "full": ["pytest"],
            "extra": ["ruff check .", "mypy ."],
        },
    }


def detect_task_runners(root: Path) -> dict[str, Any] | None:
    present = [f for f in TASK_RUNNERS if (root / f).exists()]
    if not present:
        return None
    targets: list[str] = []
    mk = root / "Makefile"
    if mk.exists():
        try:
            for line in mk.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if (stripped and not stripped.startswith("#")
                        and not stripped.startswith("\t")
                        and ":" in line and "=" not in line.split(":", 1)[0]):
                    target = line.split(":", 1)[0].strip()
                    if target and " " not in target:
                        targets.append(target)
        except OSError:
            pass
    return {
        "stack": "Make/Just",
        "files": present,
        "targets": targets,
    }


# ── § 3 — REPORT — Markdown + JSON ──

def build_report(root: Path) -> tuple[dict[str, Any], int]:
    detections = []
    for fn in (detect_rust, detect_node, detect_python, detect_task_runners):
        res = fn(root)
        if res:
            detections.append(res)
    status_code = 0 if detections else 1
    status = "OK" if detections else "WARN"
    report = {
        "status": status.lower(),
        "root": str(root),
        "detections": detections,
    }
    return report, status_code


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Project Detection")
    lines.append("")
    lines.append("## Status")
    lines.append(report["status"].upper())
    lines.append("")
    detections = report["detections"]
    if not detections:
        lines.append("## Stacks detectadas")
        lines.append("- Nenhuma stack reconhecida na raiz.")
        return "\n".join(lines) + "\n"
    lines.append("## Stacks detectadas")
    for d in detections:
        lines.append(f"- {d['stack']}")
    lines.append("")
    manifests = [m for d in detections for m in d.get("manifests", [])]
    if manifests:
        lines.append("## Manifestos")
        for m in manifests:
            lines.append(f"- `{m}`")
        lines.append("")
    lockfiles = [l for d in detections for l in d.get("lockfiles", [])]
    if lockfiles:
        lines.append("## Lockfiles")
        for l in lockfiles:
            lines.append(f"- `{l}`")
        lines.append("")
    for d in detections:
        if d.get("package_scripts"):
            lines.append("## Scripts disponíveis")
            lines.append("### package.json")
            for k, v in d["package_scripts"].items():
                lines.append(f"- `{k}`: `{v}`")
            lines.append("")
        if d.get("targets"):
            lines.append("## Targets")
            for t in d["targets"]:
                lines.append(f"- `{t}`")
            lines.append("")
    lines.append("## Comandos sugeridos")
    lines.append("### Validação mínima")
    for d in detections:
        for c in d.get("suggested", {}).get("min", []):
            lines.append(f"- `{c}`")
    lines.append("")
    lines.append("### Validação completa")
    for d in detections:
        for c in d.get("suggested", {}).get("full", []):
            lines.append(f"- `{c}`")
    lines.append("")
    return "\n".join(lines) + "\n"


# ── § 4 — ENTRYPOINT — Locate entrypoint responsibilities ──

def main(argv: list[str]) -> int:
    json_mode = "--json" in argv
    root = Path.cwd()
    cache = root / ".agent-cache"
    try:
        cache.mkdir(exist_ok=True)
    except OSError as e:
        print(f"ERRO: não foi possível criar .agent-cache/: {e}",
              file=sys.stderr)
        return 3
    report, code = build_report(root)
    md = render_markdown(report)
    try:
        (cache / "project-detect.md").write_text(md, encoding="utf-8")
        (cache / "project-detect.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8")
    except OSError as e:
        print(f"ERRO: falha ao escrever relatório: {e}", file=sys.stderr)
        return 3
    if json_mode:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        stacks = ", ".join(d["stack"] for d in report["detections"]) or "nenhuma"
        print(f"detect_project: {report['status'].upper()} — stacks: {stacks}")
        print("Relatório: .agent-cache/project-detect.md")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
