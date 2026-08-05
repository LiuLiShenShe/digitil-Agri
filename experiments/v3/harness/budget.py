"""Budget enforcer — identical limits for all methods."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BudgetConfig:
    max_llm_calls: int = 30
    max_tool_calls: int = 100
    max_repair_rounds: int = 3
    max_tokens: int = 500_000
    max_cost: float = 10.0        # USD
    timeout_seconds: int = 300


class BudgetExhausted(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class BudgetEnforcer:
    def __init__(self, config: BudgetConfig | None = None) -> None:
        self.config = config or BudgetConfig()
        self.llm_calls = 0
        self.tool_calls = 0
        self.repair_rounds = 0
        self.tokens = 0
        self.cost = 0.0

    def assert_tool_budget(self, tool: str = "") -> None:
        self.tool_calls += 1
        if self.tool_calls > self.config.max_tool_calls:
            raise BudgetExhausted(f"tool_calls={self.tool_calls} > max {self.config.max_tool_calls}")

    def assert_llm_budget(self) -> None:
        self.llm_calls += 1
        if self.llm_calls > self.config.max_llm_calls:
            raise BudgetExhausted(f"llm_calls={self.llm_calls} > max {self.config.max_llm_calls}")

    def assert_repair_budget(self) -> bool:
        self.repair_rounds += 1
        if self.repair_rounds > self.config.max_repair_rounds:
            return False
        return True

    def add_tokens(self, n: int) -> None:
        self.tokens += n
        if self.tokens > self.config.max_tokens:
            raise BudgetExhausted(f"tokens={self.tokens} > max {self.config.max_tokens}")

    def add_cost(self, delta: float) -> None:
        self.cost += delta
        if self.cost > self.config.max_cost:
            raise BudgetExhausted(f"cost={self.cost} > max {self.config.max_cost}")

    def summary(self) -> dict[str, Any]:
        return {
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "repair_rounds": self.repair_rounds,
            "tokens": self.tokens,
            "cost": self.cost,
        }
