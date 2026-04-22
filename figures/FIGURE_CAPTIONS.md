# Figure captions

**Figure 1. NDA core loop.** Belnap-state contradiction is treated as a control signal rather than smoothed away. The loop freezes verified witnesses, proposes structural mediation, verifies candidates through Gate 6, stress-tests them in practice and commits accepted macro-nodes to the DKG. RLCR affects proposal ordering only; fatal shortcuts are stored as negative topology.

**Figure 2. Object-cell, method and architectural form.** The figure separates three levels of description: the object-cell as a minimal resistant relation in the environment, the NDA method cycle as action, resistance, antinomy, mediation and verification, and the architectural form as a persistent DKG record with provenance and rejection topology.

**Figure 3. Stage 3 ablation outcomes.** Exact recovery and final frozen-witness preservation rates across six EML variants, averaged over three seeds and 39 targets. The preservation metric measures whether already verified witnesses remain intact; it is not a discovery-success score. Loss-only, no-Gate6 and random-tree variants fail exact recovery, while removing Gradient Freeze preserves recovery but degrades frozen-witness preservation.

**Figure 4. Stage 3 flat-search boundary.** Candidate pool and scanned candidate counts under raw EML flat search at max depth 3. The shallow logarithmic witness is found, but addition, multiplication, division and squaring exhaust the flat pool without recovery, motivating macro-node curriculum discovery.

**Figure 5. Stage 4 macro-node curriculum.** Historical raw EML expansion cost and macro-depth for committed discoveries. Multiplication is represented as `exp(add(ln(x),ln(y)))`: it retains a 57-node raw EML expansion for provenance while requiring only macro-depth 3 at proposal time.

**Figure 6. Gate 6 and the Taylor trap.** A Taylor-like macro-tree surrogate obtains near-zero local training, holdout and complex-domain error, but fails asymptotic stress with MSE approximately 2.95e-1. Gate 6 rejects it as a shortcut surrogate and records the failure as negative topology rather than a DKG concept.
