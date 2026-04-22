# NDA EML PoC Stage 4 report

Stage 4 implements **Macro-node Dialectical Curriculum Discovery**. Its purpose is to close the Stage-3 boundary: shallow flat EML discovery finds the primitive layer but does not discover arithmetic witnesses such as multiplication without hierarchical reuse.

## Main result

The Stage-4 engine discovers multiplication without a human-authored arithmetic registry:

```text
x_times_y -> mul := exp(add(ln(x), ln(y)))
```

The discovered `mul` macro has:

```text
macro_depth = 3
historical_expansion_cost = 57 raw EML nodes
manual_registry_dependency = 0
```

This is the intended hierarchical sublation result: the search treats previously verified `exp`, `ln`, and `add` as O(1) macro-primitives, while retaining the full raw EML expansion for audit.

## Curriculum discoveries

See `results/stage4/stage4_curriculum_discoveries.csv` for the full table. The main path is:

```text
exp_x       -> exp   = eml(x,1)
ln_x        -> ln    = eml(1,eml(eml(1,x),1))
zero_const  -> zero  = ln(1)
x_minus_y   -> sub   = eml(ln(x),exp(y))
neg_x       -> neg   = sub(zero,x)
x_plus_y    -> add   = sub(sub(x,zero),sub(zero,y))
x_times_y   -> mul   = exp(add(ln(x),ln(y)))
x_div_y     -> div   = exp(sub(ln(x),ln(y)))
x_square    -> square = mul(x,x)
```

## Flat-search boundary

The Stage-4 report preserves the Stage-3 boundary:

```text
ln_x       found at raw depth 3
x_plus_y   not found at raw depth 3
x_times_y  not found at raw depth 3
x_div_y    not found at raw depth 3
x_square   not found at raw depth 3
```

## Taylor trap

A third-order Taylor macro-tree for `exp(x)` is a valid constructive macro expression and fits a local grid:

```text
train MSE ≈ 3.35e-18
```

Gate 6 rejects it because asymptotic stress fails:

```text
asymptotic MSE ≈ 2.95e-01
reasons = unbounded_node_growth;asymptotic_stress_failure
```

This is the Stage-4 response to the Taylor trap: a surrogate cannot become a concept merely because it is made out of legal macro-nodes and fits a local training grid.

## RLCR / Negative topology

`CleanRLCR` uses no scalar penalties for Gate 6 or Zero-Text failures:

```text
scalar_penalties_used = 0
```

Fatal rejections are stored in the DKG graveyard (`stage4_graveyard.csv`) as negative topology, not as reward shaping.

## Test status

The Stage-4 test file `tests/test_stage4_discovery.py` passes:

```text
Ran 3 tests in 0.782s
OK
```

The full repository still contains earlier Stage-2/Stage-3 tests; the Stage-4-specific smoke check is the authoritative check for this increment.
