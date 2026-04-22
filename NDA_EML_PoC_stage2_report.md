# NDA EML PoC Stage 2 report

## Status

Stage 2 extends the Stage 1 scaffold from shallow unary witnesses to a bootstrapped arithmetic witness registry. The implementation remains intentionally small and auditable: no LLM, no text embeddings, no retrieval memory, no cross-instance memory and no learned sidecar participate in the verification loop.

The stage tests the following NDA mechanisms in the EML sandbox:

- constructive growth of pure EML trees;
- Gate 6 as operational anti-eclectic barrier;
- complex-domain validation;
- Gradient Freeze as historical preservation of committed witnesses;
- RLCR as candidate-order policy only, not truth authority;
- ablations against shortcut acceptance, no-freeze memory loss, no-RLCR slower search, random-tree failure and numeric-only fitting.

## Stage-2 constructive witnesses

Let:

```text
E(a,b) = eml(a,b) = exp(a) - log(b)
```

The registry uses these identities:

```text
exp(x)  = E(x, 1)
log(x)  = E(1, E(E(1, x), 1))
0       = log(1)
a - b   = E(log(a), exp(b))
-a      = 0 - a
a + b   = a - (0 - b)
a*b     = exp(log(a) + log(b))
a/b     = exp(log(a) - log(b))
a^2     = a*a
```

All accepted witnesses are pure EML trees over terminals `1`, `x`, `y` and binary EML nodes. They are constructive witnesses, not minimality claims.

Representative `nda_full` witnesses from seed 0:

| Target | Nodes | Depth | RPN prefix / full RPN when short |
|---|---:|---:|---|
| `one_const` | 1 | 0 | `1` |
| `identity_x` | 1 | 0 | `x` |
| `e_const` | 3 | 1 | `11E` |
| `zero_const` | 7 | 3 | `111E1EE` |
| `exp_x` | 3 | 1 | `x1E` |
| `ln_x` | 7 | 3 | `11xE1EE` |
| `neg_x` | 17 | 7 | `11111E1EEE1EEx1EE` |
| `x_minus_y` | 11 | 4 | `11xE1EEy1EE` |
| `x_plus_y` | 27 | 9 | `11xE1EE11111E1EEE1EEy1EE1EE` |
| `x_times_y` | 41 | 10 | `1111xE1EEE1EE...` |
| `x_div_y` | 25 | 8 | `1111xE1EEE1EE11yE1EE1EE1E` |
| `x_square` | 41 | 10 | `1111xE1EEE1EE...` |

## Verification protocol

For every target, Gate 6 checks:

1. candidate is a pure EML tree, not a shortcut;
2. node/depth limits are respected;
3. training-grid MSE passes threshold;
4. held-out real-domain MSE passes threshold;
5. non-zero complex-domain MSE passes threshold;
6. frozen witness mutation is rejected.

The no-Gate6 variant is deliberately configured without RLCR sorting, so the injected training-table shortcut is accepted before constructive witnesses. This demonstrates the purpose of Gate 6: training success alone is not a verified action schema.

## Test run

```text
Ran 3 tests in 0.057s
OK
```

Command:

```bash
cd nda_eml_poc_stage2
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -v
```

## Ablation command

```bash
cd nda_eml_poc_stage2
PYTHONPATH=src /usr/bin/python3 run_stage2_all.py
```

The included `run_stage2_all.py` was used to produce the bundled result artifacts.

## Summary metrics

| Variant | Exact recovery | Mean holdout MSE | Mean complex MSE | Mean candidate evals | Gate 6 rejects | Preservation |
|---|---:|---:|---:|---:|---:|---:|
| `gradient_only` | 0.000 | 1.268e-02 | 4.025e-02 | 1.0 | 0.00 | 1.000 |
| `nda_full` | 1.000 | 9.056e-32 | 5.933e-32 | 1.0 | 0.00 | 1.000 |
| `no_freeze` | 1.000 | 9.056e-32 | 5.933e-32 | 1.0 | 0.00 | 0.462 |
| `no_gate6` | 0.000 | 2.683e-01 | 3.130e-01 | 1.0 | 0.00 | 0.231 |
| `no_rlcr` | 1.000 | 9.056e-32 | 5.933e-32 | 7.8 | 1.00 | 1.000 |
| `random_tree` | 0.000 | 1.913e+00 | 7.739e-01 | 5.8 | 0.00 | 1.000 |

## Interpretation

`nda_full` verifies the full Stage-2 arithmetic registry across real held-out and complex-domain points.

`no_gate6` fails as intended: the injected training-table shortcut can satisfy the training grid but does not generalize and is not a constructive EML tree.

`no_freeze` still solves current targets but loses historical preservation because committed witnesses are evicted after the fixed capacity is exceeded. This isolates the value of Gradient Freeze as a historical memory invariant.

`no_rlcr` still solves the target suite because constructive witnesses exist, but it evaluates more candidates on average. RLCR is therefore functioning only as a search-order policy.

`gradient_only` approximates some target behaviour numerically but does not produce an EML tree, so exact recovery remains zero under the constructive criterion.

`random_tree` fails to recover the arithmetic witnesses from bounded safe decoys. This is expected; Stage 2 tests bootstrapped construction, not blind symbolic search at full depth.

## Limitations

This is still a PoC scaffold, not a final symbolic-regression benchmark.

Main limitations:

- witnesses are manually constructed from EML identities rather than discovered by a general search engine;
- formulas are not minimal;
- target suite is small;
- complex validation uses bounded non-zero complex points, not formal proof over the whole complex plane;
- random-tree baseline is intentionally bounded and safe, not a state-of-the-art symbolic regression method;
- no GPU batch verifier is included yet;
- no SWE-bench/code-sandbox branch is included yet.

## Next technical step

Stage 3 should split into two tracks:

1. **EML discovery track:** search for shorter/minimal witnesses for `x+y`, `x*y`, `x/y`, `x^2`, compare against the constructive registry, and add symbolic simplification.
2. **Verification hardening track:** add property-based random complex validation, counterexample search, JSON artifact schema validation and a small GPU/parallel batch verifier interface that remains advisory only.
