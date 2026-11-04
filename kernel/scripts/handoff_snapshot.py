# ────────────────────────────────────────────
# TASK 2.2.0 — handoff_snapshot.py
# § - Expose the stable handoff_snapshot.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'memory/handoff/handoff_snapshot.py')
