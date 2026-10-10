"""Atlas: inspect saved JSON only; never import or rerun CSP producer."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect(run):
    checks = []
    def check(label, ok): checks.append({'label': label, 'passed': bool(ok)})
    expect = json.loads((ROOT / 'expected.json').read_text())
    fixture = json.loads((ROOT / 'inputs/problems.json').read_text())
    check('complete', run.get('collection_complete') and run.get('target_count') == 1 and not run.get('errors'))
    check('fixed-inputs', run.get('input_unchanged') and all(sha(ROOT / n) == h for n,h in run['input_sha256'].items()))
    command = run['commands'][0]
    check('priority-cleanup', command['success'] and command['priority']['priority']['verified_before_exec'] and command['priority']['cpu_limit']['verified_before_exec'] and command['owned_process_reaped'] and command['owned_group_after'] == 'absent' and command['exit_code'] == 0)
    stream = ROOT / command['stdout']['path']
    check('stdout-binding', sha(stream) == command['stdout']['sha256'] and [json.loads(x) for x in stream.read_text().splitlines()] == run['records'])
    gate = run['resource_gate']; observation = gate['record']
    check('resource-binding', sha(ROOT / gate['path']) == gate['sha256'] and json.loads((ROOT / gate['path']).read_text()) == observation and gate['age_seconds'] <= 60 and observation['allowed'])
    check('policy-binding', observation['policy_input_hashes'] == {n:sha(ROOT / n) for n in ['resources.py','resource_parse.py','resource_policy.py']})
    check('reference-binding', observation['root_browser_reference_sha256'] == sha(ROOT / 'records/root-browser-reference.json') and observation['root_browser_reference'] == json.loads((ROOT / 'records/root-browser-reference.json').read_text()))
    decision = observation['root_batch_decision_file']; dp=Path(decision['path'])
    check('decision-binding', sha(dp)==decision['sha256'] and json.loads(dp.read_text())==observation['root_batch_decision'])
    check('fixture-binding', run['records'][1]['fixture']==fixture and run['records'][1]['sha256']==sha(ROOT / 'inputs/problems.json'))
    cases = [r for r in run['records'] if r['kind']=='case']
    check('case-order', [c['id'] for c in cases] == [e['id'] for e in expect['cases']])
    for c,e in zip(cases,expect['cases']):
        tag=c['id'];p=next(p for p in fixture['problems'] if p['id']==c['problem'])
        def ck(label,ok): check(tag+':'+label,ok)
        for name in ['solutions','metrics','final_assignment','final_domains','final_trail','classification']:
            ck(name,c[name]==e[name])
        # Separate fixed all-assignment oracle, not another recursive search.
        valid=[]
        for bits in expect['all_assignments']:
            a=dict(zip('ABCD',map(int,bits)))
            if all(a[v] in p['initial_domains'][v] for v in 'ABCD') and all(a[x]!=a[y] for x,y in p['edges']):valid.append(bits)
        ck('full-assignment-oracle', c['solutions']==valid if c['mode']!='missing-restore' else c['solutions']==['0101'] and valid==['0101','1010'])
        events=c['events'];prev={'assignment':{},'domains':copy.deepcopy(p['initial_domains']),'trail':[],'solutions':[],'metrics':{k:0 for k in e['metrics']}}
        action_counts={k:0 for k in e['metrics']};counter_actions={'ENTER':'search_calls','TRY':'candidate_attempts','CHECK_ASSIGNED':'assigned_constraint_tests','REJECT_CANDIDATE':'consistency_rejections','CHECK_FUTURE':'propagation_tests','PRUNE':'removed_values','RESTORE':'restored_values','WIPEOUT':'domain_wipeouts','SOLUTION':'solutions'}
        all_transitions=True;reasons=True;restores=True;checks_correct=True;snapshots=True
        for seq,t in enumerate(events):
            action=t['action'];d=t['detail'];a=copy.deepcopy(prev['assignment']);domains=copy.deepcopy(prev['domains']);trail=copy.deepcopy(prev['trail']);solutions=prev['solutions'][:]
            if action in counter_actions: action_counts[counter_actions[action]]+=1
            if action=='ASSIGN':a[d['variable']]=d['color']
            elif action=='UNASSIGN': a.pop(d['variable'],None)
            elif action=='PRUNE':
                v,k=d['variable'],d['color'];why=d['reason'];av=why['assigned_variable']
                reasons &= why['edge'] in p['edges'] and sorted([v,av])==why['edge'] and av in a and a[av]==why['assigned_color']==k and v not in a and k in domains[v]
                if k in domains[v]: domains[v].remove(k)
                trail.append([v,k])
            elif action=='RESTORE':
                pair=[d['variable'],d['color']]
                restores &= bool(trail) and trail[-1]==pair and len(trail)>d['mark'] and pair[1] not in domains[pair[0]]
                if trail:trail.pop()
                domains[pair[0]]=sorted(set(domains[pair[0]]+[pair[1]]))
            elif action=='SOLUTION':solutions.append(''.join(str(a[v]) for v in 'ABCD'))
            elif action=='CANDIDATES':snapshots &= d['candidates']==domains[d['variable']]
            elif action=='WIPEOUT':checks_correct &= domains[d['variable']]==[]
            elif action=='CHECK_ASSIGNED':checks_correct &= d['passes']==(d['color']!=d['neighbor_value']) and a.get(d['neighbor'])==d['neighbor_value']
            elif action=='CHECK_FUTURE':checks_correct &= d['passes']==(d['color']!=d['candidate']) and d['neighbor'] not in a and d['candidate'] in domains[d['neighbor']]
            all_transitions &= t['seq']==seq and t['assignment']==a and t['domains']==domains and t['trail']==trail and t['solutions']==solutions and t['metrics']==action_counts
            prev=t
        ck('event-transitions',all_transitions);ck('prune-reason',reasons);ck('restore-order',restores);ck('event-counter',action_counts==c['metrics']);ck('actual-checks',checks_correct);ck('candidate-snapshot',snapshots)
        ck('final-trace-state',prev['assignment']==c['final_assignment'] and prev['domains']==c['final_domains'] and prev['trail']==c['final_trail'] and prev['solutions']==c['solutions'])
        if c['id']=='triangle-isolated--forward-checking':
            witness=expect['important_witnesses']['triangle_after_A0']
            ck('nonempty-not-solved',any(t['assignment']==witness['assignment'] and t['domains']==witness['domains'] for t in events) and not c['solutions'])
        if c['mode']=='missing-restore':
            wipes=[(i,t) for i,t in enumerate(events) if t['action']=='WIPEOUT'];ck('fault-stop-before-D',len(wipes)==1 and wipes[0][1]['detail']['variable']=='B' and wipes[0][1]['assignment']=={'A':1} and not any(t['action']=='CHECK_FUTURE' for t in events[wipes[0][0]+1:]))
    return checks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);args=ap.parse_args();r=json.loads(args.run.read_text())
    checks=inspect(r);mutations=[]
    def mutate(name,change,label):
        v=copy.deepcopy(r);change(v);failed=[x['label'] for x in inspect(v) if not x['passed']]
        mutations.append({'name':name,'failed_labels':failed,'required_label':label,'passed':label in failed})
    def case(v): return next(c for c in v['records'] if c.get('id')=='square--forward-checking')
    mutate('solution missing',lambda v:case(v)['solutions'].pop(),'square--forward-checking:solutions')
    mutate('final domain corrupted',lambda v:case(v)['final_domains'].update(B=[1]),'square--forward-checking:final_domains')
    mutate('prune reason forged',lambda v:next(t for t in case(v)['events'] if t['action']=='PRUNE')['detail']['reason'].update(edge=['A','C']),'square--forward-checking:prune-reason')
    mutate('restore order forged',lambda v:next(t for t in case(v)['events'] if t['action']=='RESTORE')['detail'].update(variable='D'),'square--forward-checking:restore-order')
    mutate('counter corrupted',lambda v:case(v)['metrics'].update(candidate_attempts=99),'square--forward-checking:metrics')
    mutate('stdout binding corrupted',lambda v:v['commands'][0]['stdout'].update(sha256='0'*64),'stdout-binding')
    report={'project':'Atlas','passed':all(x['passed'] for x in checks+mutations),'checks':checks,'check_count':len(checks),'mutations':mutations,'target_runs':0,'scope':'saved-value checks and six mutations; producer not imported','run_sha256':sha(args.run),'verifier_sha256':sha(Path(__file__))}
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
