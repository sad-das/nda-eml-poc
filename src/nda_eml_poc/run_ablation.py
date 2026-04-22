from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from .agent import NDAStage2Agent, VariantConfig

VARIANTS = {
    "nda_full": VariantConfig("nda_full"),
    "no_freeze": VariantConfig("no_freeze", freeze=False),
    "no_gate6": VariantConfig("no_gate6", gate6=False, rlcr=False),
    "no_rlcr": VariantConfig("no_rlcr", rlcr=False),
    "random_tree": VariantConfig("random_tree", random_tree=True, constructive_registry=False, inject_shortcut_first=False, budget=400),
    "gradient_only": VariantConfig("gradient_only", gradient_only=True, gate6=False, constructive_registry=False, inject_shortcut_first=False),
}


def summarize(runs):
    rows = []
    for variant in sorted(set(r.variant for r in runs)):
        rs = [r for r in runs if r.variant == variant]
        results = [tr for r in rs for tr in r.results]
        rows.append({
            "variant": variant,
            "runs": len(rs),
            "targets": len(results),
            "exact_recovery_rate": mean([1.0 if r.exact_recovery else 0.0 for r in results]),
            "mean_holdout_mse": mean([r.holdout_mse for r in results]),
            "mean_complex_mse": mean([r.complex_mse for r in results]),
            "mean_candidate_evals": mean([r.candidate_evals for r in results]),
            "mean_gate6_rejections": mean([r.gate6_rejections for r in results]),
            "final_preservation_rate": mean([r.final_preservation_rate for r in rs]),
            "mean_nodes_accepted_or_best": mean([r.candidate_nodes for r in results]),
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def write_report(path: Path, summary_rows: list[dict]) -> None:
    lines = ["# NDA EML PoC Stage 3 baseline ablation results", "", "| Variant | Exact recovery | Holdout MSE | Complex MSE | Candidate evals | Gate 6 rejects | Preservation |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in summary_rows:
        lines.append(f"| `{r['variant']}` | {r['exact_recovery_rate']:.3f} | {r['mean_holdout_mse']:.3e} | {r['mean_complex_mse']:.3e} | {r['mean_candidate_evals']:.1f} | {r['mean_gate6_rejections']:.2f} | {r['final_preservation_rate']:.3f} |")
    lines.extend([
        "",
        "Stage 3 keeps the Stage-2 arithmetic witness registry and uses this table as the baseline ablation layer for the additional discovery and hardening passes.",
        "The constructive witnesses are pure EML trees; they are not asserted to be minimal. Stage-3 minimality/discovery diagnostics are written separately by nda_eml_poc.stage3_hardening.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/stage2")
    ap.add_argument("--seeds", nargs="*", type=int, default=[0, 1, 2])
    ap.add_argument("--variants", nargs="*", default=list(VARIANTS))
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    runs = []
    for variant_name in args.variants:
        cfg = VARIANTS[variant_name]
        for seed in args.seeds:
            agent = NDAStage2Agent(cfg, seed=seed)
            run = agent.run()
            runs.append(run)
            (out / f"run_{variant_name}_seed{seed}.json").write_text(json.dumps(run.to_jsonable(), ensure_ascii=False, indent=2), encoding="utf-8")
    summary_rows = summarize(runs)
    target_rows = [tr.__dict__ for run in runs for tr in run.results]
    write_csv(out / "summary_metrics.csv", summary_rows)
    write_csv(out / "target_results.csv", target_rows)
    (out / "summary_metrics.json").write_text(json.dumps(summary_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(out / "REPORT.md", summary_rows)

if __name__ == "__main__":
    main()
