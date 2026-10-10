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
    e=json.loads((ROOT/'expected.json').read_text())
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
    rows=r['records'];check(len(rows)==6,'six complete runtime records')
    env=rows[0];check(env['kind']=='environment' and env['kotlin_stdlib_version']=='2.4.10' and env['java_version']=='17.0.17' and env['max_workers']==2,'runtime environment; compiler pinned separately')
    check(type(env['main_thread_id']) is int,'actual main thread ID')
    check(rows[-1]=={'kind':'batch-complete','cases':4},'batch terminator')
    check(r['explicit_environment']['JAVA_OPTS']=='-Xms32m -Xmx256m -XX:ActiveProcessorCount=1','compiler JVM options')
    for a,x in zip(rows[1:5],e['cases']):
        label=x['id'];check(a['kind']=='case' and a['id']==label,'fixed case order '+label)
        check(a['complete'] is True and a['errors']==[],'case complete '+label)
        check(a['before_workers']=={'initialized':False,'initializer_calls':0,'payload_value':None,'payload_value_observed':False},'before getter is not a payload read '+label)
        check(a['initializer_calls']==1 and a['initialized_after'] is True,'one successful initialization '+label)
        check(a['initialization_detail_available'] is True and len(a['initialization'])==1,'initialization detail '+label)
        init=a['initialization'][0];check(init['event']=='constructed' and init['plain_initial_value']==0 and init['atomic_initial_value']==0,'constructor values '+label)
        workers=a['workers'];check(len(workers)==2 and [w['worker'] for w in workers]==['A','B'],'two collected workers '+label)
        ids=[w['thread_id'] for w in workers];check(all(type(i) is int and i>0 and i!=env['main_thread_id'] for i in ids) and len(set(ids))==2 and init['thread_id'] in ids,'two actual distinct worker IDs '+label)
        check(a['collection_order']==['A','B'] and a['collection_order_is_execution_order'] is False,'collection is not CPU order '+label)
        check(a['references']=={'worker_payloads_same':True,'main_payload_same':True,'atomic_storage_same':x['storage_references_same'],'update_lock_same':x['update_lock_references_same']},'actual reference identities '+label)
        check(a['cleanup']['executor_terminated'] is True and a['cleanup']['alive_threads']==[],'executor recovered '+label)
        check(sorted(t['id'] for t in a['cleanup']['created_threads'])==sorted(ids),'created and completed worker correspondence '+label)
        check(a['cleanup']['thread_join_budget_ms']==300 and sorted(t['id'] for t in a['cleanup']['thread_joins'])==sorted(ids) and all(t['alive_after'] is False for t in a['cleanup']['thread_joins']),'actual owned threads ended within finite join '+label)
        check(type(a['final_value']) is int and a['final_value']==x['final_value'] and a['classification']==x['classification'],'counter result and interpretation '+label)
        for w in workers:
            check(w['update_count']==1 and type(w['returned']) is int,'one update per worker '+label+w['worker'])
            if label=='plain-split': mid=[('read',0),('after-read-barrier-passed',None),('write',1)]
            elif label=='atomic-split': mid=[('atomic-get',0),('after-read-barrier-passed',None),('atomic-set',1)]
            elif label=='locked-rmw': mid=[('before-lock-barrier-passed',None),('locked-read',w['old']),('locked-write',w['written']),('lock-released',None)]
            else: mid=[('before-update-barrier-passed',None),('incrementAndGet-return',w['returned'])]
            events=[('start-passed',None),('payload-obtained',None)]+mid+[('worker-complete',w['returned'])]
            check(w['events']==[{'event':n,'value':v} for n,v in events],'worker-local partial order '+label+w['worker'])
        if label.endswith('split'):
            for key,wkey in [('cached_reads','old'),('written_values','written'),('worker_results','returned')]:check([w[wkey] for w in workers]==x[key],label+' '+key)
        elif label=='locked-rmw':
            check(all(type(w['old']) is int and type(w['written']) is int and w['returned']==w['written'] for w in workers),'return captured inside compound update '+label)
            check(sorted([[w['old'],w['written']] for w in workers])==x['sorted_old_new_pairs'],'lock order allowed set '+label)
            check(sorted(w['returned'] for w in workers)==x['sorted_worker_results'],'lock return set '+label)
        else:
            check(all(w['old'] is None and w['written'] is None for w in workers),'atomic old is not a separate observed get')
            check(sorted(w['returned'] for w in workers)==x['sorted_worker_results'],'atomic return allowed set')
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
        changed('lost update silently fixed',lambda x:x['records'][1].update(final_value=2))
        changed('split atomic treated as compound atomic',lambda x:x['records'][2]['workers'][1].update(returned=2))
        changed('same worker ID counted twice',lambda x:x['records'][1]['workers'][1].update(thread_id=x['records'][1]['workers'][0]['thread_id']))
        changed('different payload accepted',lambda x:x['records'][3]['references'].update(worker_payloads_same=False))
        changed('initialization duplicated',lambda x:x['records'][1].update(initializer_calls=2))
        changed('constructor value invented as pre-get read',lambda x:x['records'][1]['before_workers'].update(payload_value=0,payload_value_observed=True))
        changed('atomic old invented',lambda x:x['records'][4]['workers'][0].update(old=0))
        changed('collection called global order',lambda x:x['records'][2].update(collection_order_is_execution_order=True))
        changed('barrier moved after write',lambda x:x['records'][1]['workers'][0]['events'].reverse())
        changed('priority not established',lambda x:x['commands'][0]['priority']['priority'].update(after=0))
        report['mutations']=tests;report['passed']=True
    except Exception as ex:report['errors'].append({'type':type(ex).__name__,'detail':str(ex)})
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':report.get('count'),'mutations':len(report.get('mutations',[]))}));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
