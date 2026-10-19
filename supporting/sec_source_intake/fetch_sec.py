"""Free SEC public JSON intake; one declared client, no retries or keys."""
import base64
from datetime import datetime, timezone
import gzip, hashlib, json, os, time
import urllib.error, urllib.request

event=json.load(open(os.environ["GITHUB_EVENT_PATH"]))
if event["repository"]["private"] or event["repository"]["full_name"]!="Prasanna-K-123/inflation-vintages":
    raise SystemExit("Only the reviewed public repository is permitted")
AGENT="PrasannaK-AcademicResearch/1.0 (+https://github.com/Prasanna-K-123)"
last_request=0.
def get(url):
    global last_request
    time.sleep(max(0,1-(time.monotonic()-last_request)))
    last_request=time.monotonic()
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":AGENT}),timeout=30) as response:
            raw=response.read(30000001)
            metadata={key:response.headers.get(key) for key in ("Content-Type","Last-Modified","ETag","Date")}
    except urllib.error.HTTPError as error:
        print("PROJECTMAX_ACCESS_FAILURE "+json.dumps({"url":url,"http_status":error.code,"retried":False}),flush=True)
        raise SystemExit("Public source access declined; stop without retry or alternate identity") from None
    if len(raw)>30000000:raise SystemExit("Source byte ceiling exceeded")
    return raw,metadata
def emit(name,url,raw,metadata):
    packed=gzip.compress(raw,mtime=0);encoded=base64.b64encode(packed).decode("ascii")
    chunks=[encoded[i:i+3000] for i in range(0,len(encoded),3000)]
    manifest={"name":name,"url":url,"retrieved_utc":datetime.now(timezone.utc).isoformat(),
        "original_bytes":len(raw),"original_sha256":hashlib.sha256(raw).hexdigest(),
        "gzip_bytes":len(packed),"gzip_sha256":hashlib.sha256(packed).hexdigest(),
        "chunks":len(chunks),"server_metadata":metadata}
    print("PROJECTMAX_SEC_MANIFEST "+json.dumps(manifest,sort_keys=True),flush=True)
    for i,chunk in enumerate(chunks):print("PROJECTMAX_SEC_DATA "+name+" "+str(i)+" "+chunk,flush=True)
    print("PROJECTMAX_SEC_COMPLETE "+name+" "+manifest["original_sha256"],flush=True)

url="https://www.sec.gov/files/company_tickers.json"
raw,headers=get(url);registry=json.loads(raw);emit("company_tickers.json",url,raw,headers)
wanted={"WMT":"WALMART","COST":"COSTCO","TGT":"TARGET","MSFT":"MICROSOFT","ADBE":"ADOBE","ORCL":"ORACLE","INFY":"INFOSYS","WIT":"WIPRO","RDY":"REDDY"}
identities={}
for ticker,word in wanted.items():
    found=[v for v in registry.values() if v.get("ticker")==ticker]
    if len(found)!=1 or word not in found[0]["title"].upper() or type(found[0]["cik_str"]) is not int:
        raise SystemExit("Source identity ambiguity: "+ticker)
    identities[ticker]=found[0]
print("PROJECTMAX_SEC_IDENTITIES "+json.dumps(identities,sort_keys=True),flush=True)
for ticker,identity in identities.items():
    cik=identity["cik_str"]
    for kind,url in [
        ("companyfacts","https://data.sec.gov/api/xbrl/companyfacts/CIK"+str(cik).zfill(10)+".json"),
        ("submissions","https://data.sec.gov/submissions/CIK"+str(cik).zfill(10)+".json")]:
        raw,headers=get(url);data=json.loads(raw)
        if int(data.get("cik",-1))!=cik:raise SystemExit("Wrong source identity")
        emit(ticker+"_"+kind+".json",url,raw,headers)
print("PROJECTMAX_SEC_CAMPAIGN_COMPLETE",flush=True)
