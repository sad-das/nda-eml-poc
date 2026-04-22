# Reproducibility

The repository uses NumPy only. The default run is deterministic for fixed seeds.

Recommended smoke run:

```bash
PYTHONPATH=src /usr/bin/python3 -m nda_eml_poc.run_ablation \
  --out results/stage2 \
  --seeds 0 1 2
```

Recommended tests:

```bash
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests
```

Artifacts produced by a run:

- `summary_metrics.csv`
- `target_results.csv`
- per-variant/per-seed JSON traces
- `REPORT.md`

The results are a proof-of-concept scaffold, not a claim that NDA has solved general symbolic regression or AGI.
