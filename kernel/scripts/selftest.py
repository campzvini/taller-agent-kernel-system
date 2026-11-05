# ────────────────────────────────────────────
# TASK 2.2.1 — selftest.py
# § - Expose the stable selftest.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'assurance/testing/selftest.py')
