# ────────────────────────────────────────────
# CODEX-ENV 2.0 — selftest.py
# § - Exercise the governed lifecycle end to end against a throwaway project · Python
# Taller Dev 2026
# VAI CORINTHIANS!
# ────────────────────────────────────────────

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
FAILURES: list[str] = []

# ── § 1 — HARNESS — run a gate command and assert on its outcome ──


def gate(root: Path, workflow: str, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HARNESS / f"{workflow}_gate.py"), "--cwd", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout + proc.stderr


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"  {'PASS' if condition else 'FAIL'} {name}")
    if not condition:
        FAILURES.append(f"{name} :: {detail}".strip())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


# ── § 2 — FIXTURE — the smallest governed project that is still coherent ──

CONSTITUTION = """tdsl: constitution@1
schema_revision: local:fixture
id: @constitution/fixture
version: 1
status: proposed
purpose: fixture
"""

SPEC = """tdsl: spec@1
schema_revision: local:fixture
id: @spec/001-fixture
version: 1
status: proposed
purpose: fixture

requirements:
  requirement R1:
    statement ln: |
      o sistema faz a coisa
success_criteria:
  criterion S1:
    statement ln: |
      a coisa e observavel
user_journeys:
  journey J1:
    priority: P1
    statement ln: |
      operador faz a coisa
"""

PLAN = """tdsl: plan@1
schema_revision: local:fixture
id: @plan/001-fixture
version: 1
status: proposed
purpose: fixture
spec_ref: @spec/001-fixture

components:
  component C1:
    responsibility ln: |
      faz a coisa
boundaries:
  boundary B1:
    between: [C1 C1]
validations:
  validation V1:
    level: unit
    proves: [@spec/001-fixture#requirement/R1 @spec/001-fixture#criterion/S1]
"""

TASKS = """tdsl: tasks@1
schema_revision: local:fixture
id: @tasks/001-fixture
version: 1
status: proposed
purpose: fixture
spec_ref: @spec/001-fixture
plan_ref: @plan/001-fixture

tasks:
  task T001:
    action ln: |
      faz a coisa
    status: pending
    requirement_refs: [@spec/001-fixture#requirement/R1]
    plan_refs: [@plan/001-fixture#component/C1]
    file_refs: unknown
    validation_refs: [@plan/001-fixture#validation/V1]
    depends_on: []

execution_order: [T001]
"""

ANALYSIS = """tdsl: analysis@1
schema_revision: local:fixture
id: @analysis/001-fixture
version: 1
status: proposed
purpose: fixture
result: pass

findings: []
"""


# ── § 3 — CASES — one per defect or rule this package now claims to hold ──


def run_sdd(root: Path) -> None:
    base = root / ".protocol"
    feature = base / "features" / "001-fixture"

    code, out = gate(root, "sdd", "init", "--name", "fixture")
    check("init succeeds", code == 0, out)
    check("init places skeletons outside the artifact paths",
          (base / ".scaffold" / "spec.tdsl").is_file() and not (base / "spec.tdsl").is_file())

    code, out = gate(root, "sdd", "state")
    check("a fresh project is not reported ready to execute",
          "next_phase: constitution" in out, out)

    write(base / "constitution.tdsl", CONSTITUTION)

    # D1: an anchor with no active_feature field used to be rewritten unchanged
    # while the command still printed OK.
    anchor = base / "project.tdsl"
    stripped = "\n".join(line for line in anchor.read_text(encoding="utf-8").split("\n")
                         if not line.startswith("active_feature"))
    write(anchor, stripped if stripped.endswith("\n") else stripped + "\n")
    code, out = gate(root, "sdd", "feature", "001-fixture")
    check("feature repairs an anchor with no active_feature",
          code == 0 and "active_feature: 001-fixture" in anchor.read_text(encoding="utf-8"), out)

    write(feature / "spec.tdsl", SPEC)
    write(feature / "plan.tdsl", PLAN)
    write(feature / "tasks.tdsl", TASKS)

    code, out = gate(root, "sdd", "check", str(feature / "tasks.tdsl"))
    check("tasks conformance passes", code == 0, out)

    code, out = gate(root, "sdd", "analyze")
    check("coherence passes on a coherent fixture", code == 0, out)

    code, out = gate(root, "sdd", "state")
    check("a record set missing only analysis routes to analyze",
          "next_phase: analyze" in out, out)

    write(feature / "analysis.tdsl", ANALYSIS)
    code, out = gate(root, "sdd", "state")
    check("a complete record set routes to execute", "next_phase: execute" in out, out)

    # The whole point: a delivered feature and a feature mid-flight used to be
    # the same state, because only file existence was consulted.
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "delivered")
    check("close records delivery", code == 0, out)
    code, out = gate(root, "sdd", "state")
    check("a delivered feature stops routing", "next_phase: idle" in out, out)
    check("the delivered feature stays in the register", "delivered" in out, out)

    code, out = gate(root, "sdd", "gate", "specify")
    check("a phase refuses to run off a closed feature", code != 0, out)

    code, out = gate(root, "sdd", "feature", "001-fixture")
    check("the cursor cannot silently reopen a closed feature", code != 0, out)
    code, out = gate(root, "sdd", "feature", "001-fixture", "--reopen")
    check("--reopen puts it back in work", code == 0, out)

    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "superseded")
    check("superseded without a successor refuses", code != 0, out)
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "abandoned")
    check("abandoned without a reason refuses", code != 0, out)

    # A successor that exists is not enough: naming itself satisfies the letter
    # and records no substitution at all.
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "superseded",
                     "--successor", "001-fixture")
    check("a feature cannot succeed itself", code != 0, out)
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "superseded",
                     "--successor", "099-nonexistent")
    check("an unknown successor refuses", code != 0, out)

    # Arguments only mean something in the state that requires them.
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "delivered",
                     "--reason", "qualquer")
    check("--reason outside abandoned refuses", code != 0, out)
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "delivered",
                     "--successor", "001-fixture")
    check("--successor outside superseded refuses", code != 0, out)

    gate(root, "sdd", "feature", "003-abandoned")
    gate(root, "sdd", "close", "003-abandoned", "--as", "abandoned", "--reason", "escopo caiu")
    gate(root, "sdd", "feature", "001-fixture", "--reopen")
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "superseded",
                     "--successor", "003-abandoned")
    check("an abandoned successor refuses", code != 0, out)

    # A -> B then B -> A asserts that everything replaced everything.
    gate(root, "sdd", "feature", "004-later")
    gate(root, "sdd", "close", "004-later", "--as", "superseded", "--successor", "001-fixture")
    gate(root, "sdd", "feature", "001-fixture", "--reopen")
    code, out = gate(root, "sdd", "close", "001-fixture", "--as", "superseded",
                     "--successor", "004-later")
    check("a succession cycle refuses", code != 0, out)

    gate(root, "sdd", "feature", "001-fixture", "--reopen")

    # Idempotence: the register is rewritten in place, never appended beside itself.
    gate(root, "sdd", "close", "001-fixture", "--as", "heritage")
    gate(root, "sdd", "feature", "002-second")
    gate(root, "sdd", "close", "002-second", "--as", "historical")
    text = anchor.read_text(encoding="utf-8")
    check("the anchor holds exactly one register", text.count("\nfeatures:") == 1, text)
    check("both features are registered",
          "001-fixture" in text and "002-second" in text, text)


def run_boot(root: Path) -> None:
    proc = subprocess.run([sys.executable, str(HARNESS / "session_init.py"), "--hook"],
                          cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    report = root / ".agent-cache" / "session-report.md"
    # D2: rendering the governance table used to raise KeyError and take the
    # whole boot report down with it.
    check("boot does not crash on a governed project",
          "Traceback" not in (proc.stdout + proc.stderr), proc.stdout + proc.stderr)
    check("boot renders the governance table",
          report.is_file() and "Governan" in report.read_text(encoding="utf-8"))
    check("boot context exposes workflow feature and next phase",
          all(label in proc.stdout for label in
              ("Workflow: sdd", "Feature ativa:", "Próxima fase:")),
          proc.stdout)



DECOMPOSITION_CYCLE = """tdsl: local:decomposition@1
schema_revision: local:decomposition@1
id: @decomposition/001-fixture
version: 1
status: proposed
purpose: fixture
tasks_ref: @tasks/001-fixture

subtasks:
  subtask T001.1:
    parent: T001
    action ln: |
      a
    status: pending
    file_refs: unknown
    depends_on: [T001.2]
  subtask T001.2:
    parent: T001
    action ln: |
      b
    status: pending
    file_refs: unknown
    depends_on: [T001.1]
"""


def run_decomposition(root: Path) -> None:
    feature = root / ".protocol" / "features" / "001-fixture"
    path = feature / "decomposition.tdsl"
    write(path, DECOMPOSITION_CYCLE)
    code, out = gate(root, "sdd", "check", str(path))
    # The subtask check validated parents and cross-parent edges but had no cycle
    # detection at all, so a decomposition that could never run passed.
    check("a cyclic decomposition refuses", code != 0 and "cycle" in out, out)

    write(path, DECOMPOSITION_CYCLE.replace("depends_on: [T001.2]", "depends_on: []"))
    code, out = gate(root, "sdd", "check", str(path))
    check("an acyclic decomposition passes", code == 0, out)



def run_integral(root: Path) -> None:
    code, out = gate(root, "sdd", "init", "--name", "plano", "--mode", "integral")
    check("integral init succeeds", code == 0, out)
    write(root / ".protocol" / "constitution.tdsl", "tdsl: constitution@1\n")
    for fid in ("001-alpha", "002-beta"):
        (root / ".protocol" / "features" / fid).mkdir(parents=True, exist_ok=True)
    for a in ("spec", "plan", "tasks", "analysis"):
        write(root / ".protocol" / "features" / "001-alpha" / f"{a}.tdsl", f"tdsl: {a}@1\n")
    code, out = gate(root, "sdd", "state", "--json")
    snap = json.loads(out) if code == 0 else {}
    check("integral routes planning to the unplanned feature",
          snap.get("next_phase") == "specify" and snap.get("next_feature") == "002-beta", out)
    code, out = gate(root, "sdd", "roadmap")
    check("roadmap reports incomplete planning", "planning incomplete" in out, out)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    workspace = Path(tempfile.mkdtemp(prefix="protocol-selftest-"))
    try:
        for name in ("sdd", "decomposition", "boot", "integral"):
            root = workspace / name
            root.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True)
            print(f"[{name}]")
            if name == "sdd":
                run_sdd(root)
            elif name == "decomposition":
                run_sdd(root)          # a task set to decompose
                run_decomposition(root)
            elif name == "boot":
                run_sdd(root)          # a governed project to render
                run_boot(root)
            else:
                run_integral(root)
            print("")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

    if FAILURES:
        print(f"selftest: FAIL ({len(FAILURES)})")
        for failure in FAILURES:
            print(f"  {failure.splitlines()[0]}")
        return 1
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
