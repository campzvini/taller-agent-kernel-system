# ────────────────────────────────────────────
# TASK 2.2.0 — code_map.py
# § - Expose the stable code_map.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'context/mapping/code_map.py')
