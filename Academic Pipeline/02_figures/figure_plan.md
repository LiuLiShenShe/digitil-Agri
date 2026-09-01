# Figure Plan — COMPAG KAFarmTwin Paper

## Main Paper Figures

### Fig. 1. KAFarmTwin System Architecture
- **Type**: Block diagram / flowchart
- **Content**: Three-stage pipeline: (a) LLM IntentIR parsing, (b) deterministic Knowledge Compilation (ontology, mapping, binding, unit, constraint, asset-policy), (c) validation-triggered typed repair
- **Key elements**: LLM shaded (stochastic), deterministic modules white; repair loop with transactional commit
- **Status**: Referenced in paper, to be created

### Fig. 2. External300 CVSR by Task Category
- **Type**: Grouped bar chart
- **Content**: KF vs SA CVSR for 5 categories (rule_repair, scene_construction, asset_routing, data_binding, memory_query)
- **Key annotations**: Highlight concentration of improvement in rule_repair; ceiling effects in data_binding/memory_query
- **Status**: Referenced in paper, to be created

### Fig. 3. Ablation Study Results
- **Type**: Two-panel figure
- **Panel (a)**: CVSR for full (0.550), A1 no_compiler (0.370), A2 no_typed_repair (0.580), A3 no_ontology (0.530)
- **Panel (b)**: Fatal rate for same variants (0.000, 0.010, 0.220, 0.000)
- **Key message**: Typed repair contributes safety rather than CVSR
- **Status**: Referenced in paper, to be created

### Fig. 4. Cross-Model-Family Robustness
- **Type**: Forest plot
- **Content**: Point estimates and 95% CI for KF–SA CVSR difference across 5 model families
- **Key annotation**: All intervals have positive lower bounds
- **Status**: Referenced in paper, to be created

### Fig. 5. Execution-Trace Example
- **Type**: Annotated trace diagram
- **Content**: Links IntentIR → tool-call IDs → evidence IDs → validation findings → repair operator → deterministic patch → post-repair validation
- **Key distinction**: Executable evidence vs LLM-generated narration
- **Status**: Referenced in paper, to be created

## Supplementary Figures (if space permits)

### Fig. A1. DirectRepair Failure Decomposition (NEW)
- **Type**: Stacked bar or Sankey diagram
- **Content**: 60 tasks decomposed into:
  - Category A (6 tasks): Correct nodes+edges+bindings, no evidence → fail evidence_ok
  - Category C (54 tasks): Correct nodes+edges, empty bindings → fail R6/all_bindings
- **Key message**: SRRR=100%, SESR=10% — semantic understanding is complete, structured output is the bottleneck
- **Status**: NEW — based on P0-5S analysis

### Fig. A2. Asset-Routing Failure Taxonomy
- **Type**: Pie chart or treemap
- **Content**: 55 failed tasks: 78.2% policy error, 20.0% ID-only, 1.8% mixed
- **Key message**: Policy-level routing error, not structural construction failure
- **Status**: Referenced in Appendix A4, to be created
