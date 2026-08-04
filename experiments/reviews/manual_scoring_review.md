# Manual Scoring Review

This file records the human spot-check protocol for the paper experiments. The goal is to verify that the automatic scorer does not count irrelevant objects, wrong-direction relations, invalid bindings, or fake trace steps as correct results.

## Review Scope

The minimum review covers one representative task from each task category and all five methods. This gives 5 tasks x 5 methods = 25 structured outputs.

| Category | Task | Review Focus | Status |
| --- | --- | --- | --- |
| Scene construction | T01 | Object hierarchy, tomato rows/plants, weather station, pump, camera, sensor group, trace steps. | TODO |
| Asset routing | T07 | F2DMAS route, lightweight GLB route, placeholder assets, generation tasks, routing reasons. | TODO |
| Data binding | T13 | Sensor metrics, units, timestamps, target greenhouse/object binding, trace evidence. | TODO |
| Rule correction | T24 | Wrong pump asset binding detection, replacement asset, `controls`/`has_asset` relation, zero rule conflict. | TODO |
| Historical query | T30 | Object memory, event evidence, greenhouse daily report, traceable query result. | TODO |

## Output Checklist

| Task | Method | Auto Success | Auto RA Evidence | Auto BA Evidence | Rule Conflict | Trace | Human Decision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| T01 | Direct-LLM | 1 | 28/38 | 6/10 | 0/6 | 1/1 | TODO |
| T01 | Single-Agent | 1 | 29/38 | 3/10 | 0/4 | 4/5 | TODO |
| T01 | RAG-Agent | 1 | 28/38 | 7/10 | 0/6 | 5/5 | TODO |
| T01 | Multi-Agent | 1 | 28/38 | 7/10 | 0/6 | 5/5 | TODO |
| T01 | Ours | 1 | 38/38 | 10/10 | 0/6 | 5/5 | TODO |
| T07 | Direct-LLM | 1 | 22/31 | 20/24 | 0/4 | 1/1 | TODO |
| T07 | Single-Agent | 1 | 22/31 | 20/24 | 0/3 | 4/5 | TODO |
| T07 | RAG-Agent | 1 | 22/31 | 22/24 | 0/10 | 2/5 | TODO |
| T07 | Multi-Agent | 1 | 22/31 | 22/24 | 0/3 | 5/5 | TODO |
| T07 | Ours | 1 | 31/31 | 24/24 | 0/4 | 5/5 | TODO |
| T13 | Direct-LLM | 1 | 1/15 | 5/12 | 0/3 | 1/1 | TODO |
| T13 | Single-Agent | 1 | 1/15 | 1/12 | 0/3 | 4/5 | TODO |
| T13 | RAG-Agent | 1 | 1/15 | 1/12 | 0/4 | 2/5 | TODO |
| T13 | Multi-Agent | 1 | 1/15 | 4/12 | 0/1 | 5/5 | TODO |
| T13 | Ours | 1 | 15/15 | 7/12 | 0/3 | 5/5 | TODO |
| T24 | Direct-LLM | 1 | 3/14 | 1/9 | 1/1 | 1/1 | TODO |
| T24 | Single-Agent | 1 | 1/14 | 1/9 | 1/1 | 3/5 | TODO |
| T24 | RAG-Agent | 0 | 3/14 | 1/9 | 1/3 | 2/5 | TODO |
| T24 | Multi-Agent | 1 | 4/14 | 1/9 | 1/1 | 5/5 | TODO |
| T24 | Ours | 1 | 4/14 | 2/9 | 0/5 | 5/5 | TODO |
| T30 | Direct-LLM | 1 | 3/16 | 3/20 | 0/4 | 1/1 | TODO |
| T30 | Single-Agent | 1 | 5/16 | 5/20 | 0/4 | 5/5 | TODO |
| T30 | RAG-Agent | 1 | 4/16 | 4/20 | 0/10 | 2/5 | TODO |
| T30 | Multi-Agent | 1 | 11/16 | 5/20 | 0/5 | 5/5 | TODO |
| T30 | Ours | 1 | 16/16 | 14/20 | 0/4 | 5/5 | TODO |

## Review Criteria

| Field | Pass Criterion |
| --- | --- |
| Objects | Required objects exist and object types match task semantics. Extra objects are not counted unless they support the task. |
| Relations | Subject, predicate, and object are semantically correct; hierarchy direction must be correct for `contains`, `belongs_to`, and `located_in`. |
| Bindings | Binding subject, target, and type are valid for assets, data, events, or business objects. |
| Rules | Violated rules match the task checkpoints; fatal violations are not ignored. |
| Trace | Trace steps correspond to real planning, layout, asset routing, binding, validation, memory/query, or controlled tool actions. |

## Paper Text

The following paragraph can be used in the experiment setting section after the spot-check is completed:

> To reduce potential bias from automatic scoring, we manually reviewed one representative task from each category and checked the outputs of all five methods, resulting in 25 reviewed outputs. The review covered objects, relations, bindings, rule violations, and trace steps against task semantics. The spot-check confirmed that the scoring script did not count irrelevant objects, wrong-direction relations, invalid bindings, or non-substantive trace records as correct outputs.

## Review Notes

### T01 Scene Construction

- Source row: `experiments/results/main_experiment_raw.csv`, task `T01`, method `Ours`.
- Current automatic score: success 1, required objects 30, generated objects 25, required relations 38, correct relations 38, required bindings 10, correct bindings 10, checked rules 6, violated rules 0, trace 5/5.
- Human decision: TODO.
- Notes: TODO.

### T07 Asset Routing

- Source row: `experiments/results/main_experiment_raw.csv`, task `T07`, method `Ours`.
- Current automatic score: success 1, required objects 24, generated objects 22, required relations 31, correct relations 31, required bindings 24, correct bindings 24, checked rules 4, violated rules 0, trace 5/5.
- Human decision: TODO.
- Notes: TODO.

### T13 Data Binding

- Source row: `experiments/results/main_experiment_raw.csv`, task `T13`, method `Ours`.
- Current automatic score: success 1, required objects 10, generated objects 3, required relations 15, correct relations 15, required bindings 12, correct bindings 7, checked rules 3, violated rules 0, trace 5/5.
- Human decision: TODO.
- Notes: TODO.

### T24 Rule Correction

- Source row: `experiments/results/main_experiment_raw.csv`, task `T24`, method `Ours`.
- Current automatic score: success 1, required objects 9, generated objects 1, required relations 14, correct relations 4, required bindings 9, correct bindings 2, checked rules 5, violated rules 0, trace 5/5.
- Human decision: TODO.
- Notes: TODO.

### T30 Historical Query

- Source row: `experiments/results/main_experiment_raw.csv`, task `T30`, method `Ours`.
- Current automatic score: success 1, required objects 8, generated objects 6, required relations 16, correct relations 16, required bindings 20, correct bindings 14, checked rules 4, violated rules 0, trace 5/5.
- Human decision: TODO.
- Notes: TODO.
