# ────────────────────────────────────────────
# TASK 2.2.1 — session_init.py
# § - Expose the stable session_init.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'context/session/session_init.py')
