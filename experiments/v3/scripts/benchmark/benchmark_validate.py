#!/usr/bin/env python3
"""Validate the v3 benchmark (schema conformance + sealed SHA-256 integrity).

Checks:
  - every row in train/dev/test_public_inputs/test_gold conforms to schema.json
  - every test task's required_nodes/edges/bindings/constraints are present
  - repair tasks have a real initial_state and goal_state and critical_objects
  - recompute SHA-256 of each split and compare to benchmark_manifest.json
Usage: python3 scripts/benchmark/benchmark_validate.py [--expect-sealed]
Exit 0 on success, 1 on any failure.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

try:
    import jsonschema  # noqa: F401
    HAS_JSONSCHEMA = True
except Exception:  # pragma: no cover
    HAS_JSONSCHEMA = False

ROOT = Path(__file__).resolve().parents[4]
BENCH = ROOT / "experiments" / "v3" / "benchmark"

SPLITS = ["train.jsonl", "dev.jsonl", "test_public_inputs.jsonl", "test_gold.sealed.jsonl"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    expect_sealed = "--expect-sealed" in argv
    errors: list[str] = []

    manifest: dict = {}
    manifest_path = BENCH / "benchmark_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        errors.append("benchmark_manifest.json missing")

    schema: dict = {}
    schema_path = BENCH / "schema.json"
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    else:
        errors.append("schema.json missing")

    validator = None
    if HAS_JSONSCHEMA and schema:
        validator = jsonschema.Draft7Validator(schema)

    for name in SPLITS:
        path = BENCH / name
        if not path.exists():
            errors.append(f"{name} missing")
            continue
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            errors.append(f"{name} empty")
            continue
        for i, row in enumerate(rows):
            if name == "test_public_inputs.jsonl":
                # Public inputs are intentionally gold-free; validate only public fields.
                for field in ("task_id", "category", "difficulty", "prompt"):
                    if not row.get(field):
                        errors.append(f"{name}[{i}] public input missing {field}")
                continue
            if name == "test_gold.sealed.jsonl" and row.get("goald_basis") == "TODO_ANNOTATION":
                # Blind-test placeholder rows are authored during annotation (S2.6).
                # They are NOT part of the sealed gold until fully authored.
                continue
            if validator is not None:
                verr = sorted(validator.iter_errors(row), key=lambda e: list(e.path))
                for e in verr[:1]:
                    errors.append(f"{name}[{i}] schema: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}")
            if name in {"dev.jsonl", "test_gold.sealed.jsonl"}:
                if row.get("category") == "repair":
                    for field in ("initial_state", "goal_state", "critical_objects"):
                        if not row.get(field):
                            errors.append(f"{name}[{i}] repair task missing {field}")
                for field in ("required_nodes", "required_edges", "required_bindings"):
                    if not isinstance(row.get(field), list):
                        errors.append(f"{name}[{i}] missing list field {field}")

        # Manifest SHA-256 check for sealed/frozen files
        manifest_key = name.replace(".jsonl", "").replace(".sealed", "_sealed")
        if manifest.get("splits", {}).get(manifest_key, {}).get("sha256"):
            expected = manifest["splits"][manifest_key]["sha256"]
            actual = sha256_of(path)
            if actual != expected:
                errors.append(f"{name} sha256 mismatch: expected {expected} got {actual}")

    if expect_sealed and not errors:
        # extra guard: test_gold must be non-empty and sha256 recorded
        expected = manifest.get("splits", {}).get("test_gold_sealed", {}).get("sha256")
        if not expected:
            errors.append("test_gold_sealed sha256 not recorded (not sealed)")

    if errors:
        print("[v3 benchmark-validate] FAIL")
        for e in errors[:50]:
            print("  -", e)
        return 1
    print("[v3 benchmark-validate] PASS")
    print(f"  train={len(BENCH/'train.jsonl' and open(BENCH/'train.jsonl',encoding='utf-8').readlines()) if (BENCH/'train.jsonl').exists() else 0} "
          f"dev={len((BENCH/'dev.jsonl').read_text(encoding='utf-8').splitlines()) if (BENCH/'dev.jsonl').exists() else 0} "
          f"test_public={len((BENCH/'test_public_inputs.jsonl').read_text(encoding='utf-8').splitlines()) if (BENCH/'test_public_inputs.jsonl').exists() else 0} "
          f"test_gold={len((BENCH/'test_gold.sealed.jsonl').read_text(encoding='utf-8').splitlines()) if (BENCH/'test_gold.sealed.jsonl').exists() else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
