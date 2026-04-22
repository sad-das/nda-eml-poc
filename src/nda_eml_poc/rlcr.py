from __future__ import annotations

from dataclasses import dataclass, field
from .eml import Expr

@dataclass
class RLCRPolicy:
    """Policy over mediator search only; never an authority for truth."""
    weights: dict[str, float] = field(default_factory=lambda: {
        "constructive": 1.5,
        "terminal": 0.8,
        "eml": 0.3,
        "shortcut": -5.0,
        "decoy": -1.0,
    })
    lr: float = 0.25

    def score(self, expr: Expr, tag: str = "eml") -> float:
        base = self.weights.get(tag, 0.0)
        # Prefer smaller constructive witnesses when tags tie.
        return base - 0.002 * expr.node_count - 0.01 * expr.depth

    def update(self, tag: str, reward: float) -> None:
        old = self.weights.get(tag, 0.0)
        self.weights[tag] = old + self.lr * (reward - old)
