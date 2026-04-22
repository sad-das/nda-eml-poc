# NDA EML PoC Stage 3: discovery and verification hardening

Stage 3 keeps the Stage-2 bootstrapped EML registry but adds two stricter checks: bounded shallow discovery and adversarial validation of constructive witnesses versus non-constructive training-table shortcuts.

## Bounded shallow discovery summary

| Family | Rows | Shallow found | Same as registry | Shorter than registry | Mean pool | Mean scanned |
|---|---:|---:|---:|---:|---:|---:|
| binary | 15 | 0.200 | 0.200 | 0.000 | 21612.0 | 17290.2 |
| unary | 24 | 0.750 | 0.750 | 0.000 | 1446.0 | 374.1 |

## Adversarial hardening summary

| Family | Rows | Witness pass | Shortcut Gate6 rejection | Shortcut adversarial failure | Mean witness real MSE | Mean witness complex MSE |
|---|---:|---:|---:|---:|---:|---:|
| binary | 15 | 1.000 | 1.000 | 1.000 | 1.724e-31 | 1.887e-31 |
| unary | 24 | 1.000 | 1.000 | 0.625 | 1.125e-31 | 1.485e-31 |

## Interpretation

Bounded discovery at depth 3 recovers the shallow terminal and elementary witnesses, including the logarithm identity, but does not claim to discover the deeper bootstrapped arithmetic witnesses. Those remain constructive registry witnesses in this stage.

The hardening pass verifies that registry witnesses remain stable on fresh real and complex points, while deliberately injected training-table shortcuts are rejected by Gate 6. Nontrivial shortcuts also fail adversarial generalization; constant shortcuts can numerically generalize by accident but are still rejected because they are not constructive EML trees.

## Limitations

Stage 3 is not yet a general symbolic-regression solver. It is a verification-hardening and bounded-discovery layer on top of the Stage-2 scaffold. Stage 4 should add generated EML tasks, stronger search policies and external baselines.
