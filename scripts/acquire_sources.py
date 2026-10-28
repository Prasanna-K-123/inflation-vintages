"""Reacquire pinned official bytes; never rewrite the historical manifest."""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def acquire(root=ROOT, *, receipt=None, workers=4):
    root = Path(root)
    manifest_path = root / 'data/source_manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    started = datetime.now(timezone.utc).isoformat()
    receipt = Path(receipt) if receipt else root / 'reports/acquisition' / (started.replace(':', '-') + '.json')
    if receipt.resolve() == manifest_path.resolve() or receipt.exists():
        raise ValueError('Acquisition receipt must be a new file, not the pinned manifest')

    def get(source):
        item = {'reference_month': source['reference_month'], 'url': source['url'],
                'expected_sha256': source['sha256'], 'expected_bytes': source['bytes'],
                'checked_at_utc': datetime.now(timezone.utc).isoformat()}
        try:
            target = root / source['file']
            if not target.resolve().is_relative_to((root / 'data/raw').resolve()):
                raise ValueError('Manifest cache path is outside data/raw')
            if not source['url'].startswith('https://www.pib.gov.in/'):
                raise ValueError('Source is outside the pinned official PIB host')
            cached = target.exists()
            item['origin'] = 'existing_cache' if cached else 'network'
            if cached:
                raw = target.read_bytes()
            else:
                with urllib.request.urlopen(source['url'], timeout=30) as response:
                    raw = response.read()
                item['retrieved_at_utc'] = datetime.now(timezone.utc).isoformat()
            item.update(observed_sha256=hashlib.sha256(raw).hexdigest(), observed_bytes=len(raw))
            if item['observed_sha256'] != source['sha256'] or len(raw) != source['bytes']:
                raise ValueError('Source bytes differ from the frozen manifest; not accepted')
            if not cached:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(raw)
            item['status'] = 'verified'
        except Exception as error:
            item.update(status='failed', error=type(error).__name__ + ': ' + str(error))
        return item

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(get, manifest))
    unchanged = manifest_path.read_bytes() == manifest_bytes
    result = {'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
              'pinned_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
              'pinned_manifest_unchanged': unchanged,
              'all_verified': unchanged and all(x['status'] == 'verified' for x in results),
              'sources': results,
              'scope': 'Original retrieval metadata is preserved. Cache checks are not new retrievals; changed bytes are rejected, not adopted as historical vintages.'}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, help='New JSON receipt path; default reports/acquisition/current-UTC.json')
    args = parser.parse_args()
    result = acquire(receipt=args.receipt)
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}, indent=2))
    raise SystemExit(0 if result['all_verified'] else 1)
