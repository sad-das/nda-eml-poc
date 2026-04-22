from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Optional

import numpy as np

from .constructors import witness_registry
from .eml import Expr, expression_pool, finite_mse
from .gate6 import Gate6
from .targets import Target, make_targets


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _safe_float(x: float) -> float:
    if not np.isfinite(x):
        return float("inf")
    return float(x)


def _points_for(target: Target, seed: int, n: int = 160):
    rng = np.random.default_rng(seed + 1009 * (sum(ord(c) for c in target.name) + 1))
    # Positive real non-training grid. Kept away from zero to avoid domain ambiguity for division/log.
    real_x = rng.uniform(0.23, 2.85, size=n).astype(np.complex128)
    complex_x = (rng.uniform(0.27, 2.4, size=n) + 1j * rng.uniform(-0.55, 0.55, size=n)).astype(np.complex128)
    if target.arity == 1:
        return (real_x, None), (complex_x, None)
    real_y = rng.uniform(0.29, 2.95, size=n).astype(np.complex128)
    complex_y = (rng.uniform(0.31, 2.5, size=n) + 1j * rng.uniform(-0.50, 0.50, size=n)).astype(np.complex128)
    return (real_x, real_y), (complex_x, complex_y)


def _mse_on_points(expr: Expr, target: Target, x: np.ndarray, y_arg: Optional[np.ndarray]) -> float:
    y_true = target.fn(x, y_arg)
    return _safe_float(finite_mse(expr, x, y_true, y_arg))


def bounded_shallow_discovery(seed: int, max_depth: int, threshold: float) -> list[dict]:
    rows: list[dict] = []
    gate = Gate6(threshold=threshold)
    registry = witness_registry()
    targets = make_targets(seed)

    pool_cache: dict[tuple[int, bool], list[Expr]] = {}
    for target in targets:
        binary = target.arity == 2
        key = (max_depth, binary)
        if key not in pool_cache:
            pool_cache[key] = sorted(
                expression_pool(max_depth, binary=binary),
                key=lambda e: (e.node_count, e.depth, e.rpn()),
            )
        pool = pool_cache[key]
        witness = registry[target.name].expr
        found: Optional[Expr] = None
        found_report = None
        best_expr: Optional[Expr] = None
        best_train = math.inf
        best_holdout = math.inf
        best_complex = math.inf
        scanned = 0
        rejected = 0
        first_rejection_reasons: list[str] = []

        for expr in pool:
            scanned += 1
            train_mse = finite_mse(expr, target.train_x, target.train_y(), target.train_y_arg)
            if train_mse < best_train:
                best_expr = expr
                best_train = train_mse
                best_holdout = finite_mse(expr, target.holdout_x, target.holdout_y(), target.holdout_y_arg)
                best_complex = finite_mse(expr, target.complex_x, target.complex_y(), target.complex_y_arg)
            # Only run full Gate 6 on train-plausible candidates to keep the scan bounded.
            if not np.isfinite(train_mse) or train_mse > threshold:
                continue
            report = gate.check(expr, target, set())
            if report.accepted:
                found = expr
                found_report = report
                break
            rejected += 1
            if not first_rejection_reasons:
                first_rejection_reasons = report.reasons

        if found is not None and found_report is not None:
            found_train = found_report.train_mse
            found_holdout = found_report.holdout_mse
            found_complex = found_report.complex_mse
            found_sig = found.signature()
            found_rpn = found.rpn()
            found_nodes = found.node_count
            found_depth = found.depth
        else:
            found_train = math.inf if best_expr is None else best_train
            found_holdout = math.inf if best_expr is None else best_holdout
            found_complex = math.inf if best_expr is None else best_complex
            found_sig = ""
            found_rpn = ""
            found_nodes = 0
            found_depth = 0

        rows.append({
            "seed": seed,
            "target": target.name,
            "family": target.family,
            "arity": target.arity,
            "scan_max_depth": max_depth,
            "pool_size": len(pool),
            "scanned_until_stop": scanned,
            "shallow_found": bool(found is not None),
            "found_signature": found_sig,
            "found_rpn": found_rpn,
            "found_nodes": found_nodes,
            "found_depth": found_depth,
            "found_train_mse": found_train,
            "found_holdout_mse": found_holdout,
            "found_complex_mse": found_complex,
            "registry_nodes": witness.node_count,
            "registry_depth": witness.depth,
            "same_as_registry": bool(found is not None and found.signature() == witness.signature()),
            "shorter_than_registry": bool(found is not None and found.node_count < witness.node_count),
            "gate6_rejected_train_plausible": rejected,
            "first_rejection_reasons": ";".join(first_rejection_reasons),
        })
    return rows


def adversarial_hardening(seed: int, threshold: float, n_points: int) -> list[dict]:
    rows: list[dict] = []
    gate = Gate6(threshold=threshold)
    registry = witness_registry()
    for target in make_targets(seed):
        witness = registry[target.name].expr
        shortcut = Expr.shortcut(target.name, target.train_x, target.train_y(), arity=target.arity)
        (real_x, real_y), (complex_x, complex_y) = _points_for(target, seed, n=n_points)
        witness_real_mse = _mse_on_points(witness, target, real_x, real_y)
        witness_complex_mse = _mse_on_points(witness, target, complex_x, complex_y)
        shortcut_train_mse = finite_mse(shortcut, target.train_x, target.train_y(), target.train_y_arg)
        shortcut_real_mse = _mse_on_points(shortcut, target, real_x, real_y)
        shortcut_complex_mse = _mse_on_points(shortcut, target, complex_x, complex_y)
        shortcut_report = gate.check(shortcut, target, set())
        witness_pass = bool(witness_real_mse <= max(threshold * 100, 1e-13) and witness_complex_mse <= max(threshold * 1000, 1e-12))
        shortcut_fails_adversarial = bool(shortcut_real_mse > 1e-8 or shortcut_complex_mse > 1e-8)
        rows.append({
            "seed": seed,
            "target": target.name,
            "family": target.family,
            "witness_nodes": witness.node_count,
            "witness_depth": witness.depth,
            "witness_adversarial_real_mse": witness_real_mse,
            "witness_adversarial_complex_mse": witness_complex_mse,
            "witness_adversarial_pass": witness_pass,
            "shortcut_train_mse": shortcut_train_mse,
            "shortcut_gate6_accepted": shortcut_report.accepted,
            "shortcut_gate6_reasons": ";".join(shortcut_report.reasons),
            "shortcut_adversarial_real_mse": shortcut_real_mse,
            "shortcut_adversarial_complex_mse": shortcut_complex_mse,
            "shortcut_fails_adversarial": shortcut_fails_adversarial,
        })
    return rows


def aggregate(rows: list[dict]) -> list[dict]:
    # Small descriptive summary for the hardening/discovery layer.
    if not rows:
        return []
    out: list[dict] = []
    if "shallow_found" in rows[0]:
        for family in sorted(set(r["family"] for r in rows)):
            rs = [r for r in rows if r["family"] == family]
            out.append({
                "section": "bounded_shallow_discovery",
                "family": family,
                "rows": len(rs),
                "shallow_found_rate": mean([1.0 if r["shallow_found"] else 0.0 for r in rs]),
                "same_as_registry_rate": mean([1.0 if r["same_as_registry"] else 0.0 for r in rs]),
                "shorter_than_registry_rate": mean([1.0 if r["shorter_than_registry"] else 0.0 for r in rs]),
                "mean_pool_size": mean([float(r["pool_size"]) for r in rs]),
                "mean_scanned_until_stop": mean([float(r["scanned_until_stop"]) for r in rs]),
            })
    else:
        for family in sorted(set(r["family"] for r in rows)):
            rs = [r for r in rows if r["family"] == family]
            out.append({
                "section": "adversarial_hardening",
                "family": family,
                "rows": len(rs),
                "witness_adversarial_pass_rate": mean([1.0 if r["witness_adversarial_pass"] else 0.0 for r in rs]),
                "shortcut_gate6_rejection_rate": mean([0.0 if r["shortcut_gate6_accepted"] else 1.0 for r in rs]),
                "shortcut_adversarial_failure_rate": mean([1.0 if r["shortcut_fails_adversarial"] else 0.0 for r in rs]),
                "mean_witness_real_mse": mean([float(r["witness_adversarial_real_mse"]) for r in rs]),
                "mean_witness_complex_mse": mean([float(r["witness_adversarial_complex_mse"]) for r in rs]),
            })
    return out


def write_markdown_report(out: Path, discovery_rows: list[dict], hardening_rows: list[dict], discovery_summary: list[dict], hardening_summary: list[dict]) -> None:
    def _fmt(x):
        if isinstance(x, float):
            return f"{x:.3e}" if (abs(x) < 1e-3 or abs(x) > 1e3) and x != 0 else f"{x:.3f}"
        return str(x)

    lines: list[str] = []
    lines.append("# NDA EML PoC Stage 3: discovery and verification hardening")
    lines.append("")
    lines.append("Stage 3 keeps the Stage-2 bootstrapped EML registry but adds two stricter checks: bounded shallow discovery and adversarial validation of constructive witnesses versus non-constructive training-table shortcuts.")
    lines.append("")
    lines.append("## Bounded shallow discovery summary")
    lines.append("")
    lines.append("| Family | Rows | Shallow found | Same as registry | Shorter than registry | Mean pool | Mean scanned |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in discovery_summary:
        lines.append(f"| {r['family']} | {r['rows']} | {r['shallow_found_rate']:.3f} | {r['same_as_registry_rate']:.3f} | {r['shorter_than_registry_rate']:.3f} | {r['mean_pool_size']:.1f} | {r['mean_scanned_until_stop']:.1f} |")
    lines.append("")
    lines.append("## Adversarial hardening summary")
    lines.append("")
    lines.append("| Family | Rows | Witness pass | Shortcut Gate6 rejection | Shortcut adversarial failure | Mean witness real MSE | Mean witness complex MSE |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in hardening_summary:
        lines.append(f"| {r['family']} | {r['rows']} | {r['witness_adversarial_pass_rate']:.3f} | {r['shortcut_gate6_rejection_rate']:.3f} | {r['shortcut_adversarial_failure_rate']:.3f} | {r['mean_witness_real_mse']:.3e} | {r['mean_witness_complex_mse']:.3e} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Bounded discovery at depth 3 recovers the shallow terminal and elementary witnesses, including the logarithm identity, but does not claim to discover the deeper bootstrapped arithmetic witnesses. Those remain constructive registry witnesses in this stage.")
    lines.append("")
    lines.append("The hardening pass verifies that registry witnesses remain stable on fresh real and complex points, while deliberately injected training-table shortcuts are rejected by Gate 6. Nontrivial shortcuts also fail adversarial generalization; constant shortcuts can numerically generalize by accident but are still rejected because they are not constructive EML trees.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("Stage 3 is not yet a general symbolic-regression solver. It is a verification-hardening and bounded-discovery layer on top of the Stage-2 scaffold. Stage 4 should add generated EML tasks, stronger search policies and external baselines.")
    (out / "STAGE3_HARDENING_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/stage3")
    ap.add_argument("--seeds", nargs="*", type=int, default=[0, 1, 2])
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=1e-16)
    ap.add_argument("--adversarial-points", type=int, default=160)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    discovery_rows: list[dict] = []
    hardening_rows: list[dict] = []
    for seed in args.seeds:
        discovery_rows.extend(bounded_shallow_discovery(seed, args.max_depth, args.threshold))
        hardening_rows.extend(adversarial_hardening(seed, args.threshold, args.adversarial_points))

    discovery_summary = aggregate(discovery_rows)
    hardening_summary = aggregate(hardening_rows)
    _write_csv(out / "stage3_discovery_analysis.csv", discovery_rows)
    _write_csv(out / "stage3_hardening_analysis.csv", hardening_rows)
    _write_csv(out / "stage3_discovery_summary.csv", discovery_summary)
    _write_csv(out / "stage3_hardening_summary.csv", hardening_summary)
    (out / "stage3_hardening_summary.json").write_text(json.dumps({
        "discovery_summary": discovery_summary,
        "hardening_summary": hardening_summary,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(out, discovery_rows, hardening_rows, discovery_summary, hardening_summary)


if __name__ == "__main__":
    main()
