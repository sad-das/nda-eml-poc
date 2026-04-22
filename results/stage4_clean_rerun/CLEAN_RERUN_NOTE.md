# Clean Stage 4 rerun note

The Stage 4 curriculum runner was invoked from a freshly unpacked repository tree with:

```bash
PYTHONPATH=src python -c "from pathlib import Path; from nda_eml_poc.stage4_discovery import run; run(Path('results/stage4_clean_rerun'), 0)"
```

The runner generated the Stage 4 CSV/JSON/REPORT artifacts in this directory. Unit tests over the same unpacked tree are stored in `../stage4/CLEAN_FULL_TEST_OUTPUT.txt` and passed with `Ran 8 tests ... OK`.
