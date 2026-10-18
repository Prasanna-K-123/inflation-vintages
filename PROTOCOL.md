# Indian CPI release vintages and one-release-ahead forecasting

Frozen17October2026 before forecasting or model comparison. This extends the locked project scope; it does not join old/new measurement regimes into a single rescaled series.

## Source and feasible panel

Recover the48 official PIB/MoSPI monthly releases for reference months January2022–December2025, plus the12February2026 new-base release as a measurement-break document. All primary forecast targets are All-India Combined headline CPI year-on-year inflation (%) on base2012=100, explicitly provisional in that month's release. Current provisional, previous-month final and prior-year comparison values are distinct vintage records, with exact source table/row/cell locators, file hash and publication timestamp.

Use the conservative timestamp printed by PIB, with IST offset+05:30, as the availability timestamp. Forecast cutoffs are one minute after the preceding reference month's recovered release timestamp. Retrospectively retrieved publication-dated documents reconstruct vintages; they are not cryptographically verified contemporaneous snapshots and may have been edited. Preserve this limitation. Do not call values copied from2025 time-series annexes information available in2022.

Validate reference month, base, Combined rather than Rural/Urban/food metrics, provisional/final labels, current/previous/prior-year column ordering, unique source keys and strictly increasing release times. Identical desktop/mobile duplicate tables in one PIB page are collapsed only after matching cell values. Missing/conflicting cells stop the audit rather than become0. Source records remain independent of a later source-code license.

The January2026 new-base target is not appended to the old series. The base2024 release changes basket/weights/classification; old-base training may not be carried through it by a cosmetic rescaling. The2025 new-base backcast, first published2026, is unavailable to a2025-origin forecast. A new-base forecasting exercise requires its own adequate history and future evaluation; none is claimed in this milestone.

## Fixed models and splits

Initial training: first provisional values January2022–December2023. Development: January–June2024. Final: July2024–December2025,18releases. Development/training labels are available before the first final forecast cutoff; preserve actual release timestamps, not just month labels. Model coefficients are fitted once throughDecember2023 and remain fixed; new observed lags update predictions at each later cutoff.

Baseline1: persistence, last available provisional headline rate at the preceding month's release. Baseline2: same reference month a year earlier, using the latest vintage actually published by the forecast cutoff. No revised value from the target release enters its prediction.

Single challenger: Ridge AR(1), intercept and last released monthly headline rate, feature standardized on the23 training pairs, alpha1. Fixed specification; no lag/alpha search, external predictors, early stopping or model shopping. This deliberately small model avoids a large model relative to the short recovered archive. It is a forecast association, not a causal inflation model.

Select baseline by development mean squared error; ties1e-8 favour persistence. Challenger replaces the selected baseline only if development MSE is lower by more than1e-8. Freeze model coefficients, code/protocol/data hashes, selected comparator and final predictions before any final-test error is computed. No final refit, recalibration or test-best baseline substitution.

## Subsequent final-evaluation gate

Compare frozen methods on18 first-provisional targets: MAE, RMSE, signed error and full per-release predictions. Primary contrast: paired squared error, challenger minus selected baseline. Use2000 circular moving-block bootstrap draws, blocks3monthly releases, resampling whole release dates. Report a95% conditional percentile interval and the short-panel/dependence limitations. No guarantee of current-market predictive performance.

Hindsight diagnostic: replace the previous month's actually available provisional value with its later final value, using the same frozen AR(1) coefficients. This leaks a revision not yet available at the forecast cutoff. Quantify its error change; do not assume contamination necessarily improves apparent accuracy. A separate later-revised target analysis must be labeled and cannot replace the first-release target. Revision differences remain in percentage points, not percent changes.

Required failure checks: timestamp equality/cutoffs; a revision one minute later is excluded; missing vintage and conflicting source cells are errors; base mismatch is rejected; training targets cannot include final-period labels; future revisions/values do not change earlier as-of queries; simple baseline identities and Ridge prediction arithmetic reconcile independently. Source table extractions receive spot checks against both official HTML and attached official PDFs. Documentary source agreement is not independent review.

## Finite milestone

Current work aims to complete A (audited48release panel), B (reproducible timestamp-aware baselines) and C (fixed AR1/development decision/final forecast freeze). It must not claim D/E/F before actual final evaluation, failure analysis, research paper/dated brief, clean public release and verified demo. No current inflation forecast, ongoing automation, outreach or posting is included. The portfolio target is achieved only through accepted work, not by changing gate definitions.
