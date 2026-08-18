#!/usr/bin/env bash
# Launch the full frozen-test_v2 formal run in the background.
# All 5 fair methods x 20 test tasks x 5 runs, real DeepSeek-V4-Flash.
# Interrupt-safe: v3_runs.jsonl is append-only, summary regenerated at the end.
# Usage: bash experiments/v3/scripts/launch_formal_test_run.sh
set -euo pipefail

# Resolve repo root robustly (works regardless of cwd): walk up to the git root.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "$0")/../../.." && pwd)")"
cd "$ROOT"
echo "[launch] repo root = $ROOT"

# Clean results dir first (fresh formal run, no stale contamination).
mkdir -p experiments/v3/results
# Move any existing results aside (keep provenance) rather than delete.
STAMP="formal_$(date +%Y%m%d_%H%M%S)"
if [ -s experiments/v3/results/v3_runs.jsonl ]; then
  mkdir -p experiments/v3/results/archive_$STAMP
  mv experiments/v3/results/v3_runs.jsonl experiments/v3/results/archive_$STAMP/ || true
  mv experiments/v3/results/v3_summary.json experiments/v3/results/archive_$STAMP/ 2>/dev/null || true
  mv experiments/v3/results/v3_summary.csv experiments/v3/results/archive_$STAMP/ 2>/dev/null || true
fi

# Load API credentials without printing them.
if [ ! -f .env ]; then
  echo "[launch] ERROR: .env not found at repo root $ROOT" >&2
  exit 2
fi
set -a; . ./.env; set +a

echo "[launch] $(date) starting formal run on frozen test_v2 (5 methods x 20 tasks x 5 runs)"
echo "[launch] log -> logs/formal_test_run.log"
mkdir -p logs
nohup python3 experiments/v3/scripts/run_fair_baselines.py \
  --split test --runs 5 \
  --methods SingleAgent-AllTools,ReAct-AllTools,GenericMultiAgent-AllTools,GenericRepair-AllTools,KAFarmTwin-TypedRepair \
  > logs/formal_test_run.log 2>&1 &
PID=$!
echo "[launch] PID=$PID"
echo "$PID" > logs/formal_test_run.pid
echo "[launch] launched; watch: tail -f logs/formal_test_run.log"
echo "[launch] when done, run: python3 experiments/v3/scripts/run_sota_gate.py"