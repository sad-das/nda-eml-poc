from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
from .eml import Expr, finite_mse
from .targets import Target

@dataclass
class Gate6Report:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    train_mse: float = float("inf")
    holdout_mse: float = float("inf")
    complex_mse: float = float("inf")

class Gate6:
    """Operational UNSAT / anti-eclectic gate for EML witnesses."""
    def __init__(self, threshold: float = 1e-16, max_nodes: int = 512, max_depth: int = 64) -> None:
        self.threshold = threshold
        self.max_nodes = max_nodes
        self.max_depth = max_depth

    def check(self, expr: Expr, target: Target, frozen_signatures: set[str], *, mutation_requested: bool = False) -> Gate6Report:
        reasons: list[str] = []
        if not expr.is_eml_tree:
            reasons.append("non_constructive_shortcut_or_non_eml_tree")
        if expr.node_count > self.max_nodes:
            reasons.append("unbounded_node_growth")
        if expr.depth > self.max_depth:
            reasons.append("unbounded_depth_growth")
        if mutation_requested and expr.signature() in frozen_signatures:
            reasons.append("frozen_witness_mutation_attempt")

        train_mse = finite_mse(expr, target.train_x, target.train_y(), target.train_y_arg)
        holdout_mse = finite_mse(expr, target.holdout_x, target.holdout_y(), target.holdout_y_arg)
        complex_mse = finite_mse(expr, target.complex_x, target.complex_y(), target.complex_y_arg)

        if not np.isfinite(train_mse) or train_mse > self.threshold:
            reasons.append("train_grid_failure")
        if not np.isfinite(holdout_mse) or holdout_mse > self.threshold:
            reasons.append("holdout_generalization_failure")
        if not np.isfinite(complex_mse) or complex_mse > max(self.threshold * 100, 1e-13):
            reasons.append("complex_domain_failure")

        return Gate6Report(not reasons, reasons, train_mse, holdout_mse, complex_mse)
