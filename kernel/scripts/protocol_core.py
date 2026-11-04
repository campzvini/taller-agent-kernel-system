# ────────────────────────────────────────────
# TASK 2.2.0 — protocol_core.py
# § - Expose the stable protocol_core.py entrypoint · Python
# VAI CORINTHIANS!
# ────────────────────────────────────────────

# ── § 1 — ENTRYPOINT — Load the authoritative departmental implementation ──
from _entrypoint import load as _load_task_entrypoint

_load_task_entrypoint(globals(), 'governance/sdd/protocol_core.py')
