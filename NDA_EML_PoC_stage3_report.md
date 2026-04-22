# NDA EML PoC Stage 3 report

## Status

Stage 3 implements a discovery-and-hardening layer over the Stage-2 EML scaffold. It does not claim to be a general symbolic-regression engine. Its purpose is narrower: verify that the bootstrapped EML registry remains stable under adversarial validation, expose the depth boundary of bounded shallow discovery, and preserve the NDA ablation loop for Gate 6, Gradient Freeze and RLCR.

## Implemented additions

- `nda_eml_poc.stage3_hardening`: bounded shallow EML-tree discovery up to configurable depth.
- Adversarial real/complex validation points outside the training and holdout grids.
- Explicit comparison between constructive registry witnesses and non-constructive training-table shortcuts.
- CSV outputs for discovery analysis, hardening analysis and summaries.
- Stage-3 unit tests for shallow discovery and Gate-6 shortcut rejection.

## Baseline ablation results

| Variant | Exact recovery | Holdout MSE | Complex MSE | Candidate evals | Gate 6 rejects | Preservation |
|---|---:|---:|---:|---:|---:|---:|
| `gradient_only` | 0.000 | 1.268e-02 | 4.025e-02 | 1.0 | 0.00 | 1.000 |
| `nda_full` | 1.000 | 9.056e-32 | 5.933e-32 | 1.0 | 0.00 | 1.000 |
| `no_freeze` | 1.000 | 9.056e-32 | 5.933e-32 | 1.0 | 0.00 | 0.462 |
| `no_gate6` | 0.000 | 2.683e-01 | 3.130e-01 | 1.0 | 0.00 | 0.231 |
| `no_rlcr` | 1.000 | 9.056e-32 | 5.933e-32 | 7.8 | 1.00 | 1.000 |
| `random_tree` | 0.000 | 1.913e+00 | 7.739e-01 | 5.8 | 0.00 | 1.000 |

## Bounded shallow discovery

| Family | Rows | Shallow found | Same as registry | Mean pool | Mean scanned |
|---|---:|---:|---:|---:|---:|
| binary | 15 | 0.200 | 0.200 | 21612.0 | 17290.2 |
| unary | 24 | 0.750 | 0.750 | 1446.0 | 374.1 |

At `max_depth=3`, shallow discovery recovers terminal and elementary witnesses: `one_const`, `identity_x`, `identity_y`, `e_const`, `zero_const`, `exp_x`, and `ln_x`. It does not recover deeper bootstrapped arithmetic witnesses such as `x_minus_y`, `x_plus_y`, `x_times_y`, `x_div_y` or `x_square`; these remain constructive registry witnesses in Stage 3.

### Seed-0 discovery boundary

| Target | Shallow found | Found depth | Registry depth | Found nodes | Registry nodes |
|---|---:|---:|---:|---:|---:|
| `one_const` | True | 0 | 0 | 1 | 1 |
| `identity_x` | True | 0 | 0 | 1 | 1 |
| `e_const` | True | 1 | 1 | 3 | 3 |
| `zero_const` | True | 3 | 3 | 7 | 7 |
| `exp_x` | True | 1 | 1 | 3 | 3 |
| `ln_x` | True | 3 | 3 | 7 | 7 |
| `neg_x` | False | 0 | 7 | 0 | 17 |
| `x_square` | False | 0 | 10 | 0 | 41 |
| `identity_y` | True | 0 | 0 | 1 | 1 |
| `x_minus_y` | False | 0 | 4 | 0 | 11 |
| `x_plus_y` | False | 0 | 9 | 0 | 27 |
| `x_times_y` | False | 0 | 10 | 0 | 41 |
| `x_div_y` | False | 0 | 8 | 0 | 25 |

## Adversarial hardening

| Family | Rows | Witness pass | Shortcut Gate6 rejection | Shortcut adversarial failure | Mean witness real MSE | Mean witness complex MSE |
|---|---:|---:|---:|---:|---:|---:|
| binary | 15 | 1.000 | 1.000 | 1.000 | 1.724e-31 | 1.887e-31 |
| unary | 24 | 1.000 | 1.000 | 0.625 | 1.125e-31 | 1.485e-31 |

All constructive registry witnesses pass fresh real and complex adversarial points. All training-table shortcuts are rejected by Gate 6. Nontrivial shortcuts also fail adversarial generalization; constant shortcuts can numerically generalize by accident but remain invalid because they are not constructive EML trees.

## Verification

```text
Ran 5 tests in 4.610s
OK
```

## Commands

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m nda_eml_poc.run_ablation --out results/stage3 --seeds 0 1 2
PYTHONPATH=src python3 -m nda_eml_poc.stage3_hardening --out results/stage3 --seeds 0 1 2 --max-depth 3 --adversarial-points 160
```

## Limitations

- Stage 3 uses bounded enumeration to depth 3; it is not yet an open-ended discovery engine.
- Arithmetic witnesses remain bootstrapped registry constructions, not discovered minimal formulas.
- The baselines are still internal toy baselines; Stage 4 should add generated EML tasks and stronger external symbolic-regression baselines.
- The current real/complex domains are controlled and avoid some difficult branch-cut cases.

## Next step

Stage 4 should move from fixed target witnesses to generated EML tasks: create random constructive trees, hide their formulas, recover them under a budget, compare against symbolic-regression baselines, and add counterexample-guided Gate-6 hardening.
