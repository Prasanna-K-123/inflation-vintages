"""Score the sealed final forecast panel without fitting or selecting models."""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inflation_vintages.core import VintageStore, ar1_prediction, shift_month


def read(name):
    return json.loads((ROOT / name).read_text())


def dump(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def verify_freeze():
    frozen = read('reports/model_freeze.json')
    for name, digest in frozen['sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Frozen input differs: ' + name)
    return frozen


def metrics(prediction, actual):
    errors = np.asarray(prediction) - np.asarray(actual)
    return {'mae_pp': float(np.abs(errors).mean()),
            'rmse_pp': float(np.sqrt(np.square(errors).mean())),
            'mse_pp_squared': float(np.square(errors).mean()),
            'mean_error_pp': float(errors.mean())}


def block_interval(values, draws, block, seed):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(values), size=(draws, (len(values)+block-1)//block))
    indices = ((starts[:, :, None] + np.arange(block)) % len(values)).reshape(draws, -1)[:, :len(values)]
    samples = values[indices].mean(axis=1)
    return {'mean': float(values.mean()), 'conditional_95_percentile_interval':
            [float(x) for x in np.quantile(samples, [.025, .975])],
            'draws': draws, 'circular_block_months': block, 'seed': seed}


def verify_cell(row):
    path = ROOT / row['source_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != row['source_sha256']:
        raise RuntimeError('Source bytes differ: ' + str(path))
    cells = html.fromstring(path.read_bytes()).xpath(row['cell_xpath'])
    if len(cells) != 1 or float(cells[0].text_content().strip()) != row['value']:
        raise RuntimeError('Source numeric cell does not reconcile')


def run():
    frozen = verify_freeze()
    plan = read('reports/final_evaluation_plan.json')
    panel = read('data/processed/vintages.json')
    store = VintageStore(panel)
    forecasts = read('data/processed/final_forecasts.json')
    releases = {r['reference_month']: r for r in read('data/processed/releases.json')}
    model = read('artifacts/ar1.json')
    rows = []
    revised = []
    hindsight = []
    for row in forecasts:
        month = row['target_month']
        release = releases[month]
        cutoff = datetime.fromisoformat(row['forecast_cutoff'])
        publication = datetime.fromisoformat(row['target_publication'])
        assert cutoff < publication
        target_rows = [v for v in panel if v['reference_month'] == month
                       and v['release_reference_month'] == month and v['status'] == 'provisional']
        assert len(target_rows) == 1
        target = target_rows[0]
        assert target['published_at'] == release['published_at'] == row['target_publication']
        assert target['value'] == release['first_provisional']
        verify_cell(target)
        for key in ['lag_source', 'seasonal_source']:
            assert datetime.fromisoformat(row[key]['published_at']) <= cutoff
            verify_cell(row[key])
        true_lag = store.asof(shift_month(month, -1), cutoff)
        assert true_lag['value'] == row['forecasts']['persistence']
        assert abs(ar1_prediction(true_lag['value'], model)-row['forecasts']['ridge_ar1']) < 1e-12
        final_lag = [v for v in panel if v['reference_month'] == shift_month(month, -1)
                     and v['release_reference_month'] == month and v['status'] == 'final']
        assert len(final_lag) == 1
        final_lag = final_lag[0]
        assert datetime.fromisoformat(final_lag['published_at']) == publication > cutoff
        verify_cell(final_lag)
        contaminated = ar1_prediction(final_lag['value'], model)
        hindsight.append(contaminated)
        later = [v for v in panel if v['reference_month'] == month
                 and v['release_reference_month'] == shift_month(month, 1) and v['status'] == 'final']
        if later:
            assert len(later) == 1
            later_source = later[0]
            verify_cell(later_source)
            later_value = later_source['value']
        else:
            assert month == '2025-12'
            evidence = read('reports/base_break_evidence.json')
            manifest = read('data/source_manifest.json')
            document = next(v for v in manifest if v['url'] == evidence['source'])
            assert document['sha256'] == evidence['source_sha256']
            path = ROOT / document['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence['source_sha256']
            tree = html.fromstring(path.read_bytes())
            source_row = evidence['rows'][1]
            actual_cells = [' '.join(c.text_content().split()) for c in tree.xpath(source_row['xpath'])[0].xpath('./td|./th')]
            assert actual_cells == source_row['cells']
            later_value = float(actual_cells[-1])
            assert later_value == 1.33
            later_source = {'source_url': evidence['source'], 'source_sha256': evidence['source_sha256'],
                            'row_xpath': source_row['xpath'], 'base': 2012,
                            'published_at': '2026-02-12', 'status': 'final', 'value': later_value,
                            'auxiliary_not_in_frozen_vintage_panel': True}
        revised.append(later_value)
        actual = target['value']
        rows.append({**row, 'first_provisional_actual': actual, 'actual_source': target,
                     'errors_pp': {k: value-actual for k, value in row['forecasts'].items()},
                     'hindsight_lag_final': final_lag, 'hindsight_ar1_prediction': contaminated,
                     'hindsight_minus_honest_prediction_pp': contaminated-row['forecasts']['ridge_ar1'],
                     'later_final_target': later_value, 'later_final_source': later_source})
    assert len(rows) == 18
    assert [r['target_month'] for r in rows] == [shift_month('2024-07', i) for i in range(18)]
    actual = np.array([r['first_provisional_actual'] for r in rows])
    predictions = {k: np.array([r['forecasts'][k] for r in rows]) for k in rows[0]['forecasts']}
    baseline = frozen['selected_baseline']
    squared_difference = np.square(predictions['ridge_ar1']-actual)-np.square(predictions[baseline]-actual)
    primary = block_interval(squared_difference, plan['bootstrap_draws'], plan['circular_block_months'], plan['seed'])
    primary['contrast'] = plan['primary_contrast']
    primary['positive_favours'] = baseline
    result = {'target': frozen['target'], 'first_month': rows[0]['target_month'], 'last_month': rows[-1]['target_month'],
              'n_releases': len(rows), 'metrics': {k: metrics(v, actual) for k, v in predictions.items()},
              'selected_forecast_frozen_on_development': frozen['selected_forecast'],
              'primary_paired_squared_error': primary,
              'hindsight_diagnostic': {'metrics_same_frozen_ar1_with_unavailable_final_lag': metrics(hindsight, actual),
                  'mse_change_contaminated_minus_honest': float(np.mean(np.square(np.array(hindsight)-actual)-np.square(predictions['ridge_ar1']-actual))),
                  'changed_lag_releases': sum(abs(r['hindsight_minus_honest_prediction_pp']) > 1e-12 for r in rows),
                  'max_abs_forecast_change_pp': float(np.max(np.abs(np.array(hindsight)-predictions['ridge_ar1']))),
                  'warning': 'Later-final lag is published only with target, after cutoff. Not an available forecast.'},
              'later_final_target_diagnostic': {'metrics': {k: metrics(v, revised) for k, v in predictions.items()},
                  'changed_targets': int(np.count_nonzero(np.asarray(revised) != actual)),
                  'max_abs_target_revision_pp': float(np.max(np.abs(np.asarray(revised)-actual))),
                  'warning': 'Different estimand. Does not replace first-provisional primary evaluation.'},
              'error_decomposition': {year: {k: metrics(v[[r['target_month'].startswith(year) for r in rows]],
                                     actual[[r['target_month'].startswith(year) for r in rows]]) for k, v in predictions.items()}
                                     for year in ['2024', '2025']},
              'per_release': rows,
              'limitations': ['18 dependent releases; conditional bootstrap interval only.',
                  'Publication-dated reconstruction, not immutable archived snapshots.',
                  'Small training/development panel and fixed coefficients.',
                  'No new-base/current inflation forecast; no causal policy effect.',
                  'Hindsight does not necessarily improve measured performance.']}
    dump('reports/final.json', result)
    verify_freeze()
    dump('reports/final_verification.json', {'all_checks_passed': True, 'guarded_hashes_before_after': len(frozen['sha256']),
         'scored_first_release_targets': len(rows), 'source_cells_verified': 18*4+17,
         'last_old_base_final_auxiliary_row_verified': True, 'all_lags_before_cutoff': True,
         'all_hindsight_lags_after_cutoff': True, 'selection_changed_after_test': False,
         'seed': plan['seed'], 'public_release': False})
    print(json.dumps({k: v for k, v in result.items() if k not in ['per_release', 'limitations', 'error_decomposition']}, indent=2))


if __name__ == '__main__':
    run()
