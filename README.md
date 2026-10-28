# Indian CPI release vintages

> A core study in a seven-project quantitative decision science portfolio. [Explore related projects](#related-projects).

[![Public research checks](https://github.com/Prasanna-K-123/inflation-vintages/actions/workflows/verify.yml/badge.svg)](https://github.com/Prasanna-K-123/inflation-vintages/actions/workflows/verify.yml)

A publication-aware economic research pipeline for old-base Combined headline CPI inflation. It separates first provisional values from later final and prior-year observations and refuses to join the 2026 base revision into a cosmetic rescaling.

The archive contains 48 official releases and 144 vintage observations, with fixed models, an 18-release final evaluation, a research paper and a dated two-page brief. Persistence final RMSE is 0.8185 pp versus fixed AR(1) 1.6901. Retain the already selected simple baseline. See [research paper](reports/RESEARCH_PAPER.md), [PDF paper](output/pdf/P6_Inflation_Research_Paper.pdf) and [two-page brief](output/pdf/P6_December_2025_Forecast_Brief.pdf). The [live explorer](https://prasanna-k-123.github.io/inflation-vintages/) has separately dated desktop, 375/320-pixel layout, native keyboard and PDF-download observations in the [release record](docs/RELEASE.md). No current inflation forecast is claimed.

## Automated public checks

The automated checks run on public files without private data, credentials or model refitting. They include unit tests, explorer arithmetic and the public numeric reproduction. Original-document re-audit is separate.

## Reproduce numeric results from the public checkout

Install the pinned requirements, then run:

```bash
python scripts/reproduce_numeric_results.py
```

This requires no raw-document cache or private model artifact. It checks ten
published frozen-file hashes, reconstructs the original model-artifact hash from
its published coefficients, independently reproduces the 23-pair Ridge fit,
reconstructs all 54 final forecasts, and reproduces primary/later-final metrics,
the paired block interval and hindsight diagnostic. A clean public-file-only run
passed. It is a numeric reproduction of the published vintage table; it does
not independently re-audit the original HTML/PDF source bytes or XPath cells.

## Reproduce the full source-cell audit

Use pinned requirements and the original cached source documents. The acquisition
command below checks the documented official URLs against the existing manifest;
it preserves original retrieval dates and writes a separate current UTC receipt.
Changed bytes are rejected and never adopted as historical sources. Then:

```bash
python scripts/acquire_sources.py
python scripts/build_vintages.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/restore_frozen_model.py
python scripts/verify_milestone.py
python scripts/report_milestone.py
python scripts/evaluate_final.py
python scripts/report_final.py
```

The source manifest pins document bytes; local cached files are not silently redownloaded. The freeze guards the historical scientific code, vintage data, model coefficients, development selection and final forecasts. The exact original builder is retained in `reproducibility/original_build_vintages.py`; the current header parser is an explicit post-freeze correction. Original freeze files are unchanged. `restore_frozen_model.py` reconstructs the original artifact from published coefficients and verifies its original hash without refitting. The original `train_and_freeze.py` remains research history, not the current reproduction entry point. Recovery may store source documents as data/raw_sources.tar.xz; restore using scripts/restore_sources.py before rerunning a source audit.

PIB pages now have different HTML bytes from the frozen cache. If original bytes
are unavailable, the full frozen-source command must stop. A separate current-page
audit checks current official statistics, headers and publication timestamps
against the published historical table without replacing either dataset:

```bash
python scripts/audit_current_sources.py --cache work/current_sources --output work/current_source_comparison.json
```

Use new paths for each audit. This checks documentary agreement today, not
immutable historical snapshots or byte-identical source reconstruction. See the
[26 October revision](reports/source_integrity_revision_20261026.json) and
[initial source comparison](reports/current_source_comparison_20261026.json).
That audit verified 47 of 48 old-base releases and the four new-base evidence
rows; one network read failed. The [28 October retry](reports/current_source_retry_20261028.json)
retrieved only the failed March 2025 page and verified its nine cells, semantic
headers and publication timestamp. The combined evidence covers all 48 old-base
releases. None of the 49 retrieved documents matched the original byte hashes.
Earlier successful checks retain their 26 October retrieval dates.

To retry failed downloads without redownloading successful sources or altering
the prior receipt, use fresh output paths:

```bash
python scripts/audit_current_sources.py --cache work/current_retry --output work/current_retry.json --retry-from work/current_source_comparison.json
```

The retry validates the prior receipt's frozen manifest and source identities
before carrying evidence forward. The [verification record](reports/source_integrity_verification_20261026.json)
records 13 passing tests, unchanged public numerical results and the limits of
this source comparison. It does not certify recovery of the original raw cache.

## Sources and limits

The chart also has an expandable table of all 18 months. Its caption identifies
the method, target and any unavailable-lag diagnostic; the selected month is
marked. Solid and dashed lines distinguish the plotted series. Control changes
update a concise result status. `node tests/check_explorer.cjs` checks all 108
normal views, 18 hindsight views and 2,268 displayed table rows against the saved
evidence. See the [23 October accessibility revision](reports/accessibility_revision_20261023.json)
for scope; these script checks are separate from native browser or screen-reader testing.

Official PIB/MoSPI public statistical releases are attributed in each observation, with exact table cell XPath, original document hash and IST publication timestamp. Acquisition deliberately avoids replacing unavailable legacy MoSPI PDFs with third-party numeric summaries. Independent PDF/HTML agreement is documentary verification, not external independent review.

These are publication-dated reconstructed vintages retrieved later, not immutable historic snapshots. Training 23 pairs and development 6 releases are small samples. New-base 2024 history/backcasts published 2026 cannot be used at 2025 cutoffs. Government source content is not relicensed under a future code license. No personal investment or monetary-policy recommendation follows from these forecasts.

## Explore the saved evidence

Open [the offline explorer](docs/index.html). Its data and JavaScript are embedded; no account, API key or local server is required. Reports and downloadable artifacts are packaged under the same hosting folder. Official source links require internet access.

```bash
python scripts/build_demo.py
node tests/check_explorer.cjs
python scripts/verify_demo_links.py
```

The checks execute the actual page script against the saved Python results and verify local links, page headings and form labels. They do not establish rendered browser, mobile, keyboard or live-site behaviour. Actual desktop, 375/320-pixel browser, keyboard and live-link checks are recorded separately in [the release record](docs/RELEASE.md).
The static link check records its current UTC execution under ignored
`work/demo_link_verification.json`; the original committed receipt remains historical evidence.

## 20 October maintenance

The [parser dependency revision](reports/dependency_revision_20261020.json) replaces
the old PDF parser with pypdf 6.21.1 after five official PDF/HTML cross-checks,
all seven boundary tests and the public numeric reproduction passed. Original
environment pins are retained for research history. The
[accessibility revision](reports/accessibility_revision_20261020.json) improves
text contrast without changing the study or its forecasts.

## Related projects

Start with [operational forecasting and allocation](https://github.com/Prasanna-K-123/demand-inventory),
[causal customer decisions](https://github.com/Prasanna-K-123/causal-customer-decisions)
and [bank-risk model validation](https://github.com/Prasanna-K-123/credit-risk-model-validation).
Alongside this publication-aware economic study, the other core projects cover
[corporate financial decisions](https://github.com/Prasanna-K-123/financial-decision-lab),
[treasury and ALM](https://github.com/Prasanna-K-123/treasury-alm), and
[insurance pricing and reserve uncertainty](https://github.com/Prasanna-K-123/insurance-price-reserve-risk).
Each addresses a different decision and makes its data, evaluation and limitations inspectable.
