from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np

Array = np.ndarray

@dataclass(frozen=True)
class Target:
    name: str
    family: str
    arity: int
    train_x: Array
    holdout_x: Array
    complex_x: Array
    train_y_arg: Optional[Array] = None
    holdout_y_arg: Optional[Array] = None
    complex_y_arg: Optional[Array] = None

    def fn(self, x: Array, y: Optional[Array] = None) -> Array:
        x = np.asarray(x, dtype=np.complex128)
        if y is not None:
            y = np.asarray(y, dtype=np.complex128)
        if self.name == "one_const": return np.ones_like(x, dtype=np.complex128)
        if self.name == "identity_x": return x
        if self.name == "identity_y": return y if y is not None else np.ones_like(x)
        if self.name == "e_const": return np.ones_like(x, dtype=np.complex128) * np.e
        if self.name == "zero_const": return np.zeros_like(x, dtype=np.complex128)
        if self.name == "exp_x": return np.exp(x)
        if self.name == "ln_x": return np.log(x)
        if self.name == "neg_x": return -x
        if self.name == "x_minus_y": return x - y
        if self.name == "x_plus_y": return x + y
        if self.name == "x_times_y": return x * y
        if self.name == "x_div_y": return x / y
        if self.name == "x_square": return x * x
        raise ValueError(f"unknown target {self.name}")

    def train_y(self) -> Array:
        return self.fn(self.train_x, self.train_y_arg)

    def holdout_y(self) -> Array:
        return self.fn(self.holdout_x, self.holdout_y_arg)

    def complex_y(self) -> Array:
        return self.fn(self.complex_x, self.complex_y_arg)


def make_targets(seed: int = 0) -> list[Target]:
    rng = np.random.default_rng(seed)
    # Positive real domain for formulas that use log(x), x/y, etc.
    train_x = np.array([0.35, 0.6, 0.9, 1.25, 1.7, 2.1], dtype=np.complex128)
    train_y = np.array([1.6, 0.45, 2.3, 0.8, 1.2, 1.9], dtype=np.complex128)
    holdout_x = np.sort(rng.uniform(0.28, 2.4, size=96)).astype(np.complex128)
    holdout_y = np.sort(rng.uniform(0.31, 2.5, size=96)).astype(np.complex128)
    # Non-zero complex points. Kept modest to avoid overflow in nested EML trees.
    complex_x = (rng.uniform(0.35, 1.8, size=48) + 1j * rng.uniform(-0.35, 0.35, size=48)).astype(np.complex128)
    complex_y = (rng.uniform(0.4, 1.9, size=48) + 1j * rng.uniform(-0.35, 0.35, size=48)).astype(np.complex128)
    unary = [
        "one_const", "identity_x", "e_const", "zero_const", "exp_x", "ln_x", "neg_x", "x_square",
    ]
    binary = ["identity_y", "x_minus_y", "x_plus_y", "x_times_y", "x_div_y"]
    targets: list[Target] = []
    for name in unary:
        targets.append(Target(name, "unary", 1, train_x, holdout_x, complex_x))
    for name in binary:
        targets.append(Target(name, "binary", 2, train_x, holdout_x, complex_x, train_y, holdout_y, complex_y))
    return targets
