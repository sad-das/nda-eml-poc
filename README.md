# nda-eml-poc

`nda-eml-poc` is the executable EML proof-of-concept repository for the paper draft **Native Dialectical Architecture: contradiction-preserving topological growth for practice-grounded concept formation**.

Author: Denis Shilov (Independent Researcher, Chelyabinsk, Russia; ORCID: https://orcid.org/0009-0003-1770-1671).

## Scope

This repository contains Stage 1–4 artifacts for the EML branch of Native Dialectical Architecture (NDA). It is a restricted mathematical proof-of-concept, not a claim that the EML branch constitutes AGI.

The experimental substrate is the EML operator:

```text
eml(x, y) = exp(x) - log(y)
```

with pure expression trees over terminals `1`, `x`, `y` and the binary node `eml(S, S)`. The repository implements:

- Stage 1 minimal EML scaffold;
- Stage 2 bootstrapped arithmetic witnesses;
- Stage 3 bounded shallow discovery and verification hardening;
- Stage 4 macro-node dialectical curriculum discovery;
- Gate 6 rejection of shortcuts and Taylor-like parametric surrogates;
- Gradient Freeze as preservation of verified witnesses;
- Clean RLCR as proposal-ordering only, never as truth authority;
- Negative topology / DKG Graveyard for fatal rejection signatures.

## Main Stage 4 result

Stage 4 discovers multiplication without a human-authored raw registry witness:

```text
x * y = exp(add(ln(x), ln(y)))
```

The macro-level discovery has:

```text
manual_registry_dependency = 0
macro_depth = 3
historical_expansion_cost = 57 raw EML nodes
```

The system uses verified macro-nodes (`ln`, `exp`, `add`) as atomic proposal primitives while preserving their raw EML expansion for provenance and audit.

## Install / test

Use Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
```

## Reproduce Stage 3 and Stage 4 artifacts

```bash
PYTHONPATH=src python -m nda_eml_poc.run_ablation \
  --out results/stage3 --seeds 0 1 2

PYTHONPATH=src python -m nda_eml_poc.stage3_hardening \
  --out results/stage3 --seeds 0 1 2 --max-depth 3 --adversarial-points 160

PYTHONPATH=src python -m nda_eml_poc.stage4_discovery \
  --out results/stage4 --seed 0
```

## Repository contents

```text
src/nda_eml_poc/        source code
tests/                  unit tests
results/stage3/         Stage 3 CSV/JSON artifacts
results/stage4/         Stage 4 CSV/JSON/TXT artifacts
figures/                manuscript figure drafts
NDA_EML_PoC_stage*.md   stage reports
REPRODUCIBILITY.md      reproducibility notes
ARTIFACT_MANIFEST.md    artifact map
SHA256SUMS              checksums
```

## License

MIT License. Copyright (c) 2026 Denis Shilov.

## Citation

Please cite the archived Zenodo software release:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19688532.svg)](https://doi.org/10.5281/zenodo.19688532)

```text
Shilov, D. (2026). nda-eml-poc: EML proof-of-concept for Native Dialectical Architecture (v1.0.0-paper). Zenodo. https://doi.org/10.5281/zenodo.19688532
```
