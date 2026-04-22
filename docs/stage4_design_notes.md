# Stage 4 design notes: Macro-node Dialectical Curriculum Discovery

Stage 4 addresses the Stage-3 boundary: flat raw-EML enumeration can recover the primitive layer (`exp`, `ln`) but does not reach arithmetic witnesses such as multiplication within a shallow depth budget.

## Core mechanism

A verified witness is promoted to a `MacroNode`:

- `proposal_cost(M) = 1`: the synthesis engine may use the committed witness as one atomic proposal primitive at the next curriculum level.
- `historical_expansion_cost(M) = size(expand_to_raw_eml(M))`: the raw EML expansion is retained for provenance, audit and reproduction.

This implements hierarchical sublation without hiding historical complexity.

## Search

`SynthesisEngine` uses a bounded directed macro-pattern search, not a human-authored constructive registry. It enumerates generic composition motifs over the current DKG vocabulary:

- direct unary and binary macro application;
- binary mediation over one-step macro terms;
- outer-unary over inner-binary compositions, making `exp(add(ln(x), ln(y)))` reachable after `exp`, `ln` and `add` have been committed.

The curriculum supplies tasks, not mediators.

## Gate 6 hardening

`Gate6Stage4` keeps constructiveness and train/holdout/complex checks, then adds asymptotic stress points. This rejects legitimate-looking macro-polynomial surrogates such as a Taylor polynomial for `exp(x)` that fits a local grid but diverges outside the local radius.

## RLCR cleanliness

`CleanRLCR` updates only positive proposal priors from verified mediators. Gate 6 and Zero-Text violations are fatal rejections and are recorded in `NegativeTopology` / DKG graveyard; they are not scalar penalties.
