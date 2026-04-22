from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import random
import time
from typing import Optional

from .constructors import witness_registry
from .eml import Expr, expression_pool, finite_mse
from .gate6 import Gate6
from .rlcr import RLCRPolicy
from .targets import Target, make_targets

@dataclass(frozen=True)
class VariantConfig:
    name: str
    gate6: bool = True
    freeze: bool = True
    rlcr: bool = True
    random_tree: bool = False
    gradient_only: bool = False
    constructive_registry: bool = True
    inject_shortcut_first: bool = True
    no_freeze_capacity: int = 6
    max_depth: int = 2
    budget: int = 400
    threshold: float = 1e-16

@dataclass
class Candidate:
    expr: Expr
    tag: str
    source: str

@dataclass
class TargetResult:
    target: str
    family: str
    variant: str
    seed: int
    candidate: str
    rpn: str
    candidate_source: str
    candidate_tag: str
    candidate_depth: int
    candidate_nodes: int
    is_eml_tree: bool
    train_mse: float
    holdout_mse: float
    complex_mse: float
    exact_recovery: bool
    candidate_evals: int
    gate6_rejections: int
    gate6_rejection_reasons: list[str]
    mutation_events: int
    preservation_rate_after_commit: float
    belnap_status_before_commit: str
    runtime_sec: float

@dataclass
class AblationRun:
    variant: str
    seed: int
    results: list[TargetResult] = field(default_factory=list)
    final_preservation_rate: float = 1.0
    policy_weights: dict[str, float] = field(default_factory=dict)

    def to_jsonable(self) -> dict:
        return {
            "variant": self.variant,
            "seed": self.seed,
            "final_preservation_rate": self.final_preservation_rate,
            "policy_weights": self.policy_weights,
            "results": [r.__dict__ for r in self.results],
        }

class NDAStage2Agent:
    def __init__(self, config: VariantConfig, seed: int = 0) -> None:
        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)
        self.gate = Gate6(config.threshold)
        self.policy = RLCRPolicy() if config.rlcr else None
        self.registry = witness_registry()
        self.library: dict[str, Expr] = {}
        self.order: list[str] = []
        self.original_verified: dict[str, Expr] = {}
        self.frozen: set[str] = set()
        self.pool_unary = expression_pool(config.max_depth, binary=False)
        self.pool_binary = expression_pool(config.max_depth, binary=True)

    def run(self) -> AblationRun:
        run = AblationRun(self.config.name, self.seed)
        targets = make_targets(self.seed)
        for target in targets:
            run.results.append(self.solve_target(target))
        run.final_preservation_rate = self._preservation_rate(targets)
        run.policy_weights = dict(self.policy.weights) if self.policy else {}
        return run

    def solve_target(self, target: Target) -> TargetResult:
        if self.config.gradient_only:
            return self._solve_gradient_proxy(target)
        start = time.time()
        gate6_rejections = 0
        rejection_reasons: list[str] = []
        mutation_events = 0
        best_expr: Optional[Expr] = None
        best_tag = "none"
        best_source = "none"
        best_train = math.inf
        best_holdout = math.inf
        best_complex = math.inf
        belnap = "N"
        candidate_evals = 0

        for candidate in self._ordered_candidates(target)[: self.config.budget]:
            candidate_evals += 1
            expr = candidate.expr
            train_mse = finite_mse(expr, target.train_x, target.train_y(), target.train_y_arg)
            holdout_mse = finite_mse(expr, target.holdout_x, target.holdout_y(), target.holdout_y_arg)
            complex_mse = finite_mse(expr, target.complex_x, target.complex_y(), target.complex_y_arg)
            if train_mse < best_train:
                best_expr, best_train, best_holdout, best_complex = expr, train_mse, holdout_mse, complex_mse
                best_tag, best_source = candidate.tag, candidate.source
            if train_mse <= self.config.threshold:
                # There is positive evidence on the training grid. If holdout/complex fails,
                # this is Belnap B: both apparent confirmation and practical resistance.
                belnap = "T" if (holdout_mse <= self.config.threshold and complex_mse <= 1e-13) else "B"
            else:
                belnap = "F"
                continue

            if self.config.gate6:
                report = self.gate.check(expr, target, self.frozen, mutation_requested=False)
                if not report.accepted:
                    gate6_rejections += 1
                    rejection_reasons.extend(report.reasons)
                    if self.policy:
                        self.policy.update(candidate.tag, reward=-0.8)
                    continue
                best_expr, best_train, best_holdout, best_complex = expr, report.train_mse, report.holdout_mse, report.complex_mse
                best_tag, best_source = candidate.tag, candidate.source
            # If Gate 6 is disabled, accepting on training data is intentionally unsafe.
            mutation_events += self._commit(target.name, best_expr)
            if self.policy:
                reward = 1.0 if best_expr.is_eml_tree and best_holdout <= self.config.threshold and best_complex <= 1e-13 else -0.5
                self.policy.update(candidate.tag, reward=reward)
            break

        if best_expr is None:
            best_expr = Expr.shortcut("no_candidate", target.train_x, target.train_y(), arity=target.arity)
            best_tag = "shortcut"
            best_source = "fallback"
        exact = bool(best_expr.is_eml_tree and best_holdout <= self.config.threshold and best_complex <= 1e-13)
        return TargetResult(
            target=target.name,
            family=target.family,
            variant=self.config.name,
            seed=self.seed,
            candidate=best_expr.signature(),
            rpn=best_expr.rpn(),
            candidate_source=best_source,
            candidate_tag=best_tag,
            candidate_depth=best_expr.depth,
            candidate_nodes=best_expr.node_count,
            is_eml_tree=best_expr.is_eml_tree,
            train_mse=best_train,
            holdout_mse=best_holdout,
            complex_mse=best_complex,
            exact_recovery=exact,
            candidate_evals=candidate_evals,
            gate6_rejections=gate6_rejections,
            gate6_rejection_reasons=sorted(set(rejection_reasons)),
            mutation_events=mutation_events,
            preservation_rate_after_commit=self._preservation_rate(make_targets(self.seed)),
            belnap_status_before_commit=belnap,
            runtime_sec=time.time() - start,
        )

    def _ordered_candidates(self, target: Target) -> list[Candidate]:
        candidates: list[Candidate] = []
        if self.config.inject_shortcut_first:
            candidates.append(Candidate(Expr.shortcut(target.name, target.train_x, target.train_y(), arity=target.arity), "shortcut", "training_table_shortcut"))
        # Safe decoys. Stage 2 intentionally avoids evaluating arbitrary deep
        # decoy trees because overflow-heavy EML compositions are not the object
        # of this ablation. The random-tree baseline still receives this bounded
        # safe pool and therefore tests lack of constructive synthesis rather
        # than numerical pathologies.
        safe_names = ["one_const", "identity_x", "e_const", "zero_const", "exp_x", "ln_x"]
        if target.arity == 2:
            safe_names.insert(2, "identity_y")
        pool = [self.registry[n].expr for n in safe_names if n in self.registry and n != target.name]
        self.rng.shuffle(pool)
        if self.config.random_tree:
            return [Candidate(e, "eml", "bounded_safe_random_tree") for e in pool[: self.config.budget]]
        candidates.extend(Candidate(e, "eml", "bounded_safe_decoy") for e in pool[: min(len(pool), 8)])
        if self.config.constructive_registry and target.name in self.registry:
            witness = self.registry[target.name]
            candidates.append(Candidate(witness.expr, "constructive", witness.derivation))
        if self.policy:
            candidates.sort(key=lambda c: (-self.policy.score(c.expr, c.tag), c.expr.node_count, c.expr.depth, c.expr.rpn()))
        # Without RLCR we intentionally leave shortcut and decoys before constructive witnesses.
        return candidates

    def _commit(self, name: str, expr: Expr) -> int:
        mutations = 0
        if not self.config.freeze and len(self.library) >= self.config.no_freeze_capacity:
            victim = self.order.pop(0)
            self.library.pop(victim, None)
            mutations += 1
        self.library[name] = expr
        if name not in self.order:
            self.order.append(name)
        self.original_verified.setdefault(name, expr)
        if self.config.freeze and expr.is_eml_tree:
            self.frozen.add(expr.signature())
        return mutations

    def _preservation_rate(self, targets: list[Target]) -> float:
        if not self.original_verified:
            return 1.0
        by_name = {t.name: t for t in targets}
        ok = 0
        total = 0
        for name, original in self.original_verified.items():
            total += 1
            if name not in self.library:
                continue
            target = by_name[name]
            current = self.library[name]
            mse = finite_mse(current, target.holdout_x, target.holdout_y(), target.holdout_y_arg)
            cmse = finite_mse(current, target.complex_x, target.complex_y(), target.complex_y_arg)
            if current.signature() == original.signature() and mse <= self.config.threshold and cmse <= 1e-13:
                ok += 1
        return ok / total if total else 1.0

    def _solve_gradient_proxy(self, target: Target) -> TargetResult:
        """Numerical baseline: least-squares polynomial/features, no constructive tree."""
        start = time.time()
        x = target.train_x.astype(np.complex128) if False else None  # keeps static analyzers quiet
        import numpy as np
        tx = target.train_x.astype(np.complex128)
        hx = target.holdout_x.astype(np.complex128)
        cx = target.complex_x.astype(np.complex128)
        if target.arity == 2:
            tyarg = target.train_y_arg.astype(np.complex128)
            hyarg = target.holdout_y_arg.astype(np.complex128)
            cyarg = target.complex_y_arg.astype(np.complex128)
            def features(a, b):
                return np.vstack([np.ones_like(a), a, b, a*b, a*a, b*b, 1/(b+1e-9)]).T
            A = features(tx, tyarg)
            coef, *_ = np.linalg.lstsq(A, target.train_y(), rcond=None)
            train_pred = A @ coef
            hold_pred = features(hx, hyarg) @ coef
            complex_pred = features(cx, cyarg) @ coef
        else:
            def features(a):
                return np.vstack([np.ones_like(a), a, a*a, a**3, np.exp(a), np.log(a)]).T
            A = features(tx)
            coef, *_ = np.linalg.lstsq(A, target.train_y(), rcond=None)
            train_pred = A @ coef
            hold_pred = features(hx) @ coef
            complex_pred = features(cx) @ coef
        train_mse = float(np.mean(np.abs(train_pred - target.train_y()) ** 2))
        holdout_mse = float(np.mean(np.abs(hold_pred - target.holdout_y()) ** 2))
        complex_mse = float(np.mean(np.abs(complex_pred - target.complex_y()) ** 2))
        return TargetResult(
            target=target.name,
            family=target.family,
            variant=self.config.name,
            seed=self.seed,
            candidate="numeric_least_squares_feature_model",
            rpn="",
            candidate_source="numeric_baseline",
            candidate_tag="numeric",
            candidate_depth=0,
            candidate_nodes=0,
            is_eml_tree=False,
            train_mse=train_mse,
            holdout_mse=holdout_mse,
            complex_mse=complex_mse,
            exact_recovery=False,
            candidate_evals=1,
            gate6_rejections=0,
            gate6_rejection_reasons=[],
            mutation_events=0,
            preservation_rate_after_commit=1.0,
            belnap_status_before_commit="T" if train_mse <= self.config.threshold else "F",
            runtime_sec=time.time() - start,
        )
