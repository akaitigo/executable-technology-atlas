"""Finite fictional state model, no network or cloud calls."""
import argparse,datetime,hashlib,itertools,json,platform,time
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODES=['shared','local','replicated']
def load(n):return json.loads((ROOT/n).read_text())
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def ratio(f):return {'numerator':f.numerator,'denominator':f.denominator,'text':str(f)}
def validate(faults):
    if type(faults) is not list or any(type(x) is not str for x in faults):raise ValueError('invalid-fault-list')
    if len(set(faults))!=len(faults):raise ValueError('duplicate-fault')
    if any(x not in load('fixture.json')['faults'] for x in faults):raise ValueError('unknown-fault')
def evaluate(mode,faults):
    validate(faults)
    if mode not in MODES:raise ValueError('unsupported-mode')
    architecture=load('architectures.json');nodes=architecture['nodes'];graph=architecture['graphs'][mode];failed=set(faults)
    health={n:n not in failed and v['zone'] not in failed for n,v in nodes.items()};paths=[]
    def walk(path):
        n=path[-1]
        if n.startswith('dep-'):
            blocked=[x for x in path if not health[x]];cost=sum(nodes[x]['latency'] for x in path)
            if nodes[path[1]]['zone']!=nodes[n]['zone']:cost+=load('fixture.json')['latencySynthetic']['crossZone']
            paths.append({'nodes':path,'blockedNodes':blocked,'usable':not blocked,'latencySyntheticUnits':cost});return
        for child in graph[n]:walk(path+[child])
    walk(['router']);usable=[p for p in paths if p['usable']];best=min(usable,key=lambda p:(p['latencySyntheticUnits'],p['nodes'])) if usable else None
    return {'mode':mode,'faults':sorted(faults),'nodeHealth':health,'graph':graph,'paths':paths,'serviceUp':bool(usable),'selectedPath':best['nodes'] if best else None,'latencySyntheticUnits':best['latencySyntheticUnits'] if best else None}
def matrix():
    f=load('fixture.json');rows=[];up=Fraction(f['upProbability']['numerator'],f['upProbability']['denominator']);sums={m:Fraction(0) for m in MODES}
    for bits in itertools.product((False,True),repeat=len(f['faults'])):
        faults=[n for n,b in zip(f['faults'],bits) if b];weight=up**(len(bits)-sum(bits))*(1-up)**sum(bits);results=[evaluate(m,faults) for m in MODES]
        for r in results:
            if r['serviceUp']:sums[r['mode']]+=weight
        rows.append({'mask':''.join('1' if b else '0' for b in bits),'faults':faults,'probabilityUnderAssumptions':ratio(weight),'results':results})
    return {'faultOrder':f['faults'],'rows':rows,'assumption':'all seven Bernoulli failure variables independent, up=99/100; fictional snapshot probability, not measured availability or SLA','modeledAvailability':{m:ratio(v) for m,v in sums.items()},'upStateCounts':{m:sum(next(r for r in x['results'] if r['mode']==m)['serviceUp'] for x in rows) for m in MODES}}
def run(case):
    f=load('fixture.json')
    if case not in f['cases']:raise ValueError('unsupported-case')
    faults=f['cases'][case];start=time.perf_counter_ns()
    try:results=[evaluate(m,faults) for m in MODES];status='modeled';reason=None
    except ValueError as e:results=[];status='rejected';reason=str(e)
    return {'case':case,'input':faults,'inputDigest':digest(faults),'status':status,'reason':reason,'results':results,'executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executionObservedNs':time.perf_counter_ns()-start,'environment':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()},'scope':'fictional read-only dependency model; replication already complete; no write quorum, service latency measurement, SLA or real cloud'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=list(load('fixture.json')['cases']),default='dep-a');a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))
