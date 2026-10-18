import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timedelta
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inflation_vintages.core import VintageStore,shift_month,baseline_predictions,ar1_prediction
from build_vintages import dump

def run():
    records=json.loads((ROOT/'data/processed/vintages.json').read_text());releases=json.loads((ROOT/'data/processed/releases.json').read_text())
    store=VintageStore(records);by_month={r['reference_month']:r for r in releases}
    paths=['PROTOCOL.md','src/inflation_vintages/core.py','scripts/build_vintages.py','scripts/train_and_freeze.py',
           'data/processed/vintages.json','data/processed/releases.json','data/source_manifest.json']
    sha={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    freeze=ROOT/'reports/protocol_freeze.json'
    if freeze.exists():
        if json.loads(freeze.read_text())['sha256']!=sha:raise RuntimeError('Frozen study changed')
    else:dump(freeze,{'sha256':sha,'status':'Frozen before model fit/development evaluation; final errors not computed'})
    # Training targets and predecessor first-release values all precede the first development forecast cutoff.
    train=[r for r in releases if '2022-02'<=r['reference_month']<='2023-12']
    xx=[];yy=[];training_rows=[]
    for r in train:
        prev=by_month[shift_month(r['reference_month'],-1)];cut=datetime.fromisoformat(prev['published_at'])+timedelta(minutes=1)
        if datetime.fromisoformat(r['published_at'])<=cut:raise ValueError('Training target unavailable ordering')
        x=store.asof(prev['reference_month'],cut)['value'];xx.append(x);yy.append(r['first_provisional'])
        training_rows.append({'target_month':r['reference_month'],'cutoff':cut.isoformat(),'x_last_release':x,'first_target':r['first_provisional']})
    x=np.array(xx)[:,None];y=np.array(yy);scaler=StandardScaler();z=scaler.fit_transform(x)
    fitted=Ridge(alpha=1.,fit_intercept=True).fit(z,y)
    model={'type':'Ridge AR1','alpha':1.,'feature_mean':float(scaler.mean_[0]),'feature_scale':float(scaler.scale_[0]),
           'coefficient_standardized':float(fitted.coef_[0]),'intercept_standardized':float(fitted.intercept_),
           'training_pairs':len(y),'training_target_end':'2023-12'}
    # Independent one-dimensional penalized closed form, including training-only standardization.
    centered=z[:,0]-z[:,0].mean();coef=float(np.dot(centered,y-y.mean())/(np.dot(centered,centered)+1))
    intercept=float(y.mean()-coef*z[:,0].mean())
    if abs(coef-model['coefficient_standardized'])>1e-12 or abs(intercept-model['intercept_standardized'])>1e-12:raise RuntimeError('Ridge closed-form mismatch')
    all_forecasts=[]
    for r in releases:
        month=r['reference_month']
        if month<'2024-01':continue
        previous=by_month[shift_month(month,-1)];cut=datetime.fromisoformat(previous['published_at'])+timedelta(minutes=1)
        if datetime.fromisoformat(r['published_at'])<=cut:raise RuntimeError('Target release already known at cutoff')
        b=baseline_predictions(store,month,cut);b['ridge_ar1']=ar1_prediction(b['persistence'],model)
        row={'target_month':month,'forecast_cutoff':cut.isoformat(),'target_publication':r['published_at'],
             'split':'development' if month<='2024-06' else 'final','forecasts':b,
             'lag_source':store.asof(shift_month(month,-1),cut),
             'seasonal_source':store.asof(shift_month(month,-12),cut)}
        if row['split']=='development':row['first_provisional_actual']=r['first_provisional']
        all_forecasts.append(row)
    dev=[r for r in all_forecasts if r['split']=='development'];final=[r for r in all_forecasts if r['split']=='final']
    if len(dev)!=6 or len(final)!=18:raise RuntimeError('Split counts')
    first_cut=datetime.fromisoformat(dev[0]['forecast_cutoff']);last_training=datetime.fromisoformat(by_month['2023-12']['published_at'])
    if last_training>first_cut:raise RuntimeError('Training label from future')
    metrics={}
    for name in ['persistence','seasonal_12month','ridge_ar1']:
        err=np.array([r['forecasts'][name]-r['first_provisional_actual'] for r in dev])
        metrics[name]={'mse':float(np.mean(err**2)),'rmse':float(np.sqrt(np.mean(err**2))),'mae':float(np.mean(abs(err))),'mean_error':float(err.mean())}
    base='persistence' if metrics['persistence']['mse']<=metrics['seasonal_12month']['mse']+1e-8 else 'seasonal_12month'
    selected='ridge_ar1' if metrics['ridge_ar1']['mse']<metrics[base]['mse']-1e-8 else base
    dump(ROOT/'artifacts/ar1.json',model);dump(ROOT/'reports/training_audit.json',training_rows)
    dump(ROOT/'reports/development.json',{'metrics':metrics,'selected_baseline':base,'selected_forecast':selected,
        'development_predictions':dev,'model':model,'closed_form_coefficient_difference':coef-model['coefficient_standardized'],
        'closed_form_intercept_difference':intercept-model['intercept_standardized'],
        'development_release_count':6,'final_release_count':18,'final_metrics_computed':False,
        'small_sample_limit':'Only23trainingpairs and6developmentreleases; no strong accuracy claim'})
    dump(ROOT/'data/processed/final_forecasts.json',final)
    protected=paths+['artifacts/ar1.json','reports/development.json','reports/protocol_freeze.json','data/processed/final_forecasts.json']
    dump(ROOT/'reports/model_freeze.json',{'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected},
        'selected_baseline':base,'selected_forecast':selected,'status':'Before final18release error evaluation',
        'target':'First provisional Combined CPI headline YoY percent, base2012','final_targets':['2024-07','2025-12'],
        'public_release_complete':False,'current_new_base_forecast_claimed':False})
    print(json.dumps({'model':model,'development':metrics,'selected_baseline':base,'selected_forecast':selected,
                      'frozen_final_forecasts':len(final),'final_metrics_computed':False},indent=2))

if __name__=='__main__':run()
