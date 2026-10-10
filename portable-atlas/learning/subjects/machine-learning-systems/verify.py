# SPDX-License-Identifier: Apache-2.0
"""Independent hand-prediction/schema oracle, source binding, explicit record option."""
import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import re
import sys
sys.dont_write_bytecode=True
import pipeline
import route

HERE=Path(__file__).resolve().parent
SOURCES=['pipeline.py','verify.py','route.py','serve.py','model.json','inputs.json','index.html','README.md',
         'VERIFICATION.md','coverage.json','sources.json','skills/atlas-machine-learning-systems/SKILL.md']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def near(a,b):
    assert abs(a-b)<1e-10, (a,b)


def numeric(v):
    # Separate oracle domain, no production validator call.
    return type(v) in (int,float) and 0<=v<=100 and (type(v) is int or math.isfinite(v))


def contract_oracle(request):
    return (isinstance(request,dict) and request.get('schema_version')=='study-features-v1'
            and request.get('model_version')=='manual-linear-v1'
            and request.get('features')==['hours_studied','practice_tasks'])


def values_oracle(request):
    return (isinstance(request,dict) and isinstance(request.get('values'),list)
            and len(request['values'])==2 and all(numeric(v) for v in request['values']))


def semantic_prediction(request):
    # Golden hand formula bound to this manual fixture, not production weights or dot-product code.
    if not isinstance(request,dict) or request.get('schema_version')!='study-features-v1' or request.get('model_version')!='manual-linear-v1':
        return None
    names=request.get('features')
    if not isinstance(names,list) or len(names)!=2 or set(names)!={'hours_studied','practice_tasks'} or not values_oracle(request):
        return None
    named=dict(zip(names,request['values']))
    hours=Fraction(str(named['hours_studied']))
    tasks=Fraction(str(named['practice_tasks']))
    return float(1+2*hours+tasks/2)


def check_trace(result):
    trace=result['trace']
    assert trace[0]['stage']=='artifact'
    if result['status']=='rejected':
        assert result['output'] is None and trace[-1]['status']=='rejected'
        assert all(t['stage']!='output' for t in trace)
        return
    subtotal=1.0
    adds=[t for t in trace if t['stage']=='multiply-add']
    assert len(adds)==2
    for step, weight in zip(adds,[2,.5]):
        near(step['weight'],weight)
        near(step['contribution'],step['value']*weight)
        subtotal+=step['contribution']
        near(step['subtotal'],subtotal)
    near(result['output'],subtotal)
    assert trace[-1]['output']==result['output']


def stats_oracle(values):
    fractions=[Fraction(str(v)) for v in values]
    n=len(fractions)
    mean=sum(fractions)/n
    var=sum((v-mean)**2 for v in fractions)/n
    return dict(n=n,mean=float(mean),population_std=math.sqrt(float(var)),minimum=min(values),maximum=max(values))


def execute():
    model, model_hash=pipeline.load_model(HERE/'model.json')
    assert model['weights']==[2,.5] and model['bias']==1 and model['features']==['hours_studied','practice_tasks']
    inputs=json.loads((HERE/'inputs.json').read_text())
    runs=[]
    for request in inputs['requests']:
        policies={}
        for policy in ('strict','naive'):
            result=pipeline.infer(model,model_hash,request,policy)
            expect=(contract_oracle(request) if policy=='strict' else True) and values_oracle(request)
            assert (result['status']=='predicted')==expect, request['id']
            check_trace(result)
            if expect and policy=='strict':
                near(result['output'],semantic_prediction(request))
            policies[policy]=result
        runs.append(dict(id=request['id'],input=request,semantic_oracle=semantic_prediction(request),
                         schema_oracle_accepts=contract_oracle(request) and values_oracle(request),policies=policies))
    by={r['id']:r for r in runs}
    assert by['normal']['policies']['strict']['output']==11
    assert by['reordered']['semantic_oracle']==11
    assert by['reordered']['policies']['strict']['status']=='rejected'
    assert by['reordered']['policies']['naive']['output']==18.5
    assert by['zero-boundary']['policies']['strict']['output']==1
    assert by['max-boundary']['policies']['strict']['output']==251
    rng=random.Random(20261005)
    for _ in range(100):
        request=dict(schema_version='study-features-v1',model_version='manual-linear-v1',
                     features=['hours_studied','practice_tasks'],values=[rng.randint(0,100)/2,rng.randint(0,100)/2])
        for policy in ('strict','naive'):
            result=pipeline.infer(model,model_hash,request,policy)
            near(result['output'],semantic_prediction(request))
            check_trace(result)
        swapped=copy.deepcopy(request)
        swapped['features'].reverse();swapped['values'].reverse()
        assert semantic_prediction(swapped)==semantic_prediction(request)
        assert pipeline.infer(model,model_hash,swapped)['status']=='rejected'
    edge_rejections=[]
    for name,request in [('nan',dict(inputs['requests'][0],values=[float('nan'),8])),
                         ('infinity',dict(inputs['requests'][0],values=[float('inf'),8])),
                         ('not-object',None),('not-array',dict(inputs['requests'][0],values=3)),
                         ('negative',dict(inputs['requests'][0],values=[-1,8])),
                         ('huge-integer',dict(inputs['requests'][0],values=[10**400,8]))]:
        results={policy:pipeline.infer(model,model_hash,request,policy) for policy in ('strict','naive')}
        assert all(r['status']=='rejected' for r in results.values())
        # JSON cannot portably represent NaN/Inf. Store explicit tagged input, preserve rejection trace.
        portable=copy.deepcopy(request)
        if name in ('nan','infinity'):
            portable['values'][0]={'nonfinite':name}
        edge_rejections.append(dict(id=name,input_representation=portable,policies=results))
    try:
        pipeline.infer(model,model_hash,inputs['requests'][0],'unknown')
    except ValueError as e:
        option_rejection=str(e)
    else:
        raise AssertionError('unknown policy')
    batches={}
    for name,rows in inputs['batches'].items():
        observed=pipeline.describe(model,model_hash,rows)
        for i,feature in enumerate(['hours_studied','practice_tasks']):
            expected=stats_oracle([r[i] for r in rows])
            for key,value in expected.items():near(observed['features'][feature][key],value)
        expected_scores=[float(1+2*Fraction(str(row[0]))+Fraction(str(row[1]))/2) for row in rows]
        assert observed['predictions']==expected_scores
        for key,value in stats_oracle(expected_scores).items():near(observed['output'][key],value)
        batches[name]=dict(input=rows,result=observed)
    delta={f:batches['new_input']['result']['features'][f]['mean']-batches['reference']['result']['features'][f]['mean'] for f in ['hours_studied','practice_tasks']}
    assert delta=={'hours_studied':9.0,'practice_tasks':0.0}
    assert batches['new_input']['result']['output']['mean']-batches['reference']['result']['output']['mean']==18
    batch_rejections=[]
    for name,rows in [('empty',[]),('too-many',[[1,2]]*33),('bad-row',[[1]])]:
        try:pipeline.describe(model,model_hash,rows)
        except ValueError as e:batch_rejections.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    artifact_rejections=[]
    for name,change in [('format',{'artifact_format':'unknown'}),('model-version',{'model_version':'manual-linear-v2'}),
                        ('schema-version',{'schema_version':'study-features-v2'}),('weight-shape',{'weights':[2]}),
                        ('nonfinite-weight',{'weights':[float('inf'),.5]}),('output-contract',{'output':'unknown'})]:
        try:pipeline.validate_model(dict(model,**change))
        except ValueError as e:artifact_rejections.append(dict(id=name,error=str(e)))
        else:raise AssertionError(name)
    return dict(pipeline_version=pipeline.VERSION,model=model,model_sha256=model_hash,input_sha256=digest(HERE/'inputs.json'),
                runs=runs,edge_rejections=edge_rejections,option_rejection=option_rejection,randomized_requests=100,
                batches=batches,mean_deltas=delta,batch_rejections=batch_rejections,artifact_rejections=artifact_rejections,
                oracle='independent literal schema contract and named Fraction hand formula; population stats by rational sums',
                author_routing_smoke={'schema':route.route('schema'),'production-deploy':route.route('production-deploy')})


def docs_check(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json'}
    for f in ['README.md','skills/atlas-machine-learning-systems/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve()
                assert target.exists() or (record and target in planned), link
    text=(HERE/'README.md').read_text()
    assert all(word in text for word in ['前提','主要概念','実務判断','限界','原典','未教材'])
    coverage=json.loads((HERE/'coverage.json').read_text())
    sources=json.loads((HERE/'sources.json').read_text())
    ids={s['id'] for s in sources}
    assert 2<=len(coverage['next_experiments'])<=4
    for item in coverage['areas']+coverage['next_experiments']:
        assert item['source'] in ids and item['question']
    html=(HERE/'index.html').read_text()
    assert all(x in html for x in ['coverage.json','sources.json','README.md'])
    assert route.route('schema')['status']=='supported' and route.route('production-deploy')['status']=='unsupported'


def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    data=execute();docs_check(args.record)
    sources={f:digest(HERE/f) for f in SOURCES}
    folder=HERE/'observations'
    if args.record:
        (folder/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        artifacts=['observations/raw.json','observations/ui-qa.json']
        if (folder/'ui-matrix.json').exists():artifacts.append('observations/ui-matrix.json')
        if (folder/'preview-http.log').exists():artifacts.append('observations/preview-http.log')
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --record',
                     environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),
                     model_sha256=data['model_sha256'],input_sha256=data['input_sha256'],sources=sources,
                     artifacts={f:digest(HERE/f) for f in artifacts},
                     checks=dict(runtime_oracle='passed',roadmap_links_binding='passed',author_routing_smoke='passed; not independent AgentEval',
                                 actual_iab_qa=json.loads((folder/'ui-qa.json').read_text())['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text())
        assert sources==receipt['sources'], 'source changed; record only by explicit --record'
        for f,expected in receipt['artifacts'].items():assert expected==digest(HERE/f), f
        assert data==json.loads((folder/'raw.json').read_text()), 'runtime replay mismatch'
        qa=json.loads((folder/'ui-qa.json').read_text())
        if 'observed_raw_sha256' in qa.get('iab',{}):
            assert qa['iab']['observed_raw_sha256']==digest(folder/'raw.json'), 'UI observed raw binding mismatch'
    print(json.dumps(dict(status='passed',record=args.record,runs=len(data['runs']),randomized_requests=100,
                         edge_rejections=len(data['edge_rejections']),batch_rejections=len(data['batch_rejections']))))

if __name__=='__main__':main()
