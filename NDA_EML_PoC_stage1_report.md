# NDA EML PoC Stage 1 — implementation report

## Status

A minimal executable repository has been assembled for the first EML proof-of-concept branch of Native Dialectical Architecture. The goal of this stage is narrow: convert the publication-level architecture into runnable interfaces and produce a first smoke-scale ablation log.

This is not an empirical validation of NDA as a whole. It is an implementation scaffold for testing the core mechanisms in a mathematically clean domain.

## Repository

Repository directory in the artifact package:

```text
nda_eml_poc_stage1/
  src/nda_eml_poc/
    eml.py
    belnap.py
    gate6.py
    rlcr.py
    targets.py
    agent.py
    run_ablation.py
  tests/
    test_current_smoke.py
  docs/
    design_notes.md
    reproducibility.md
  results/minimal/
    REPORT.md
    target_results.csv
    summary_metrics.csv
    summary_metrics.json
    run_<variant>_seed<seed>.json
    exact_recovery_rate.svg
    preservation_rate.svg
```

## Implemented mechanisms

### 1. EML object-cell

The object-cell is implemented as the real-domain relation:

```text
eml(x, y) = exp(x) - ln(y)
```

The grammar used in the smoke run is:

```text
S -> 1 | x | eml(S, S)
```

The first benchmark restricts inputs to positive real values so that branch/domain failures are surfaced as Gate 6 rejection events rather than hidden in complex arithmetic.

### 2. Gate 6

`Gate6` is implemented as a bounded operational substitute for pure `UNSAT`. It rejects:

- non-EML hardcoded shortcut candidates;
- non-finite branch/domain failures;
- candidates that fit only the training grid but fail held-out validation;
- attempted frozen-subtree mutation;
- unbounded depth growth.

The smoke run injects a training-table shortcut into the candidate list. `nda_full` rejects it. `no_gate6` accepts it, which produces zero training error but poor held-out behavior and no constructive EML witness.

### 3. Gradient Freeze

Verified witnesses are frozen in the full condition. The `no_freeze` ablation simulates destructive fixed-capacity rewriting by allowing only two verified concept slots. This makes the current target solvable but causes loss of earlier verified witnesses.

### 4. RLCR

`RLCRPolicy` updates only candidate ordering. It cannot accept a candidate, alter Gate 6, or rewrite verified witnesses. In this smoke run, RLCR reduces mean candidate evaluations relative to `no_rlcr`, but the search space is still too small for a strong claim.

### 5. Baselines

The stage includes:

- `nda_full`;
- `no_freeze`;
- `no_gate6`;
- `no_rlcr`;
- `random_tree`;
- `gradient_only`, implemented as a fixed-topology degree-5 polynomial fitted by Adam-style updates.

## Command used

```bash
cd nda_eml_poc_stage1
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -v
PYTHONPATH=src /usr/bin/python3 -m nda_eml_poc.run_ablation \
  --out results/minimal \
  --seeds 0 1 2 \
  --max-depth 3 \
  --budget 2500
```

## Aggregate smoke metrics

| Variant | Exact recovery rate | Mean holdout MSE | Mean candidate evals | Mean Gate 6 rejections | Final preservation rate |
|---|---:|---:|---:|---:|---:|
| gradient_only | 0.000 | 9.380e-03 | 250.0 | 0.00 | 1.000 |
| nda_full | 1.000 | 4.141e-33 | 15.8 | 1.00 | 1.000 |
| no_freeze | 1.000 | 4.141e-33 | 15.8 | 1.00 | 0.500 |
| no_gate6 | 0.000 | 1.409e-01 | 1.0 | 0.00 | 0.250 |
| no_rlcr | 1.000 | 9.636e-33 | 77.4 | 1.00 | 1.000 |
| random_tree | 1.000 | 6.452e-33 | 412.6 | 0.00 | 1.000 |

## Interpretation

The smoke results show that the mechanisms are executable and produce separable ablation signals:

1. `nda_full` recovers all shallow EML witnesses in the toy target set and rejects the injected shortcut.
2. `no_gate6` demonstrates the intended failure mode: a shortcut can satisfy the training grid but fails as a constructive witness.
3. `no_freeze` solves current tasks but does not preserve the full historical witness set.
4. `no_rlcr` still solves the toy task set but uses more candidate evaluations than `nda_full`.
5. `gradient_only` produces continuous approximation but no constructive EML tree.

## Limits

This is deliberately a smoke test. It is not yet suitable as a journal-level empirical section.

Current limits:

- only four shallow targets are used: `e_const`, `exp_x`, `eml_self`, `ln_x`;
- evaluation is real-domain only;
- `random_tree` is too strong in a depth-3 search space because the target witnesses are shallow;
- `RLCR` is tested only as simple production-key reordering;
- no genetic programming, PySR, complex-domain validation, symbolic simplification, or deeper arithmetic/trigonometric families are included;
- Gate 6 shortcut rejection is intentionally injected rather than discovered from a naturally large overfitting space.

## Immediate next steps

1. Add EML-1 targets: addition, subtraction, multiplication, division and square.
2. Add complex-domain evaluation with explicit branch-cut reporting.
3. Replace the toy RLCR key with a typed production policy.
4. Add a proper genetic programming baseline.
5. Add a parameterized EML-tree baseline instead of polynomial-only `gradient_only`.
6. Add exact symbolic verification for known witnesses.
7. Increase repeated seeds to at least 30 once deeper search is optimized.
8. Prepare a `results/v0.2` ablation table suitable for the empirical section of the paper.
