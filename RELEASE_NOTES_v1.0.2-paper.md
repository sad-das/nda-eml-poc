# v1.0.2-paper

This release updates the publication SVG figures for the NDA EML proof-of-concept paper package.

It supersedes `v1.0.1-paper` for manuscript citation if the revised figures are used. No experimental code, Stage 1-4 result logic, or reported numerical claims were changed.

## Changes

- Redraw all six SVG figures in a cleaner scientific style.
- Fix text spacing and label overlap across figures.
- Correct the Figure 6 log-scale axis for the Taylor-trap asymptotic MSE.
- Clarify that Figure 3 preservation measures frozen-witness retention, not new discovery.
- Update figure captions and regenerate `SHA256SUMS`.

## DOI

- Version DOI: `10.5281/zenodo.19689202`
- Concept DOI: `10.5281/zenodo.19688531`

## Validation

- SVG XML validation passed.
- Text-overlap check passed for all six SVG figures.
- `SHA256SUMS` verification passed.
- Unit tests passed: 8/8.
