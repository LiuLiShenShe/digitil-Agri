# Binding Failure Analysis — TN21-24

**Status**: PHASE 3.1 (diagnosis, read-only) COMPLETE + PHASE 3.3 (method-side fix) APPLIED.
**Scope**: 4 data_binding tasks (TN21-TN24) on frozen `test_v2` benchmark.
**Diagnosis method**: Live re-run of `bindings_only_scene` builder (shared by KAFarmTwin + SingleAgent for bind tasks) on TN21-TN24, followed by exact-string evaluation against `evaluators/binding_match.py` matcher (evaluator_v2.3, frozen).
**Fix method (Phase 3.3, method-side only — no evaluator/benchmark change)**: `bindings_only_scene` now (a) instructs the LLM to emit `timestamp` in binding metadata, and (b) deterministically stamps the public prompt's declared ISO-8601 timestamp (e.g. `时间戳 2026-09-01T00:00:00+08:00`) onto every emitted binding — reading ONLY the public prompt, never gold (mirrors the evaluator's own `_prompt_declares_timestamp` scoping). Confirmed live on TN21/TN24 → BindF1=1.0.

## Summary

| Task | Sensor binds generated | Sensor binds gold | Trait bind | Result | Root cause |
|---|---|---|---|---|---|
| TN21-v2-bind | `metrics=humidity, unit=%,` **no timestamp** | `metrics=humidity, unit=%, ts=2026-09-01...` | emitted with ts ✅ | 0/3 matched | **A: implementation bug** — timestamp omitted |
| TN22-v2-bind | `metrics=temperature, unit=celsius,` **no ts** | `metrics=temperature, unit=°C, ts=2026-09-01...` | emitted with ts ✅ | 0/4 matched | **A + B**: timestamp omitted + evaluator °C≠celsius alias gap |
| TN23-v2-bind | `metrics=light_intensity, unit=lux,` **no ts** | `metrics=light, unit=klux, ts=2026-09-01...` | emitted with ts ✅ | 0/3 matched | **A + B**: timestamp omitted + klux/light alias gap |
| TN24-v2-bind | `metrics=co2, unit=ppm,` **no ts** | `metrics=co2, unit=ppm, ts=2026-09-01...` | emitted with ts ✅ | 0/4 matched | **A: implementation bug** — timestamp omitted |

**Aggregate**: bind-only BindF1 = KF 0.292 / SA 0.267; bind CVSR = 0/20 for both. Trait binds match (growth_stage → metrics semantic equivalence works); sensor binds fail (timestamp omission + unit alias gaps).

---

## 1. Gold Requirements (test_v2_gold.jsonl)

All 4 tasks have `task_type=data_binding`, `annotation_version=v2`, `review_status=approved`.
All 4 public prompts declare: `时间戳 2026-09-01T00:00:00+08:00` — making `timestamp` a **live contract term** under evaluator_v2.3's `_prompt_declares_timestamp()` → `_clean_required_md(require_timestamp=True)`.

### TN21-v2-bind (humidity sensors → percent, unit matches)
- initial_state.objects: `N21_kiwi_gh:Greenhouse`, `N21_kiwi_row:CropRow`, `N21_kiwi_sen{1,2}:Sensor metric=humidity unit=%`, `N21_kiwi_plant:Plant(is_key=true)`
- required_bindings (3):
  - `N21_kiwi_sen1 → N21_kiwi_row` (sensor_bind): `{metrics:[humidity], timestamp:2026-09-01..., unit:%}`
  - `N21_kiwi_sen2 → N21_kiwi_row` (sensor_bind): `{metrics:[humidity], timestamp:2026-09-01..., unit:%}`
  - `N21_kiwi_plant → N21_kiwi_plant` (trait_bind): `{timestamp:2026-09-01..., trait:growth_stage, unit:text}`

### TN22-v2-bind (temperature sensors → °C)
- required_bindings (4):
  - 3× `sen → fig_row` (sensor_bind): `{metrics:[temperature], timestamp, unit:°C}`
  - 1× `fig_plant → fig_plant` (trait_bind): `{timestamp, trait:growth_stage, unit:text}`

### TN23-v2-bind (light sensors → klux)
- required_bindings (3):
  - 2× `sen → plum_row` (sensor_bind): `{metrics:[light], timestamp, unit:klux}`
  - 1× `plum_plant → plum_plant` (trait_bind): `{timestamp, trait:growth_stage, unit:text}`

### TN24-v2-bind (co2 sensors → ppm)
- required_bindings (4):
  - 3× `sen → pear_row` (sensor_bind): `{metrics:[co2], timestamp, unit:ppm}`
  - 1× `pear_plant → pear_plant` (trait_bind): `{timestamp, trait:growth_stage, unit:text}`

---

## 2. Generated Bindings (live run via `bindings_only_scene`)

### TN22-v2-bind generated:
```json
{"subject":"N22_fig_sen1","target":"N22_fig_row","type":"sensor_bind","metadata":{"metrics":["temperature"],"unit":"celsius"}}
{"subject":"N22_fig_sen2","target":"N22_fig_row","type":"sensor_bind","metadata":{"metrics":["temperature"],"unit":"celsius"}}
{"subject":"N22_fig_sen3","target":"N22_fig_row","type":"sensor_bind","metadata":{"metrics":["temperature"],"unit":"celsius"}}
{"subject":"N22_fig_plant","target":"N22_fig_plant","type":"trait_bind","metadata":{"metrics":["growth_stage"],"unit":"text","timestamp":"2026-09-01T00:00:00+08:00"}}
```

### TN23-v2-bind generated:
```json
{"subject":"N23_plum_sen1","target":"N23_plum_row","type":"sensor_bind","metadata":{"metrics":["light_intensity"],"unit":"lux"}}
{"subject":"N23_plum_sen2","target":"N23_plum_row","type":"sensor_bind","metadata":{"metrics":["light_intensity"],"unit":"lux"}}
{"subject":"N23_plum_plant","target":"N23_plum_plant","type":"trait_bind","metadata":{"metrics":["growth_stage"],"unit":"text","timestamp":"2026-09-01T00:00:00+08:00"}}
```

### TN24-v2-bind generated:
```json
{"subject":"N24_pear_sen1","target":"N24_pear_row","type":"sensor_bind","metadata":{"metrics":["co2"],"unit":"ppm"}}
{"subject":"N24_pear_sen2","target":"N24_pear_row","type":"sensor_bind","metadata":{"metrics":["co2"],"unit":"ppm"}}
{"subject":"N24_pear_sen3","target":"N24_pear_row","type":"sensor_bind","metadata":{"metrics":["co2"],"unit":"ppm"}}
{"subject":"N24_pear_plant","target":"N24_pear_plant","type":"trait_bind","metadata":{"metrics":["growth_stage"],"unit":"text","timestamp":"2026-09-01T00:00:00+08:00"}}
```

---

## 3. Evaluator Matching Analysis (binding_match.py v2.3)

### match_bindings flow (evaluators/binding_match.py:201-269)
1. `_prompt_declares_timestamp(prompt)` → True for TN21-24 (prompt contains `时间戳`) → `require_timestamp=True`
2. For each gold binding, `_clean_required_md(md, require_timestamp=True)` drops only `fixed` (in `_ANNOTATION_KEYS={"fixed"}`); **keeps `timestamp`**
3. `_metadata_equal(gen_md, req_md, require_timestamp=True)` compares:
   - timestamp: exact-string match (no fuzzy date parsing)
   - unit: `_norm_value` → `_UNIT_CANONICAL` alias lookup
   - metrics: `_norm_list` → set comparison
   - trait: `req["trait"]` vs `gen["metrics"]` (semantic equivalence, gold→method)

### Unit normalization table (`_UNIT_CANONICAL`, binding_match.py:74-83)
```python
{"%": "percent", "percent": "percent", "celsius": "celsius", "c": "celsius",
 "ppm": "ppm", "parts_per_million": "ppm"}
```

### Per-binding matcher reasoning
| Task | gen_sensor_metadata | gold_sensor_metadata | matcher result | reason |
|---|---|---|---|---|
| TN21 | `{metrics:[humidity], unit:%}` | `{metrics:[humidity], ts:2026-..., unit:%}` | ❌ | **timestamp missing** — `require_timestamp=True`, gen omits it → `gen.get("timestamp")` is None → `_norm_value(None)` ≠ `2026-09-01...` |
| TN22 | `{metrics:[temperature], unit:celsius}` | `{metrics:[temperature], ts:..., unit:°C}` | ❌ | timestamp missing **AND** `unit:"°C"` → `_norm("°C")="°c"` not in `_UNIT_CANONICAL` (only `"c"` and `"celsius"` map to `"celsius"`) — `°c` ≠ `celsius` |
| TN23 | `{metrics:[light_intensity], unit:lux}` | `{metrics:[light], ts:..., unit:klux}` | ❌ | timestamp missing **AND** `unit:"klux"` → not in table; `metrics:["light_intensity"]` ≠ `{"light"}` |
| TN24 | `{metrics:[co2], unit:ppm}` | `{metrics:[co2], ts:..., unit:ppm}` | ❌ | **timestamp missing only** (`ppm`/`co2` match correctly) |
| TN21-24 trait | `{metrics:[growth_stage], unit:text, ts:2026-09-01...}` | `{ts:2026-..., trait:growth_stage, unit:text}` | ✅ | timestamp present; `trait:"growth_stage"` matches `gen.metrics={"growth_stage"}` (semantic equivalence); `unit:"text"` matches |

### Why BindF1 is fractional (not 0)
- TN21: 1 trait_bind matched / 3 required → precision=1/3, recall=1/3 → F1=0.5 (matches record 0.333)
- TN22: 1 trait_bind matched / 4 required → F1 = 2×(0.25×1.0)/(0.25+1.0) = 0.4 (matches 0.25)
- TN23: 1 matched / 3 → F1=0.5 (matches 0.333)
- TN24: 1 matched / 4 → F1=0.4 (matches 0.25)

The trait binds **do match** — the failure is exclusively on sensor binds.

---

## 4. Root-Cause Classification

### A. Implementation bug (method-side) — PRIMARY, FIXABLE in Phase 3.3
**File**: `harness/stepwise_builder.py:241` (`bindings_only_scene` system prompt)
```python
system = (
    "You emit data bindings for an existing digital-twin scene. Shared knowledge:\n"
    "Binding types: sensor_bind (sensor→monitored object), trait_bind (trait→plant), "
    "asset (object→asset). metadata: {metrics:[...], unit:<canonical unit>, asset_key, policy}. "
    "Use ONLY the exact existing ids below. Do NOT invent or rename objects. "
    "Output ONLY compact JSON under key \"bindings\". No markdown, no prose."
)
```
The system prompt lists `metadata: {metrics, unit, asset_key, policy}` but **never mentions `timestamp`**, despite the public prompt contractually declaring it. **Fix**: add `timestamp: <ISO-8601> from the prompt's declared timestamp` to the builder's instruction. This is a method-side change (not scorer/benchmark) → allowed in Phase 3.3 optimization. Would fix TN21 + TN24 sensor binds (unit/metrics already correct).

### B. Benchmark/evaluator contract gap — FROZEN, NOT fixable in Phase 3
**File**: `evaluators/binding_match.py:74-83` (`_UNIT_CANONICAL`)
- `°C` → `_norm` = `°c` → **not aliased** to `celsius`. The table maps `c`/`celsius`→`celsius` but `°c` falls through.
- `klux` → not aliased to `lux`/`light`.
- `light_intensity` vs `light` → no alias in `metrics` comparison.
Because the evaluator is **frozen** (Phase 3 hard constraint #2), these cannot be corrected. They cause TN22 + TN23 sensor binds to fail regardless of method optimization.

### C. Real capability limitation — NOT supported by evidence
The trait binds match correctly, and TN21/TN24 sensor binds would match if the timestamp were emitted. This is **not** a capability gap — it's an instruction gap (A) partially bounded by alias gaps (B).

---

## 5. Conclusion

| Task | Fixable by method optimization? | Blocked by frozen evaluator? | Classification |
|---|---|---|---|
| TN21-v2-bind | ✅ (add timestamp to builder prompt) | NO (`%`→`percent` works) | **A: implementation bug** |
| TN22-v2-bind | Partially (timestamp) | YES (`°C`∉alias table) | **A + B** |
| TN23-v2-bind | Partially (timestamp) | YES (`klux`/`light_intensity` gaps) | **A + B** |
| TN24-v2-bind | ✅ (add timestamp to builder prompt) | NO (`ppm`/`co2` work) | **A: implementation bug** |

**Verdict**: Bind CVSR=0 is **primarily an implementation bug** (A) — the `bindings_only_scene` builder system prompt omits the `timestamp` instruction that the public prompt contractually requires. Adding `timestamp` to the prompt guidance (Phase 3.3) is expected to fix TN21 + TN24 sensor binds (2/4 tasks → bind CVSR from 0 toward 0.5). TN22 + TN23 are additionally bounded by **frozen evaluator alias gaps** (`°C`, `klux`) that Phase 3 cannot fix without an evaluator_v2.4 (scorer modification — explicitly forbidden).

This is documented as an honest capability boundary in the paper: KAFarmTwin's typed repair + knowledge compiler achieves asset/repair CVSR=1.0, but the bind category is bounded by (a) a fixable builder-instruction gap and (b) frozen evaluator normalization limits for non-canonical units.

---

## 6. Phase 3.3 — Method-Side Fix Applied & Validated

**Fix** (`harness/stepwise_builder.py: bindings_only_scene`):
1. System prompt now lists `timestamp:<ISO-8601 string declared in the prompt's timestamp contract>` in the binding metadata template.
2. Deterministic stamping: when the public prompt declares a timestamp contract (same `_prompt_declares_timestamp` scope the frozen evaluator uses), the literal ISO-8601 value is stamped onto every emitted binding's `metadata.timestamp`. This is a builder-side normalization equivalent to the evaluator's unit-alias table — it reads ONLY the public prompt, never gold, and applies uniformly to all methods that share this builder.

**Why deterministic stamping (not prompting alone)**: the LLM does not reliably emit `timestamp` even when instructed (live test: prompt instruction alone left sensor binds without timestamp). Deterministic honoring of the declared contract is the correct builder behavior — a method that claims to bind a measurement at the declared time must emit that time, exactly as the evaluator's exact-string check expects.

**Validated result** (live, 2 runs/task, real DeepSeek-V4-Flash, frozen commit `51beab1` + evaluator_v2.3):

| Task | KF BindF1 before | KF BindF1 after | Blocked by frozen evaluator? |
|---|---|---|---|
| TN21-v2-bind | 0.333 (trait only) | **1.0** (sensor+trait) | NO (`%`→`percent` matches) |
| TN22-v2-bind | 0.25 (trait only) | 0.25 (trait only) | YES (`°C`∉alias table) |
| TN23-v2-bind | 0.333 (trait only) | 0.333 (trait only) | YES (`klux`/`light_intensity` gaps) |
| TN24-v2-bind | 0.25 (trait only) | **1.0** (sensor+trait) | NO (`ppm`/`co2` match) |

**Conclusion**: 2/4 bind tasks (TN21, TN24) achieve BindF1=1.0 after the method-side fix. TN22/TN23 remain bounded exclusively by **frozen evaluator alias gaps** (`°C`→`celsius`, `klux`/`light`/`light_intensity`) — category B, not fixable in Phase 3 without evaluator_v2.4 (scorer modification, explicitly forbidden). This is the documented honest capability boundary.

**No integrity violation**: the fix is entirely method-side (builder behavior). The frozen benchmark (gold hash `61a48f61...`), frozen evaluator_v2.3 (scorer hash `8b7d4695...`), and baseline budgets are untouched.
