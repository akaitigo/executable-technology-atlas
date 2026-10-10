import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(c,v):
    f=json.loads((ROOT/'fixtures.json').read_text())[c];e=oracle.inspect(c);a=v['result']
    assert v['case']==c and v['fixture']==f and v['utc'].endswith('+00:00')
    for n,h in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for k,x in e.items():assert a[k]==x,(c,k,a[k],x)
    ind=oracle.independent(f)
    if ind:
        assert ind['sccs']==a['sccs'] and ind['impacted_modules']==a['impacted_modules']
        assert a['selected_test_counts']=={t:1 for t in e['selected_tests']}
        assert len(a['trace'])<=4*len(f['nodes'])+len(f['edges'])
        owner={n:'+'.join(g) for g in ind['sccs'] for n in g}
        expected=sorted({(owner[x],owner[y]) for x,y in f['edges'] if owner[x]!=owner[y]})
        assert a['condensation_edges']==[list(x) for x in expected]
        # Topological sink removal is independent of producer impact traversal.
        remaining=set(owner.values());arcs=set(expected)
        while remaining:
            sinks={x for x in remaining if not any(a==x and b in remaining for a,b in arcs)}
            assert sinks;remaining-=sinks
    else:assert a['selected_test_counts']=={} and a['trace']==[]
def verify():
    files=sorted((ROOT/'observations').glob('*/raw.json'));assert files
    for p in files:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for c,v in raw.items():validate(c,v)
        for k in ['sccs','condensation_edges','cyclic_sccs','impacted_sccs','impacted_modules','selected_tests']:assert raw['cycle-price']['result'][k]==raw['order-reversed']['result'][k]
    rejected=[]
    for label,c,k,x in [('split cyclic SCC','cycle-price','sccs',[['audit'],['invoice'],['price'],['report']]),('omit cyclic impact','cycle-price','impacted_modules',['report']),('duplicate test','cycle-price','selected_tests',['T-invoice','T-price','T-report','T-price']),('include independent audit','cycle-price','selected_tests',['T-audit','T-invoice','T-price','T-report']),('unknown accepted','unknown-change','status','ANALYZED'),('fault no loss','bad-cycle','missing_modules',[])]:
        v=copy.deepcopy(raw[c]);v['result'][k]=x
        try:validate(c,v)
        except AssertionError:rejected.append(label);continue
        raise AssertionError('escaped '+label)
    return dict(analyzed=5,bad_selection=2,expected_subset_refusals=2,recorded_runs=len(files),mutants_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
