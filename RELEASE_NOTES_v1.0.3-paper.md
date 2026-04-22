# v1.0.3-paper

This release fixes the checksum manifest for the NDA EML proof-of-concept paper package.

It supersedes `v1.0.2-paper` for manuscript citation because `v1.0.2-paper` contained a `SHA256SUMS` manifest that referenced local Python bytecode cache files not present in the GitHub/Zenodo source archive.

No experimental code, Stage 1-4 result logic, figures, or reported numerical claims were changed.

## Changes

- Regenerate `SHA256SUMS` from tracked Git files only.
- Exclude Python `__pycache__` and `*.pyc` files from checksum verification.
- Update package and citation metadata for `v1.0.3-paper`.

## Validation

- `SHA256SUMS` verification passed locally.
- Unit tests passed locally: 8/8.
- GitHub Actions should be checked after publishing this commit/tag.
