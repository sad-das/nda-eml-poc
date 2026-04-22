# Reproducibility

## Minimal environment

- Python 3.13 tested.
- NumPy required.
- No LLM, text embeddings, retrieval memory, cross-instance memory or learned sidecar are used in the EML PoC.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Expected current result:

```text
Ran 8 tests
OK
```

## Run Stage 4

```bash
PYTHONPATH=src python -m nda_eml_poc.stage4_discovery --out results/stage4 --seed 0
```

Expected key artifacts:

- `results/stage4/stage4_curriculum_discoveries.csv`
- `results/stage4/stage4_committed_macros.csv`
- `results/stage4/stage4_taylor_trap.csv`
- `results/stage4/stage4_graveyard.csv`
- `results/stage4/stage4_run.json`

## Author-ready metadata note

Author metadata, LICENSE, CITATION.cff and `.zenodo.json` were filled after the Stage 4 code/results were generated. No experimental source code was changed except package metadata (`pyproject.toml` and `__version__`). The clean test log already included in `results/stage4_clean_rerun/` should still be repeated after cloning the public GitHub repository.
