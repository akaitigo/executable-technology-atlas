# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,json,math,platform,random,re,sys
from fractions import Fraction as F
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import preprocessing as engine,route
HERE=Path(__file__).resolve().parent
SOURCES=['preprocessing.py','verify.py','route.py','serve.py','fixtures.json','hand-oracle.json','README.md','VERIFICATION.md','index.html','coverage.json','sources.json','skills/atlas-train-only-preprocessing/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def materialize(value):
    if isinstance(value,dict) and set(value)=={'special_float'}:return float('nan') if value['special_float']=='nan' else float('inf')
    if isinstance(value,dict):return {k:materialize(v) for k,v in value.items()}
    if isinstance(value,list):return [materialize(v) for v in value]
    return value

def oracle(f,policy):
    # Does not call fit/transform/predict/validator/sqrt; rational second moment and raw coordinate distance.
    rows=f['train'] if policy=='train-only' else f['train']+f['heldout'];n=len(rows)
    means=[sum(F(str(r['values'][j])) for r in rows)/n for j in [0,1]]
    variances=[sum(F(str(r['values'][j]))**2 for r in rows)/n-means[j]**2 for j in [0,1]]
    q=next(r for r in f['heldout'] if r['id']==f['query_id'])['values'];den=[v if v else F(1) for v in variances]
    distances=[sum((F(str(q[j]))-F(str(r['values'][j])))**2/den[j] for j in [0,1]) for r in f['train']]
    choice=min(range(len(distances)),key=lambda i:(distances[i],i))
    return means,variances,distances,choice

def close(a,b):assert math.isclose(a,float(b),rel_tol=1e-12,abs_tol=1e-12),(a,b)
def check(f,p,r,hand=None):
    means,variances,distances,choice=oracle(f,p);assert r['status']=='PREDICTED' and r['prediction']==f['train'][choice]['label'] and r['neighbor_id']==f['train'][choice]['id']
    expected_ids=[x['id'] for x in (f['train'] if p=='train-only' else f['train']+f['heldout'])];assert r['params']['fit_row_ids']==expected_ids and r['params']['n']==len(expected_ids)
    for j in [0,1]:
        close(r['params']['mean'][j],means[j]);close(r['params']['variance'][j],variances[j]);close(r['params']['scale'][j]**2,variances[j] if variances[j] else 1)
        assert r['params']['zero_variance'][j]==(variances[j]==0)
    assert len(r['model'])==len(f['train'])
    for row,input in zip(r['model'],f['train']):
        for j in [0,1]:close(row['transformed'][j]*r['params']['scale'][j]+float(means[j]),F(str(input['values'][j])))
    query=next(x for x in f['heldout'] if x['id']==f['query_id'])
    for j in [0,1]:close(r['query_transformed'][j]*r['params']['scale'][j]+float(means[j]),F(str(query['values'][j])))
    for row,d in zip(r['distances'],distances):close(row['squared_distance'],d)
    if hand:
        assert means==[F(v) for v in hand['mean']] and variances==[F(v) for v in hand['variance']] and distances==[F(v) for v in hand['distances']] and r['prediction']==hand['prediction']
    assert engine.canonical(r['params'])==r['parameter_sha256']
    return dict(mean=[str(v) for v in means],variance=[str(v) for v in variances],squared_distances=[str(v) for v in distances],prediction=f['train'][choice]['label'])
def stable(r):return {k:v for k,v in r.items() if k!='fit_at_utc'}

def execute():
    fixtures=json.loads((HERE/'fixtures.json').read_text());hand=json.loads((HERE/'hand-oracle.json').read_text());runs=[]
    for encoded in fixtures:
        f=materialize(encoded);out={};independent={}
        for p in ['train-only','leaked']:
            r=engine.execute(f,p)
            if encoded['id'] in hand:independent[p]=check(f,p,r,hand[encoded['id']][p])
            else:assert r['status']=='REJECTED' and r['params'] is r['prediction'] is None and len(r['trace'])==1
            out[p]=r
        runs.append(dict(id=encoded['id'],input=encoded,policies=out,independent_fraction=independent))
    small=runs[0]['policies'];expanded=runs[1]['policies']
    assert small['train-only']['params']==expanded['train-only']['params'] and small['train-only']['parameter_sha256']==expanded['train-only']['parameter_sha256']
    assert small['train-only']['distances']==expanded['train-only']['distances'] and small['train-only']['prediction']==expanded['train-only']['prediction']=='A'
    assert small['leaked']['params']!=expanded['leaked']['params'] and small['leaked']['prediction']=='A' and expanded['leaked']['prediction']=='B'
    rng=random.Random(20261005);randomized=[]
    for i in range(100):
        f=copy.deepcopy(fixtures[0]);f['heldout'][0]['values']=[rng.randint(-10,20),rng.randint(-5,5)];g=copy.deepcopy(f);g['heldout'].append(dict(id='outlier',values=[rng.randint(-100,100),rng.randint(20,200)]))
        outcomes={}
        for p in ['train-only','leaked']:
            left=engine.execute(f,p);right=engine.execute(g,p);check(f,p,left);check(g,p,right)
            if p=='train-only':assert left['params']==right['params'] and left['distances']==right['distances'] and left['prediction']==right['prediction']
            outcomes[p]=dict(small=left,expanded=right)
        randomized.append(dict(small_input=f,expanded_input=g,policies=outcomes))
    invalid_options=[]
    for name,f,p in [('not-object',None,'train-only'),('policy',fixtures[0],'unknown')]:
        r=engine.execute(f,p);assert r['status']=='REJECTED';invalid_options.append(dict(id=name,result=r))
    return dict(version=engine.VERSION,seed=20261005,fixtures_sha256=digest(HERE/'fixtures.json'),hand_sha256=digest(HERE/'hand-oracle.json'),runs=runs,randomized=randomized,invalid_options=invalid_options,invariance=dict(train_only_parameter_unchanged=True,train_only_same_query_prediction_unchanged=True,leaked_same_query_A_to_B=True),author_routing_smoke={'preprocessing':route.route('preprocessing'),'production-train':route.route('production-train')},scope='Synthetic finite fit/transform/1NN; heldout feature contamination only; no evaluation accuracy or generalization guarantee')

def docs(record):
    planned={HERE/'observations/raw.json',HERE/'observations/receipt.json',HERE/'observations/fitted-parameters.json'}
    for f in ['README.md','skills/atlas-train-only-preprocessing/SKILL.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
            if not link.startswith(('https:','#')):
                target=((HERE/f).parent/link.split('#')[0]).resolve();assert target.exists() or record and target in planned,link
    assert all(w in (HERE/'README.md').read_text() for w in ['前提','主要概念','実務判断','限界','原典','未教材'])
    coverage=json.loads((HERE/'coverage.json').read_text());ids={x['id'] for x in json.loads((HERE/'sources.json').read_text())}
    assert 2<=len(coverage['next_experiments'])<=4
    for row in coverage['areas']+coverage['next_experiments']:assert row['source'] in ids and row['question']
    assert all(s in (HERE/'index.html').read_text() for s in ['coverage.json','sources.json','README.md'])

def compare(old,new):
    assert old['fixtures_sha256']==new['fixtures_sha256'] and old['hand_sha256']==new['hand_sha256']
    assert len(old['runs'])==len(new['runs'])==14 and len(old['randomized'])==len(new['randomized'])==100
    for a,b in zip(old['runs'],new['runs']):
        assert a['id']==b['id'] and a['input']==b['input'] and a['independent_fraction']==b['independent_fraction']
        for p in ['train-only','leaked']:assert stable(a['policies'][p])==stable(b['policies'][p])
    for a,b in zip(old['randomized'],new['randomized']):
        assert a['small_input']==b['small_input'] and a['expanded_input']==b['expanded_input']
        for p in ['train-only','leaked']:
            for c in ['small','expanded']:assert stable(a['policies'][p][c])==stable(b['policies'][p][c])
    assert old['invalid_options']==new['invalid_options']

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record',action='store_true');g.add_argument('--seal-record',action='store_true');args=p.parse_args();raw=execute();docs(args.record)
    folder=HERE/'observations';qa=json.loads((folder/'ui-qa.json').read_text());sources={f:digest(HERE/f) for f in SOURCES}
    if qa['status']=='passed':
        for key,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json')]:assert qa[key]==digest(HERE/f)
        rows=json.loads((folder/'ui-matrix.json').read_text())['rows'];assert len(rows)==28 and len({(r['id'],r['policy']) for r in rows})==28
        for row in rows:
            result=next(r for r in raw['runs'] if r['id']==row['id'])['policies'][row['policy']]
            for key in ['status','prediction','parameter_sha256','error']:assert row[key]==result[key]
    if args.seal_record:compare(json.loads((folder/'raw.json').read_text()),raw)
    if args.record or args.seal_record:
        if args.record:
            assert not qa.get('observed_raw_sha256'),'Use --seal-record to preserve actual UI observation'
            (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
            params=[dict(id=r['id'],policies={p:dict(fit_at_utc=o.get('fit_at_utc'),params=o['params'],parameter_sha256=o['parameter_sha256']) for p,o in r['policies'].items()}) for r in raw['runs']]
            (folder/'fitted-parameters.json').write_text(json.dumps(params,indent=2)+'\n')
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
        names=['observations/raw.json','observations/fitted-parameters.json','observations/ui-qa.json']
        for name in ['ui-matrix.json','preview-http.log','default-bind.txt','skill-smoke.json','iteration-failure.txt']:
            if (folder/name).exists():names.append('observations/'+name)
        receipt=dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py --seal-record' if args.seal_record else 'python3 verify.py --record',environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),inputs=dict(fixtures=raw['fixtures_sha256'],hand_oracle=raw['hand_sha256']),sources=sources,artifacts={f:digest(HERE/f) for f in names},checks=dict(fraction_hand_parameter_distance='passed',cohort_invariance='passed',docs='passed',author_smoke='passed; not independent AgentEval',actual_iab_qa=qa['status']))
        (folder/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    else:
        receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources
        for f,h in receipt['artifacts'].items():assert digest(HERE/f)==h,f
        compare(json.loads((folder/'raw.json').read_text()),raw)
        if qa.get('observed_raw_sha256'):assert qa['observed_raw_sha256']==digest(folder/'raw.json')
    print(json.dumps(dict(status='passed',record=args.record,seal_record=args.seal_record,cases=14,policies=2,normal_cases=4,rejected_cases=10,random_cohort_pairs=100,invalid_options=2,invariance='train-only A/A; leaked A/B')))
if __name__=='__main__':main()
