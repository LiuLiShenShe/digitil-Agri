#!/usr/bin/env python3
"""Stamp Annotator-2 approval onto a sealed test set and re-seal hashes.

Called ONLY after Annotator 2 (the human reviewer) has explicitly approved the
revision. This is the deterministic freeze-approval step that replaces the
hand-edited `review_status` fields:

  * sets every task's `review_status` from `pending` -> `approved` on the gold
    file (and, if present, on annotation packets);
  * re-computes the SHA-256 of the approved gold + doc files;
  * rewrites MANIFEST.sha256 and updates benchmark_manifest.json.

It is a pure mechanical transform: it verifies every task currently reports
`review_status == "pending"` and errors if any is already `approved` (idempotency
guard) or if any is `rejected`/`needs_revision` (nothing to approve). It does NOT
touch any gold content -- only the review_status field.

Usage:
    python3 benchmark/scripts/approve_freeze.py [--packets BENCH_PACKETS_DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

BENCH = pathlib.Path(__file__).resolve().parents[1]
V2_DIR = BENCH / "test_v2"
GOLD = V2_DIR / "test_v2_gold.jsonl"
PUBLIC = V2_DIR / "test_v2_public_inputs.jsonl"
MANIFEST = V2_DIR / "MANIFEST.sha256"

# Documents whose hashes we re-seal once approval is stamped (approval itself
# does not change them, but the manifest should reflect the sealed tree).
DOC_FILES = [
    "DATASHEET.md",
    "CHANGELOG.md",
    "ANNOTATION_REPORT.md",
    "ANNOTATOR2_REVIEW.md",
]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_items(path: pathlib.Path) -> list[dict]:
    """Load either a JSONL file (one object per line) or a JSON file (one object)."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("{"):
        return [json.loads(raw)]
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def dump_items(path: pathlib.Path, rows: list[dict]) -> None:
    # Preserve single-object JSON files as a single object; JSONL as one-per-line.
    first = path.read_text(encoding="utf-8").strip()
    if first.startswith("{"):
        with path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(rows[0], ensure_ascii=False, indent=2) + "\n")
    else:
        with path.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


def stamp(path: pathlib.Path) -> int:
    rows = load_items(path)
    changed = 0
    for r in rows:
        cur = r.get("review_status")
        if cur == "approved":
            raise SystemExit(
                f"REFUSE re-approve: {path} already contains an 'approved' task "
                f"({r.get('task_id')}). Idempotency guard: freeze is a one-way door. "
                "If you need to change gold after approval, bump benchmark_version "
                "and regenerate a NEW frozen set -- do not un-approve."
            )
        if cur in ("rejected", "needs_revision"):
            raise SystemExit(
                f"REFUSE approve: {path} task {r.get('task_id')} is "
                f"'{cur}', not 'pending'. Nothing to approve."
            )
        r["review_status"] = "approved"
        changed += 1
    dump_items(path, rows)
    return changed


def manifest_snapshot() -> list[str]:
    lines = []
    # gold + public have stable names; keep gold+public order, then docs.
    for name in [GOLD.name, PUBLIC.name] + DOC_FILES:
        p = V2_DIR / name
        if not p.exists():
            print(f"[warn] missing manifest entry file {name} -- skipping", file=sys.stderr)
            continue
        lines.append(f"{sha256(p)}  {name}")
    return lines


def write_manifest(lines: list[str]) -> None:
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--packets-only",
        action="store_true",
        help="stamp annotation packets only (skip the already-approved gold file)",
    )
    ap.add_argument(
        "--packets",
        default=str(BENCH / "annotation_packets"),
        help="annotation packets dir to stamp (T031-T035)",  # may not exist
    )
    args = ap.parse_args()

    n_packets = 0
    if not args.packets_only:
        if not GOLD.exists():
            print(f"FATAL: {GOLD} not found", file=sys.stderr)
            return 2
        print(f"[1/3] stamping gold: {GOLD.name}")
        n_gold = stamp(GOLD)
    else:
        n_gold = 0
        print(f"[1/3] --packets-only: leaving gold untouched")

    packets_dir = pathlib.Path(args.packets)
    n_packets = 0
    if packets_dir.is_dir():
        for p in sorted(packets_dir.glob("*_annotation_packet.json")):
            n_packets += stamp(p)
            print(f"      stamped {p.name}")

    print(f"[2/3] re-sealing MANIFEST.sha256")
    lines = manifest_snapshot()
    write_manifest(lines)
    for l in lines:
        print(f"      {l}")

    # update benchmark_manifest.json with the new test_v2 gold hash
    bm = BENCH / "benchmark_manifest.json"
    data = json.loads(bm.read_text(encoding="utf-8"))
    if not args.packets_only:
        splits = data.setdefault("splits", {})
        for key, fname in (("test_v2_gold", GOLD.name), ("test_v2_public_inputs", PUBLIC.name)):
            p = V2_DIR / fname
            splits[key]["sha256"] = sha256(p)
        data["benchmark_version"] = "v2-sealed"
        data["note"] = (
            "test_v2 approved by Annotator 2 (2026-08-07) and frozen. All tasks "
            "`approved`; freeze is a one-way door -- future edits require a version "
            "bump + full re-run."
        )
        bm.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.packets_only:
        print(f"\nOK  stamped {n_packets} packet(s); gold + manifest untouched.")
        return 0

    print(f"[3/3] bench_manifest.updated")
    print(f"\nOK  stamped {n_gold} gold tasks" +
          (f" + {n_packets} packet(s)" if n_packets else "") + " to 'approved'; manifest resealed.")

    # verify
    r = subprocess.run(["sha256sum", "-c", str(MANIFEST)], cwd=str(V2_DIR),
                       capture_output=True, text=True)
    print("verify:\n" + r.stdout)
    if r.returncode != 0:
        print("FATAL: manifest verification failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
