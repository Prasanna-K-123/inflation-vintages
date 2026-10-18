"""Build the self-contained explorer from sealed scientific evidence."""
import hashlib,json
from export_reports import export_reports
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUTS=["reports/final.json"]
def read(name):return json.loads((ROOT/name).read_text())
def guard():
    frozen=read('reports/model_freeze.json')
    for name,digest in frozen['sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Frozen input changed: '+name

def run():
    guard()
    export_reports()
    data=read('reports/final.json')
    encoded=json.dumps(data,separators=(',',':'),sort_keys=True,allow_nan=False).replace('<','\\u003c')
    template=(ROOT/'docs/demo.template.html').read_text()
    style=(ROOT/'docs/style.css').read_text()
    assert template.count('__DATA__')==1 and template.count('__STYLE__')==1
    html=template.replace('__DATA__',encoded).replace('__STYLE__',style)
    assert '__DATA__' not in html and '__STYLE__' not in html
    (ROOT/'docs/index.html').write_text(html)
    guard()
    manifest={'html_sha256':hashlib.sha256(html.encode()).hexdigest(),'scientific_inputs_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},'self_contained':True,'models_refitted':False,'browser_verified':False,'public_release_complete':False}
    (ROOT/'reports/demo_build.json').write_text(json.dumps(manifest,indent=2)+chr(10))
    print('Built self-contained explorer; scientific seals unchanged; actual-browser verification open.')

if __name__=='__main__':run()

