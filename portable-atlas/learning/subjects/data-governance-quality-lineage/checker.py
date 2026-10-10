"""Fixed hand violations, totals and lineage oracle. Imports no engine/runner."""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CASES={'normal','lower-bound','upper-bound','nonnull','below-range','above-range','duplicate-id','missing-reference','unknown-class','empty','combined-bad','cycle','orphan-node','orphan-column','same-source-cache','source-change'}
CONTRACT={'version':1,'required':['id','category','amount','class'],'amount_range':[0,1000000],'unique':'id','reference':['products.category','categories.id'],'classes':['public','internal']}
BASEPRODUCTS=[{'id':'p1','category':'c1','amount':100,'class':'public'},{'id':'p2','category':'c2','amount':0,'class':'internal'}]
CATEGORIES=[{'id':'c1'},{'id':'c2'}]
GRAPH={'products':{'parents':[],'columns':['id','category','amount','class']},'categories':{'parents':[],'columns':['id']},'validated':{'parents':['products','categories'],'columns':['id','category','amount','class']},'totals':{'parents':['validated'],'columns':['category','amount_sum','class']}}
COLUMNS=[{'target':'validated.id','sources':['products.id']},{'target':'validated.category','sources':['products.category','categories.id']},{'target':'validated.amount','sources':['products.amount']},{'target':'validated.class','sources':['products.class']},{'target':'totals.category','sources':['validated.category']},{'target':'totals.amount_sum','sources':['validated.amount']},{'target':'totals.class','sources':['validated.class']}]
TOTALS=[{'category':'c1','amount_sum':100,'class':'public','product_rows':[1]},{'category':'c2','amount_sum':0,'class':'internal','product_rows':[2]}]
def raw(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def violation(row,column,rule,actual,expected):return {'table':'products','row':row,'column':column,'rule':rule,'actual':actual,'expected':expected}
HAND={
'nonnull':[violation(1,'amount','nonnull',None,'non-null/nonempty')],
'below-range':[violation(1,'amount','range',-1,[0,1000000])],
'above-range':[violation(1,'amount','range',1000001,[0,1000000])],
'duplicate-id':[violation(2,'id','unique','p2','unique id')],
'missing-reference':[violation(1,'category','reference','c9','categories.id')],
'unknown-class':[violation(1,'class','known-class','secret',['public','internal'])],
'combined-bad':[violation(1,'amount','range',-1,[0,1000000]),violation(1,'category','reference','c9','categories.id'),violation(1,'class','known-class','secret',['public','internal'])]
}
ERRORS={'cycle':[{'kind':'cycle'}],'orphan-node':[{'kind':'orphan-node','node':'totals','parent':'missing'}],'orphan-column':[{'kind':'orphan-column','endpoint':'validated.absent'}]}
def oracle(folder):
    obs=read(folder/'observation.json');assert {r['id'] for r in obs['runs']}==CASES and len(obs['runs'])==16,'exact case set';reports=[]
    for run in obs['runs']:
        key=run['id'];case=folder/key;request=read(case/'input.json');result=read(case/'result.json');command=read(case/'command.json');trace=read(case/'trace.json')
        expected_products=json.loads(json.dumps(BASEPRODUCTS));expected_graph=json.loads(json.dumps(GRAPH));expected_columns=json.loads(json.dumps(COLUMNS))
        mutations={'lower-bound':('amount',0),'upper-bound':('amount',1000000),'nonnull':('amount',None),'below-range':('amount',-1),'above-range':('amount',1000001),'duplicate-id':('id','p2'),'missing-reference':('category','c9'),'unknown-class':('class','secret'),'source-change':('amount',101)}
        if key in mutations:col,value=mutations[key];expected_products[0][col]=value
        if key=='empty':expected_products=[]
        if key=='combined-bad':expected_products[0].update({'amount':-1,'category':'c9','class':'secret'})
        if key=='cycle':expected_graph['validated']['parents']=['totals']
        if key=='orphan-node':expected_graph['totals']['parents']=['missing']
        if key=='orphan-column':expected_columns[5]['sources']=['validated.absent']
        assert request['sources']=={'products':expected_products,'categories':CATEGORIES},'hand input rows'
        assert request['graph']==expected_graph and request['column_lineage']==expected_columns,'hand input lineage'
        for s in ('stdin','stdout','stderr'):assert sha(command[s].encode())==command[s+'_digest'],'raw command digest'
        assert command['stderr']=='' and json.loads(command['stdin'])==request,'raw input/stderr'
        assert trace==[json.loads(line) for line in command['stdout'].splitlines()],'raw trace'
        decision='rejected' if key in HAND or key in ERRORS else 'invalidated' if key=='source-change' else 'reused' if key=='same-source-cache' else 'accepted'
        exit_code=2 if decision=='rejected' else 3 if decision=='invalidated' else 0
        assert command['exit_code']==run['exit_code']==result['exit_code']==exit_code,'exit code'
        assert result['decision']==decision and trace[-1]=={'event':decision,'exit_code':exit_code,'output_rows':len(result['output'])},'hand decision'
        violations=HAND.get(key,[]);errors=ERRORS.get(key,[])
        assert result['violations']==violations,'hand violations differ'
        assert [{k:v for k,v in e.items() if k!='event'} for e in trace if e['event']=='violation']==violations,'trace violations'
        assert result['graph_errors']==errors,'hand graph errors differ'
        assert result['contract']==CONTRACT,'hand contract'
        assert [e for e in trace if e['event']=='quality-checked']==[{'event':'quality-checked','violation_count':len(violations),'rows':len(expected_products)}],'quality stage'
        order=[] if decision=='rejected' else ['products','categories','validated','totals']
        assert result['order']==order,'hand topology differs'
        assert result['column_lineage']==expected_columns,'hand column lineage'
        totals=json.loads(json.dumps(TOTALS)) if decision in ('accepted','reused') else []
        if key=='empty':totals=[]
        if key=='lower-bound':totals[0]['amount_sum']=0
        if key=='upper-bound':totals[0]['amount_sum']=1000000
        assert result['output']==totals,'hand aggregate differs'
        bindings={'sources':{n:sha(raw(rows)) for n,rows in request['sources'].items()},'contract':sha(raw(CONTRACT)),'lineage':sha(raw({'graph':expected_graph,'columns':expected_columns})),'producer':obs['source_bindings']['engine.py']}
        assert result['bindings']==bindings and trace[0]=={'event':'bind-input','bindings':bindings},'binding digest'
        stale=[]
        if key in ('same-source-cache','source-change'):
            prior={'sources':{'products':sha(raw(BASEPRODUCTS)),'categories':sha(raw(CATEGORIES))},'contract':sha(raw(CONTRACT)),'lineage':sha(raw({'graph':GRAPH,'columns':COLUMNS})),'producer':obs['source_bindings']['engine.py']}
            assert request['cache']=={'bindings':prior,'output':TOTALS,'output_digest':sha(raw(TOTALS))},'hand cache'
            if key=='source-change':stale=[{'kind':'source-changed','source':'products','cached':prior['sources']['products'],'current':bindings['sources']['products']}]
        else:assert 'cache' not in request,'unexpected cache'
        assert result['stale']==stale,'hand stale differs'
        expected_events=['bind-input']+['violation']*len(violations)+['quality-checked']
        if errors:expected_events+=['lineage-rejected']
        elif not violations:expected_events+=['lineage-checked', 'cache-invalidated' if key=='source-change' else 'cache-reused' if key=='same-source-cache' else 'aggregate-derived']
        expected_events+=[decision]
        assert [e['event'] for e in trace]==expected_events,'stage sequence'
        reports.append({'id':key,'decision':decision,'exit_code':exit_code,'violations':violations,'graph_errors':errors,'output':totals,'order':order,'column_lineage':expected_columns,'bindings':bindings,'stale':stale,'input_rows':len(expected_products),'violation_count':len(violations),'output_digest':sha(raw(totals)),'stages':expected_events})
    return {'passed':True,'cases':16,'independence':'Fixed hand input, violations, graph errors, order and totals; no engine/runner import','reports':reports}
def check():
    folder=ROOT/read(ROOT/'current.json')['directory'];obs=read(folder/'observation.json')
    for n,d in obs['source_bindings'].items():assert sha((ROOT/n).read_bytes())==d,'stale source '+n
    index=read(folder/'artifact-index.json');actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'};assert set(index)==actual,'artifact set'
    for n,e in index.items():
        b=(folder/n).read_bytes();assert e=={'digest':sha(b),'size':len(b)},'artifact digest '+n
    result=oracle(folder);assert result==read(folder/'oracle.json'),'saved oracle differs'
    print(json.dumps({'passed':True,'cases':16,'read_only':True}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--oracle');args=p.parse_args()
    try:
        if args.oracle:
            assert re.fullmatch(r'(observations/[0-9TZ]+|oracle-negative-[a-zA-Z0-9_-]+)',args.oracle),'oracle path';print(json.dumps(oracle(ROOT/args.oracle),ensure_ascii=False))
        else:check()
    except (AssertionError,ValueError,KeyError,OSError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
