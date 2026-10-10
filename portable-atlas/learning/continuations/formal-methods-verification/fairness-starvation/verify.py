#!/usr/bin/env python3
"""Atlas: compare saved output to the pre-written oracle; never imports/runs the producer."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check_values(records,expected):
    checks=[]
    def eq(name,actual,wanted):checks.append({'name':name,'passed':actual==wanted,'actual':actual,'expected':wanted})
    eq('nine complete records',len(records),9)
    if len(records)!=9:return checks
    env,graph=records[:2];rows=records[2:-1];states=expected['states'];targets=['Next0','Next1','Enter1']
    eq('environment kind',env.get('kind'),'environment');eq('actual nice >= 10',type(env.get('nice')) is int and env['nice']>=10,True)
    eq('no workers',env.get('workers_created'),0);eq('CPU upper bound',env.get('cpu_limit_seconds'),[2,2])
    eq('finite graph counts',[graph.get('state_count'),graph.get('nonstutter_edges'),graph.get('added_stutter_edges'),graph.get('total_edges')],[8,14,8,22])
    eq('state set',sorted(map(str,graph.get('states',[]))),sorted(map(str,states.values())))
    all_edges=[(a,action,b) for a,action,b in expected['nonstutter_edges']]+[(a,'stutter',a) for a in states]
    def event(action):
        if action=='stutter':return None
        proc,op=action.split('.');return {'process':int(proc[1:]),'action':'check-and-enter' if op=='enter' else op}
    def actual_edge(a,action,b):return {'from':states[a],'to':states[b],'action':action,'process':None if action=='stutter' else int(action[1]),'source_event':event(action)}
    eq('all graph edges',sorted(json.dumps(x,sort_keys=True) for x in graph.get('edges',[])),sorted(json.dumps(actual_edge(*x),sort_keys=True) for x in all_edges))
    eq('graph limited scope',graph.get('arbitrary_cycles_enumerated'),False);eq('graph safety',graph.get('safety_holds'),True)
    eq('event alias',graph.get('event_alias'),{'check-and-enter':'enter'})
    eq('case order',[r.get('id') for r in rows],[x['id'] for x in expected['cases']])
    for r,e in zip(rows,expected['cases']):
        key=e['id'];eq(key+' kind',r.get('kind'),'lasso')
        for f in ['valid','safety_holds','enabled','executed','fair','p1_starves']:eq(key+' '+f,r.get(f),e[f])
        eq(key+' fairness units',r.get('fairness_order'),expected['fairness_order'])
        eq(key+' infinite execution not observed',r.get('infinite_execution_observed'),False)
        eq(key+' scope',r.get('scope'),'one prefix plus one repeated finite cycle')
        for segment in ['prefix','cycle']:
            aliases=e[segment+'_states'];actions=e[segment];out=r.get(segment+'_rows',[])
            eq(key+' '+segment+' states',r.get(segment+'_states'),[states[x] for x in aliases]);eq(key+' '+segment+' actions',r.get(segment+'_actions'),actions)
            wanted=[]
            for i,action in enumerate(actions):
                a,b=aliases[i:i+2];options=[x[1] for x in expected['nonstutter_edges'] if x[0]==a]
                enabled={'Next0':any(x.startswith('P0.') for x in options),'Next1':any(x.startswith('P1.') for x in options),'Enter1':'P1.enter' in options}
                executed={'Next0':action.startswith('P0.'),'Next1':action.startswith('P1.'),'Enter1':action=='P1.enter'}
                wanted.append({**actual_edge(a,action,b),'ordinal':i,'segment':segment,'enabled':enabled,'executed':executed,'nonstutter_choices':options})
            for i,(got,want) in enumerate(zip(out,wanted)):eq(key+' '+segment+' edge '+str(i),got,want)
            eq(key+' '+segment+' row count',len(out),len(wanted))
        predicates={}
        for t in targets:
            en=e['enabled'][t];ex=e['executed'][t]
            predicates[t]={'all_enabled':all(en),'any_enabled':any(en),'any_executed':any(ex),'weak':not all(en) or any(ex),'strong':not any(en) or any(ex)}
        eq(key+' fairness predicates',r.get('predicates'),predicates)
        # Follow ordered occurrences, not whether P1 was critical anywhere in its past.
        cycle= e['cycle_states'][:-1];prefix=e['prefix_states'][:-1];cyc_critical=any(states[x][1]=='critical' for x in cycle);obligations=[]
        for segment,names in [('prefix',prefix),('cycle',cycle)]:
            for i,name in enumerate(names):
                if states[name][1]!='waiting':continue
                later=segment=='prefix' and any(states[x][1]=='critical' for x in prefix[i+1:])
                obligations.append({'segment':segment,'position':i,'state':states[name],'later_prefix_critical':later,'cycle_contains_critical':cyc_critical,'eventually_critical':bool(later or cyc_critical)})
        eq(key+' ordered request obligations',r.get('progress_obligations'),obligations)
        eq(key+' response',r.get('p1_response_holds'),not e['p1_starves'])
        eq(key+' fair starvation counterexample',r.get('fair_starvation_counterexample'),[x and e['p1_starves'] for x in e['fair']])
    eq('batch completed',records[-1],{'kind':'batch-complete','case_count':6,'retry_count':0})
    return checks

def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--mutations',action='store_true');a=p.parse_args()
    run=json.loads(a.run.read_text());expected=json.loads((ROOT/'expected.json').read_text());checks=check_values(run['records'],expected)
    def ok(name,value):checks.append({'name':name,'passed':bool(value)})
    ok('complete without errors',run['collection_complete'] and run['errors']==[] and run['input_unchanged'])
    ok('one target zero retries',run['target_count']==1 and run['exec_attempt_count']==1 and run['target_retry']==0 and run['target_start_unknown']==[])
    ok('one command',len(run['commands'])==1)
    c=run['commands'][0];pr=c['priority'];ok('priority recorded before exec',pr['priority']['verified_before_exec'] and pr['priority']['after']>=10 and pr['exec_attempted'])
    ok('bounded successful cleanup',c['success'] and c['exit_code']==0 and not c['timed_out'] and c['timeout_seconds']==3 and c['owned_process_reaped'] and c['owned_group_after']=='absent' and run['elapsed_seconds']<=11.5)
    for stream in ['stdout','stderr']:
        item=c[stream];f=ROOT/item['path'];ok(stream+' bytes/hash',f.stat().st_size==item['bytes'] and sha(f)==item['sha256'])
    raw=(ROOT/c['stdout']['path']).read_text();ok('all stdout parsed exactly',[json.loads(x) for x in raw.splitlines()]==run['records'])
    ok('stderr empty',(ROOT/c['stderr']['path']).read_bytes()==b'')
    for name,digest in run['input_sha256'].items():ok('input unchanged '+name,sha(ROOT/name)==digest)
    ok('graph input correspondence',run['records'][1]['input_sha256']==sha(ROOT/'inputs/lassos.json'))
    g=run['resource_gate'];ok('fresh resource saved',0<=g['age_seconds']<=120 and sha(ROOT/g['path'])==g['sha256'] and g['record']==json.loads((ROOT/g['path']).read_text()))
    from resource_gate import decide
    ok('resource policy still matches',decide(g['record'])==g['recomputed_decision'] and g['recomputed_decision']['allowed'])
    ok('bounded explicit environment',run['explicit_environment']=={'PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0','LC_ALL':'C','LANG':'C'})
    mutations=[]
    if a.mutations:
        def reject(label,change):
            altered=copy.deepcopy(run['records']);change(altered);failed=[x['name'] for x in check_values(altered,expected) if not x['passed']];mutations.append({'name':label,'rejected':bool(failed),'failed_checks':failed})
        reject('weak uses any instead of all',lambda r:r[5]['fair'].__setitem__(1,False))
        reject('strong vacuity is lost',lambda r:r[4]['fair'].__setitem__(2,False))
        reject('stutter counted as P1 execution',lambda r:r[2]['cycle_rows'][0]['executed'].__setitem__('Next1',True))
        reject('old entry satisfies new request',lambda r:r[7].__setitem__('p1_starves',False))
        reject('enabled read from destination',lambda r:r[5]['cycle_rows'][1]['enabled'].__setitem__('Enter1',False))
        reject('nonclosed cycle',lambda r:r[5]['cycle_states'].__setitem__(-1,expected['states']['B']))
        reject('invalid prefix edge',lambda r:r[2]['prefix_rows'][0].__setitem__('action','P0.enter'))
        reject('general cycle enumeration claim',lambda r:r[1].__setitem__('arbitrary_cycles_enumerated',True))
    result={'project':'Atlas','run_path':str(a.run.resolve().relative_to(ROOT)),'run_sha256':sha(a.run),'expected_sha256':sha(ROOT/'expected.json'),'passed':all(x['passed'] for x in checks) and all(x['rejected'] for x in mutations),'checks':len(checks),'details':checks,'mutations':mutations,'new_target_executions':0,'scope':'saved finite output only; no GUI or general-model theorem'}
    f=a.run.parent/'verification.json';f.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['details']},ensure_ascii=False));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
