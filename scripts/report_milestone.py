import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run():
    a=json.loads((ROOT/'reports/data_audit.json').read_text());d=json.loads((ROOT/'reports/development.json').read_text())
    revisions=json.loads((ROOT/'reports/revisions.json').read_text());changed=[r for r in revisions if r['revision_percentage_points']!=0]
    md=['# Indian CPI vintages: audited archive and frozen model comparison','','17 October2026. Interim milestone A/B/C. Final18release errors have not been computed; no completed economic research paper, current forecast or public release is claimed.','',
        '## What is complete','',
        f"Recovered48consecutive official monthly releases for January2022–December2025 and a separate12February2026 base-revision release. The old-base panel has{a['vintage_records']} observations: current provisional, previous-month final and prior-year reference values, each retaining the source cell, publication time, source URL and content hash. Source duplicates are collapsed only when their numeric rows agree. Five PDF/HTML document checks reconcile current headline tables.",
        '', 'The as-of query rejects unavailable vintages, conflicting same-time values, wrong bases and missing timestamps. Publication availability uses the conservative PIB posting time in IST. The archive is reconstructed from publication-dated documents retrieved later; it is not an immutable contemporaneous archive, and source edits cannot be ruled out.','',
        '## Revision evidence','',
        f"Among47provisional-to-next-release-final pairs, {len(changed)} change. Largest absolute change is{a['max_abs_revision_percentage_points']:.2f} percentage points. Preserve first-release values rather than silently replace them with today’s final history. A later revision is not available at the forecast cutoff immediately after the original release.",
        '', '| Reference month | First provisional (%) | Next-release final (%) | Revision (percentage points) |','|---|---:|---:|---:|']
    for r in changed:md.append(f"| {r['reference_month']} | {r['provisional']:.2f} | {r['next_release_final']:.2f} | {r['revision_percentage_points']:+.2f} |")
    md+=['','December2025 final old-base1.33% is documented separately in the February2026 base-break evidence. It is not an additional row of the frozen144-record old-release panel. New-base January2026 headline2.75% has a different measurement framework; those values are not spliced. The2025 new-base backcast first appeared2026 and is not treated as information available in2025.','',
         '## Baselines and bounded challenger','',
         'Training uses23monthly first-release pairs throughDecember2023. Baselines are persistence and the same reference month one year earlier, using only the vintage actually available at that cutoff. The sole challenger is Ridge AR(1), alpha1, with training-only standardization, intercept and no lag/parameter search. Coefficients remain fixed; later observed lags update predictions.','',
         'Development is January–June2024. Forecast cutoff is one minute after the preceding monthly release. The final period is July2024–December2025; its18forecasts are hash-frozen before error scoring. Model fitting, baseline selection and final predictions are separated.','',
         '| Model | Development RMSE (percentage points) | Development MAE (percentage points) |','|---|---:|---:|']
    for k,v in d['metrics'].items():md.append(f"| {k} | {v['rmse']:.6f} | {v['mae']:.6f} |")
    md+=['',f"The fixed development rule selects **{d['selected_forecast']}**. The AR(1) challenger is retained for the future comparison; it is not retuned to overturn its weaker development result. Six development releases and23training pairs are a small sample and do not support a broad accuracy claim.",
         '', 'The fitted standardized coefficient is0.5562408585825216 and intercept6.179565217391304, with feature mean6.193478260869566 and scale0.9664080005051975. Independent one-dimensional penalized least-squares arithmetic agrees to numerical tolerance. These are forecasting coefficients, not causal inflation effects.','',
         '## Verification and remaining finite steps','',
         'Seven tests cover revision cutoff equality, a revision one minute later, future changes, absent vintages, base mismatch, conflicting same-time values, timezone enforcement, month arithmetic and baseline/AR1 identities. All18saved final forecast rows are recomputed; their input publication times precede forecast cutoffs, which precede target publication. Fabricated future revisions leave every earlier as-of input unchanged. The frozen final forecast file contains no actual target/error columns.','',
         'Next: verify the freeze; compute the18first-release final errors and fixed three-month-block uncertainty; quantify hindsight-input contamination without assuming its direction; analyze later-revised targets separately; then write the full research paper and dated brief. Final evaluation, report/brief and public tagged release/demo are D/E/F and remain unaccepted. New-base forecasting needs a separately justified history and design.','',
         'Evidence: [source manifest](../data/source_manifest.json), [vintages](../data/processed/vintages.json), [data audit](data_audit.json), [development](development.json), [frozen final predictions](../data/processed/final_forecasts.json), [model freeze](model_freeze.json), [verification](milestone_verification.json), [protocol](../PROTOCOL.md).']
    (ROOT/'reports/MILESTONE_REPORT.md').write_text('\n'.join(md)+'\n');print('Interim archive/baseline/challenger report generated')

if __name__=='__main__':
    run()
    from format_prose import polish
    for document in list(ROOT.glob('README.md'))+list((ROOT/'reports').glob('*.md'))+list((ROOT/'docs').glob('*.md')):
        document.write_text(polish(document.read_text()))

