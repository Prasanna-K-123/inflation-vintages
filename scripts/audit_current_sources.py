"""Compare current official pages with historical facts without replacing vintages.

Dynamic PIB HTML can change byte hashes while retaining statistical cells.
This deliberately separate audit never accepts new bytes into the frozen
cache or rewrites the old manifest, model, data, forecasts or research results.
"""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
from lxml import html
from build_vintages import headline_candidates, normal, publication

ROOT = Path(__file__).resolve().parents[1]


def retry_sources(prior, sources, manifest_sha256):
    """Validate saved source identities before carrying forward past checks."""
    if prior.get('historical_manifest_sha256') != manifest_sha256 or not prior.get('historical_manifest_unchanged'):
        raise ValueError('Prior receipt does not verify the current frozen manifest')
    rows = prior.get('sources', [])
    by_month = {row['reference_month']: row for row in rows}
    if len(by_month) != len(rows) or set(by_month) != {row['reference_month'] for row in sources}:
        raise ValueError('Prior receipt has missing, extra or duplicate sources')
    for source in sources:
        row = by_month[source['reference_month']]
        if (row.get('url'), row.get('historical_sha256')) != (source['url'], source['sha256']):
            raise ValueError('Prior receipt source identity changed')
        if row.get('status') not in ('matched', 'failed'):
            raise ValueError('Unknown prior source status')
        if row['status'] == 'matched' and (not row.get('retrieved_at_utc') or not row.get('current_sha256')):
            raise ValueError('Prior matched source lacks retrieval provenance')
        if row['status'] == 'matched':
            evidence = (row.get('base_break_rows_matched') == 4 if source['reference_month'].endswith('_new_base')
                        else row.get('nine_cells_matched') is True and row.get('header_period_sector_mapping_verified') is True)
            if not evidence or not row.get('published_at'):
                raise ValueError('Prior matched source lacks semantic or publication evidence')
    pending = [source for source in sources if by_month[source['reference_month']]['status'] == 'failed']
    if not pending:
        raise ValueError('Prior receipt has no failed sources to retry')
    return by_month, pending


def run(cache, output, retry_from=None):
    cache, output = Path(cache), Path(output)
    if cache.exists() or output.exists():
        raise ValueError('Use a new cache directory and new receipt path')
    manifest_path = ROOT / 'data/source_manifest.json'
    original_manifest = manifest_path.read_bytes()
    sources = json.loads(original_manifest)
    previous, pending, prior_bytes = {}, sources, None
    if retry_from is not None:
        prior_bytes = Path(retry_from).read_bytes()
        previous, pending = retry_sources(json.loads(prior_bytes), sources, hashlib.sha256(original_manifest).hexdigest())
    cache.mkdir(parents=True)
    expected = {row['reference_month']: row for row in json.loads((ROOT / 'reports/extraction_audit.json').read_text())}
    releases = {row['reference_month']: row for row in json.loads((ROOT / 'data/processed/releases.json').read_text())}
    break_evidence = json.loads((ROOT / 'reports/base_break_evidence.json').read_text())
    base_break = json.loads((ROOT / 'reports/base_break.json').read_text())
    started = datetime.now(timezone.utc).isoformat()

    def one(source):
        month = source['reference_month']
        result = {'reference_month': month, 'url': source['url'], 'historical_sha256': source['sha256']}
        try:
            if not source['url'].startswith('https://www.pib.gov.in/'):
                raise ValueError('Only pinned official PIB URLs may be inspected')
            with urllib.request.urlopen(source['url'], timeout=45) as response:
                raw = response.read()
            result.update(retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                          current_sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            result['matches_historical_bytes'] = result['current_sha256'] == source['sha256']
            (cache / f'{month}.html').write_bytes(raw)
            tree = html.fromstring(raw)
            result['published_at'] = publication(tree)
            if month.endswith('_new_base'):
                for row in break_evidence['rows']:
                    matches = tree.xpath(row['xpath'])
                    if len(matches) != 1 or [normal(x) for x in matches[0].xpath('./td|./th')] != row['cells']:
                        raise ValueError('Base-break evidence row changed')
                if result['published_at'] != base_break['published_at']:
                    raise ValueError('Base-break publication metadata changed')
                result['base_break_rows_matched'] = len(break_evidence['rows'])
            else:
                candidates = headline_candidates(tree, month)
                if not candidates or any(row['numbers'] != expected[month]['numbers_rural_urban_combined_for_current_previous_prior_year'] for row in candidates):
                    raise ValueError('Current official CPI cells differ from historical facts')
                if result['published_at'] != releases[month]['published_at']:
                    raise ValueError('Publication metadata changed')
                result.update(equivalent_tables=len(candidates), nine_cells_matched=True,
                              header_period_sector_mapping_verified=True,
                              current_row_xpaths=[row['row_xpath'] for row in candidates])
            result['status'] = 'matched'
        except Exception as error:
            result.update(status='failed', error=type(error).__name__ + ': ' + str(error))
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        retried = {row['reference_month']: row for row in pool.map(one, pending)}
    results = [retried.get(source['reference_month'], previous.get(source['reference_month'])) for source in sources]
    unchanged = manifest_path.read_bytes() == original_manifest
    result = {'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'all_matched': unchanged and len(results) == 49 and all(row['status'] == 'matched' for row in results),
              'historical_manifest_unchanged': unchanged,
              'historical_manifest_sha256': hashlib.sha256(original_manifest).hexdigest(),
              'old_base_release_count': sum(row.get('nine_cells_matched', False) for row in results),
              'historical_byte_matches': sum(row.get('matches_historical_bytes', False) for row in results),
              'scope': 'Current official-page statistical cells, semantic headers and publication metadata compared with the published historical table. New retrievals are dated now; this is not original-byte or contemporaneous historical-snapshot reconstruction. No original scientific inputs changed.',
              'sources': results}
    if prior_bytes is not None:
        result['retry'] = {'prior_receipt_sha256': hashlib.sha256(prior_bytes).hexdigest(),
                           'prior_receipt': str(retry_from),
                           'retried_months': [source['reference_month'] for source in pending],
                           'carried_forward_count': len(sources) - len(pending),
                           'scope': 'Only prior failed sources were retrieved in this execution. Other rows retain their original retrieval dates and evidence; they were not fetched again.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', required=True, help='New private raw-page directory')
    parser.add_argument('--output', required=True, help='New JSON verification receipt')
    parser.add_argument('--retry-from', help='Prior receipt; re-fetch only failed sources after checking frozen identities')
    args = parser.parse_args()
    result = run(args.cache, args.output, args.retry_from)
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}, indent=2))
    raise SystemExit(0 if result['all_matched'] else 1)
