# Final Claim Consistency Report

**Paper:** `/data/fj/数字孪生-paper-work/Academic Pipeline/09_final_paper.md`
**Claims checked:** 126
**Tables checked:** 13
**Citations checked:** 6
**Overall status:** DISCREPANCIES FOUND

## Stale/Incorrect Numbers

- `ERROR` **Section 5.4 / Table 6**
  - DirectRepair Obj-F1 reported as 0.000, should be 1.000
  - Expected: Obj-F1 = 1.000
  - Found: Obj-F1 = 0.000

## Unsupported Claims (not found in paper)

No issues found.

## Table/Figure Numbering Issues

No issues found.

## Citation Consistency

- `ERROR` **In-text citation**
  - Citation (Jonquet et al., 2018) has no matching reference entry
  - Expected: entry in References
  - Found: (Jonquet et al., 2018)

- `ERROR` **In-text citation**
  - Citation (Yao et al., 2023a) has no matching reference entry
  - Expected: entry in References
  - Found: (Yao et al., 2023a)

- `ERROR` **In-text citation**
  - Citation (Schick et al., 2023) has no matching reference entry
  - Expected: entry in References
  - Found: (Schick et al., 2023)

- `ERROR` **In-text citation**
  - Citation (Wei et al., 2022) has no matching reference entry
  - Expected: entry in References
  - Found: (Wei et al., 2022)

- `ERROR` **In-text citation**
  - Citation (Li et al., 2023) has no matching reference entry
  - Expected: entry in References
  - Found: (Li et al., 2023)

- `ERROR` **In-text citation**
  - Citation (Efron and Tibshirani, 1993) has no matching reference entry
  - Expected: entry in References
  - Found: (Efron and Tibshirani, 1993)

- `WARNING` **References section**
  - Reference (Compton, 2012) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Compton, 2012)

- `WARNING` **References section**
  - Reference (d'Avila Garcez, 2023) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (d'Avila Garcez, 2023)

- `WARNING` **References section**
  - Reference (Gao, 2023) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Gao, 2023)

- `WARNING` **References section**
  - Reference (Grieves, 2014) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Grieves, 2014)

- `WARNING` **References section**
  - Reference (Hogan, 2021) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Hogan, 2021)

- `WARNING` **References section**
  - Reference (Janowicz, 2019) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Janowicz, 2019)

- `WARNING` **References section**
  - Reference (Jones, 2020) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Jones, 2020)

- `WARNING` **References section**
  - Reference (Kamilaris, 2018) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Kamilaris, 2018)

- `WARNING` **References section**
  - Reference (Kojima, 2022) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Kojima, 2022)

- `WARNING` **References section**
  - Reference (Lewis, 2020) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Lewis, 2020)

- `WARNING` **References section**
  - Reference (Liakos, 2018) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Liakos, 2018)

- `WARNING` **References section**
  - Reference (McNemar, 1947) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (McNemar, 1947)

- `WARNING` **References section**
  - Reference (Park, 2023) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Park, 2023)

- `WARNING` **References section**
  - Reference (Pylianidis, 2021) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Pylianidis, 2021)

- `WARNING` **References section**
  - Reference (Shinn, 2023) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Shinn, 2023)

- `WARNING` **References section**
  - Reference (Staab, 2009) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Staab, 2009)

- `WARNING` **References section**
  - Reference (Tao, 2019) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Tao, 2019)

- `WARNING` **References section**
  - Reference (Verdouw, 2021) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Verdouw, 2021)

- `WARNING` **References section**
  - Reference (Walter, 2017) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Walter, 2017)

- `WARNING` **References section**
  - Reference (Wang, 2023) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Wang, 2023)

- `WARNING` **References section**
  - Reference (Wolfert, 2017) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Wolfert, 2017)

- `WARNING` **References section**
  - Reference (Xi, 2023) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Xi, 2023)

- `WARNING` **References section**
  - Reference (Yao, 2023b) appears in bibliography but no matching in-text citation found
  - Expected: cited in text
  - Found: (Yao, 2023b)

## Internal Contradictions

- `INFO` **Table 8 - GLM-5.2**
  - Cross-model diff for GLM-5.2: paper reports 24.33 pp but (0.737 - 0.493) * 100 = 24.4 pp. May reflect rounding of underlying CVSR values.
  - Expected: 24.33 pp
  - Found: 24.4 pp

## Summary

| Severity | Count |
|:---------|------:|
| ERROR | 7 |
| WARNING | 23 |
| INFO | 1 |
| **Total** | **31** |

**Result: 7 errors and 23 warnings require attention.**