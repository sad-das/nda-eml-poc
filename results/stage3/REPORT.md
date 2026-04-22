# NDA EML PoC Stage 3 baseline ablation results

| Variant | Exact recovery | Holdout MSE | Complex MSE | Candidate evals | Gate 6 rejects | Preservation |
|---|---:|---:|---:|---:|---:|---:|
| `gradient_only` | 0.000 | 1.268e-02 | 4.025e-02 | 1.0 | 0.00 | 1.000 |
| `nda_full` | 1.000 | 9.056e-32 | 5.933e-32 | 1.0 | 0.00 | 1.000 |
| `no_freeze` | 1.000 | 9.056e-32 | 5.933e-32 | 1.0 | 0.00 | 0.462 |
| `no_gate6` | 0.000 | 2.683e-01 | 3.130e-01 | 1.0 | 0.00 | 0.231 |
| `no_rlcr` | 1.000 | 9.056e-32 | 5.933e-32 | 7.8 | 1.00 | 1.000 |
| `random_tree` | 0.000 | 1.913e+00 | 7.739e-01 | 5.8 | 0.00 | 1.000 |

Stage 3 keeps the Stage-2 arithmetic witness registry and uses this table as the baseline ablation layer for the additional discovery and hardening passes.
The constructive witnesses are pure EML trees; they are not asserted to be minimal. Stage-3 minimality/discovery diagnostics are written separately by nda_eml_poc.stage3_hardening.
