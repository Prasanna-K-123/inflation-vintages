# When a simple inflation forecast survives stricter evidence

Prasanna K | Economic research portfolio | Prepared 17 October 2026

## Result and decision

On 18 held-out monthly releases, July 2024-December 2025, development-selected persistence has RMSE 0.8185 percentage points (pp), versus 1.6901 for a fixed Ridge AR(1). The primary paired squared-error difference, AR(1) minus persistence, is 2.186524 pp squared; its conditional 95% circular-block percentile interval is [0.613693, 3.816555]. Retain the already selected persistence baseline for this old-base experiment. The test does not trigger model reselection, retuning or a claim about present-day inflation forecasting.

## Measurement before modelling

The release-vintage dataset contains 48 consecutive official PIB/MoSPI releases, January 2022-December 2025, and 144 distinct old-base (2012=100) Combined headline year-on-year observations: current provisional, previous-month final and prior-year reference. Seven of 47 available provisional-to-next-release-final comparisons change, by at most 0.10 pp. Rural, Urban, food, levels and new-base observations cannot enter the headline target by label similarity. Identical desktop/mobile HTML tables are collapsed only after all nine numerical values agree.

Each record carries its reference month, base, metric, sector, status, source URL, exact table-cell XPath, source SHA256 and printed PIB timestamp with IST offset. A forecast is cut one minute after the previous month's release. The as-of query selects only a matching base/metric/sector observation published by that time. A value first disclosed in the target release is unavailable even when it describes the preceding month.

These are retrospectively retrieved, publication-dated documents, not cryptographically authenticated contemporaneous web snapshots. Later document editing cannot be ruled out. Five attached official PDF tables reconcile to the HTML values and were visually checked; this is source agreement, not external independent review. Source content remains attributed to its publisher and is not relicensed with code.

## Frozen design

Training uses 23 pairs, February 2022-December 2023, constructed from first-provisional targets and the previous release's observed lag. Standardization is fitted only on training data. The sole challenger is a Ridge regression of inflation on its lag, alpha 1, with intercept. There is no parameter or lag search, no macro feature whose vintage is unknown, and no refit after December 2023. A separate one-dimensional penalized closed form reconciles the fitted coefficient and intercept.

Development comprises six releases, January-June 2024. Persistence RMSE is 0.2948; seasonal-12-month RMSE is 0.8897; AR(1) RMSE is 0.5969. Persistence wins the predeclared selection rule. Eleven frozen file hashes cover protocol, extraction/core/training code, source manifest, panel, model, development results and the 18 final predictions. The evaluation plan fixes 2,000 circular moving-block draws of three monthly dates, seed 20261017, before first final scoring. No outcome is used to revise these choices.

## Held-out performance

Error is forecast minus first-provisional target; positive error means overprediction. MAE, RMSE and signed error use pp, not relative percentage changes. Seasonal-12-month remains a diagnostic comparator; it cannot replace the development-selected baseline after the test.

| Frozen method | MAE (pp) | RMSE (pp) | Mean error (pp) |
|---|---:|---:|---:|
| persistence | 0.6828 | 0.8185 | +0.2083 |
| ridge_ar1 | 1.5397 | 1.6901 | +1.4053 |
| seasonal_12month | 2.3356 | 2.8280 | +2.1344 |

The primary interval resamples paired errors jointly by release date. It is conditional on this short panel, fixed model and block choice. Eighteen dependent dates and six development dates cannot support a universal superiority claim, reliable regime-specific uncertainty or calibrated individual prediction intervals. The interval is not an inflation forecast range.

## Where the errors arise

AR(1) error equals the persistence lag error plus its model adjustment away from the last observed release. Mean persistence lag error is +0.208333 pp; the average AR(1) adjustment is +1.196937, summing to AR(1)'s mean error +1.405270. Its MSE decomposes into lag component 0.669972, model-adjustment component 1.948181 and cross term +0.238343, summing to 2.856496. This is an exact arithmetic identity, not causal attribution to food prices, policy or another driver.

The fixed regression shrinks predictions toward its high-inflation 2022-23 training environment. This is a plausible explanation of its positive adjustment during subsequent lower inflation, not a separately identified causal effect. Year subsets are descriptive only and are not used to choose another model. Their exact scores are in final.json.

## Quantifying hindsight and revisions

Replacing each previous-month provisional lag with its final value, disclosed only with the target release, changes four final-period predictions. The largest change is 0.057558 pp. With the same frozen coefficients, contaminated AR(1) RMSE is 1.685431, versus honest 1.690117; MSE changes by -0.015820. Here contamination makes accuracy look slightly better. That direction was not assumed in advance and is not a general law.

A separate later-final-target evaluation changes four of 18 targets, with maximum absolute revision 0.10 pp. Persistence RMSE is 0.817360 on that different target. This does not replace the first-release primary score. December 2025's old-base final 1.33 is verified in the pinned February 2026 release as auxiliary evidence; it is not silently added to the sealed vintage panel.

## Series break and stopping rule

The 12 February 2026 release starts base 2024=100. January 2026 new-base headline inflation is 2.75%, while the separate December 2025 final old-base headline is 1.33%. Changes in basket, weights and classification mean these cannot be joined by a cosmetic rescaling. New-base 2025 backcasts first published in 2026 are not available at 2025 origins. This study stops its primary target at December 2025. It does not issue a current October 2026 forecast or claim validation on the new base.

## Reproduction and failure checks

Restore pinned sources if necessary, run the source audit and seven boundary tests, verify the 11 frozen hashes, then run evaluate_final.py and report_final.py. Every primary target, lag, seasonal input and later-final comparison is traced to its numerical HTML cell; the last final uses a separately verified row. Failure checks reject missing vintage/base/timezone, conflicting cells and unavailable values; future revisions leave prior queries unchanged. Two evaluation outputs reproduce byte for byte from the fixed panel in the recorded environment. This is local reproduction, not independent external replication or cross-platform proof.

## Full final release ledger

| Target month | Forecast cutoff (IST) | First target (%) | Persistence (%) | AR(1) (%) | Persistence error (pp) |
|---|---|---:|---:|---:|---:|
| 2024-07 | 2024-07-12T17:31:00+05:30 | 3.54 | 5.08 | 5.5387 | +1.54 |
| 2024-08 | 2024-08-12T17:31:00+05:30 | 3.65 | 3.54 | 4.6523 | -0.11 |
| 2024-09 | 2024-09-12T17:31:00+05:30 | 5.49 | 3.65 | 4.7156 | -1.84 |
| 2024-10 | 2024-10-14T17:31:00+05:30 | 6.21 | 5.49 | 5.7747 | -0.72 |
| 2024-11 | 2024-11-12T16:01:00+05:30 | 5.48 | 6.21 | 6.1891 | +0.73 |
| 2024-12 | 2024-12-12T16:01:00+05:30 | 5.22 | 5.48 | 5.7689 | +0.26 |
| 2025-01 | 2025-01-13T16:01:00+05:30 | 4.31 | 5.22 | 5.6193 | +0.91 |
| 2025-02 | 2025-02-12T16:01:00+05:30 | 3.61 | 4.31 | 5.0955 | +0.70 |
| 2025-03 | 2025-03-12T16:01:00+05:30 | 3.34 | 3.61 | 4.6926 | +0.27 |
| 2025-04 | 2025-04-15T16:01:00+05:30 | 3.16 | 3.34 | 4.5372 | +0.18 |
| 2025-05 | 2025-05-13T16:01:00+05:30 | 2.82 | 3.16 | 4.4336 | +0.34 |
| 2025-06 | 2025-06-12T16:01:00+05:30 | 2.10 | 2.82 | 4.2379 | +0.72 |
| 2025-07 | 2025-07-14T16:01:00+05:30 | 1.55 | 2.10 | 3.8235 | +0.55 |
| 2025-08 | 2025-08-12T16:01:00+05:30 | 2.07 | 1.55 | 3.5069 | -0.52 |
| 2025-09 | 2025-09-12T16:01:00+05:30 | 1.54 | 2.07 | 3.8062 | +0.53 |
| 2025-10 | 2025-10-13T16:01:00+05:30 | 0.25 | 1.54 | 3.5011 | +1.29 |
| 2025-11 | 2025-11-12T16:01:00+05:30 | 0.71 | 0.25 | 2.7586 | -0.46 |
| 2025-12 | 2025-12-12T16:01:00+05:30 | 1.33 | 0.71 | 3.0234 | -0.62 |

## Sources

The complete 49-document official URL/hash ledger is data/source_manifest.json. Observation-level locators are in data/processed/vintages.json and reports/final.json. Five PDF comparisons are documented in reports/source_spot_checks.json. The base-break and final old-base row are in reports/base_break.json and reports/base_break_evidence.json. These are government statistical releases, not third-party numeric summaries. Study protocol and fixed evaluation plan are preserved separately; no raw document is passed off as original research.
