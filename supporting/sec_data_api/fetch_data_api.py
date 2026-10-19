"""Ordinary access to the documented, distinct data.sec.gov public APIs.

The earlier www.sec.gov ticker-registry request was declined. This does not
retry it, change identity or use a proxy. Stop at any declined API request.
"""
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

event = json.load(open(os.environ['GITHUB_EVENT_PATH']))
if event['repository']['private'] or event['repository']['full_name'] != 'Prasanna-K-123/inflation-vintages':
    raise SystemExit('Only the reviewed public repository is permitted')
AGENT = 'PrasannaK-AcademicResearch/1.0 (+https://github.com/Prasanna-K-123)'
issuers = [('MSFT', 789019, 'MICROSOFT'), ('WMT', 104169, 'WALMART'),
           ('COST', 909832, 'COSTCO'), ('TGT', 27419, 'TARGET'),
           ('ADBE', 796343, 'ADOBE'), ('ORCL', 1341439, 'ORACLE'),
           ('INFY', 1067491, 'INFOSYS'), ('WIT', 1123799, 'WIPRO'),
           ('RDY', 1135951, 'REDDY')]
last_request = 0.0
for ticker, cik, name_word in issuers:
    for kind, url in [
        ('submissions', 'https://data.sec.gov/submissions/CIK' + str(cik).zfill(10) + '.json'),
        ('companyfacts', 'https://data.sec.gov/api/xbrl/companyfacts/CIK' + str(cik).zfill(10) + '.json')]:
        time.sleep(max(0, 1 - (time.monotonic() - last_request)))
        last_request = time.monotonic()
        try:
            request = urllib.request.Request(url, headers={'User-Agent': AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(30000001)
                headers = {k: response.headers.get(k) for k in ('Content-Type', 'Last-Modified', 'ETag', 'Date')}
        except urllib.error.HTTPError as error:
            print('PROJECTMAX_DATA_API_FAILURE ' + json.dumps({'url': url, 'http_status': error.code,
                'retried': False, 'identity_changed': False}), flush=True)
            raise SystemExit('API access declined; stop the campaign without retry') from None
        if len(raw) > 30000000:
            raise SystemExit('Source byte ceiling exceeded')
        data = json.loads(raw)
        if int(data.get('cik', -1)) != cik:
            raise SystemExit('Response CIK does not match the candidate issuer')
        actual_name = data.get('name', data.get('entityName', ''))
        if name_word not in actual_name.upper():
            raise SystemExit('Response name does not match the candidate issuer')
        if kind == 'submissions' and ticker not in data.get('tickers', []):
            raise SystemExit('Response ticker does not match the candidate issuer')
        packed = gzip.compress(raw, mtime=0)
        encoded = base64.b64encode(packed).decode('ascii')
        chunks = [encoded[i:i+3000] for i in range(0, len(encoded), 3000)]
        filename = ticker + '_' + kind + '.json'
        manifest = {'name': filename, 'url': url, 'issuer_name': actual_name,
            'cik': cik, 'ticker': ticker, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
            'original_bytes': len(raw), 'original_sha256': hashlib.sha256(raw).hexdigest(),
            'gzip_bytes': len(packed), 'gzip_sha256': hashlib.sha256(packed).hexdigest(),
            'chunks': len(chunks), 'server_metadata': headers}
        print('PROJECTMAX_SEC_MANIFEST ' + json.dumps(manifest, sort_keys=True), flush=True)
        for i, chunk in enumerate(chunks):
            print('PROJECTMAX_SEC_DATA ' + filename + ' ' + str(i) + ' ' + chunk, flush=True)
        print('PROJECTMAX_SEC_COMPLETE ' + filename + ' ' + manifest['original_sha256'], flush=True)
print('PROJECTMAX_DATA_API_CAMPAIGN_COMPLETE', flush=True)
