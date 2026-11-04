# ────────────────────────────────────────────
# TASK 2.2.0 — commit_context.py
# § - Collect diff context for commit without executing git add or git commit · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def is_clean(short_status: str) -> bool:
    return not short_status.strip()


# ── § 2 — COLLECTORS — Collect bounded observations from existing sources ──

def collect_status(root: Path) -> tuple[str, str]:
    _, full = run_git(["status"], root)
    _, short = run_git(["status", "--short"], root)
    return full, short


def collect_staged(root: Path) -> tuple[str, str]:
    _, stat = run_git(["diff", "--staged", "--stat"], root)
    _, diff = run_git(["diff", "--staged"], root)
    return stat, diff


def collect_unstaged(root: Path) -> tuple[str, str]:
    _, stat = run_git(["diff", "--stat"], root)
    _, diff = run_git(["diff"], root)
    return stat, diff


def parse_modified_files(short_status: str) -> list[str]:
    files: list[str] = []
    for line in short_status.splitlines():
        if not line.strip():
            continue
        # format: XY path or XY old_path -> new_path
        parts = line[3:].strip()
        if " -> " in parts:
            parts = parts.split(" -> ")[-1]
        files.append(parts.strip())
    return files



def collect_delivery_state(root: Path, owned_paths: list[str] | None = None) -> dict[str, Any]:
    """Report actual Git changes; explicit path scope never implies authority or ownership."""
    code, raw = run_git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], root)
    if code:
        raise ValueError("cannot inspect Git delivery state")
    fields = iter(raw.split("\0"))
    changes = []
    from code_map import SOURCE_SUFFIXES
    for item in fields:
        if not item:
            continue
        status, path = item[:2], item[3:]
        original = next(fields, "") if "R" in status or "C" in status else None
        changes.append({"path": path, "original_path": original, "status": status,
                        "code_candidate": any(Path(name).suffix.lower() in SOURCE_SUFFIXES for name in (path, original) if name)})
    head_code, head = run_git(["rev-parse", "HEAD"], root)
    selected = set(owned_paths or [])
    return {"head": head.strip() if head_code == 0 else None,
            "changes": changes,
            "code_candidates": [item["path"] for item in changes if item["code_candidate"]],
            "scope_provided": owned_paths is not None,
            "selected_paths": [item["path"] for item in changes if item["path"] in selected],
            "excluded_paths": [item["path"] for item in changes if item["path"] not in selected],
            "authority": "not_inferred", "staged_by_helper": False}

def group_by_directory(files: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for f in files:
        p = Path(f)
        directory = str(p.parent) if str(p.parent) != "." else "(root)"
        groups.setdefault(directory, []).append(f)
    return groups


# ── § 3 — MULTI — UNIT DETECTION ──

_DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}
_TEST_PATTERNS = ["test", "spec", "tests", "__test__"]
_CONFIG_EXTENSIONS = {".toml", ".json", ".yaml", ".yml", ".env", ".ini", ".cfg"}


def _is_doc(path: str) -> bool:
    return Path(path).suffix.lower() in _DOC_EXTENSIONS


def _is_test(path: str) -> bool:
    p = path.lower()
    return any(pat in p for pat in _TEST_PATTERNS)


def _is_config(path: str) -> bool:
    return Path(path).suffix.lower() in _CONFIG_EXTENSIONS


def detect_multi_unit_signals(files: list[str]) -> list[str]:
    """Return list of human-readable signals suggesting multiple logical units."""
    signals: list[str] = []
    if not files:
        return signals

    docs = [f for f in files if _is_doc(f)]
    code = [f for f in files if not _is_doc(f) and not _is_config(f)]
    tests = [f for f in files if _is_test(f)]
    configs = [f for f in files if _is_config(f)]

    # Docs + code without obvious relation
    if docs and code:
        # check if docs are under docs/specs — acceptable relation to code
        spec_docs = [d for d in docs if "specs" in d.lower() or "adr" in d.lower()]
        unrelated_docs = [d for d in docs if d not in spec_docs]
        if unrelated_docs and code:
            signals.append(
                f"Mix of documentation ({len(unrelated_docs)} files) "
                f"and code ({len(code)} files) with no apparent relation."
            )

    # Tests from different modules (multiple distinct test directories)
    if tests:
        test_dirs = {str(Path(t).parent) for t in tests}
        if len(test_dirs) > 1:
            signals.append(
                f"Tests from {len(test_dirs)} distinct directories: "
                + ", ".join(sorted(test_dirs))
            )

    # Config files alongside feature code
    if configs and code:
        signals.append(
            f"Config files ({len(configs)}) mixed with feature code ({len(code)})."
        )

    # Many directories without common pattern
    dirs = {str(Path(f).parent) for f in files}
    if len(dirs) > 4:
        signals.append(
            f"Changes spread across {len(dirs)} directories with no clear common scope."
        )

    return signals


def detect_probable_scopes(groups: dict[str, list[str]]) -> list[str]:
    """Derive probable conventional-commit scopes from directory names."""
    scopes: list[str] = []
    for directory in groups:
        parts = Path(directory).parts
        # take the most specific meaningful part (skip root, src, lib)
        skip = {".", "(root)", "src", "lib", "app", "tests", "test"}
        for part in reversed(parts):
            if part.lower() not in skip:
                candidate = part.lower().replace("_", "-")
                if candidate not in scopes:
                    scopes.append(candidate)
                break
        else:
            if "(root)" not in scopes and directory == "(root)":
                scopes.append("root")
    return scopes


# ── § 4 — VALIDATION EVIDENCE — Locate validation evidence responsibilities ──

def check_agent_cache(root: Path) -> list[str]:
    cache_dir = root / ".agent-cache"
    if not cache_dir.exists():
        return []
    return [f.name for f in sorted(cache_dir.iterdir()) if f.is_file()]


# ── § 5 — REPORT GENERATION — Locate report generation responsibilities ──

def build_report(
    root: Path,
    full_status: str,
    short_status: str,
    staged_stat: str,
    staged_diff: str,
    unstaged_stat: str,
    unstaged_diff: str,
    files: list[str],
    groups: dict[str, list[str]],
    scopes: list[str],
    signals: list[str],
    cache_files: list[str],
) -> tuple[str, dict[str, Any]]:
    status_label = "WARN" if signals else "OK"
    has_staged = bool(staged_stat.strip())
    has_unstaged = bool(unstaged_stat.strip())

    # ── Markdown ──
    md_lines: list[str] = ["# Commit Context", "", "## Status", status_label, ""]

    md_lines += ["## Working tree", "```", short_status.strip() or "(clean)", "```", ""]

    if has_staged:
        md_lines += ["## Staged diff stat", "```", staged_stat.strip(), "```", ""]

    if has_unstaged:
        md_lines += ["## Unstaged diff stat", "```", unstaged_stat.strip(), "```", ""]

    if groups:
        md_lines.append("## Arquivos por área")
        for directory, dir_files in sorted(groups.items()):
            md_lines.append(f"### `{directory}/`")
            for f in dir_files:
                md_lines.append(f"- `{f}`")
        md_lines.append("")

    if scopes:
        md_lines += ["## Escopos prováveis"]
        for s in scopes:
            md_lines.append(f"- `{s}`")
        md_lines.append("")

    if signals:
        md_lines += ["## Possíveis unidades lógicas"]
        for i, sig in enumerate(signals, 1):
            md_lines.append(f"{i}. {sig}")
        md_lines.append("")
    else:
        md_lines += ["## Possíveis unidades lógicas", "Nenhum sinal detectado.", ""]

    md_lines.append("## Validação detectada")
    if cache_files:
        for cf in cache_files:
            md_lines.append(f"- `.agent-cache/{cf}`")
    else:
        md_lines.append("- Nenhuma evidência em `.agent-cache/`.")
    md_lines.append("")

    if signals:
        md_lines += [
            "## Recomendação",
            "Considerar separar commits por unidade lógica antes de prosseguir.",
            "",
        ]

    md = "\n".join(md_lines)

    # ── JSON ──
    data: dict[str, Any] = {
        "status": status_label.lower(),
        "repo_root": str(root),
        "has_staged": has_staged,
        "has_unstaged": has_unstaged,
        "files": files,
        "probable_scopes": scopes,
        "multi_unit_signals": signals,
        "validation_cache": cache_files,
    }

    return md, data


# ── § 6 — MAIN — Dispatch the public command and publish its report ──

def main() -> int:
    parser = argparse.ArgumentParser(description="Observe commit context without staging or granting authority")
    parser.add_argument("--owned-path", action="append", default=None)
    args = parser.parse_args()
    cwd = Path.cwd()
    root = git_root(cwd)
    if root is None:
        print("ERROR: not inside a git repository.", file=sys.stderr)
        return 3

    full_status, short_status = collect_status(root)
    staged_stat, staged_diff = collect_staged(root)
    unstaged_stat, unstaged_diff = collect_unstaged(root)

    delivery = collect_delivery_state(root, args.owned_path)
    files = [change["path"] for change in delivery["changes"]]
    groups = group_by_directory(files)
    scopes = detect_probable_scopes(groups)
    signals = detect_multi_unit_signals(files)
    cache_files = check_agent_cache(root)

    md, data = build_report(
        root, full_status, short_status,
        staged_stat, staged_diff,
        unstaged_stat, unstaged_diff,
        files, groups, scopes, signals, cache_files,
    )

    data["delivery"] = delivery
    md += "\n\n## Delivery scope observation\n\n```json\n" + json.dumps(data["delivery"], ensure_ascii=False, indent=2) + "\n```\n"

    cache_dir = root / ".agent-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    md_path = cache_dir / "commit-context.md"
    json_path = cache_dir / "commit-context.json"

    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    exit_code = 1 if signals else 0
    status_label = "WARN" if signals else "OK"

    print(f"[{status_label}] commit-context written to {md_path}")
    if signals:
        print(f"  Signals detected: {len(signals)} possible logical unit(s).")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
