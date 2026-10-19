"""Acquire three official issuer-origin reference documents, without retries.

These references do not substitute for missing SEC structured inputs, change
the experiment or establish a completed source gate. No extraction is scored.
"""
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

event=json.load(open(os.environ['GITHUB_EVENT_PATH']))
if event['repository']['private'] or event['repository']['full_name']!='Prasanna-K-123/inflation-vintages':
    raise SystemExit('Only the reviewed public standard-runner repository is permitted')
sources=[
    (2023,'https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY23Q4_10K',
     'https://www.microsoft.com/investor/reports/ar23/download-center/index.html'),
    (2024,'https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY24Q4_10K',
     'https://www.microsoft.com/investor/reports/ar24/download-center/index.html'),
    (2025,'https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY25q4_10K',
     'https://www.microsoft.com/investor/reports/ar25/download-center/index.html')]
agent='PrasannaK-AcademicResearch/1.0 (+https://github.com/Prasanna-K-123)'
for year,url,origin in sources:
    time.sleep(1)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':agent}),timeout=30) as response:
            final_url=response.geturl()
            parts=urllib.parse.urlsplit(final_url)
            if parts.scheme!='https' or not (parts.hostname or '').endswith('.microsoft.com'):
                raise SystemExit('Unexpected source redirect; stop')
            raw=response.read(10000001)
            headers={key:response.headers.get(key) for key in ('Content-Type','Last-Modified','ETag','Date')}
    except urllib.error.HTTPError as error:
        print('PROJECTMAX_REFERENCE_ACCESS_FAILURE '+json.dumps({'url':url,'http_status':error.code,'retried':False}),flush=True)
        raise SystemExit('Issuer source access declined; no retry or identity change') from None
    if len(raw)>10000000:raise SystemExit('Source byte ceiling exceeded')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if sum(x.file_size for x in archive.infolist())>100000000:raise SystemExit('Unexpected decompressed size')
        if '[Content_Types].xml' not in archive.namelist() or 'word/document.xml' not in archive.namelist():
            raise SystemExit('Expected actual DOCX bytes, not an error page')
        if archive.testzip() is not None:raise SystemExit('DOCX CRC failure')
    filename='MSFT_FY'+str(year)+'_10K_issuer_reference.docx'
    packed=gzip.compress(raw,mtime=0);encoded=base64.b64encode(packed).decode('ascii')
    chunks=[encoded[i:i+3000] for i in range(0,len(encoded),3000)]
    manifest={'name':filename,'candidate_issuer':'Microsoft Corporation','candidate_fiscal_year':year,
        'official_download_center':origin,'url':url,'final_url':final_url,
        'retrieved_utc':datetime.now(timezone.utc).isoformat(),'original_bytes':len(raw),
        'original_sha256':hashlib.sha256(raw).hexdigest(),'gzip_bytes':len(packed),
        'gzip_sha256':hashlib.sha256(packed).hexdigest(),'chunks':len(chunks),
        'server_metadata':headers,'docx_crc_passed':True,
        'original_edgar_accession_verified':False,'structured_companyfacts_acquired':False,
        'extraction_scores_computed':False,'source_gate_A_accepted':False}
    print('PROJECTMAX_REFERENCE_MANIFEST '+json.dumps(manifest,sort_keys=True),flush=True)
    for i,chunk in enumerate(chunks):
        print('PROJECTMAX_REFERENCE_DATA '+filename+' '+str(i)+' '+chunk,flush=True)
    print('PROJECTMAX_REFERENCE_COMPLETE '+filename+' '+manifest['original_sha256'],flush=True)
print('PROJECTMAX_REFERENCE_CAMPAIGN_COMPLETE',flush=True)
