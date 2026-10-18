from datetime import datetime
import math

def shift_month(month,offset):
    y,m=map(int,month.split('-'));n=12*y+m-1+offset
    return f'{n//12}-{n%12+1:02d}'

class VintageStore:
    def __init__(self,records):
        self.rows=[];seen={}
        for r in records:
            row=dict(r);dt=datetime.fromisoformat(row['published_at'])
            if dt.tzinfo is None:raise ValueError('Availability timestamp needs timezone')
            if not math.isfinite(row['value']):raise ValueError('Nonfinite CPI observation')
            key=(row['reference_month'],row['base'],row['metric'],row['sector'],dt)
            if key in seen and seen[key]!=row['value']:raise ValueError('Conflicting same-vintage observations')
            if key not in seen:self.rows.append(row);seen[key]=row['value']

    def asof(self,month,cutoff,base=2012):
        when=datetime.fromisoformat(cutoff) if isinstance(cutoff,str) else cutoff
        if when.tzinfo is None:raise ValueError('Forecast cutoff needs timezone')
        eligible=[r for r in self.rows if r['reference_month']==month and r['base']==base
                  and r['metric']=='headline_yoy_percent' and r['sector']=='Combined'
                  and datetime.fromisoformat(r['published_at'])<=when]
        if not eligible:raise ValueError(f'No observed base{base} headline vintage for {month} by {when.isoformat()}')
        return max(eligible,key=lambda r:datetime.fromisoformat(r['published_at']))

def baseline_predictions(store,target_month,cutoff):
    return {'persistence':store.asof(shift_month(target_month,-1),cutoff)['value'],
            'seasonal_12month':store.asof(shift_month(target_month,-12),cutoff)['value']}

def ar1_prediction(last_rate,model):
    return model['intercept_standardized']+model['coefficient_standardized']*(last_rate-model['feature_mean'])/model['feature_scale']
