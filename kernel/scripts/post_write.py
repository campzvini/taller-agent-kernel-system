# ────────────────────────────────────────────
# TASK 2.2.0 — post_write.py
# § - Expose the stable post_write.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'runtime/structure/post_write.py')
