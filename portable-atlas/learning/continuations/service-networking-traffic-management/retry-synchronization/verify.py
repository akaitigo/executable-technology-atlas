"""Saved-only verifier: literal intervals + interval membership, no producer import."""
import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REFUSALS=['retry-bool','budget-float','capacity-bool','capacity-changed','delay-bool','delay-float',
          'delay-zero','delay-negative','delay-missing','client-order','case-id','extra-case',
          'missing-case','extra-key','schema','last-tick','missing-key']
SCOPE={'finite_virtual_tick_model':True,'network_requests':0,'sleep_calls':0,'random_draws':0,
       'real_proxy':False,'response_loss_modelled':False,'general_idempotency_claim':False,
       'browser_launches':0,'server_launches':0}


def exact(a,b):
    assert type(a) is type(b),('type',type(a).__name__,type(b).__name__)
    if isinstance(a,dict):
        assert a.keys()==b.keys(),'keys'
        for k in a:exact(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b),'length'
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b,('value',a,b)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def expected_client(client,t,attempts,denials,delays):
    started=[a for a in attempts if a['client']==client and a['start']<=t]
    finished=[a for a in started if a['finish']<=t]
    active=[a for a in started if a['start']<=t<a['finish']]
    success=[a for a in finished if a['accepted']]
    blocked=[d for d in denials if d['client']==client and d['tick']<=t]
    exhausted=[a for a in finished if a['ordinal']==3 and not a['accepted']]
    terminal=None;completion=None;due=None;flight=None
    if blocked:status='CALL_BUDGET';terminal=blocked[0]['tick']
    elif success:status='SUCCEEDED';terminal=completion=success[0]['finish']
    elif exhausted:status='RETRY_EXHAUSTED';terminal=exhausted[0]['finish']
    elif active:status='RUNNING';flight=active[0]['finish']
    else:
        status='WAITING'
        due=finished[-1]['finish']+delays[finished[-1]['ordinal']-1] if finished else 0
    retries=max(0,len(started)-1)
    return dict(client=client,status=status,attempts=len(started),retries_used=retries,
                retries_remaining=2-retries,next_due=due,in_flight_finish=flight,
                completion_tick=completion,terminal_tick=terminal,effects=len(success))


def expected_values(fixture,hand):
    cases=[];columns=hand['columns']
    for c in fixture['cases']:
        h=hand['cases'][c['id']]
        attempts=[dict(zip(columns['attempts'],r)) for r in h['attempts']]
        denials=[dict(zip(columns['budget_denials'],r)) for r in h['budget_denials']]
        ticks=[]
        for r in h['ticks']:
            row=dict(zip(columns['ticks'],r));t=row['tick']
            for k in ['candidates','started','accepted','budget_denied']:row[k]=list(row[k])
            row['budget_remaining']=c['call_budget']-row['calls_used']
            row['completed']=[dict(client=a['client'],ordinal=a['ordinal'],outcome=a['outcome'],effect=int(a['accepted']))
                              for a in attempts if a['finish']==t]
            row['clients']=[expected_client(client,t,attempts,denials,c['delays'][i])
                            for i,client in enumerate(fixture['clients'])]
            # Relations checked from the separately fixed interval list, not state updates.
            assert row['calls_used']==sum(a['start']<=t for a in attempts)
            assert row['retries_used']==sum(a['start']<=t and a['ordinal']>1 for a in attempts)
            assert row['effects']==sum(a['finish']<=t and a['accepted'] for a in attempts)
            assert row['started']==[a['client'] for a in attempts if a['start']==t]
            assert row['accepted']==[a['client'] for a in attempts if a['start']==t and a['accepted']]
            ticks.append(row)
        final=[dict(zip(columns['clients'],r),next_due=None,in_flight_finish=None) for r in h['clients']]
        exact(final,ticks[-1]['clients'])
        cases.append(dict(id=c['id'],attempts=attempts,budget_denials=denials,ticks=ticks,clients=final,summary=h['summary']))
    return {'cases':cases}


def check(data):
    assert set(data)=={'schema','run','fixture','values','scope','input_rejections'}
    assert data['schema']=='atlas-retry-concentration-run-v1'
    fixture=json.loads((ROOT/'fixtures.json').read_text())
    hand=json.loads((ROOT/'hand-oracle.json').read_text())
    exact(data['fixture'],fixture)
    exact(data['values'],expected_values(fixture,hand))
    exact(data['scope'],SCOPE)
    exact(data['input_rejections'],[dict(id=n,rejected=True,reason='FIXED_INPUT_REQUIRED',attempts=0,state_updates=0) for n in REFUSALS])
    run=data['run'];assert set(run)=={'run_id','observed_at_utc','pid','actual_nice','source_hashes'}
    assert type(run['pid']) is int and run['pid']>0
    assert type(run['actual_nice']) is int and run['actual_nice']==10
    timestamp=datetime.fromisoformat(run['observed_at_utc'])
    assert timestamp.utcoffset() is not None and timestamp.utcoffset().total_seconds()==0
    assert run['run_id']=='retry-concentration-'+timestamp.strftime('%Y%m%dT%H%M%S%fZ')
    exact(run['source_hashes'],{n:sha(ROOT/n) for n in ['model.py','observe.py','fixtures.json','CONTRACT.md','contract-lock.json']})
    for n,h in json.loads((ROOT/'contract-lock.json').read_text())['files'].items():assert sha(ROOT/n)==h,n
    return dict(cases=4,ticks=32,client_states=128,attempts=30,successes=13,overloaded=17,
                retries=14,budget_denials=2,input_rejections=17)


def tamper_checks(data):
    edits=[('call-count',['values','cases',0,'summary','calls'],8),
           ('candidate-missing',['values','cases',3,'ticks',2,'candidates'],['B']),
           ('budget-order',['values','cases',3,'budget_denials',0,'client'],'B'),
           ('retry-on-refusal',['values','cases',3,'ticks',2,'clients',2,'retries_remaining'],1),
           ('effect-before-finish',['values','cases',0,'ticks',0,'effects'],1),
           ('future-success-leak',['values','cases',1,'ticks',3,'clients',2,'status'],'SUCCEEDED'),
           ('late-due',['values','cases',2,'ticks',5,'clients',3,'next_due'],7),
           ('failure-to-success',['values','cases',0,'attempts',1,'outcome'],'SUCCESS'),
           ('admission',['values','cases',0,'attempts',1,'accepted'],True),
           ('start-based-delay',['values','cases',0,'ticks',1,'clients',2,'next_due'],1),
           ('initial-peak-hidden',['values','cases',1,'summary','peak_all_starts'],1),
           ('scope',['scope','random_draws'],1),('priority',['run','actual_nice'],0),
           ('refusal-updated',['input_rejections',0,'state_updates'],1),
           ('fixture-float',['fixture','attempt_duration'],1.0),
           ('missing-case',['values','cases'],data['values']['cases'][:-1])]
    out=[]
    for name,path,value in edits:
        bad=copy.deepcopy(data);target=bad
        for k in path[:-1]:target=target[k]
        target[path[-1]]=value
        try:check(bad)
        except (AssertionError,ValueError,KeyError,TypeError):out.append(dict(id=name,rejected=True))
        else:raise AssertionError('saved tamper accepted: '+name)
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();data=json.loads(a.result.read_text())
    report=dict(passed=True,result_path=str(a.result.resolve()),result_sha256=sha(a.result),
                verify_source_sha256=sha(Path(__file__)),run_id=data['run']['run_id'],checked=check(data),
                tamper_checks=tamper_checks(data),producer_executions=0)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
