# KAFarmTwin v3 Statistical Report

## Per-Method Summary (all tasks x all runs)

| method | CVSR | pass1 | pass3 | pass5 | objF1 | critR | relF1 | bindF1 | fatal | cost | p95_latency |
|--------|------|-------|-------|-------|-------|-------|-------|--------|-------|------|-------------|
| KAFarmTwin-TypedRepair | 0.3750 | 0.3750 | 0.4286 | 0.3750 | 0.7986 | 0.8750 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0ms |
| SingleAgent-AllTools | 0.2500 | 0.2500 | 0.2857 | 0.2500 | 0.5097 | 0.5250 | 0.0000 | 0.0000 | 0.1500 | 0.0000 | 0ms |

## Paired Bootstrap: KAFarmTwin vs Baselines

### vs SingleAgent-AllTools
  - mean diff: +0.1250
  - 95% CI: [+0.0250, +0.2250]
  - CI lower > 0: True
  - p-value (H0: diff <= 0): 0.0044

## Pareto Frontier: ['KAFarmTwin-TypedRepair']
