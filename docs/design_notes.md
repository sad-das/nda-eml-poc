# Design notes

## Stage-2 change relative to Stage 1

Stage 1 demonstrated shallow EML recovery and anti-shortcut behaviour. Stage 2 adds a bootstrapped constructive registry: once `exp`, `ln` and `0` are available as verified EML trees, arithmetic witnesses can be composed as larger EML trees.

## Constructive identities

Let `E(a,b)=eml(a,b)=exp(a)-log(b)`.

- `exp(x) = E(x,1)`
- `log(x) = E(1, E(E(1,x),1))`
- `0 = log(1)`
- `a - b = E(log(a), exp(b))`
- `-a = 0 - a`
- `a + b = a - (-b)`
- `a*b = exp(log(a)+log(b))`
- `a/b = exp(log(a)-log(b))`
- `a^2 = a*a`

The resulting trees are pure EML trees but not necessarily shortest expressions.

## Gate 6

Gate 6 is the operational substitute for idealized UNSAT. It rejects non-constructive shortcuts, failures on held-out points, complex-domain failures and unbounded tree growth. It does not prove mathematical impossibility; it certifies failure within the bounded operational regime.

## RLCR

RLCR changes only candidate ordering. It cannot override Gate 6, cannot accept candidates, and cannot rewrite committed witnesses.
