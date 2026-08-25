"""Tests for External300 review-identity correction (post-2026-08-25 honesty fix).

These tests enforce that the External300 benchmark is NOT misrepresented as an
independently double-blind reviewed benchmark. The original run filled Reviewer A,
Reviewer B and Adjudicator columns from ONE author confirmation; that must not be
read back as three independent reviewers.
"""
from __future__ import annotations

import json
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
RESULTS_EXT300 = V3 / "results" / "external300"
BENCH = V3 / "benchmark" / "external300_candidate"


def _load_fc(name: str) -> dict:
    p = RESULTS_EXT300 / name
    assert p.exists(), f"missing freeze-check file: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def test_freeze_check_has_three_way_review_split():
    fc = _load_fc("FREEZE_CHECK_POSTRUN_CORRECTED.json")
    names = {c["check"] for c in fc["checks"]}
    for expected in {
        "review_records_complete",
        "author_confirmation_present",
        "independent_human_review_evidence",
    }:
        assert expected in names, f"missing check {expected} in {names}"


def test_independent_human_review_evidence_is_blocked_not_passed():
    fc = _load_fc("FREEZE_CHECK_POSTRUN_CORRECTED.json")
    indep = next(c for c in fc["checks"] if c["check"] == "independent_human_review_evidence")
    assert indep["status"] != "PASS", "independent review must NOT be reported as PASS"
    assert indep["status"] in {"BLOCKED", "FAIL"}, indep["status"]
    # it must read NOT_ESTABLISHED
    assert "NOT_ESTABLISHED" in indep["detail"], indep["detail"]


def test_corrected_freeze_check_has_no_independently_reviewed_pass():
    text = (RESULTS_EXT300 / "FREEZE_CHECK_POSTRUN_CORRECTED.json").read_text(encoding="utf-8")
    assert "independently reviewed PASS" not in text, "must not claim 300/300 independently reviewed"
    assert "independently reviewed" not in text or "NOT" in text or "not" in text


def test_review_provenance_correction_file_exists_with_correct_interpretation():
    corr = RESULTS_EXT300 / "REVIEW_PROVENANCE_CORRECTION.json"
    assert corr.exists(), "REVIEW_PROVENANCE_CORRECTION.json missing"
    data = json.loads(corr.read_text(encoding="utf-8"))
    interp = data.get("corrected_interpretation", {})
    assert interp.get("human_review_mode") == "author_confirmation", interp
    assert interp.get("human_reviewer_count") == 1, interp
    assert interp.get("independent_review") is False, interp
    assert interp.get("double_human_review") is False, interp
    assert interp.get("gold_standard") is False, interp
    assert interp.get("benchmark_role") == "author-reviewed controlled benchmark", interp


def test_review_queue_untouched_single_author_source():
    queue = BENCH / "external300_review_queue.csv"
    assert queue.exists()
    import csv
    rows = list(csv.DictReader(queue.open(encoding="utf-8")))
    assert len(rows) == 300, f"expected 300 rows, got {len(rows)}"
    # All reviewer_a_comments derive from the SAME single author confirmation string
    a_comments = {r.get("reviewer_a_comments", "") for r in rows}
    # The confirmation text contains the unified execution directive marker
    unified = [c for c in a_comments if "unified execution directive" in c]
    assert unified, "expected the single author-confirmation marker in reviewer_a_comments"


def test_protocol_deviation_document_exists():
    dev = RESULTS_EXT300 / "PROTOCOL_DEVIATION_EXTERNAL300.md"
    assert dev.exists(), "PROTOCOL_DEVIATION_EXTERNAL300.md missing"
    text = dev.read_text(encoding="utf-8")
    assert "author_confirmation" in text or "author-generated" in text, "deviation doc must state author-review identity"
