from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple
import math
import numpy as np

Array = np.ndarray


def as_complex(x: Array | Iterable[complex]) -> Array:
    return np.asarray(x, dtype=np.complex128)


def eml_eval(left: Array, right: Array) -> Array:
    """Evaluate eml(x, y) = exp(x) - log(y) with extended IEEE semantics.

    NumPy's complex logarithm returns -inf for log(0+0j), and exp(-inf)=0.
    This is intentional: the EML paper notes that several compiled formulas rely
    on extended-real/IEEE behaviour such as log(0)=-inf and exp(-inf)=0.
    """
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        out = np.exp(left) - np.log(right)
    return np.asarray(out, dtype=np.complex128)


@dataclass(frozen=True)
class Expr:
    kind: str
    left: Optional["Expr"] = None
    right: Optional["Expr"] = None
    label: Optional[str] = None
    shortcut_x: Optional[Tuple[complex, ...]] = None
    shortcut_y: Optional[Tuple[complex, ...]] = None
    arity: int = 1

    @staticmethod
    def one() -> "Expr":
        return Expr("one")

    @staticmethod
    def x() -> "Expr":
        return Expr("x")

    @staticmethod
    def y() -> "Expr":
        return Expr("y", arity=2)

    @staticmethod
    def eml(left: "Expr", right: "Expr") -> "Expr":
        return Expr("eml", left=left, right=right, arity=max(left.arity, right.arity))

    @staticmethod
    def shortcut(name: str, x_train: Array, y_train: Array, arity: int = 1) -> "Expr":
        return Expr(
            "shortcut",
            label=name,
            shortcut_x=tuple(complex(v) for v in np.asarray(x_train).ravel()),
            shortcut_y=tuple(complex(v) for v in np.asarray(y_train).ravel()),
            arity=arity,
        )

    @property
    def is_eml_tree(self) -> bool:
        if self.kind in {"one", "x"}:
            return True
        if self.kind == "y":
            return True
        if self.kind == "eml":
            assert self.left is not None and self.right is not None
            return self.left.is_eml_tree and self.right.is_eml_tree
        return False

    @property
    def depth(self) -> int:
        if self.kind in {"one", "x", "y", "shortcut"}:
            return 0
        assert self.left is not None and self.right is not None
        return 1 + max(self.left.depth, self.right.depth)

    @property
    def node_count(self) -> int:
        if self.kind in {"one", "x", "y", "shortcut"}:
            return 1
        assert self.left is not None and self.right is not None
        return 1 + self.left.node_count + self.right.node_count

    def eval(self, x: Array, y: Optional[Array] = None) -> Array:
        x = as_complex(x)
        if y is None:
            y = np.ones_like(x, dtype=np.complex128)
        else:
            y = as_complex(y)
        if self.kind == "one":
            return np.ones_like(x, dtype=np.complex128)
        if self.kind == "x":
            return x.astype(np.complex128)
        if self.kind == "y":
            return y.astype(np.complex128)
        if self.kind == "eml":
            assert self.left is not None and self.right is not None
            return eml_eval(self.left.eval(x, y), self.right.eval(x, y))
        if self.kind == "shortcut":
            # Deliberately non-constructive baseline: table lookup on training shape,
            # nearest-neighbour elsewhere. Gate 6 must reject this.
            tx = np.asarray(self.shortcut_x, dtype=np.complex128)
            ty = np.asarray(self.shortcut_y, dtype=np.complex128)
            flat_x = x.ravel()
            if len(flat_x) == len(tx) and np.allclose(flat_x, tx, rtol=0, atol=1e-12):
                return ty.reshape(x.shape)
            idx = np.abs(flat_x[:, None] - tx[None, :]).argmin(axis=1)
            return ty[idx].reshape(x.shape)
        raise ValueError(f"unknown expression kind: {self.kind}")

    def signature(self) -> str:
        if self.kind == "one":
            return "1"
        if self.kind == "x":
            return "x"
        if self.kind == "y":
            return "y"
        if self.kind == "shortcut":
            return f"shortcut[{self.label}]"
        assert self.left is not None and self.right is not None
        return f"eml({self.left.signature()},{self.right.signature()})"

    def rpn(self) -> str:
        if self.kind == "one":
            return "1"
        if self.kind == "x":
            return "x"
        if self.kind == "y":
            return "y"
        if self.kind == "shortcut":
            return f"shortcut[{self.label}]"
        assert self.left is not None and self.right is not None
        return f"{self.left.rpn()}{self.right.rpn()}E"

    def feature_key(self) -> str:
        if self.kind in {"one", "x", "y", "shortcut"}:
            return self.kind if self.kind != "shortcut" else "shortcut"
        assert self.left is not None and self.right is not None
        return f"eml:{self.left.kind}:{self.right.kind}:d{self.depth}:n{self.node_count}"

    def __str__(self) -> str:
        return self.signature()


def finite_mse(expr: Expr, x: Array, y_true: Array, y_arg: Optional[Array] = None) -> float:
    pred = expr.eval(x, y_arg)
    y_true = as_complex(y_true)
    if pred.shape != y_true.shape or np.any(np.isnan(pred.real)) or np.any(np.isnan(pred.imag)):
        return math.inf
    diff = pred - y_true
    # Allow infinities only when target also has them at the same coordinates.
    if not np.all(np.isfinite(diff)):
        return math.inf
    return float(np.mean(np.abs(diff) ** 2))


def expression_pool(max_depth: int, *, binary: bool = False) -> list[Expr]:
    terminals = [Expr.one(), Expr.x()] + ([Expr.y()] if binary else [])
    by_depth = [terminals]
    all_exprs = list(terminals)
    seen = {e.signature() for e in all_exprs}
    for depth in range(1, max_depth + 1):
        level: list[Expr] = []
        candidates = [e for ds in by_depth for e in ds]
        for left in candidates:
            for right in candidates:
                if 1 + max(left.depth, right.depth) != depth:
                    continue
                expr = Expr.eml(left, right)
                sig = expr.signature()
                if sig not in seen:
                    seen.add(sig)
                    level.append(expr)
        by_depth.append(level)
        all_exprs.extend(level)
    return all_exprs
