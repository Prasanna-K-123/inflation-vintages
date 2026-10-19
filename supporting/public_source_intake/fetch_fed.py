"""One public-source download; emits a hash-checked transport in free job logs."""
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
import urllib.request

event = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
if event["repository"]["private"] or event["repository"]["full_name"] != "Prasanna-K-123/inflation-vintages":
    raise SystemExit("Only the reviewed public repository is allowed")
url = "https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv"
request = urllib.request.Request(url, headers={
    "User-Agent": "PrasannaK-AcademicResearch/1.0 (+https://github.com/Prasanna-K-123)"
})
with urllib.request.urlopen(request, timeout=45) as response:
    raw = response.read(60000001)
    metadata = {key:response.headers.get(key) for key in ("Content-Type","Last-Modified","ETag","Date")}
if len(raw) > 60000000 or b"Date," not in raw or b"SVENY01" not in raw:
    raise SystemExit("Source byte limit or expected GSW CSV header failed")
packed = gzip.compress(raw, mtime=0)
encoded = base64.b64encode(packed).decode("ascii")
chunks = [encoded[i:i+3000] for i in range(0,len(encoded),3000)]
manifest = {"name":"feds200628.csv","url":url,"retrieved_utc":datetime.now(timezone.utc).isoformat(),
    "original_bytes":len(raw),"original_sha256":hashlib.sha256(raw).hexdigest(),
    "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
    "chunks":len(chunks),"server_metadata":metadata,"payment_required":False,
    "artifact_storage_used":False,"cache_used":False,"provider_calls":0,"outreach_emails":0}
print("PROJECTMAX_MANIFEST "+json.dumps(manifest,sort_keys=True), flush=True)
for index,chunk in enumerate(chunks):
    print("PROJECTMAX_DATA "+str(index)+" "+chunk, flush=True)
print("PROJECTMAX_COMPLETE "+manifest["original_sha256"], flush=True)
