#!/usr/bin/env python3
"""Atlas: compare saved runtime values with fixed hand expectations, never run Kotlin."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(r,files=True):
    checks=[]
    def check(ok,n):
        checks.append(n)
        if not ok:raise AssertionError(n)
    e=json.loads((ROOT/'expected.json').read_text());bindings=json.loads((ROOT/'binding-expectations.json').read_text())['cases']
    check(r['collection_complete'] is True and r['errors']==[],'complete without execution errors')
    check((r['compile_count'],r['jvm_count'],r['retry_count'])==(1,1,0),'one compile one JVM no retries')
    check(r['exec_attempt_counts']=={'compile':1,'runtime':1} and r['unconfirmed_target_starts']==[],'confirmed starts separate from attempts')
    check(r['input_unchanged'] is True and r['elapsed_seconds']<45,'inputs unchanged and bounded time')
    if files:
        for n,h in r['input_sha256'].items():check(digest(ROOT/n)==h,'input '+n)
        gate=r['resource_gate'];check(digest(ROOT/gate['path'])==gate['sha256'],'resource bytes')
        check(0<=gate['age_seconds']<=120,'fresh gate')
        from run import validate_gate_binding
        validate_gate_binding(gate['record']);check(True,'resource policy and root reference binding')
        from resource_policy import evaluate
        check(evaluate(gate['record'])['allowed'],'resource decision')
    check(len(r['commands'])==2,'two command records')
    for c,soft in zip(r['commands'],[12,8]):
        check(c['success'] and c['exit_code']==0 and not c['timed_out'] and c['target_start_confirmed'],'actual process success '+c['label'])
        check(c['owned_process_reaped'] and c['owned_group_after']=='absent','owned child recovered '+c['label'])
        p=c['priority'];check(p['priority']['verified_before_exec'] and p['priority']['after']>=10 and p['exec_attempted'],'actual priority '+c['label'])
        check(p['cpu_limit']['verified_before_exec'] and p['cpu_limit']['actual']==[soft,soft+1],'CPU limit '+c['label'])
        if files:
            for stream in ['stdout','stderr']:
                x=c[stream];f=ROOT/x['path'];check(digest(f)==x['sha256'] and f.stat().st_size==x['bytes'],'complete '+c['label']+' '+stream)
            if c['label']=='runtime':check([json.loads(l) for l in (ROOT/c['stdout']['path']).read_text().splitlines()]==r['records'],'complete stdout to records')
    rows=r['records'];check(len(rows)==5,'five complete runtime records')
    env=rows[0];check(env['kind']=='environment' and env['kotlin_version']=='2.4.10' and env['java_version']=='17.0.17' and env['thread']=='main' and env['workers_created']==0,'runtime environment; compiler pinned separately')
    check(rows[-1]=={'kind':'batch-complete','cases':3,'workers_created':0},'batch terminator')
    for actual,expected,b in zip(rows[1:4],e['cases'],bindings):
        check(actual['kind']=='case' and actual['id']==expected['id']==b['id'],'case order')
        check(len(actual['snapshots'])==6,'six snapshots '+actual['id'])
        for i,(a,x) in enumerate(zip(actual['snapshots'],expected['snapshots'])):
            for key in x:check(a[key]==x[key],actual['id']+' '+str(i)+' '+key)
        check(actual['final']==expected['final'],'final counters/classification '+actual['id'])
        for k in ['provider_same_reference','slot_same_reference','binding_owner_references_match','access_owner_references_match']:
            check(actual['binding'][k] is b[k],'actual reference relation '+actual['id']+' '+k)
        check(actual['binding']['property_names']==['label']*(5+expected['final']['bind_calls']),'property metadata '+actual['id'])
    if files:
        a=r['artifact'];check(digest(ROOT/a['path'])==a['sha256'],'artifact bytes')
    return checks

def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args();r=json.loads(args.run.read_text());report={'project':'Atlas','run':str(args.run),'run_sha256':digest(args.run),'passed':False,'errors':[]}
    try:
        report['checks']=verify(r);report['count']=len(report['checks']);tests=[]
        def changed(name,fn):
            x=copy.deepcopy(r);fn(x)
            try:verify(x,False)
            except AssertionError as ex:tests.append({'name':name,'rejected':True,'reason':str(ex)});return
            raise AssertionError('mutation accepted: '+name)
        changed('shared counters doubled',lambda x:x['records'][3]['final'].update(get_calls=8))
        changed('bind repeated during reads',lambda x:x['records'][2]['snapshots'][2].update(bind_calls=4))
        changed('snapshot introduced getter',lambda x:x['records'][1]['snapshots'][0]['owners'][0].update(gets=1))
        changed('same provider confused with same slot',lambda x:x['records'][2]['binding'].update(slot_same_reference=True))
        changed('design violation treated as runtime failure',lambda x:x['records'][3]['final'].update(runtime_exit=1))
        changed('wrong access owner reference',lambda x:x['records'][3]['binding'].update(access_owner_references_match=False))
        changed('write lost',lambda x:x['records'][1]['snapshots'][3]['owners'][0].update(value='A'))
        changed('priority not established',lambda x:x['commands'][0]['priority']['priority'].update(after=0))
        report['mutations']=tests;report['passed']=True
    except Exception as ex:report['errors'].append({'type':type(ex).__name__,'detail':str(ex)})
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report.get('count'),'mutations':len(report.get('mutations',[]))}));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
