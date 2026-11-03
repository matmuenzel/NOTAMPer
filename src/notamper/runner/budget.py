"""Call and cost budget for a benchmark run."""

from __future__ import annotations

# USD per 1M tokens (input, output). Keyed by model-name prefix (provider prefix stripped);
# the longest matching prefix wins, so dated ids like claude-opus-4-1-20250805 are covered.
DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-4": (15.0, 75.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-haiku-4": (1.0, 5.0),
    "claude-opus-4-1": (15.0, 75.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
}


class BudgetExceeded(Exception):
    """Raised before a call that would exceed the configured budget."""


def _price_key(model: str) -> str:
    return model.split(":", 1)[-1].split("@", 1)[0]


class Budget:
    """Tracks API calls and estimated spend; mock and local (ollama) models are free."""

    def __init__(
        self,
        max_calls: int | None = None,
        max_usd: float | None = None,
        prices: dict[str, tuple[float, float]] = DEFAULT_PRICES,
    ) -> None:
        self.max_calls = max_calls
        self.max_usd = max_usd
        self.prices = prices
        self._calls = 0
        self._spent = 0.0

    @property
    def calls(self) -> int:
        return self._calls

    @property
    def spent_usd(self) -> float:
        return self._spent

    def price_for(self, model: str) -> tuple[float, float]:
        """Longest-prefix price match; unknown models use the most expensive listed price."""
        name = _price_key(model)
        matches = [k for k in self.prices if name.startswith(k)]
        if matches:
            return self.prices[max(matches, key=len)]
        return (
            max(p[0] for p in self.prices.values()),
            max(p[1] for p in self.prices.values()),
        )

    def check(self) -> None:
        """Raise BudgetExceeded if one more call is not allowed."""
        if self.max_calls is not None and self._calls + 1 > self.max_calls:
            raise BudgetExceeded(f"max_calls={self.max_calls} reached")
        if self.max_usd is not None and self._spent >= self.max_usd:
            raise BudgetExceeded(f"max_usd={self.max_usd} reached")

    def charge(self, model: str, in_tok: int, out_tok: int) -> float:
        """Record one call and return its estimated cost in USD."""
        if model.startswith(("mock:", "ollama:")):
            price = (0.0, 0.0)
        else:
            price = self.price_for(model)
        cost = (in_tok * price[0] + out_tok * price[1]) / 1_000_000
        self._calls += 1
        self._spent += cost
        return cost
