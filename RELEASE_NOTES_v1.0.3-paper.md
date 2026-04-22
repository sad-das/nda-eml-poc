# v1.0.3-paper

This release fixes the checksum manifest for the NDA EML proof-of-concept paper package.

It supersedes `v1.0.2-paper` for manuscript citation because `v1.0.2-paper` contained a `SHA256SUMS` manifest that referenced local Python bytecode cache files not present in the GitHub/Zenodo source archive.

No experimental code, Stage 1-4 result logic, figures, or reported numerical claims were changed.

## Changes

- Regenerate `SHA256SUMS` from tracked Git files only.
- Exclude Python `__pycache__` and `*.pyc` files from checksum verification.
- Update package and citation metadata for `v1.0.3-paper`.

## DOI

- Version DOI: `10.5281/zenodo.19692414`
- Concept DOI: `10.5281/zenodo.19688531`

## Validation

- GitHub Actions passed on `v1.0.3-paper`.
- `SHA256SUMS` verification passed.
- Unit tests passed: 8/8.
