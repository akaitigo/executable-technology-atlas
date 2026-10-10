"""Read-only independent hand-state / transition contract; no store engine imports."""
import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RESOURCES={
 'base':{'id':'base','depends_on':[],'value':{'zone':'task-local'}},
 'config':{'id':'config','depends_on':['base'],'value':{'text':'v2'}},
 'service':{'id':'service','depends_on':['config'],'value':{'replicas':2}},
}
# Handwritten before record, not derived from planner output.
HAND={'normal':(0,['base','config','service'],[]), 'before-second':(70,['base'],['config','service']), 'after-second':(71,['base','config'],['service'])}
def state(ids):return {'revision':len(ids),'resources':{name:RESOURCES[name] for name in ids}}
def events(command):return [json.loads(line) for line in command['stdout'].splitlines()]
def inspect(raw,contract):
    issues=[]
    if len(raw['cases'])!=3 or {c['id'] for c in raw['cases']}!=set(HAND):return ['case denominator']
    if contract['initial']!={'revision':0,'resources':{}} or contract['desired']!={'resources':list(RESOURCES.values())}:issues.append('independent desired/initial')
    for case in raw['cases']:
        name=case['id'];code,partial_ids,remaining=HAND[name];want=state(partial_ids)
        if case['first_exit']!=code or case['partial']!=want:issues.append(name+': no automatic rollback / partial state')
        if case['blind_exit']!=22 or case['after_blind']!=want:issues.append(name+': duplicate replay unchanged')
        if case['refreshed']!=want:issues.append(name+': actual refresh')
        recovery={'observed_revision':len(partial_ids),'actions':[{'operation':'create','resource':RESOURCES[id]} for id in remaining],'scope':'synthetic create-only ordered plan'}
        if case['recovery_plan']!=recovery:issues.append(name+': independently fixed recovery suffix')
        if case['recovery_exit']!=0 or case['final']!=state(['base','config','service']):issues.append(name+': final state')
        if case['noop_plan']!={'observed_revision':3,'actions':[],'scope':'synthetic create-only ordered plan'} or case['noop_exit']!=0 or case['noop_store_hash_mtime_unchanged'] is not True:issues.append(name+': second no-op')
        trace=case['trace'];expected=['apply-start']
        for i in range(len(partial_ids)):expected+=['action-start','persisted']
        if name=='normal':expected+=['apply-complete']
        elif name=='before-second':expected+=['action-start','injected-fault']
        else:expected+=['injected-fault']
        if [e['kind'] for e in trace]!=expected:issues.append(name+': fault boundary trace')
        writes=[e for e in trace if e['kind']=='persisted']
        if [e['id'] for e in writes]!=partial_ids or [e['state'] for e in writes]!=[state(partial_ids[:i+1]) for i in range(len(partial_ids))]:issues.append(name+': intermediate write states')
        if name!='normal' and (trace[-1].get('rollback') is not False or trace[-1].get('point')!=name or trace[-1].get('revision')!=len(partial_ids)):issues.append(name+': explicit failure')
        times=[datetime.fromisoformat(e['at']) for e in trace]
        if times!=sorted(times):issues.append(name+': trace UTC ordering')
    return issues
def main():
    payload=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.PARTIAL_OBSERVATION = ').strip().removesuffix(';'))
    raw=payload['raw'];folder=ROOT/'observations'/raw['run_id']
    assert raw==json.loads((folder/'raw.json').read_text()) and payload['contracts']==json.loads((folder/'contracts.json').read_text()),'UI binding'
    for path,digest in raw['source_digests'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'source '+path
    index=json.loads((folder/'artifact-index.json').read_text())['artifacts']
    assert set(index)=={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'},'artifact denominator'
    for path,info in index.items():
        data=(folder/path).read_bytes();assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256'],'artifact '+path
    assert not inspect(raw,payload['contracts']),inspect(raw,payload['contracts'])
    for case in raw['cases']:
        name=case['id'];directory=folder/name;code,partial_ids,remaining=HAND[name]
        for file,key in [('partial.json','partial'),('after-blind.json','after_blind'),('refreshed.json','refreshed'),('final.json','final'),('store.json','final'),('recovery-plan.json','recovery_plan'),('noop-plan.json','noop_plan')]:assert json.loads((directory/file).read_text())==case[key],name+'/'+file+' actual store binding'
        assert json.loads((directory/'initial.json').read_text())==state([])
        original=json.loads((directory/'original-plan.json').read_text());assert original=={'observed_revision':0,'actions':[{'operation':'create','resource':r} for r in RESOURCES.values()],'scope':'synthetic create-only ordered plan'}
        expected_codes={'initial-plan':0,'first-apply':code,'blind-replay':22,'refresh':0,'replan':0,'recovery-apply':0,'second-plan':0,'noop-apply':0}
        for label,want in expected_codes.items():
            cmd=json.loads((directory/(label+'-command.json')).read_text());assert cmd['exit']==want and cmd['timeout_seconds']==5
            assert datetime.fromisoformat(cmd['started_at'])<=datetime.fromisoformat(cmd['ended_at'])
            if want==0:assert cmd['stderr']==''
            elif want==22:assert 'DuplicateCreate: base' in cmd['stderr']
            else:assert 'InjectedFault: '+name in cmd['stderr']
            if label=='first-apply':assert events(cmd)==case['trace']
            if label=='refresh':assert events(cmd)[0]['state']==case['refreshed'] and events(cmd)[0]['sha256']==index[name+'/partial.json']['sha256']
            if label=='recovery-apply':assert [e['id'] for e in events(cmd) if e['kind']=='persisted']==remaining
    negative=[]
    for label in ('pretend-rollback','blind-overwrite','recreate-all','false-noop'):
        bad=copy.deepcopy(raw)
        if label=='pretend-rollback':bad['cases'][1]['partial']=state([])
        elif label=='blind-overwrite':bad['cases'][1]['after_blind']=state(['base','config','service'])
        elif label=='recreate-all':bad['cases'][2]['recovery_plan']['actions'].insert(0,{'operation':'create','resource':RESOURCES['base']})
        else:bad['cases'][2]['noop_store_hash_mtime_unchanged']=False
        assert inspect(bad,payload['contracts']),label;negative.append(label)
    from route import ROUTES,UNSUPPORTED,route
    assert all(route(q)['target']==target and not route(q)['executed'] for q,target in ROUTES.items())
    assert all(not route(q)['supported'] and not route(q)['executed'] for q in UNSUPPORTED)
    skill=ROOT/'skills/atlas-partial-apply-recovery/SKILL.md'
    for target in re.findall(r'\]\(([^)]+)\)',skill.read_text()):assert (skill.parent/target).resolve().is_file(),target
    print(json.dumps({'cases':3,'independent_hand_transitions':True,'negative_controls':negative,'command_store_binding':True,'source_artifacts':True,'skill_routes':'6 normal / 4 unsupported; structural only','read_only':True},ensure_ascii=False))
if __name__=='__main__':main()
