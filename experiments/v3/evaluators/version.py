"""Evaluator versioning + fingerprint (G, P1-5).

Introduces evaluator_v2.2 (the scorer-correctness rebuild: critical-recall id_map,
memory replay snapshot, unit/binding contract alignment). Every run record is
stamped with EVALUATOR_VERSION + EVALUATOR_HASH (sha256 over the concatenated
scorer module sources), so the SOTA gate can refuse to score old runs against new
code — a provenance guard that prevents "regressed scorer + stale results" gaming.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

EVALUATOR_VERSION = "evaluator_v2.2"

# Scorer modules whose source contributes to the fingerprint.
_SCORER_MODULES = (
    "metrics.py", "node_match.py", "edge_match.py", "binding_match.py",
    "rule_engine.py", "replay.py", "trace_evidence.py", "state_match.py",
    "query_cvsr.py", "register_adapters.py", "task_types.py",
)

_EVAL_DIR = Path(__file__).resolve().parent


def evaluator_fingerprint() -> str:
    """sha256 over the concatenated source of the scorer modules (stable, deterministic)."""
    h = hashlib.sha256()
    for name in _SCORER_MODULES:
        p = _EVAL_DIR / name
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(b"<missing>")
        h.update(b"\0")
    return h.hexdigest()


def evaluator_provenance() -> dict[str, str]:
    return {"evaluator_version": EVALUATOR_VERSION, "evaluator_hash": evaluator_fingerprint()}


def stamp_record(rec: dict) -> dict:
    """Attach evaluator provenance to a run record (mutates + returns it)."""
    rec["evaluator_version"] = EVALUATOR_VERSION
    rec["evaluator_hash"] = evaluator_fingerprint()
    return rec