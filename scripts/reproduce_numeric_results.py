"""Reproduce public numeric evidence without claiming a raw-document re-audit."""
from datetime import datetime, timedelta
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from inflation_vintages.core import VintageStore,shift_month,baseline_predictions,ar1_prediction
from evaluate_final import metrics,block_interval
from method_integrity import verify_frozen_inputs

def read(name):return json.loads((ROOT/name).read_text())

if __name__=='__main__':
    seal=read('reports/model_freeze.json')
    checked=verify_frozen_inputs(ROOT,seal,skip=('artifacts/ar1.json',))
    panel=read('data/processed/vintages.json');store=VintageStore(panel)
    releases={r['reference_month']:r for r in read('data/processed/releases.json')}
    model=read('reports/development.json')['model']
    reconstructed_model_bytes=(json.dumps(model,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    assert hashlib.sha256(reconstructed_model_bytes).hexdigest()==seal['sha256']['artifacts/ar1.json']
    # Reconstruct the declared training fit through independent 1D ridge algebra.
    xx=[];yy=[]
    for month,r in sorted(releases.items()):
        if '2022-02'<=month<='2023-12':
            prev=releases[shift_month(month,-1)]
            cutoff=datetime.fromisoformat(prev['published_at'])+timedelta(minutes=1)
            assert cutoff<datetime.fromisoformat(r['published_at'])
            xx.append(store.asof(prev['reference_month'],cutoff)['value'])
            yy.append(r['first_provisional'])
    x=np.asarray(xx);y=np.asarray(yy);mean=float(x.mean());scale=float(x.std(ddof=0))
    z=(x-mean)/scale;centered=z-z.mean()
    coef=float(np.dot(centered,y-y.mean())/(np.dot(centered,centered)+1.))
    intercept=float(y.mean()-coef*z.mean())
    differences={k:abs(value-model[k]) for k,value in [
        ('feature_mean',mean),('feature_scale',scale),
        ('coefficient_standardized',coef),('intercept_standardized',intercept)]}
    assert len(y)==23 and max(differences.values())<1e-12
    forecasts=read('data/processed/final_forecasts.json');expected=read('reports/final.json')
    actual=[];predictions={k:[] for k in forecasts[0]['forecasts']};hindsight=[];later=[]
    for row in forecasts:
        month=row['target_month'];cutoff=datetime.fromisoformat(row['forecast_cutoff'])
        assert cutoff<datetime.fromisoformat(row['target_publication'])
        values=baseline_predictions(store,month,cutoff)
        values['ridge_ar1']=ar1_prediction(values['persistence'],model)
        for key,value in values.items():
            assert abs(value-row['forecasts'][key])<1e-12
            predictions[key].append(value)
        target=next(v for v in panel if v['reference_month']==month and v['release_reference_month']==month and v['status']=='provisional')
        assert target['published_at']==row['target_publication']
        actual.append(target['value'])
        final_lag=next(v for v in panel if v['reference_month']==shift_month(month,-1) and v['release_reference_month']==month and v['status']=='final')
        assert datetime.fromisoformat(final_lag['published_at'])>cutoff
        hindsight.append(ar1_prediction(final_lag['value'],model))
        candidates=[v for v in panel if v['reference_month']==month and v['release_reference_month']==shift_month(month,1) and v['status']=='final']
        if candidates:later.append(candidates[0]['value'])
        else:
            assert month=='2025-12'
            later.append(float(read('reports/base_break_evidence.json')['rows'][1]['cells'][-1]))
    actual=np.array(actual);predictions={k:np.array(v) for k,v in predictions.items()}
    recomputed={k:metrics(v,actual) for k,v in predictions.items()}
    for key,values in recomputed.items():
        for metric,value in values.items():assert abs(value-expected['metrics'][key][metric])<1e-12
    later_metrics={k:metrics(v,later) for k,v in predictions.items()}
    for key,values in later_metrics.items():
        for metric,value in values.items():assert abs(value-expected['later_final_target_diagnostic']['metrics'][key][metric])<1e-12
    plan=read('reports/final_evaluation_plan.json');base=seal['selected_baseline']
    delta=(predictions['ridge_ar1']-actual)**2-(predictions[base]-actual)**2
    interval=block_interval(delta,plan['bootstrap_draws'],plan['circular_block_months'],plan['seed'])
    for key,value in interval.items():assert value==expected['primary_paired_squared_error'][key]
    hmetrics=metrics(hindsight,actual)
    for key,value in hmetrics.items():assert abs(value-expected['hindsight_diagnostic']['metrics_same_frozen_ar1_with_unavailable_final_lag'][key])<1e-12
    result={'passed':True,'published_frozen_hashes_checked':len(checked),'reconstructed_model_artifact_hash_matches':True,'training_pairs':len(y),
            'independent_training_coefficient_absolute_differences':differences,
            'frozen_final_forecasts_reconstructed':len(forecasts)*len(predictions),
            'primary_metrics':recomputed,'later_final_metrics':later_metrics,
            'primary_paired_interval':interval,'hindsight_metrics':hmetrics,
            'raw_document_hash_and_XPath_reaudit_performed':False,
            'method_revision':'26 October header parser and acquisition correction; original builder retained for historical freeze verification; this command does not run source parsing.',
            'scope':'Numeric reproduction from the published frozen vintage table and publication metadata. This does not reacquire or independently re-audit original source documents. Full source-cell audit remains evaluate_final.py with pinned raw bytes.'}
    (ROOT/'reports/numeric_reproduction.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
