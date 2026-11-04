# ────────────────────────────────────────────
# TASK 2.2.0 — detect_project.py
# § - Expose the stable detect_project.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'context/acquisition/detect_project.py')
