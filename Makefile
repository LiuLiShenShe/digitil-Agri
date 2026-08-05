# KAFarmTwin v3 evaluation Makefile
#
# Root command entry points for the v3 rebuild. See
#   openspec/changes/rebuild-kafarmtwin-sota-evaluation/specs/sota-gate/spec.md
# for the gate definition.

PY := python3
PYTEST := $(PY) -m pytest
# Source .env if present (so AGNES_* / LLM_* vars are available to the harness)
ENV := set -a; test -f .env && . ./.env; set +a;

V3 := experiments/v3
BENCH := $(V3)/benchmark
SCRIPTS := $(V3)/scripts
GO_BACKEND := digital-twingo/scene-server-go

.PHONY: audit benchmark-validate evaluator-test backend-test frontend-build smoke \
        run-dev run-test ablation robustness statistical-report reproduce-paper sota-gate

## Security + OpenSpec audit
audit:
	@echo "[audit] scanning for committed secrets (excluding .env, node_modules, dist)..."
	@! grep -rnE 'sk-[A-Za-z0-9]{16,}' --include='*.py' --include='*.go' --include='*.ts' --include='*.js' --include='*.vue' \
	    --include='*.yml' --include='*.yaml' --include='*.json' --include='*.md' . 2>/dev/null | grep -vE '\.env|node_modules|/dist/|legacy' || true
	@echo "[audit] openspec validate..."
	openspec validate --all --strict

## Validate benchmark schema + sealed SHA-256
benchmark-validate:
	$(PY) $(SCRIPTS)/benchmark/benchmark_validate.py

## Anti-cheat + evaluator + statistical unit tests
evaluator-test:
	$(PYTEST) $(V3)/tests/test_anti_cheat.py $(V3)/tests/test_statistical.py -q

## Backend Go tests
backend-test:
	cd $(GO_BACKEND) && go test ./...

## Frontend build (only when touching frontend)
frontend-build:
	cd digital-twingo/scene-design-v2 && ./node_modules/.bin/vite build

## Smoke: 3 tasks x each method 1 run on dev (real LLM or mock)
smoke:
	$(ENV) $(PY) $(SCRIPTS)/run_fair_baselines.py --split dev --max-tasks 3 --runs 1 --smoke

## Full run-test: dev+test, each (task x method x model) >= 5 runs
run-test:
	$(ENV) $(PY) $(SCRIPTS)/run_fair_baselines.py --split dev --runs 5
	$(ENV) $(PY) $(SCRIPTS)/run_fair_baselines.py --split test --runs 5

## Dev split small validation
run-dev:
	$(ENV) $(PY) $(SCRIPTS)/run_fair_baselines.py --split dev --runs 1

## End-to-end ablation (feature flags, >= 5 runs)
ablation:
	$(ENV) $(PY) $(SCRIPTS)/run_ablation_v3.py --runs 5

## Multi-model robustness
robustness:
	$(ENV) $(PY) $(SCRIPTS)/run_robustness.py

## Statistical report (bootstrap CI, pass^k, Pareto)
statistical-report:
	$(ENV) $(PY) $(SCRIPTS)/statistical_report.py

## Reproduce paper numbers from new results (fails on hand-copied legacy numbers)
reproduce-paper:
	$(ENV) $(PY) $(SCRIPTS)/run_sota_gate.py --reproduce-paper

## SOTA gate — non-zero exit until all conditions pass
sota-gate:
	$(ENV) $(PY) $(SCRIPTS)/run_sota_gate.py
