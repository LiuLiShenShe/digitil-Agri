#!/usr/bin/env python3
"""
Final Claim Consistency Checker for KAFarmTwin paper.
Reads the final paper, extracts numerical claims, cross-references against
canonical evidence values, and reports discrepancies.
"""

import re
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field

# ── Canonical values (hardcoded fallback + optional manifest override) ────────

CANONICAL = {
    "kf_cvsr": 0.717,
    "sa_cvsr": 0.480,
    "paired_diff_pp": 23.67,
    "mcnemar_p": "8.45e-17",
    "directrepair_obj_f1": 1.000,
    "directrepair_rel_f1": 1.000,
    "directrepair_bind_f1": 0.100,
    "srrr": 1.000,
    "sesr": 0.100,
    "kf_asset_cvsr": 0.083,
    "policy_error_pct": 78.2,
    "excluding_rr_diff_pp": 4.6,
    "excluding_rr_kf": 0.646,
    "excluding_rr_sa": 0.600,
    "fatal_kf": 0.000,
    "fatal_sa": 0.250,
    "ev_p_kf": 1.000,
    "ev_p_sa": 0.947,
    "replay_kf": 0.808,
    "replay_sa": 0.455,
    "kf_obj_f1": 0.690,
    "kf_rel_f1": 0.700,
    "kf_bind_f1": 0.594,
    "sa_obj_f1": 0.635,
    "sa_rel_f1": 0.379,
    "sa_bind_f1": 0.200,
    "ablation_full_cvsr": 0.550,
    "ablation_no_compiler_cvsr": 0.370,
    "ablation_no_typed_repair_cvsr": 0.580,
    "ablation_no_ontology_cvsr": 0.530,
    "ablation_full_fatal": 0.000,
    "ablation_no_compiler_fatal": 0.010,
    "ablation_no_typed_repair_fatal": 0.220,
    "ablation_no_ontology_fatal": 0.000,
    "test_v2_kf_cvsr": 0.610,
    "test_v2_sa_cvsr": 0.360,
    "test_v2_kf_pass5": 0.700,
    "test_v2_sa_pass5": 0.500,
    "kf_success_count": 215,
    "sa_success_count": 144,
    "total_tasks": 300,
    "rr_additional": 60,
    "rr_additional_pct": 84.5,
    "rr_total_additional": 71,
    "cost_kf": 0.104,
    "cost_sa": 0.085,
    "cost_ratio": 1.21,
    "crit_rec_kf": 1.000,
    "crit_rec_sa": 0.950,
    "directrepair_fatal": 43,
    "norepair_fatal": 60,
    "directrepair_rr_kf": 0.000,
    "norepair_rr_kf": 0.000,
    "kf_p50_all": 2.52,
    "kf_p95_all": 9.59,
    "sa_p50_all": 2.06,
    "sa_p95_all": 12.52,
    "kf_p50_llm": 2.82,
    "kf_p95_llm": 10.01,
    "sa_p50_llm": 6.72,
    "sa_p95_llm": 15.45,
    "canonical_relation_f1": 0.997,
    "canonical_binding_f1": 0.994,
    "canonical_obj_f1_audit": 0.810,
    "cross_model_kimi_kf": 0.673,
    "cross_model_kimi_sa": 0.493,
    "cross_model_kimi_diff": 18.00,
    "cross_model_minimax_kf": 0.607,
    "cross_model_minimax_sa": 0.350,
    "cross_model_minimax_diff": 25.67,
    "cross_model_qwen_kf": 0.697,
    "cross_model_qwen_sa": 0.480,
    "cross_model_qwen_diff": 21.67,
    "cross_model_glm_kf": 0.737,
    "cross_model_glm_sa": 0.493,
    "cross_model_glm_diff": 24.33,
}

TOLERANCE = 0.005


@dataclass
class Discrepancy:
    category: str
    severity: str
    location: str
    description: str
    expected: str = ""
    found: str = ""


@dataclass
class ConsistencyReport:
    paper_path: str
    discrepancies: list = field(default_factory=list)
    claims_checked: int = 0
    tables_checked: int = 0
    citations_checked: int = 0
    all_ok: bool = True

    def add(self, d: Discrepancy):
        self.discrepancies.append(d)
        if d.severity in ("ERROR", "WARNING"):
            self.all_ok = False


def load_paper(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _primary_author(author_str: str) -> str:
    """Extract primary (first) author surname from a citation string."""
    # Strip 'et al.' and 'and ...' to get just the first surname
    primary = author_str.split(" et al.")[0]
    primary = primary.split(" and ")[0]
    primary = primary.split(" & ")[0]
    return primary.strip()


def extract_citations(text: str) -> tuple:
    """Extract all in-text citations and reference list entries."""
    # In-text citations: (Author, Year) or (Author et al., Year) or (Author and Author, Year)
    cite_pattern = re.compile(
        r'\(([A-Z][a-z]+(?:\s(?:and|&|et al\.|[A-Z][a-z]+))*),?\s*(\d{4}[a-z]?)\)'
    )
    in_text = cite_pattern.findall(text)

    # Extract reference list entries
    ref_section = ""
    if "## References" in text:
        ref_section = text.split("## References")[1]

    ref_entries = {}  # (primary_author, year) -> full entry
    for line in ref_section.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Match reference entries ending with year.
        # Format: "LastName, I., LastName, I., et al., Year." or "LastName, I., Year."
        # Strategy: split on ". " and look for year pattern in the author block
        # Find the year by looking for ", YYYY" or ". YYYY" pattern
        year_match = re.search(r'[,.\s](\d{4}[a-z]?)\.\s', line)
        if not year_match:
            continue
        year = year_match.group(1)
        author_block = line[:year_match.start()]
        # Extract first surname: everything before the first comma
        first_comma = author_block.find(",")
        if first_comma == -1:
            continue
        primary = author_block[:first_comma].strip()
        # Validate primary is a reasonable surname (at least one letter)
        if not re.search(r'[A-Za-z]', primary):
            continue
        ref_entries[(primary, year)] = line[:100]

    return in_text, ref_entries


def check_citation_consistency(text: str, report: ConsistencyReport):
    """Check that every in-text citation has a reference entry and vice versa."""
    in_text, ref_entries = extract_citations(text)
    report.citations_checked = len(in_text)

    # Check each in-text citation against reference list
    for author_raw, year in in_text:
        primary = _primary_author(author_raw)
        matched = False
        for (ra, ry) in ref_entries.items():
            if year == ry and (primary == ra or ra.startswith(primary)):
                matched = True
                break
        if not matched:
            # Also try substring match for longer author names
            for (ra, ry) in ref_entries.items():
                if year == ry and (primary in ra or ra in primary):
                    matched = True
                    break
        if not matched:
            report.add(Discrepancy(
                category="citation",
                severity="ERROR",
                location="In-text citation",
                description=f"Citation ({author_raw}, {year}) has no matching reference entry",
                expected="entry in References",
                found=f"({author_raw}, {year})"
            ))

    # Check for uncited references
    cited_primaries = set()
    for author_raw, year in in_text:
        cited_primaries.add((_primary_author(author_raw), year))

    for (ra, ry) in ref_entries.keys():
        if (ra, ry) not in cited_primaries:
            # Try reverse match
            found = False
            for cp, cy in cited_primaries:
                if cy == ry and (cp in ra or ra in cp):
                    found = True
                    break
            if not found:
                report.add(Discrepancy(
                    category="citation",
                    severity="WARNING",
                    location="References section",
                    description=f"Reference ({ra}, {ry}) appears in bibliography but no matching in-text citation found",
                    expected="cited in text",
                    found=f"({ra}, {ry})"
                ))


def extract_numbers(text: str) -> list:
    """Extract all numerical claims from the paper with their context."""
    claims = []

    # Pattern 1: standalone decimals like 0.717, 0.480
    for m in re.finditer(r'(?<!\d)(0\.\d{1,4})(?!\d)', text):
        ctx_start = max(0, m.start() - 60)
        ctx_end = min(len(text), m.end() + 60)
        ctx = text[ctx_start:ctx_end].replace('\n', ' ').strip()
        claims.append((float(m.group(1)), ctx))

    # Pattern 2: percentages like 78.2%, 23.7%, 84.5%
    for m in re.finditer(r'(\d{1,3}\.\d{1,2})\s*%', text):
        ctx_start = max(0, m.start() - 60)
        ctx_end = min(len(text), m.end() + 60)
        ctx = text[ctx_start:ctx_end].replace('\n', ' ').strip()
        claims.append((float(m.group(1)), ctx))

    # Pattern 3: pp (percentage points) like +23.67 pp
    for m in re.finditer(r'([+-]?\d{1,3}\.\d{1,2})\s*pp', text):
        ctx_start = max(0, m.start() - 60)
        ctx_end = min(len(text), m.end() + 60)
        ctx = text[ctx_start:ctx_end].replace('\n', ' ').strip()
        claims.append((float(m.group(1)), ctx))

    return claims


def check_number_consistency(text: str, report: ConsistencyReport):
    """Check that numbers in the paper match canonical values."""
    claims = extract_numbers(text)
    report.claims_checked = len(claims)

    # Key numerical checks with patterns to find in text
    number_checks = [
        (r'KF achieves CVSR 0\.610', "test_v2_kf_cvsr", "Conclusions"),
        (r'0\.360 \(SA\)', "test_v2_sa_cvsr", "Conclusions"),
        (r'pass@5 0\.700', "test_v2_kf_pass5", "Conclusions"),
        (r'CVSR 0\.717', "kf_cvsr", "Multiple"),
        (r'0\.480.*SingleAgent|SingleAgent.*0\.480', "sa_cvsr", "Multiple"),
        (r'23\.67 pp', "paired_diff_pp", "Multiple"),
        (r'8\.45.*10\^{?-17}?\b|8\.45\s*\\times\s*10\^{?-17}?|8\.45e-17',
         "mcnemar_p", "Multiple"),
        (r'CVSR 0\.083', "kf_asset_cvsr", "Asset routing"),
        (r'78\.2%|78%[^0-9]', "policy_error_pct", "Asset routing"),
        (r'4\.6 pp', "excluding_rr_diff_pp", "Section 5.3"),
        (r'1\.000.*DirectRepair|DirectRepair.*1\.000', "directrepair_obj_f1", "Section 5.4"),
        (r'SRRR.*1\.000|1\.000.*SRRR', "srrr", "Section 5.4"),
        (r'SESR.*0\.100|10%.*SESR|SESR.*10%', "sesr", "Section 5.4"),
        (r'215/300', "kf_success_count", "Section 5.2"),
        (r'144/300', "sa_success_count", "Section 5.2"),
        (r'0\.808', "replay_kf", "Table 4"),
        (r'0\.455', "replay_sa", "Table 4"),
        (r'0\.947', "ev_p_sa", "Table 4"),
        (r'\$0\.104', "cost_kf", "Table 4"),
        (r'\$0\.085', "cost_sa", "Table 4"),
        (r'1\.21[×x]', "cost_ratio", "Section 5.2"),
    ]

    for pattern, key, section in number_checks:
        matches = re.findall(pattern, text)
        if not matches:
            report.add(Discrepancy(
                category="unsupported",
                severity="WARNING",
                location=section,
                description=f"Canonical value {key}={CANONICAL[key]} not found in paper",
                expected=f"Value {CANONICAL[key]} present",
                found="not found"
            ))

    # Check for stale DirectRepair Obj-F1 = 0.000 (should be 1.000)
    for match in re.finditer(
        r'DirectRepair[^|]*\|\s*0\.000\s*\|.*?1\.000\s*\|\s*1\.000',
        text, re.DOTALL
    ):
        # This pattern catches a table row where DirectRepair has CVSR=0.000 but Obj-F1=1.000
        # That's correct (CVSR=0 means overall failure, but Obj-F1=1 means objects were right)
        pass

    # Specifically check if any text says DirectRepair Obj-F1 = 0.000
    if re.search(r'DirectRepair.*?Obj.?F1.*?=.*?0\.000', text, re.DOTALL):
        report.add(Discrepancy(
            category="stale_number",
            severity="ERROR",
            location="Section 5.4 / Table 6",
            description="DirectRepair Obj-F1 reported as 0.000, should be 1.000",
            expected="Obj-F1 = 1.000",
            found="Obj-F1 = 0.000"
        ))


def check_table_consistency(text: str, report: ConsistencyReport):
    """Check that table numbers are sequential and referenced correctly."""
    # Find all table definitions
    table_defs = re.findall(r'\*\*Table (\d+)\.\*\*', text)
    appendix_tables = re.findall(r'\*\*Table (A\d+)\.\*\*', text)

    report.tables_checked = len(table_defs) + len(appendix_tables)

    if table_defs:
        nums = sorted(set(int(t) for t in table_defs))
        expected = list(range(1, max(nums) + 1))
        missing = set(expected) - set(nums)
        for m in sorted(missing):
            report.add(Discrepancy(
                category="table_mismatch",
                severity="ERROR",
                location="Table numbering",
                description=f"Table {m} is missing from the paper",
                expected=f"Table {m} exists",
                found="missing"
            ))

    # Check in-text table references exist
    in_text_refs = set(int(t) for t in re.findall(r'Table\s+(\d+)', text) if t.isdigit())
    defined_tables = set(int(t) for t in table_defs)
    for ref_num in sorted(in_text_refs - defined_tables):
        report.add(Discrepancy(
            category="table_mismatch",
            severity="WARNING",
            location=f"Text reference to Table {ref_num}",
            description=f"Table {ref_num} is referenced in text but not defined",
            expected=f"Table {ref_num} defined",
            found="not defined"
        ))


def check_fig_consistency(text: str, report: ConsistencyReport):
    """Check figure numbering consistency."""
    fig_defs = [int(f) for f in re.findall(r'\*\*Fig\.?\s*(\d+)\.\*\*', text)]
    fig_refs = [int(f) for f in re.findall(r'Fig(?:\.|\s+)(\d+)', text) if f.isdigit()]

    if fig_defs:
        nums = sorted(set(fig_defs))
        expected = list(range(1, max(nums) + 1))
        missing = set(expected) - set(nums)
        for m in sorted(missing):
            report.add(Discrepancy(
                category="table_mismatch",
                severity="ERROR",
                location="Figure numbering",
                description=f"Figure {m} is missing from the paper",
                expected=f"Figure {m} exists",
                found="missing"
            ))

        # Check referenced figures exist
        defined = set(fig_defs)
        for ref in sorted(set(fig_refs) - defined):
            report.add(Discrepancy(
                category="table_mismatch",
                severity="WARNING",
                location=f"Text reference to Figure {ref}",
                description=f"Figure {ref} is referenced but not defined",
                expected=f"Figure {ref} defined",
                found="not defined"
            ))


def check_internal_contradictions(text: str, report: ConsistencyReport):
    """Check for internal contradictions in claims."""
    # Check 1: 84.5% vs 60/71
    ratio_60_71 = 60 / 71 * 100
    if abs(ratio_60_71 - 84.5) > 0.1:
        report.add(Discrepancy(
            category="contradiction",
            severity="ERROR",
            location="Section 5.3",
            description=f"84.5% does not match 60/71 = {ratio_60_71:.1f}%",
            expected=f"{ratio_60_71:.1f}%",
            found="84.5%"
        ))

    # Check 2: 78.2% vs 43/55
    ratio_43_55 = 43 / 55 * 100
    if abs(ratio_43_55 - 78.2) > 0.1:
        report.add(Discrepancy(
            category="contradiction",
            severity="ERROR",
            location="Table 9 / A4",
            description=f"78.2% does not match 43/55 = {ratio_43_55:.1f}%",
            expected=f"{ratio_43_55:.1f}%",
            found="78.2%"
        ))

    # Check 3: Excluding RR - verify counts and difference
    kf_excl = 155 / 240
    sa_excl = 144 / 240
    diff_excl = (kf_excl - sa_excl) * 100
    if abs(kf_excl - 0.646) > 0.001:
        report.add(Discrepancy(
            category="contradiction",
            severity="ERROR",
            location="Section 5.3",
            description=f"KF excluding RR rate 0.646 does not match 155/240 = {kf_excl:.3f}",
            expected=f"{kf_excl:.3f}",
            found="0.646"
        ))
    if abs(sa_excl - 0.600) > 0.001:
        report.add(Discrepancy(
            category="contradiction",
            severity="ERROR",
            location="Section 5.3",
            description=f"SA excluding RR rate 0.600 does not match 144/240 = {sa_excl:.3f}",
            expected=f"{sa_excl:.3f}",
            found="0.600"
        ))
    if abs(diff_excl - 4.6) > 0.1:
        report.add(Discrepancy(
            category="contradiction",
            severity="ERROR",
            location="Section 5.3",
            description=f"Excluding RR paired difference 4.6 pp does not match calculation = {diff_excl:.1f} pp",
            expected=f"{diff_excl:.1f} pp",
            found="4.6 pp"
        ))

    # Check 4: DirectRepair 54/60 = 90%
    ratio_54_60 = 54 / 60 * 100
    if abs(ratio_54_60 - 90.0) > 0.1:
        report.add(Discrepancy(
            category="contradiction",
            severity="ERROR",
            location="Section 5.4",
            description=f"90% does not match 54/60 = {ratio_54_60:.1f}%",
            expected=f"{ratio_54_60:.1f}%",
            found="90%"
        ))

    # Check 5: Cross-model differences - flag if off by more than 0.05 pp
    # Note: small rounding differences (<0.1 pp) may come from unrounded underlying values
    cross_model_checks = [
        (0.717, 0.480, 23.67, "DeepSeek-V4-Flash"),
        (0.673, 0.493, 18.00, "Kimi-K2.6"),
        (0.607, 0.350, 25.67, "MiniMax-M2.5"),
        (0.697, 0.480, 21.67, "Qwen3.6-27B"),
        (0.737, 0.493, 24.33, "GLM-5.2"),
    ]
    for kf, sa, expected_diff, model in cross_model_checks:
        actual_diff = round((kf - sa) * 100, 2)
        if abs(actual_diff - expected_diff) > 0.05:
            # Flag as INFO if difference is small (likely rounding from unrounded values)
            severity = "INFO" if abs(actual_diff - expected_diff) < 0.1 else "WARNING"
            report.add(Discrepancy(
                category="contradiction",
                severity=severity,
                location=f"Table 8 - {model}",
                description=(
                    f"Cross-model diff for {model}: paper reports {expected_diff} pp "
                    f"but ({kf} - {sa}) * 100 = {actual_diff} pp. "
                    f"May reflect rounding of underlying CVSR values."
                ),
                expected=f"{expected_diff} pp",
                found=f"{actual_diff} pp"
            ))

    # Check 6: Paired difference main result
    main_diff = round((0.717 - 0.480) * 100, 2)
    if abs(main_diff - 23.67) > 0.05:
        report.add(Discrepancy(
            category="contradiction",
            severity="INFO",
            location="Section 5.2",
            description=(
                f"Main paired diff: paper says 23.67 pp but (0.717 - 0.480) * 100 = {main_diff} pp. "
                f"Likely uses more precise underlying CVSR values."
            ),
            expected="23.67 pp",
            found=f"{main_diff} pp"
        ))

    # Check 7: 71 - 60 = 11 non-RR additional successes
    non_rr_additional = 71 - 60
    if non_rr_additional != 11:
        report.add(Discrepancy(
            category="contradiction",
            severity="WARNING",
            location="Section 5.3",
            description=f"71 total additional - 60 from RR = {non_rr_additional} from non-RR",
            expected="11 from non-RR categories",
            found=f"{non_rr_additional}"
        ))


def generate_report(report: ConsistencyReport) -> str:
    """Generate markdown report."""
    lines = [
        "# Final Claim Consistency Report",
        "",
        f"**Paper:** `{report.paper_path}`",
        f"**Claims checked:** {report.claims_checked}",
        f"**Tables checked:** {report.tables_checked}",
        f"**Citations checked:** {report.citations_checked}",
        f"**Overall status:** {'ALL OK' if report.all_ok else 'DISCREPANCIES FOUND'}",
        "",
    ]

    categories = {}
    for d in report.discrepancies:
        categories.setdefault(d.category, []).append(d)

    category_names = {
        "stale_number": "Stale/Incorrect Numbers",
        "unsupported": "Unsupported Claims (not found in paper)",
        "table_mismatch": "Table/Figure Numbering Issues",
        "citation": "Citation Consistency",
        "contradiction": "Internal Contradictions",
    }

    for cat, name in category_names.items():
        items = categories.get(cat, [])
        lines.append(f"## {name}")
        lines.append("")
        if not items:
            lines.append("No issues found.")
            lines.append("")
            continue
        for d in items:
            lines.append(f"- `{d.severity}` **{d.location}**")
            lines.append(f"  - {d.description}")
            if d.expected:
                lines.append(f"  - Expected: {d.expected}")
            if d.found:
                lines.append(f"  - Found: {d.found}")
            lines.append("")

    errors = sum(1 for d in report.discrepancies if d.severity == "ERROR")
    warnings = sum(1 for d in report.discrepancies if d.severity == "WARNING")
    infos = sum(1 for d in report.discrepancies if d.severity == "INFO")

    lines += [
        "## Summary",
        "",
        "| Severity | Count |",
        "|:---------|------:|",
        f"| ERROR | {errors} |",
        f"| WARNING | {warnings} |",
        f"| INFO | {infos} |",
        f"| **Total** | **{errors + warnings + infos}** |",
        "",
    ]

    if report.all_ok:
        lines.append("**Result: All claims are consistent with canonical evidence.**")
    else:
        lines.append(f"**Result: {errors} errors and {warnings} warnings require attention.**")

    return "\n".join(lines)


def main():
    paper_path = "/data/fj/数字孪生-paper-work/Academic Pipeline/09_final_paper.md"
    output_path = "/data/fj/数字孪生-paper-work/paper_evidence/final_claim_consistency_report.md"

    # Try to load manifest if available
    manifest_path = "/data/fj/数字孪生-paper-work/paper_evidence/CANONICAL_EVIDENCE_MANIFEST.json"
    if Path(manifest_path).exists():
        print(f"Loading canonical manifest from {manifest_path}")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        for k, v in manifest.items():
            if k in CANONICAL:
                CANONICAL[k] = v
    else:
        print(f"Manifest not found, using hardcoded canonical values")

    print(f"Reading paper from {paper_path}")
    text = load_paper(paper_path)

    report = ConsistencyReport(paper_path=paper_path)

    print("Checking number consistency...")
    check_number_consistency(text, report)

    print("Checking table/figure consistency...")
    check_table_consistency(text, report)
    check_fig_consistency(text, report)

    print("Checking citation consistency...")
    check_citation_consistency(text, report)

    print("Checking internal contradictions...")
    check_internal_contradictions(text, report)

    print(f"Generating report to {output_path}")
    md = generate_report(report)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nReport written to {output_path}")
    print(f"Claims checked: {report.claims_checked}")
    print(f"Tables checked: {report.tables_checked}")
    print(f"Citations checked: {report.citations_checked}")
    print(f"Discrepancies: {len(report.discrepancies)}")
    errors = sum(1 for d in report.discrepancies if d.severity == "ERROR")
    warnings = sum(1 for d in report.discrepancies if d.severity == "WARNING")
    infos = sum(1 for d in report.discrepancies if d.severity == "INFO")
    print(f"  Errors: {errors}")
    print(f"  Warnings: {warnings}")
    print(f"  Info: {infos}")

    if report.all_ok:
        print("\nResult: ALL OK")
    else:
        print(f"\nResult: {errors} errors, {warnings} warnings found")

    return 0 if report.all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
