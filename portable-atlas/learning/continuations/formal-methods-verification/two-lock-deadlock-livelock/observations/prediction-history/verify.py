# SPDX-License-Identifier: Apache-2.0
import argparse,copy,hashlib,json,platform,re,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import model,oracle,route
HERE=Path(__file__).resolve().parent
SOURCE=['model.py','oracle.py','verify.py','route.py','serve.py','hand-oracle.json','index.html','source.html','README.md','VERIFICATION.md','coverage.json','sources.json','skills/atlas-two-lock-deadlock-livelock/SKILL.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tup(id):return tuple(map(int,id.split(',')))
def edge_set(result):return {(tup(e['source']),tup(e['target']),e['process'],e['action']) for e in result['edges']}
def check_path(edges,allowed,start=None,cycle=False):
 assert edges
 if start is not None:assert tup(edges[0]['source'])==start
 for i,e in enumerate(edges):
    assert (tup(e['source']),tup(e['target']),e['process'],e['action']) in allowed
    if i:assert edges[i-1]['target']==e['source']
 if cycle:
    assert edges[0]['source']==edges[-1]['target']
    assert all(not all(pc==3 for pc in tup(e['source'])[:2]) for e in edges)
def validate_result(r):
 spec=oracle.graph(r['mode']);actual={tuple(s['state']) for s in r['states']};assert actual==spec['reachable'] and len(actual)==len(r['states']);assert edge_set(r)==spec['edges'] and len(edge_set(r))==len(r['edges'])
 for row in r['states']:
    s=tuple(row['state']);assert row['id']==model.sid(s) and row['distance']==spec['distance'][s]
    enabled={(s,tup(e['target']),e['process'],e['action']) for e in row['enabled']};expected={e for e in spec['edges'] if e[0]==s};assert enabled==expected
    assert row['completed']==(s[0]==s[1]==3);assert row['deadlock']==(not expected and not row['completed']);assert row['safe']==not_both(s)
 assert r['deadlock_count']==sum(s['deadlock'] for s in r['states']) and r['terminal_count']==sum(s['completed'] for s in r['states']) and r['safety_violations']==sum(not s['safe'] for s in r['states'])==0
 if r['shortest_deadlock_trace']:
    check_path(r['shortest_deadlock_trace'],spec['edges'],(0,0,-1,-1));last=tup(r['shortest_deadlock_trace'][-1]['target']);assert not any(e[0]==last for e in spec['edges']) and last[:2]!=(3,3);assert len(r['shortest_deadlock_trace'])==min(spec['distance'][tuple(s['state'])] for s in r['states'] if s['deadlock'])
 else:assert r['deadlock_count']==0
 if r['completion_trace']:
    check_path(r['completion_trace'],spec['edges'],(0,0,-1,-1));assert tup(r['completion_trace'][-1]['target'])[:2]==(3,3)
 if r['noncompletion_cycle']:
    check_path(r['noncompletion_cycle'],spec['edges'],cycle=True)
    if r['cycle_prefix']:
        check_path(r['cycle_prefix'],spec['edges'],(0,0,-1,-1));assert r['cycle_prefix'][-1]['target']==r['noncompletion_cycle'][0]['source']
    else:assert tup(r['noncompletion_cycle'][0]['source'])==(0,0,-1,-1)
 return spec
def not_both(s):return not (s[0]==2 and s[1]==2)
def hand_path(states,actions,mode):
 result=[]
 for i,(a,b) in enumerate(zip(states,states[1:])):
    answer=oracle.edge(tuple(a),tuple(b),mode);assert answer is not None
    if actions is not None:assert list(answer)==actions[i]
    result.append(dict(source=model.sid(a),target=model.sid(b),process=answer[0],action=answer[1]))
 return result

def execute():
 hand=json.loads((HERE/'hand-oracle.json').read_text());runs=[];pair_checks=0
 for mode in model.MODES:
    r=model.explore(mode);spec=validate_result(r);pair_checks+=len(spec['rows'])**2
    pairs={(e[0],e[1]) for e in spec['edges']};assert all(a!=b and (b,a) not in pairs for a,b in pairs)
    if mode=='retry':assert len(r['noncompletion_cycle'])==3 # independent absence of 1/2-edge cycles establishes minimality
    else:assert all(sum(b[:2])==sum(a[:2])+1 for a,b in pairs) # strict rank, no nonstuttering cycle
    if mode=='opposite':
        assert r['deadlock_count']==1 and len(r['shortest_deadlock_trace'])==2 and tup(r['shortest_deadlock_trace'][-1]['target'])==tuple(hand['opposite_deadlock_states'][-1]);assert r['noncompletion_cycle'] is None
        witness=hand_path(hand['opposite_deadlock_states'],hand['opposite_deadlock_actions'],mode);check_path(witness,spec['edges'],(0,0,-1,-1));r['hand_trace']=witness
    elif mode=='same-order':
        assert r['deadlock_count']==0 and r['noncompletion_cycle'] is None and r['terminal_count']==1;r['hand_trace']=hand_path(hand['same_order_completion_states'],None,mode);check_path(r['hand_trace'],spec['edges'],(0,0,-1,-1))
    else:
        assert r['deadlock_count']==0 and r['noncompletion_cycle'];r['hand_prefix']=hand_path(hand['retry_prefix_states'],None,mode);r['hand_cycle']=hand_path(hand['retry_balanced_cycle_states'],hand['retry_balanced_cycle_actions'],mode);check_path(r['hand_prefix'],spec['edges'],(0,0,-1,-1));check_path(r['hand_cycle'],spec['edges'],cycle=True);assert r['hand_prefix'][-1]['target']==r['hand_cycle'][0]['source'];assert all(tup(e['source'])[:2] not in [(2,2),(3,3)] for e in r['hand_cycle'])
    r['ownership_wait_table']=[dict(state=list(x['state']),waiting=x['waiting'],holds=x['holds']) for x in spec['rows']];runs.append(r)
 invalid=[]
 cases=[('unknown-mode',[0,0,-1,-1],'other'),('state-length',[0,0],'opposite'),('bool',[False,0,-1,-1],'opposite'),('float',[0.0,0,-1,-1],'opposite'),('pc-range',[5,0,-1,-1],'retry'),('owner-range',[0,0,2,-1],'opposite'),('pc-owner',[1,0,-1,-1],'opposite'),('two-first-same',[1,1,0,-1],'same-order'),('retry-pc-in-normal',[4,0,0,-1],'opposite'),('done-holds',[3,0,0,-1],'opposite')]
 for name,state,mode in cases:
    try:model.successors(state,mode)
    except ValueError as e:invalid.append(dict(id=name,state=state,mode=mode,status='EXPECTED_REFUSAL',error=str(e)))
    else:raise AssertionError(name)
 mutations=[]
 for name in ['missing-edge','stuttering-edge','false-terminal-deadlock','wrong-owner','nonclosing-cycle','disconnected-prefix']:
    r=copy.deepcopy(runs[2] if name in ['nonclosing-cycle','disconnected-prefix'] else runs[1]);r.pop('ownership_wait_table',None)
    if name=='missing-edge':r['edges'].pop()
    elif name=='stuttering-edge':r['edges'].append(dict(source=r['initial'],target=r['initial'],process=0,action='stutter'))
    elif name=='false-terminal-deadlock':next(x for x in r['states'] if x['completed'])['deadlock']=True
    elif name=='wrong-owner':r['states'][0]['state'][2]=0
    elif name=='nonclosing-cycle':r['noncompletion_cycle']=r['noncompletion_cycle'][:-1]
    else:r['cycle_prefix']=r['completion_trace']
    try:validate_result(r)
    except (AssertionError,ValueError,KeyError):mutations.append(dict(id=name,status='EXPECTED_REJECTION'))
    else:raise AssertionError(name)
 return dict(runs=runs,invalid_inputs=invalid,evidence_mutations=mutations,independent_pair_candidates=pair_checks,state_contract=hand['contract'],author_routing=dict(deadlock=route.route('deadlock'),tlc=route.route('tlc')),scope='Finite graph enumeration; no stuttering/fairness theorem/TLC/real OS locks/general formal proof')
def docs():
 for f in ['README.md','skills/atlas-two-lock-deadlock-livelock/SKILL.md']:
    for link in re.findall(r'\]\(([^)]+)\)',(HERE/f).read_text()):
        if not link.startswith(('https:','#')):assert ((HERE/f).parent/link.split('#')[0].split('?')[0]).resolve().exists(),link
 c=json.loads((HERE/'coverage.json').read_text());ids={r['id'] for r in json.loads((HERE/'sources.json').read_text())};assert 2<=len(c['next_experiments'])<=4 and all(r['source'] in ids for r in c['areas']+c['next_experiments'])
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--record');g.add_argument('--seal-record',action='store_true');args=p.parse_args();started=datetime.now(timezone.utc).isoformat();raw=execute();name=args.record or 'attempt-01';folder=HERE/'observations'/name
 if args.record:
    assert re.fullmatch(r'attempt-[0-9]+',name);folder.mkdir(exist_ok=False);raw['attempt']=dict(command='python3 verify.py --record '+name,started_at_utc=started,completed_at_utc=datetime.now(timezone.utc).isoformat(),exit_code=0,toolchain=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),input_sha256=sha(HERE/'hand-oracle.json'),executed_source_sha256={f:sha(HERE/f) for f in ['model.py','oracle.py','verify.py']})
    (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 else:
    old=json.loads((folder/'raw.json').read_text());assert {k:v for k,v in old.items() if k!='attempt'}==raw
 docs();sources={f:sha(HERE/f) for f in SOURCE};qa=json.loads((HERE/'observations/ui-qa.json').read_text())
 if qa['status']=='passed':
    for k,f in [('observed_ui_sha256','index.html'),('observed_sources_sha256','sources.json'),('observed_coverage_sha256','coverage.json'),('observed_raw_sha256','observations/attempt-01/raw.json')]:assert qa[k]==sha(HERE/f)
    ui=json.loads((HERE/'observations/ui-matrix.json').read_text());assert len(ui['rows'])==9 and len(ui['refusals'])==3
    assert {(r['mode'],r['step']) for r in ui['rows']}=={('opposite',s) for s in [0,1,2]}|{('same-order',s) for s in [0,3,6]}|{('retry',s) for s in [2,4,8]}
    assert all(r['prediction']=='cycle' and r['result'] and r['answer'] and r['retained_state']=='1,1,0,1' and r['status'].startswith('拒否') for r in ui['refusals'])
    assert all(not r['prediction'] and not r['result'] and not r['answer'] for r in ui['mode_resets']+[ui['view_reset']])
    assert ui['cycle_replay']['start']==ui['cycle_replay']['end']=='0,1,-1,1' and ui['cycle_replay']['next_enabled'] is False
    for r in ui['rows']:
        run=next(x for x in raw['runs'] if x['mode']==r['mode']);path=run['hand_prefix']+run['hand_cycle'] if r['mode']=='retry' else run['hand_trace'];assert r['state_id']==(path[r['step']-1]['target'] if r['step'] else run['initial']);actual=next(x for x in run['states'] if x['id']==r['state_id']);assert r['state']==actual['state'] and r['deadlock']==actual['deadlock'] and r['completed']==actual['completed'] and r['enabled_count']==len(actual['enabled'])
 if args.record or args.seal_record:
    files=[f for f in folder.iterdir() if f.name!='receipt.json']+[f for f in (HERE/'observations').iterdir() if f.is_file() and f.name!='read-only-proof.json'];receipt=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),command='python3 verify.py '+('--seal-record' if args.seal_record else '--record '+name),exit_code=0,sources=sources,artifacts={str(f.relative_to(HERE)):sha(f) for f in files},checks=dict(pair_graph_and_hand='passed',expected_refusals=10,evidence_mutation_rejections=6,actual_iab=qa['status'],skill='author smoke; not independent AgentEval'))
    (folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 else:
    receipt=json.loads((folder/'receipt.json').read_text());assert receipt['sources']==sources
    for f,h in receipt['artifacts'].items():assert sha(HERE/f)==h,f
 print(json.dumps(dict(status='passed',graphs=[dict(mode=r['mode'],states=len(r['states']),edges=len(r['edges']),deadlocks=r['deadlock_count'],terminals=r['terminal_count'],cycle_length=len(r['noncompletion_cycle'] or [])) for r in raw['runs']],pair_candidates=raw['independent_pair_candidates'],expected_refusals=10,evidence_mutations=6,record=args.record,seal_record=args.seal_record)))
if __name__=='__main__':main()
