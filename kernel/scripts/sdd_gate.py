# ────────────────────────────────────────────
# TASK 2.2.0 — sdd_gate.py
# § - Expose the stable sdd_gate.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'governance/sdd/sdd_gate.py')
