import copy,hashlib,itertools,json,sys
from fractions import Fraction as F
from functools import reduce
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=lambda v:str(v.numerator)+'/'+str(v.denominator)
def check_rows(raw,c,e):
    by={r['id']:r for r in raw['rows']};assert len(by)==len(raw['rows'])==7
    # Independent direct product from fixed single-answer distribution, no coin producer import.
    one={'0':{'0':F(3,4),'1':F(1,4)},'1':{'0':F(1,4),'1':F(3,4)}}
    for ident,n in (('single',1),('double',2)):
        row=by[ident];dist={x:{''.join(out):reduce(lambda a,b:a*b,(one[x][o] for o in out),F(1)) for out in itertools.product(('0','1'),repeat=n)} for x in ('0','1')}
        assert row['status']=='accepted-calculation' and row['request']=={'answers':n,'coin_profile':'fair-independent'}
        serialized={x:{o:f(v) for o,v in d.items()} for x,d in dist.items()};assert row['distribution']==e[ident]==serialized
        for x in ('0','1'):
            paths=row['paths'][x];assert len(paths)==4**n and row['path_count_per_input']==4**n and row['path_mass']==f(F(1,4**n))
            assert {tuple(t['coins']) for t in paths}==set(itertools.product((0,1),repeat=2*n))
            handmap={'0':{(0,0):'0',(0,1):'0',(1,0):'0',(1,1):'1'},'1':{(0,0):'1',(0,1):'1',(1,0):'0',(1,1):'1'}}
            for t in paths:
                assert t['mass']==f(F(1,4**n)) and t['output']==''.join(handmap[x][tuple(t['coins'][2*i:2*i+2])] for i in range(n))
            assert sum((F(t['mass']) for t in paths),F(0))==1
            assert {o:sum((F(t['mass']) for t in paths if t['output']==o),F(0)) for o in dist[x]}==dist[x]
        # Independent event enumeration via combinations, unlike producer mask loop.
        events={}
        for length in range(1,2**n+1):
            for subset in itertools.combinations(dist['0'],length):
                p0=sum((dist['0'][o] for o in subset),F(0));p1=sum((dist['1'][o] for o in subset),F(0))
                events[subset]={'outputs':list(subset),'p0':f(p0),'p1':f(p1),'ratio_0_over_1':f(p0/p1),'ratio_1_over_0':f(p1/p0)}
        assert len(row['nonempty_events'])==e['event_counts'][ident] and {tuple(t['outputs']):t for t in row['nonempty_events']}==events
        assert {tuple(t['outputs']):t for t in row['singleton_ratios']}=={k:v for k,v in events.items() if len(k)==1}
        limit=F(3**n);maximum=max(F(v[k]) for v in events.values() for k in ('ratio_0_over_1','ratio_1_over_0'))
        assert row['max_ratio']==row['normal_bound']==e['bounds'][ident]==f(maximum)==f(limit)
        assert row['normal_bound_holds'] is True and row['epsilon_symbolic']==e['epsilon_symbolic'][ident] and row['delta']=='0/1' and row['random_samples']==0
        assert row['reused_single_bound']=='3/1' and row['reused_bound_actually_holds']==(n==1) and row['faulty_marginal_max_ratio']=='3/1' and row['faulty_marginal_only_claim_holds'] is True
        bad={k:v for k,v in events.items() if F(v['ratio_0_over_1'])>3 or F(v['ratio_1_over_0'])>3};assert {tuple(t['outputs']):t for t in row['events_violating_reused_bound']}==bad
        assert len(bad)==(0 if n==1 else 2)
    for s in c['refusals']:assert by[s['id']]=={'id':s['id'],'status':'expected-refusal','request':s['request'],'reason':s['reason'],'distribution_created':False}
def main():
    raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.RR_OBSERVATION = ').strip().removesuffix(';'));d=ROOT/'observations'/raw['run_id'];assert json.loads((d/'raw.json').read_text())==raw
    for n,h in raw['source_digests'].items():assert sha(ROOT/n)==h,n
    for n,v in json.loads((d/'artifact-index.json').read_text())['artifacts'].items():assert sha(d/n)==v['sha256'] and (d/n).stat().st_size==v['bytes']
    c=json.loads((ROOT/'contracts.json').read_text());e=json.loads((ROOT/'expected-distributions.json').read_text())
    for n in ('contracts.json','expected-distributions.json'):assert (ROOT/n).read_bytes()==(d/n).read_bytes()
    cmd=json.loads((d/'command.json').read_text());assert cmd['exit']==0 and cmd['stderr']=='' and cmd['argv']==['python3','calculate.py'] and json.loads(cmd['stdout'])['rows']==raw['rows']
    check_rows(raw,c,e);controls=[]
    for fault in ('joint-bound3','wrong-path-mass','correlated-joint','event-omitted','refusal-as-success'):
        bad=copy.deepcopy(raw)
        if fault=='joint-bound3':bad['rows'][1]['reused_bound_actually_holds']=True
        if fault=='wrong-path-mass':bad['rows'][0]['paths']['0'][0]['mass']='1/2'
        if fault=='correlated-joint':bad['rows'][1]['distribution']['0']['01']='0/1'
        if fault=='event-omitted':bad['rows'][1]['nonempty_events'].pop()
        if fault=='refusal-as-success':bad['rows'][2]['status']='accepted-calculation'
        try:check_rows(bad,c,e)
        except AssertionError:controls.append(fault)
        else:raise AssertionError('escaped '+fault)
    sys.dont_write_bytecode=True
    import route
    for q,t in route.ROUTES.items():assert route.route(q)=={'supported':True,'target':t,'executed':False,'reason':None}
    for q in route.UNSUPPORTED:assert route.route(q)['supported'] is False and route.route(q)['executed'] is False
    print(json.dumps({'status':'passed','run_id':raw['run_id'],'accepted':2,'expected_refusals':5,'paths_per_input':[4,16],'events':[3,15],'max_probability_ratios':['3/1','9/1'],'epsilon_symbolic':['ln(3)','2*ln(3)'],'negative_controls_detected':controls,'skill_routes':{'normal':6,'unsupported':4,'scope':'structural only; model behavior unrun'},'random_samples':0}))
if __name__=='__main__':main()
