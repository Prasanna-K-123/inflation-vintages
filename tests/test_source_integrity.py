"""Regression checks for source provenance and header-based CPI selection."""
from datetime import datetime
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from lxml import html

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from acquire_sources import acquire
from build_vintages import headline_candidates
from audit_current_sources import retry_sources


def table(periods=None, sectors=('Rural', 'Urban', 'Combd.'), values=None):
    periods = periods or ('Jan. 2022 (Prov.)', 'Dec. 2021 (Final)', 'Jan. 2021')
    values = values or tuple(range(1, 10))
    return html.fromstring('<table><tr><th rowspan="2">Indices</th>'
        + ''.join(f'<th colspan="3">{period}</th>' for period in periods)
        + '</tr><tr>' + ''.join(f'<th>{sector}</th>' for _ in periods for sector in sectors)
        + '</tr><tr><td>CPI (General)</td>'
        + ''.join(f'<td>{value}</td>' for value in values) + '</tr></table>')


class HeaderChecks(unittest.TestCase):
    def test_reordered_period_and_sector_headers_select_semantic_cells(self):
        candidate = headline_candidates(table(), '2022-01')[0]
        self.assertEqual(candidate['numbers'], list(range(1, 10)))
        moved = table(('Jan. 2021', 'Jan. 2022 (Prov.)', 'Dec. 2021 (Final)'),
                      ('Combined', 'Urban', 'Rural'), (9, 8, 7, 3, 2, 1, 6, 5, 4))
        revised = headline_candidates(moved, '2022-01')[0]
        self.assertEqual(revised['numbers'], candidate['numbers'])
        self.assertEqual([float(moved.xpath(path)[0].text) for path in revised['numeric_cells']], list(range(1, 10)))

    def test_missing_duplicate_wrong_period_or_status_fail_closed(self):
        invalid = [table(sectors=('Rural', 'Urban', 'Urban')),
                   table(sectors=('Rural', 'Urban', 'Other')),
                   table(('Jan. 2022 (Prov.)', 'Nov. 2021 (Final)', 'Jan. 2021')),
                   table(('Jan. 2022 (Prov. Final)', 'Dec. 2021 (Final)', 'Jan. 2021')),
                   table(('Jan. 2022 (Prov.)', 'Dec. 2021', 'Jan. 2021 (Final)'))]
        for document in invalid:
            with self.subTest(document=html.tostring(document)), self.assertRaises(ValueError):
                headline_candidates(document, '2022-01')
        with self.assertRaises(ValueError):
            headline_candidates(table(), '2022-02')

    def test_prior_year_final_and_full_month_comma_headers(self):
        result = headline_candidates(table(('January, 2022 (Prov.)', 'December, 2021 (Final)', 'January,2021 (Final)')), '2022-01')
        self.assertEqual(result[0]['numbers'][2], 3)


class AcquisitionChecks(unittest.TestCase):
    def setup_manifest(self, directory, payload=b'original official bytes'):
        root = Path(directory)
        (root / 'data').mkdir()
        manifest = [{'reference_month': '2022-01', 'url': 'https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1798312',
                     'file': 'data/raw/source_1798312.html', 'bytes': len(payload),
                     'sha256': hashlib.sha256(payload).hexdigest(), 'retrieved_utc_date': '2026-10-17'}]
        path = root / 'data/source_manifest.json'
        path.write_text(json.dumps(manifest))
        return root, path, path.read_bytes()

    def test_network_receipt_is_current_and_original_manifest_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, original = self.setup_manifest(temporary)
            with patch('acquire_sources.urllib.request.urlopen', return_value=BytesIO(b'original official bytes')):
                result = acquire(root)
            self.assertTrue(result['all_verified'])
            self.assertEqual(manifest.read_bytes(), original)
            self.assertGreaterEqual(datetime.fromisoformat(result['sources'][0]['retrieved_at_utc']), datetime.fromisoformat(result['started_at_utc']))
            self.assertEqual((root / 'data/raw/source_1798312.html').read_bytes(), b'original official bytes')
            with patch('acquire_sources.urllib.request.urlopen', side_effect=AssertionError('No redownload')):
                cached = acquire(root)
            self.assertTrue(cached['all_verified'])
            self.assertNotIn('retrieved_at_utc', cached['sources'][0])
            self.assertEqual(cached['sources'][0]['origin'], 'existing_cache')

    def test_changed_bytes_fail_without_adoption_or_cache_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, manifest, original = self.setup_manifest(temporary)
            with patch('acquire_sources.urllib.request.urlopen', return_value=BytesIO(b'changed bytes')):
                result = acquire(root)
            self.assertFalse(result['all_verified'])
            target = root / 'data/raw/source_1798312.html'
            self.assertFalse(target.exists())
            target.parent.mkdir(); target.write_bytes(b'bad existing cache')
            with patch('acquire_sources.urllib.request.urlopen', side_effect=AssertionError('No redownload')):
                result = acquire(root)
            self.assertFalse(result['all_verified'])
            self.assertEqual(target.read_bytes(), b'bad existing cache')
            self.assertEqual(manifest.read_bytes(), original)
            with self.assertRaises(ValueError):
                acquire(root, receipt=manifest)


class RetryChecks(unittest.TestCase):
    def test_only_failed_sources_are_retried_with_provenance_preserved(self):
        sources = [{'reference_month': month, 'url': 'https://www.pib.gov.in/' + month, 'sha256': month}
                   for month in ('2025-02', '2025-03')]
        rows = [dict(reference_month=source['reference_month'], url=source['url'],
                     historical_sha256=source['sha256'], status=status)
                for source, status in zip(sources, ('matched', 'failed'))]
        rows[0].update(retrieved_at_utc='2026-10-26T00:00:00+00:00', current_sha256='current',
                       nine_cells_matched=True, header_period_sector_mapping_verified=True,
                       published_at='2025-03-12T16:00:00+05:30')
        prior = {'historical_manifest_sha256': 'manifest', 'historical_manifest_unchanged': True, 'sources': rows}
        before = json.dumps(prior, sort_keys=True)
        previous, pending = retry_sources(prior, sources, 'manifest')
        self.assertEqual(pending, [sources[1]])
        self.assertEqual(previous['2025-02']['retrieved_at_utc'], '2026-10-26T00:00:00+00:00')
        self.assertEqual(json.dumps(prior, sort_keys=True), before)
        for broken in ('manifest', 'url', 'duplicate', 'missing_provenance', 'missing_semantic_evidence'):
            corrupt = json.loads(before)
            if broken == 'manifest': corrupt['historical_manifest_sha256'] = 'other'
            elif broken == 'url': corrupt['sources'][0]['url'] = 'https://other.example/'
            elif broken == 'duplicate': corrupt['sources'].append(corrupt['sources'][0])
            elif broken == 'missing_provenance': del corrupt['sources'][0]['retrieved_at_utc']
            else: del corrupt['sources'][0]['nine_cells_matched']
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                retry_sources(corrupt, sources, 'manifest')


if __name__ == '__main__':
    unittest.main()
