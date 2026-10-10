import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent

def validate(case,v):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];hand=json.loads((ROOT/'hand-oracle.json').read_text())['cases'][case];r=v['result']
    assert v['case']==case and v['fixture']==f and v['utc'].endswith('+00:00') and v['runtime']['python']
    assert set(v['source_binding'])=={'search.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    assert r['status']==hand['status']
    if case=='negative-cost':
        assert r==dict(status='INPUT_REJECTED',reason='NEGATIVE_COST',search_started=False,algorithms={});return
    assert r['search_started'] is True;o=oracle.inspect(f)
    assert [[p['path'],p['cost']] for p in o['paths']]==hand['simple_paths']
    for key in ['min_cost','min_hops','least_cost_paths']:assert o[key]==hand[key]
    for node,d in o['distance_to_goal'].items():assert d is None or f['h'][node]<=d
    expected_checks=[dict(edge=[u,w,c],left=f['h'][u],right=c+f['h'][w],consistent=f['h'][u]<=c+f['h'][w]) for u,w,c in f['edges']]
    assert r['heuristic_checks']==expected_checks and all(c['consistent'] for c in expected_checks)
    assert set(r['algorithms'])=={'bfs','dijkstra','astar'}
    for name,a in r['algorithms'].items():
        path=a['path'];trace=a['trace'];assert trace and trace[0]['event']=='pop' and trace[0]['node']==f['start']
        if path is None:assert not o['paths'] and a['cost'] is None and a['hops'] is None;continue
        assert path[0]==f['start'] and path[-1]==f['goal'] and len(set(path))==len(path)
        pc=next(p for p in o['paths'] if p['path']==path);assert a['cost']==pc['cost'] and a['hops']==pc['hops']
        assert trace[-1]['event']=='pop' and trace[-1]['path']==path and trace[-1]['cost']==a['cost']
        if name=='bfs':assert path==hand['bfs_path'] and a['hops']==o['min_hops'] and a['cost']==hand['bfs_cost']
        else:assert path in o['least_cost_paths'] and a['cost']==o['min_cost']
        for t in trace:
            if t['event']=='pop':
                if name!='bfs':assert t['priority']==t['cost']+(f['h'][t['node']] if name=='astar' else 0)
                assert len(t['path'])<=5
    if all(c==1 for u,w,c in f['edges']):assert r['algorithms']['bfs']['cost']==o['min_cost']
    bad=r['bad_judgment'];assert bad==dict(enabled=case=='bad-bfs-cost-claim',claims_bfs_min_cost=case=='bad-bfs-cost-claim',rule_failed=case=='bad-bfs-cost-claim')
    return o

def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for case,v in raw.items():validate(case,v)
    rejected=[]
    def reject(label,case,edit):
        v=copy.deepcopy(raw[case]);edit(v)
        try:validate(case,v)
        except (AssertionError,StopIteration,KeyError):rejected.append(label);return
        raise AssertionError('mutation escaped '+label)
    reject('BFS weighted cost mislabeled','weighted',lambda v:v['result']['algorithms']['bfs'].update(cost=2))
    reject('Dijkstra expensive route accepted','weighted',lambda v:v['result']['algorithms']['dijkstra'].update(path=['S','G'],cost=10,hops=1))
    reject('Astar f priority corrupted','weighted',lambda v:v['result']['algorithms']['astar']['trace'][0].update(priority=0))
    reject('negative edge search marked started','negative-cost',lambda v:v['result'].update(search_started=True))
    reject('bad claim declared safe','bad-bfs-cost-claim',lambda v:v['result']['bad_judgment'].update(rule_failed=False))
    reject('heuristic edge check forged','weighted',lambda v:v['result']['heuristic_checks'][0].update(right=0))
    return dict(strict_cases=5,reachable=4,unreachable=1,bad_judgments=1,expected_input_refusals=1,recorded_runs=len(paths),oracle='all simple paths + hand table, no heap/relaxation',mutations_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
