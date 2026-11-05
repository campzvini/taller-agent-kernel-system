# ────────────────────────────────────────────
# TASK 2.2.1 — spec_lint.py
# § - Expose the stable spec_lint.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'governance/specification/spec_lint.py')
