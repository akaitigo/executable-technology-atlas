"""Independent literal oracle for every delivery sequence; no model/runner imports."""
import copy
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# final head IDs, final values, joined clock, accepted/rejected/delivered/duplicate/conflict, cost
EXPECTED={
 'connected':(['B1'],[21],[1,1],[2,0,2,0,0],174),
 'offline-logical':(['A2','B1'],[21,30],[2,1],[3,0,3,0,0],261),
 'offline-wallclock':(['A1'],[20],[2,1],[3,0,3,0,0],261),
 'buffer-one':(['A1','B1'],[20,30],[1,1],[2,1,2,0,0],174),
 'duplicates':(['A2','B1'],[21,30],[2,1],[3,0,3,1,0],346),
 'conflicting-duplicate':(['A2','B1'],[21,30],[2,1],[3,0,3,0,1],346),
 'invalid-value':([],[],[0,0],[0,2,0,0,0],0),
 'invalid-limit-zero':([],[],[0,0],[0,0,0,0,0],0),
 'invalid-limit-bool':([],[],[0,0],[0,0,0,0,0],0),
 'empty':([],[],[0,0],[0,0,0,0,0],0),
 'central-offline':([],[],[0,0],[0,3,0,0,0],0),
 'central-connected':(['B1'],[21],[1,1],[2,0,2,0,0],340),
 'zero-value':(['A1'],[0],[1,0],[1,0,1,0,0],87),
}
PACKETS={name:[] for name in EXPECTED}
for name in ('offline-logical','offline-wallclock','conflicting-duplicate'): PACKETS[name]=['A1','A2','B1']
PACKETS['buffer-one']=['A1','B1']; PACKETS['duplicates']=['A1','A2','B1','A2']; PACKETS['zero-value']=['A1']
HEAD_EVENTS={
 'A1':{'id':'A1','origin':'A','value':20,'version':[1,0],'wall_ms':100},
 'A2':{'id':'A2','origin':'A','value':21,'version':[2,0],'wall_ms':90},
 'B1':{'id':'B1','origin':'B','value':30,'version':[0,1],'wall_ms':80}}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def fp(value): return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def expect_events(name):
    if name in ('connected','central-connected'):
        return {'A1':HEAD_EVENTS['A1'],'B1':{'id':'B1','origin':'B','value':21,'version':[1,1],'wall_ms':101}}
    if name in ('offline-logical','offline-wallclock','duplicates','conflicting-duplicate'): return HEAD_EVENTS
    if name=='buffer-one': return {id:HEAD_EVENTS[id] for id in ('A1','B1')}
    if name=='zero-value': return {'A1':{'id':'A1','origin':'A','value':0,'version':[1,0],'wall_ms':0}}
    return {}

def inspect(name, record):
    result=record['result']; ids,values,clock,counts,cost=EXPECTED[name]; problems=[]
    expected_events=expect_events(name)
    if result['events']!=expected_events: problems.append('event hand oracle')
    for node in ('A','B'):
        s=result['state'][node]
        if [x['id'] for x in s['heads']]!=ids or [x['value'] for x in s['heads']]!=values or s['clock']!=clock or s['outbox']!=[] or not s['online']:
            problems.append('final state '+node)
        if s['heads']!=[expected_events[id] for id in ids]: problems.append('head envelope '+node)
        if s['seen']!={id:fp(event) for id,event in expected_events.items()}: problems.append('seen fingerprints '+node)
    if list(result['counts'].values())!=counts: problems.append('counts')
    if result['modeled_ms']!=cost: problems.append('modeled cost')
    if result['config_valid']!=(name not in ('invalid-limit-zero','invalid-limit-bool')): problems.append('config boundary')
    raw=result['raw']; operations=record['operations']
    if name.startswith('invalid-limit'):
        if len(raw)!=1 or raw[0]['disposition']!='invalid-config': problems.append('config unchanged')
    elif len(raw)!=len(operations) or [x['action'] for x in raw]!=operations:
        problems.append('all operations/raw binding')
    if raw[-1]['state']!=result['state'] or raw[-1]['counts']!=result['counts']: problems.append('final raw binding')
    if result['modeled_ms']!=sum(x.get('modeled_ms') or 0 for x in raw): problems.append('per operation cost')
    previous=None
    for step in raw:
        if previous is not None and step['at']<previous: problems.append('timestamp order')
        previous=step['at']
    if name in ('offline-logical','offline-wallclock','duplicates','conflicting-duplicate','buffer-one'):
        # Before reconnect both edits are local, outbox retained; no remote state is visible.
        offline=raw[3]['state']
        if offline['A']['online'] or offline['B']['online']: problems.append('offline placement')
        expected_A=['A1'] if name in ('offline-wallclock','buffer-one') else ['A2']
        if [x['id'] for x in offline['A']['heads']]!=expected_A or [x['id'] for x in offline['B']['heads']]!=['B1']: problems.append('local before sync')
        if offline['A']['outbox']!=(['A1'] if name=='buffer-one' else ['A1','A2']) or offline['B']['outbox']!=['B1']: problems.append('retained outbox')
    for i,x in enumerate(raw):
        if x['disposition'] in ('invalid-input','buffer-full-rejected','central-offline-blocked','same-id-conflict-held','duplicate-no-change') and i:
            if x['state']!=raw[i-1]['state']:
                # duplicate may acknowledge and remove outbox only on first successful delivery;
                # all duplicates in this input follow a successful original so entire state should match.
                problems.append('rejected/duplicate changed state')
    if name=='conflicting-duplicate' and raw[-1]['disposition']!='same-id-conflict-held': problems.append('conflict boundary')
    if name=='zero-value' and not any(x['disposition']=='offline-retained' and x['state']['A']['outbox']==['A1'] for x in raw): problems.append('offline send retention')
    return problems

def report(folder):
    assert {p.name for p in folder.iterdir() if p.is_dir()}==set(EXPECTED),'case denominator'
    rows=[]
    for name in EXPECTED:
        case=folder/name
        files=sorted(case.glob('sequence-*.json'))
        expected_orders=sorted(set(itertools.permutations(PACKETS[name])))
        records=[json.loads(p.read_text()) for p in files]
        assert [x['delivery_order'] for x in records]==[list(x) for x in expected_orders], 'all delivery sequences denominator '+name
        for record in records:
            issues=inspect(name,record)
            rows.append({'id':name,'sequence':record['sequence'],'delivery_order':record['delivery_order'],'expected':EXPECTED[name],'matches':not issues,'issues':issues})
    return {'oracle':'independent literal events/heads/clocks/counts/cost + all unique delivery sequences + boundary raw snapshots','rows':rows}

def check():
    payload=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.EDGE_OBSERVATION = ').removesuffix(';\n'))
    folder=ROOT/payload['directory']; index=json.loads((folder/'artifact-index.json').read_text()); run=json.loads((folder/'run.json').read_text())
    assert set(index)=={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'}
    for file,digest in index.items(): assert sha((folder/file).read_bytes())==digest,'artifact '+file
    for file,digest in run['source_digests'].items(): assert sha((ROOT/file).read_bytes())==digest,'stale source '+file
    assert payload['run']==run and run['started_at']<=run['completed_at']
    assert {x['id'] for x in payload['observations']}==set(EXPECTED)
    for observation in payload['observations']:
        name=observation['id']; case=folder/name
        assert observation['input']==json.loads((case/'input.json').read_text()),'input binding'
        records=[json.loads(p.read_text()) for p in sorted(case.glob('sequence-*.json'))]
        assert records==observation['sequences'],'UI raw binding'
        forged=copy.deepcopy(records[0]); forged['result']['modeled_ms']+=1
        assert inspect(name,forged),'cost negative control'
        forged=copy.deepcopy(records[0]); forged['result']['state']['A']['clock'][0]+=1
        assert inspect(name,forged),'clock negative control'
        if records[0]['result']['state']['A']['heads']:
            forged=copy.deepcopy(records[0]); forged['result']['state']['A']['heads'][0]['value']=99
            assert inspect(name,forged),'value negative control'
    actual=report(folder)
    assert all(x['matches'] for x in actual['rows']),actual
    assert json.loads(json.dumps(actual))==payload['oracle']
    assert json.loads((folder/'oracle-report.json').read_text())==payload['oracle']
    sources=json.loads((ROOT/'sources.json').read_text())
    assert all(x['url'].startswith('https://') and x['locator'] and x['binding'] for x in sources)
    for file in ('README.md','index.html','skills/atlas-edge-computing/SKILL.md'):
        text=(ROOT/file).read_text()
        for href in re.findall(r'(?:href="|\]\()([^"\)]+)',text):
            if ':' not in href and not href.startswith('#'): assert (ROOT/Path(file).parent/href.split('#')[0]).is_file(),(file,href)
    for term in ('前提','主要概念','実務判断','限界','次の実験','原典'):
        assert term in (ROOT/'README.md').read_text() and term in (ROOT/'index.html').read_text(),term
    print(json.dumps({'cases':len(EXPECTED),'sequences':len(actual['rows']),'matches':True,'read_only':True,'source_binding':True,'negative_controls':['cost','clock','value']}))

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--oracle-json': print(json.dumps(report(Path(sys.argv[2])),ensure_ascii=False))
    elif len(sys.argv)==1: check()
    else: raise SystemExit('usage: checker.py [--oracle-json RUN_DIRECTORY]')
