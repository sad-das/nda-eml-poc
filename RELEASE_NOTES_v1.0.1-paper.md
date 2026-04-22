# Release v1.0.1-paper

This release is a metadata and reproducibility hotfix for the NDA EML proof-of-concept paper package.

It supersedes `v1.0.0-paper` for manuscript citation. No experimental code, Stage 1-4 result logic, or reported Stage 4 claims were changed.

## Changes

- Normalize tracked text files to LF line endings for portable raw views and diffs.
- Regenerate `SHA256SUMS` with Unix-style paths suitable for `sha256sum -c SHA256SUMS`.
- Add GitHub Actions CI for unit tests and checksum verification.
- Update `CITATION.cff`, `.zenodo.json`, `README.md`, and package metadata for `v1.0.1-paper`.
- Keep the historical `v1.0.0-paper` DOI visible as the first archived software release.

## Main Stage 4 result

```text
x_times_y -> mul := exp(add(ln(x), ln(y)))
macro_depth = 3
historical_expansion_cost = 57 raw EML nodes
manual_registry_dependency = 0
```

## Caveat

This repository does not demonstrate AGI. It is a restricted mathematical proof-of-concept for contradiction-driven hierarchical concept formation in the EML substrate.

## DOI

Zenodo assigns the version DOI when this GitHub release is archived. Cite the DOI displayed on the Zenodo record for `v1.0.1-paper`.

Historical first archive:

```text
v1.0.0-paper: https://doi.org/10.5281/zenodo.19688532
```
