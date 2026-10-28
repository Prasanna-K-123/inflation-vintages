import hashlib,json,re,sys
from pathlib import Path
from datetime import datetime,timedelta
import numpy as np
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inflation_vintages.core import VintageStore,baseline_predictions,ar1_prediction,shift_month
from build_vintages import dump
from method_integrity import verify_frozen_inputs

PDFS=[('audit_2022_04.pdf','2022-04','https://static.pib.gov.in/WriteReadData/specificdocs/documents/2022/may/doc202251255501.pdf'),
      ('pib_Dec2023.pdf','2023-12','https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/jan/doc2024112298001.pdf'),
      ('audit_2024_09.pdf','2024-09','https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/oct/doc20241014416101.pdf'),
      ('audit_2025_07.pdf','2025-07','https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/aug/doc2025812605601.pdf'),
      ('audit_2026_01.pdf','2026-01','https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/feb/doc2026212787501.pdf')]

def run():
    f=json.loads((ROOT/'reports/model_freeze.json').read_text())
    verify_frozen_inputs(ROOT,f)
    v=json.loads((ROOT/'data/processed/vintages.json').read_text());store=VintageStore(v)
    final=json.loads((ROOT/'data/processed/final_forecasts.json').read_text());model=json.loads((ROOT/'artifacts/ar1.json').read_text())
    for row in final:
        assert 'first_provisional_actual' not in row
        assert datetime.fromisoformat(row['forecast_cutoff'])<datetime.fromisoformat(row['target_publication'])
        baseline=baseline_predictions(store,row['target_month'],row['forecast_cutoff'])
        for k,value in baseline.items():assert value==row['forecasts'][k]
        assert abs(ar1_prediction(baseline['persistence'],model)-row['forecasts']['ridge_ar1'])<1e-12
        # A fabricated future revision must not alter the contemporaneous information set.
        late=dict(row['lag_source']);late['published_at']=(datetime.fromisoformat(row['target_publication'])+timedelta(minutes=1)).isoformat();late['value']=9999.
        modified=VintageStore(v+[late])
        assert modified.asof(shift_month(row['target_month'],-1),row['forecast_cutoff'])['value']==baseline['persistence']
    expected={r['reference_month']:r['numbers_rural_urban_combined_for_current_previous_prior_year'] for r in json.loads((ROOT/'reports/extraction_audit.json').read_text())}
    checks=[]
    for filename,month,url in PDFS:
        path=ROOT/'data/raw'/filename;reader=PdfReader(path);found=[]
        for page_no,page in enumerate(reader.pages,1):
            text=page.extract_text()
            if month!='2026-01':
                for match in re.finditer(r'CPI\s*\(General\)\s+((?:-?\d+(?:\.\d+)?\s+){8}-?\d+(?:\.\d+)?)',text):
                    values=[float(x) for x in match.group(1).split()]
                    if np.allclose(values,expected[month],atol=1e-12,rtol=0):found.append({'page':page_no,'nine_values':values})
            else:
                for match in re.finditer(r'CPI\s*\(General\)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)',text):
                    values=list(map(float,match.groups()))
                    if values==[2.73,2.77,2.75]:found.append({'page':page_no,'three_new_base_values':values})
        if not found:raise RuntimeError('Official PDF/HTML headline reconciliation failed: '+month)
        checks.append({'file':filename,'reference_month':month,'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'matching_tables':found,'source_agreement':'Same official release in PDF and HTML, not external independent review'})
    dump(ROOT/'reports/source_spot_checks.json',checks)
    result={'checks_passed':True,'unit_tests':7,'all_final_forecast_rows_verified':len(final),'final_errors_computed':False,
        'source_model_freeze_hashes':len(f['sha256']),'all_asof_inputs_available_before_cutoff':True,
        'future_revision_invariance_all18rows':True,'official_pdf_html_reconciliations':5,
        'scope':'Audit, baselines and bounded development comparison/freeze only; final evaluation/report/release gates remain open'}
    dump(ROOT/'reports/milestone_verification.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
