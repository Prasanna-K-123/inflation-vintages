# Indian CPI release vintages

A publication-aware economic research pipeline for old-base Combined headline CPI inflation. It separates first provisional values from later final and prior-year observations and refuses to join the 2026 base revision into a cosmetic rescaling.

The archive contains 48 official releases and 144 vintage observations, with fixed models, an 18-release final evaluation, a research paper and a dated two-page brief. Persistence final RMSE is 0.8185 pp versus fixed AR(1) 1.6901. Retain the already selected simple baseline. See [research paper](reports/RESEARCH_PAPER.md), [PDF paper](output/pdf/P6_Inflation_Research_Paper.pdf) and [two-page brief](output/pdf/P6_December_2025_Forecast_Brief.pdf). Public release and rendered-demo verification remain pending. No current inflation forecast is claimed.

## Reproduce this milestone

Use pinned requirements and the cached source documents. New acquisition follows only the documented official URLs in scripts/acquire_sources.py. Then:

```bash
python scripts/build_vintages.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/train_and_freeze.py
python scripts/verify_milestone.py
python scripts/report_milestone.py
python scripts/evaluate_final.py
python scripts/report_final.py
```

The source manifest pins document bytes; local cached files are not silently redownloaded. The freeze guards scientific code, vintage data, model coefficients, development selection and final forecasts. Recovery may store source documents as data/raw_sources.tar.xz to avoid repeated embedded HTML assets; restore using scripts/restore_sources.py before rerunning a source audit.

## Sources and limits

Official PIB/MoSPI public statistical releases are attributed in each observation, with exact table cell XPath, original document hash and IST publication timestamp. Acquisition deliberately avoids replacing unavailable legacy Mo SPI PDFs with third-party numeric summaries. Independent PDF/HTML agreement is documentary verification, not external independent review.

These are publication-dated reconstructed vintages retrieved later, not immutable historic snapshots. Training 23 pairs and development 6 releases are small samples. New-base 2024 history/backcasts published 2026 cannot be used at 2025 cutoffs. Government source content is not relicensed under a future code license. No personal investment or monetary-policy recommendation follows from these forecasts.

## Explore the saved evidence

Open [the offline explorer](docs/index.html). Its data and JavaScript are embedded; no account, API key or local server is required. Reports and downloadable artifacts are packaged under the same hosting folder. Official source links require internet access.

```bash
python scripts/build_demo.py
node tests/check_explorer.cjs
python scripts/verify_demo_links.py
```

The checks execute the actual page script against the saved Python results and verify local links, page headings and form labels. They do not establish rendered browser, mobile, keyboard or live-site behaviour. Those checks and the verified version tag remain in [the release checklist](docs/RELEASE.md).
