# Citation Verification Report

**Paper:** `09_final_paper.md` — KAFarmTwin COMPAG
**Verification date:** 2026-09-01
**Method:** Crossref API + arXiv API + Bocha web search, cross-validated

---

## Summary

| Status | Count |
|:-------|------:|
| ✅ Verified correct | 29 |
| ❌ Author name errors | 7 |
| ❌ Fabricated reference (paper doesn't exist) | 2 |
| ❌ Wrong arXiv ID | 1 |
| ⚠️ Orphaned (in bib but not cited) | 5 |
| **Total errors** | **10** |

---

## ❌ CONFIRMED ERRORS (must fix)

### Error 1: Bourzig et al. 2021 → Akroyd et al. 2021
- **In-text:** `(Bourzig et al., 2021; Hubbard et al., 2023)` (line 81)
- **Bib entry:** `Bourzig, C., Tlili, A., Blot, J., et al., 2021.`
- **Reality:** First author is **Akroyd, Jethro** (not Bourzig). "Bourzig" does not appear as any author.
- **Correct:** `Akroyd, J., Mosbach, S., Bhave, A., Kraft, M., 2021. Universal Digital Twin — A Dynamic Knowledge Graph. Data-Centric Eng. 2, e10.` DOI: 10.1017/dce.2021.10

### Error 2: Dong et al. 2024 — wrong co-authors + wrong arXiv ID
- **Bib entry:** `Dong, Y., Zhu, H., Yu, T., et al., 2024. XGrammar: ...arXiv preprint arXiv:2411.15124.`
- **Reality:** Real XGrammar paper is arXiv **2411.15100** (not 2411.15124). Co-authors "Zhu, H." and "Yu, T." are **fabricated**.
- **Correct authors:** Yixin Dong, Charlie F. Ruan, Yaxing Cai, Ruihang Lai, Ziyi Xu, Yilong Zhao, Tianqi Chen
- **Correct:** `Dong, Y., Ruan, C.F., Cai, Y., et al., 2024. XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models. arXiv preprint arXiv:2411.15100.`

### Error 3: Garcez et al. 2019 — unverifiable
- **Bib entry:** `Garcez, A.A., Gori, M., Lamb, L.C., et al., 2019. Neural-symbolic computing: an effective methodology for principled integration of machine learning and reasoning. J. Appl. Log. 17 (4), 611–631.`
- **Reality:** Crossref cannot find this paper with these authors and venue. The 2023 review by d'Avila Garcez & Lamb is real, but this 2019 paper is **unverifiable**. May be fabricated or have incorrect metadata.
- **Action:** Either find the correct reference or remove.

### Error 4: Chen et al. 2023 program-of-thoughts — fabricated arXiv ID
- **Bib entry:** `Chen, A., Durrett, G., Ernst, M., et al., 2023. Program-of-thoughts prompting: bootstrapping complex reasoning with program generation. arXiv preprint arXiv:2310.09310.`
- **Reality:** arXiv 2310.09310 is a **physics paper** ("Weyl points and spin-orbit coupling in copper-substituted lead phosphate apatite"). The program-of-thoughts paper is **fabricated** with a wrong arXiv ID.
- **Action:** Find the correct program-of-thoughts paper or remove.

### Error 5: Wang et al. 2025 CRANE — wrong authors
- **Bib entry:** `Wang, Y., Li, Z., Zhang, H., et al., 2025. CRANE: reasoning with constrained LLM generation. arXiv preprint arXiv:2502.09061.`
- **Reality:** Real authors are **Debangshu Banerjee, Tarun Suresh, Shubham Ugare, Sasa Misailovic, Gagandeep Singh**. "Wang, Li, Zhang" are fabricated.
- **Correct:** `Banerjee, D., Suresh, T., Ugare, S., Misailovic, S., Singh, G., 2025. CRANE: Reasoning with constrained LLM generation. arXiv preprint arXiv:2502.09061.`

### Error 6: Wang et al. 2025b state-machine — wrong authors
- **Bib entry:** `Wang, Y., Chen, S., Liu, X., et al., 2025b. Memory-augmented state machine prompting: ...arXiv preprint arXiv:2510.18395.`
- **Reality:** Real authors are **Runnan Qi, Yanan Ni, Lumin Jiang, Zongyuan Li, Kuihua Huang, Xian Guo**. "Wang, Chen, Liu" are fabricated.
- **Correct:** `Qi, R., Ni, Y., Jiang, L., Li, Z., Huang, K., Guo, X., 2025. Memory-Augmented State Machine Prompting: A Novel LLM Agent Framework for Real-Time Strategy Games. arXiv preprint arXiv:2510.18395.`

### Error 7: Hubbard et al. 2023 — likely fabricated
- **Bib entry:** `Hubbard, T., Chen, H., Liu, J., et al., 2023. Digital twins using knowledge graphs for semantic interoperability. Eng. Appl. Artif. Intell. 126, 106948.`
- **Reality:** Crossref and web search cannot find this paper with these authors, title, and venue. The reference appears **fabricated**.
- **Action:** Find the correct reference or remove.

### Error 8: Panzer & Leymann 2023 — wrong authors
- **Bib entry:** `Panzer, M., Leymann, F., 2023. Ontologies in digital twins: a systematic literature review. arXiv preprint arXiv:2308.15168.`
- **Reality:** Real authors are **Erkan Karabulut, Salvatore F. Pileggi, Paul Groth, Victoria Degeler**. "Panzer" and "Leymann" are fabricated.
- **Correct:** `Karabulut, E., Pileggi, S.F., Groth, P., Degeler, V., 2023. Ontologies in Digital Twins: A Systematic Literature Review. arXiv preprint arXiv:2308.15168.`

### Error 9: Li et al. 2024 ontology KG — wrong authors
- **Bib entry:** `Li, J., Wang, S., Zhang, Y., et al., 2024. Ontology-grounded automatic knowledge graph construction by LLM under Wikidata schema. arXiv preprint arXiv:2412.20942.`
- **Reality:** Real authors are **Xiaohan Feng, Xixin Wu, Helen Meng**. "Li, Wang, Zhang" are fabricated.
- **Correct:** `Feng, X., Wu, X., Meng, H., 2024. Ontology-grounded Automatic Knowledge Graph Construction by LLM under Wikidata schema. arXiv preprint arXiv:2412.20942.`

### Error 10: Chen et al. 2025 neuro-symbolic-causal — wrong authors
- **Bib entry:** `Chen, Y., Li, Z., Wang, X., et al., 2025. Beyond prompt engineering: neuro-symbolic-causal architecture for robust multi-objective AI agents. arXiv preprint arXiv:2510.23682.`
- **Reality:** Real author is **Gokturk Aytug Akarlar** (single author). "Chen, Li, Wang" are fabricated.
- **Correct:** `Akarlar, G.A., 2025. Beyond Prompt Engineering: Neuro-Symbolic-Causal Architecture for Robust Multi-Objective AI Agents. arXiv preprint arXiv:2510.23682.`

---

## ✅ VERIFIED CORRECT (29)

| Citation | Status |
|:---------|:-------|
| Grieves, 2014 | ✅ Verified |
| Tao et al., 2019 | ✅ Verified |
| Jones et al., 2020 | ✅ Verified |
| Pylianidis et al., 2021 | ✅ Verified |
| Verdouw et al., 2021 | ✅ Verified |
| Walter et al., 2017 | ✅ Verified |
| Liakos et al., 2018 | ✅ Verified |
| Kamilaris and Prenafeta-Boldú, 2018 | ✅ Verified |
| Jonquet et al., 2018 | ✅ Verified |
| Compton et al., 2012 | ✅ Verified |
| Janowicz et al., 2019 | ✅ Verified |
| Wang et al., 2023 | ✅ Verified |
| Xi et al., 2023 | ✅ Verified |
| Yao et al., 2023a (ReAct) | ✅ Verified |
| Schick et al., 2023 (Toolformer) | ✅ Verified |
| Wei et al., 2022 | ✅ Verified |
| Li et al., 2023 (CAMEL) | ✅ Verified |
| Lewis et al., 2020 | ✅ Verified |
| Gao et al., 2023 | ✅ Verified |
| Hogan et al., 2021 | ✅ Verified |
| d'Avila Garcez and Lamb, 2023 | ✅ Verified |
| Park et al., 2023 | ✅ Verified |
| Shinn et al., 2023 | ✅ Verified |
| Krishna et al., 2017 | ✅ Verified |
| Zellers et al., 2018 | ✅ Verified (arXiv 1711.06640) |
| Tang et al., 2020 | ✅ Verified |
| Kojima et al., 2022 | ✅ Verified |
| McNemar, 1947 | ✅ Verified |
| Efron and Tibshirani, 1993 | ✅ Verified |
| Staab and Studer, 2009 | ✅ Verified (DOI: 10.1007/978-3-540-92673-3) |

---

## ⚠️ ORPHANED (in bibliography but not cited in text)

| Entry | Status |
|:------|:-------|
| Dong et al., 2024 | In bib but not cited in text (only mentioned in §2.5 as "XGrammar; Dong et al., 2024" — but the in-text citation is within the parenthetical) |
| Garcez et al., 2019 | In bib but not cited in text separately from d'Avila Garcez and Lamb, 2023 |
| Kojima et al., 2022 | In bib but not cited in text |
| Staab and Studer, 2009 | In bib but not cited in text |
| Wolfert et al., 2017 | In bib but not cited in text |

---

## Pattern Analysis

The errors follow a clear pattern: **6 out of 10 errors involve fabricated author names** where the first author surname is wrong or co-author names are invented. This is characteristic of LLM-generated references where the model "knows" the paper exists but invents plausible-sounding author names. The two fabricated references (Hubbard et al. 2023, Chen et al. 2023 program-of-thoughts) follow the same pattern.
