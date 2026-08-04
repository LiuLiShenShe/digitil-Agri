# Translation Notes for HILMA Paper

## General Notes

- **Source format**: PDF with two-column layout, extracted using pdftotext with layout preservation.
- **Extraction quality**: Generally good. Some paragraph boundaries were reconstructed from the two-column layout. Figure axis labels for Fig. 5 showed minor extraction artifacts.
- **Translation approach**: Conservative, meaning-preserving translation. All technical terms, citations, formulas, and numbers are preserved as in the original.

## Terminology Decisions

| Original Chinese | English Translation | Rationale |
|:--|:--|:--|
| 科学假设生成 | Scientific Hypothesis Generation | Direct translation; standard term in the literature |
| 人机协作 | Human-Machine Collaboration / Human-in-the-Loop | "Human-in-the-loop" is used where the framework name HILMA is referenced |
| 结构智力理论 | Theory of Structural Intelligence | Guilford's established theory; used the standard English name |
| 发散思维 / 收敛思维 | Divergent Thinking / Convergent Thinking | Standard psychological terminology from Guilford |
| 引文网络 | Citation Network | Standard bibliometrics term |
| 子图引文网络 | Subgraph Citation Network | Descriptive translation preserving the graph theory concept |
| 综述 (in context of subgraph review) | Research Review / Survey | Context-dependent; "review" for subgraph-specific, "survey" for broader contexts |
| 氮化硅陶瓷 | Silicon Nitride Ceramics | Standard materials science term |
| 通义千问 (Qwen-Max) | Qwen-Max / Tongyi Qianwen | Used the model's official name "Qwen-Max" |

## Uncertain or Challenging Extractions

1. **Fig. 5 axis labels** (p.9/p.11): The bar chart axis labels for six evaluation metrics showed extraction artifacts in the source text. Labels were reconstructed based on context from Table 1 metrics.

2. **HILMA acronym**: The English expansion "human-in-the-loop multi-agent framework" is given in the abstract, but the exact acronym derivation (HILMA = Human-In-the-Loop Multi-Agent) was inferred from context.

3. **Reference [44]**: The arXiv ID "2402.122914" may contain a typo in the original (possibly should be "2402.12914"). Preserved as-is from source.

## Skipped Content

- None. All sections of the paper were processed including:
  - Both Chinese and English abstracts
  - All body sections (Introduction through Conclusion)
  - All figures and tables (with placeholder images)
  - References [1]-[58]
  - Author biographies for all 5 authors

## Draft Mode Indicators

- Figures exist as placeholders only (assets/fig*.png). Actual figure images were not extracted from the PDF.
- Multi-column layout reconstructions for paragraphs that spanned columns are marked as reliable (confidence: high) based on content continuity.

## Version

- Generated: 2026-05-30
- Source: Journal of Computer Research and Development, Vol. 62, No. 7, pp. 1639-1652, 2025
- DOI: 10.7544/issn1000-1239.202440552
