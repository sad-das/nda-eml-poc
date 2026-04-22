# Artifact manifest

## Source code

- `src/nda_eml_poc/eml.py` — EML expression tree and evaluation.
- `src/nda_eml_poc/constructors.py` — constructive EML witnesses.
- `src/nda_eml_poc/gate6.py` — baseline Gate 6 checks.
- `src/nda_eml_poc/stage3_hardening.py` — Stage 3 bounded discovery and hardening.
- `src/nda_eml_poc/stage4_discovery.py` — Stage 4 macro-node discovery engine.

## Tests

- `tests/test_stage2_witnesses.py`
- `tests/test_stage3_hardening.py`
- `tests/test_stage4_discovery.py`

## Results

- `results/stage3/*` — Stage 3 ablation/discovery/hardening outputs.
- `results/stage4/*` — Stage 4 macro-node curriculum, Taylor-trap and policy outputs.

## Reports

- `NDA_EML_PoC_stage1_report.md`
- `NDA_EML_PoC_stage2_report.md`
- `NDA_EML_PoC_stage3_report.md`
- `NDA_EML_PoC_stage4_report.md`
