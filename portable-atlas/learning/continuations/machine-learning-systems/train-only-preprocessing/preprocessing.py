# SPDX-License-Identifier: Apache-2.0
import hashlib,json,math
from datetime import datetime,timezone
VERSION='train-only-standardization-1'
FEATURES=['x','y'];FEATURE_VERSION='xy-v1'
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate(f,policy):
    if not isinstance(f,dict):raise ValueError('fixture must be object')
    if policy not in ('train-only','leaked'):raise ValueError('unknown policy')
    if f.get('feature_version')!=FEATURE_VERSION or f.get('features')!=FEATURES:raise ValueError('feature contract mismatch')
    ids=[]
    for split in ['train','heldout']:
        rows=f.get(split)
        if not isinstance(rows,list) or not 1<=len(rows)<=32:raise ValueError(split+' must contain 1..32 rows')
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id']:raise ValueError('row ID required')
            ids.append(row['id']);x=row.get('values')
            if not isinstance(x,list) or len(x)!=2:raise ValueError('two features required')
            if any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e6 for v in x):raise ValueError('finite numeric features required; bool rejected')
            if split=='train' and row.get('label') not in ['A','B']:raise ValueError('train label A/B required')
            if split=='heldout' and 'label' in row:raise ValueError('heldout must not carry label in this lesson')
    if len(set(ids))!=len(ids):raise ValueError('train/heldout row IDs must be disjoint and unique')
    if sum(row['id']==f.get('query_id') for row in f['heldout'])!=1:raise ValueError('query ID must name one heldout row')

def fit_scaler(rows,scope):
    n=len(rows);mean=[sum(r['values'][j] for r in rows)/n for j in range(2)]
    variance=[sum((r['values'][j]-mean[j])**2 for r in rows)/n for j in range(2)]
    scale=[math.sqrt(v) if v>0 else 1.0 for v in variance]
    return dict(feature_version=FEATURE_VERSION,features=FEATURES,fit_scope=scope,fit_row_ids=[r['id'] for r in rows],n=n,mean=mean,variance=variance,scale=scale,zero_variance=[v==0 for v in variance],variance_convention='population ddof0; exact zero variance scale1')

def transform(values,params):return [(v-m)/s for v,m,s in zip(values,params['mean'],params['scale'])]
def fit_nn(rows,params):return [dict(id=r['id'],label=r['label'],transformed=transform(r['values'],params)) for r in rows]
def predict(query,model):
    distances=[dict(index=i,id=r['id'],label=r['label'],squared_distance=sum((a-b)**2 for a,b in zip(query,r['transformed']))) for i,r in enumerate(model)]
    chosen=min(distances,key=lambda r:(r['squared_distance'],r['index']))
    return chosen,distances

def execute(f,policy):
    trace=[]
    try:validate(f,policy)
    except ValueError as e:return dict(status='REJECTED',error=str(e),params=None,parameter_sha256=None,prediction=None,distances=None,trace=[dict(stage='validate',status='REJECTED',reason=str(e))])
    trace.append(dict(stage='validate',status='PASSED',train_ids=[r['id'] for r in f['train']],heldout_ids=[r['id'] for r in f['heldout']]))
    rows=f['train'] if policy=='train-only' else f['train']+f['heldout'];fit_at=datetime.now(timezone.utc).isoformat()
    params=fit_scaler(rows,policy);trace.append(dict(stage='fit_scaler',fit_row_ids=params['fit_row_ids'],mean=params['mean'],variance=params['variance'],scale=params['scale']))
    model=fit_nn(f['train'],params);trace.append(dict(stage='transform_train_and_fit_1nn',model=model))
    query=next(r for r in f['heldout'] if r['id']==f['query_id']);transformed=transform(query['values'],params);trace.append(dict(stage='transform_query',query_id=query['id'],transformed=transformed))
    chosen,distances=predict(transformed,model);trace.append(dict(stage='squared_distance',neighbors=distances))
    trace.append(dict(stage='choose',prediction=chosen['label'],neighbor_id=chosen['id'],tie_rule='first train row on exact squared-distance tie'))
    return dict(status='PREDICTED',error=None,fit_at_utc=fit_at,params=params,parameter_sha256=canonical(params),model=model,query_transformed=transformed,prediction=chosen['label'],neighbor_id=chosen['id'],distances=distances,trace=trace)
