# SPDX-License-Identifier: Apache-2.0
"""Fixed JSON artifact + strict versioned feature-vector inference. No model training."""
import hashlib
import json
import math
import statistics
from pathlib import Path

VERSION = 'tiny-inference-1'
FORMAT = 'tiny-linear-json-v1'
SCHEMA = 'study-features-v1'
MODEL = 'manual-linear-v1'
FEATURES = ['hours_studied', 'practice_tasks']


def finite_number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def load_model(path):
    raw = Path(path).read_bytes()
    model = json.loads(raw)
    validate_model(model)
    return model, hashlib.sha256(raw).hexdigest()


def validate_model(model):
    if not isinstance(model, dict) or model.get('artifact_format') != FORMAT:
        raise ValueError('unsupported artifact format')
    if model.get('model_version') != MODEL or model.get('schema_version') != SCHEMA:
        raise ValueError('unsupported artifact version')
    if model.get('features') != FEATURES or model.get('value_domain') != [0,100]:
        raise ValueError('unsupported artifact feature contract')
    weights = model.get('weights')
    if not isinstance(weights,list) or len(weights)!=2 or not all(finite_number(x) and abs(x)<=100 for x in weights):
        raise ValueError('invalid weights')
    if not finite_number(model.get('bias')) or abs(model['bias'])>100:
        raise ValueError('invalid bias')
    if model.get('output') != 'synthetic_score':
        raise ValueError('unsupported output contract')


def infer(model, model_digest, request, policy='strict'):
    if policy not in ('strict','naive'):
        raise ValueError('unsupported policy')
    trace = [dict(stage='artifact', status='loaded', model_version=model['model_version'],
                  schema_version=model['schema_version'], model_sha256=model_digest)]
    def rejected(stage, reason):
        trace.append(dict(stage=stage,status='rejected',reason=reason))
        return dict(status='rejected',output=None,error=reason,policy=policy,trace=trace)
    if not isinstance(request, dict):
        return rejected('request','request must be an object')
    if policy=='strict':
        if request.get('model_version')!=model['model_version']:
            return rejected('contract','model version mismatch')
        if request.get('schema_version')!=model['schema_version']:
            return rejected('contract','schema version mismatch')
        if request.get('features')!=model['features']:
            return rejected('contract','feature names/order mismatch')
        trace.append(dict(stage='contract',status='passed',features=request['features']))
    else:
        trace.append(dict(stage='contract',status='skipped-intentionally',reason='names/order and requested versions ignored'))
    values = request.get('values')
    if not isinstance(values,list) or len(values)!=len(model['weights']):
        return rejected('values','expected exactly two values')
    if not all(finite_number(v) for v in values):
        return rejected('values','values must be finite numbers; bool/string rejected')
    low, high = model['value_domain']
    if not all(low<=v<=high for v in values):
        return rejected('values','values outside declared domain 0..100')
    trace.append(dict(stage='values',status='passed',values=values))
    total = float(model['bias'])
    trace.append(dict(stage='bias',status='computed',subtotal=total))
    for name, value, weight in zip(model['features'],values,model['weights']):
        contribution = value*weight
        total += contribution
        trace.append(dict(stage='multiply-add',status='computed',feature_assumed=name,value=value,weight=weight,
                          contribution=contribution,subtotal=total))
    trace.append(dict(stage='output',status='computed',output=total,label=model['output']))
    return dict(status='predicted',output=total,error=None,policy=policy,trace=trace)


def describe(model, model_digest, rows):
    if not isinstance(rows,list) or not 1<=len(rows)<=32:
        raise ValueError('batch requires 1..32 rows')
    outputs=[]
    for row in rows:
        request=dict(model_version=MODEL,schema_version=SCHEMA,features=FEATURES,values=row)
        result=infer(model,model_digest,request)
        if result['status']!='predicted':
            raise ValueError('batch row rejected: '+result['error'])
        outputs.append(result['output'])
    def stats(values):
        return dict(n=len(values),mean=statistics.fmean(values),population_std=statistics.pstdev(values),
                    minimum=min(values),maximum=max(values))
    return dict(features={name:stats([r[i] for r in rows]) for i,name in enumerate(FEATURES)},
                output=stats(outputs),predictions=outputs,
                interpretation='Descriptive statistics only; no drift detector, significance test or accuracy claim')
