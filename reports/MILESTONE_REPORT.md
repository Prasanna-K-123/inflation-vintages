# Indian CPI vintages: audited archive and frozen model comparison

17 October 2026. Interim milestone A/B/C. Final 18 release errors have not been computed; no completed economic research paper, current forecast or public release is claimed.

## What is complete

Recovered 48 consecutive official monthly releases for January 2022–December 2025 and a separate 12 February 2026 base-revision release. The old-base panel has 144 observations: current provisional, previous-month final and prior-year reference values, each retaining the source cell, publication time, source URL and content hash. Source duplicates are collapsed only when their numeric rows agree. Five PDF/HTML document checks reconcile current headline tables.

The as-of query rejects unavailable vintages, conflicting same-time values, wrong bases and missing timestamps. Publication availability uses the conservative PIB posting time in IST. The archive is reconstructed from publication-dated documents retrieved later; it is not an immutable contemporaneous archive, and source edits cannot be ruled out.

## Revision evidence

Among 47 provisional-to-next-release-final pairs, 7 change. Largest absolute change is 0.10 percentage points. Preserve first-release values rather than silently replace them with today’s final history. A later revision is not available at the forecast cutoff immediately after the original release.

| Reference month | First provisional (%) | Next-release final (%) | Revision (percentage points) |
|---|---:|---:|---:|
| 2023-05 | 4.25 | 4.31 | +0.06 |
| 2023-06 | 4.81 | 4.87 | +0.06 |
| 2024-05 | 4.75 | 4.80 | +0.05 |
| 2024-07 | 3.54 | 3.60 | +0.06 |
| 2025-01 | 4.31 | 4.26 | -0.05 |
| 2025-07 | 1.55 | 1.61 | +0.06 |
| 2025-09 | 1.54 | 1.44 | -0.10 |

December 2025 final old-base 1.33% is documented separately in the February 2026 base-break evidence. It is not an additional row of the frozen 144-record old-release panel. New-base January 2026 headline 2.75% has a different measurement framework; those values are not spliced. The 2025 new-base backcast first appeared 2026 and is not treated as information available in 2025.

## Baselines and bounded challenger

Training uses 23 monthly first-release pairs through December 2023. Baselines are persistence and the same reference month one year earlier, using only the vintage actually available at that cutoff. The sole challenger is Ridge AR(1), alpha 1, with training-only standardization, intercept and no lag/parameter search. Coefficients remain fixed; later observed lags update predictions.

Development is January–June 2024. Forecast cutoff is one minute after the preceding monthly release. The final period is July 2024–December 2025; its 18 forecasts are hash-frozen before error scoring. Model fitting, baseline selection and final predictions are separated.

| Model | Development RMSE (percentage points) | Development MAE (percentage points) |
|---|---:|---:|
| persistence | 0.294816 | 0.211667 |
| ridge_ar1 | 0.596912 | 0.572366 |
| seasonal_12month | 0.889719 | 0.726667 |

The fixed development rule selects **persistence**. The AR(1) challenger is retained for the future comparison; it is not retuned to overturn its weaker development result. Six development releases and 23 training pairs are a small sample and do not support a broad accuracy claim.

The fitted standardized coefficient is 0.5562408585825216 and intercept 6.179565217391304, with feature mean 6.193478260869566 and scale 0.9664080005051975. Independent one-dimensional penalized least-squares arithmetic agrees to numerical tolerance. These are forecasting coefficients, not causal inflation effects.

## Verification and remaining finite steps

Seven tests cover revision cutoff equality, a revision one minute later, future changes, absent vintages, base mismatch, conflicting same-time values, timezone enforcement, month arithmetic and baseline/AR1 identities. All 18 saved final forecast rows are recomputed; their input publication times precede forecast cutoffs, which precede target publication. Fabricated future revisions leave every earlier as-of input unchanged. The frozen final forecast file contains no actual target/error columns.

Next: verify the freeze; compute the 18 first-release final errors and fixed three-month-block uncertainty; quantify hindsight-input contamination without assuming its direction; analyze later-revised targets separately; then write the full research paper and dated brief. Final evaluation, report/brief and public tagged release/demo are D/E/F and remain unaccepted. New-base forecasting needs a separately justified history and design.

Evidence: [source manifest](../data/source_manifest.json), [vintages](../data/processed/vintages.json), [data audit](data_audit.json), [development](development.json), [frozen final predictions](../data/processed/final_forecasts.json), [model freeze](model_freeze.json), [verification](milestone_verification.json), [protocol](../PROTOCOL.md).
