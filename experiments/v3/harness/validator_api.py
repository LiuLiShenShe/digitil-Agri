"""Single external Validator API — aligned with rule_engine.py, identical for all methods."""

from __future__ import annotations

from typing import Any

from experiments.v3.evaluators.rule_engine import RuleEngine  # type: ignore


class ValidatorAPI:
    """The one and only validation entry point used by every method (and the evaluator).

    It wraps rule_engine.RuleEngine; alignment is guaranteed because both use the
    same RuleEngine implementation. This prevents a method from gaming a different
    validator than the one the scorer uses.
    """

    def __init__(self) -> None:
        self._engine = RuleEngine()

    def validate(self, *, nodes: list[dict[str, Any]], edges: list[dict[str, Any]],
                 bindings: list[dict[str, Any]], active_rules: list[str] | None = None,
                 task: dict[str, Any] | None = None) -> dict[str, Any]:
        active = active_rules or ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]
        violations = self._engine.evaluate(nodes=nodes, edges=edges, bindings=bindings,
                                           active_rules=active, task=task)
        return {
            "valid": not any(v.severity == "fatal" for v in violations),
            "violations": [v.to_dict() for v in violations],
            "fatal_rules": sorted({v.rule_id for v in violations if v.severity == "fatal"}),
            "warning_rules": sorted({v.rule_id for v in violations if v.severity == "warning"}),
        }
