from __future__ import annotations

from dataclasses import dataclass
from .eml import Expr

ONE = Expr.one()
X = Expr.x()
Y = Expr.y()


def E(a: Expr, b: Expr) -> Expr:
    return Expr.eml(a, b)


def exp_expr(z: Expr) -> Expr:
    return E(z, ONE)


def log_expr(z: Expr) -> Expr:
    # E(1, E(E(1, z), 1)) = log(z)
    return E(ONE, E(E(ONE, z), ONE))


def zero_expr() -> Expr:
    # log(1) = 0
    return log_expr(ONE)


def sub_expr(a: Expr, b: Expr) -> Expr:
    # E(log(a), exp(b)) = a - b. Works over positive real domain and, with
    # principal log, over non-zero complex a. For a=0 it relies on log(0)=-inf.
    return E(log_expr(a), exp_expr(b))


def neg_expr(a: Expr) -> Expr:
    return sub_expr(zero_expr(), a)


def add_expr(a: Expr, b: Expr) -> Expr:
    return sub_expr(a, neg_expr(b))


def mul_expr(a: Expr, b: Expr) -> Expr:
    return exp_expr(add_expr(log_expr(a), log_expr(b)))


def div_expr(a: Expr, b: Expr) -> Expr:
    return exp_expr(sub_expr(log_expr(a), log_expr(b)))


def square_expr(a: Expr) -> Expr:
    return mul_expr(a, a)


@dataclass(frozen=True)
class Witness:
    name: str
    expr: Expr
    derivation: str
    tier: str


def witness_registry() -> dict[str, Witness]:
    """Constructive pure-EML witnesses used by the NDA full variant.

    They are not claimed to be shortest expressions. The point of stage 2 is to
    verify that a bootstrapped DKG can compose already validated mediators into
    larger pure-EML action schemas.
    """
    return {
        "one_const": Witness("one_const", ONE, "terminal 1", "terminal"),
        "identity_x": Witness("identity_x", X, "terminal x", "terminal"),
        "identity_y": Witness("identity_y", Y, "terminal y", "terminal"),
        "e_const": Witness("e_const", exp_expr(ONE), "exp(1)", "elementary"),
        "zero_const": Witness("zero_const", zero_expr(), "log(1)", "elementary"),
        "exp_x": Witness("exp_x", exp_expr(X), "eml(x,1)", "elementary"),
        "ln_x": Witness("ln_x", log_expr(X), "eml logarithm identity", "elementary"),
        "neg_x": Witness("neg_x", neg_expr(X), "0 - x", "arithmetic"),
        "x_minus_y": Witness("x_minus_y", sub_expr(X, Y), "eml(log(x), exp(y))", "arithmetic"),
        "x_plus_y": Witness("x_plus_y", add_expr(X, Y), "x - (0 - y)", "arithmetic"),
        "x_times_y": Witness("x_times_y", mul_expr(X, Y), "exp(log(x)+log(y))", "arithmetic"),
        "x_div_y": Witness("x_div_y", div_expr(X, Y), "exp(log(x)-log(y))", "arithmetic"),
        "x_square": Witness("x_square", square_expr(X), "x*x", "arithmetic"),
    }
