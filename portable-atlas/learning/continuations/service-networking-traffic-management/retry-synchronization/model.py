"""Finite virtual-tick retry lesson. No network, clocks, sleep or randomness."""
import copy

FIXTURE = {
    'schema':'atlas-fixed-retry-concentration-v1', 'clients':['A','B','C','D'],
    'initial_tick':0, 'last_tick':7, 'attempt_duration':1, 'capacity_per_tick':1, 'max_retries':2,
    'cases':[
        {'id':'synchronized','call_budget':12,'delays':[[1,1],[1,1],[1,1],[1,1]]},
        {'id':'staggered','call_budget':12,'delays':[[1,1],[1,1],[2,1],[3,1]]},
        {'id':'skewed','call_budget':12,'delays':[[1,1],[1,1],[1,1],[1,3]]},
        {'id':'budget-five','call_budget':5,'delays':[[1,1],[1,1],[1,1],[1,1]]}]}


class InvalidInput(ValueError):
    def __init__(self):
        super().__init__('FIXED_INPUT_REQUIRED')
        self.attempts = 0
        self.state_updates = 0


def identical(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, dict):
        return a.keys()==b.keys() and all(identical(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a)==len(b) and all(identical(x,y) for x,y in zip(a,b))
    return a==b


def _simulate(case, fixture):
    clients = {c:dict(client=c,status='WAITING',attempts=0,retries_used=0,
                    retries_remaining=2,next_due=0,in_flight_finish=None,
                    completion_tick=None,terminal_tick=None,effects=0) for c in fixture['clients']}
    attempts=[]; denials=[]; ticks=[]; calls=0
    for now in range(8):
        completed=[]
        for event in [e for e in attempts if e['finish']==now]:
            state=clients[event['client']]
            state['in_flight_finish']=None
            if event['accepted']:
                state.update(status='SUCCEEDED',completion_tick=now,terminal_tick=now)
                state['effects']+=1
            elif state['retries_remaining']==0:
                state.update(status='RETRY_EXHAUSTED',terminal_tick=now)
            else:
                delay=case['delays'][fixture['clients'].index(state['client'])][state['retries_used']]
                state.update(status='WAITING',next_due=now+delay)
            completed.append(dict(client=event['client'],ordinal=event['ordinal'],
                                  outcome=event['outcome'],effect=int(event['accepted'])))
        candidates=[c for c in fixture['clients'] if clients[c]['status']=='WAITING' and clients[c]['next_due']==now]
        started=[]; accepted=[]; blocked=[]
        for client in candidates:
            state=clients[client]
            state['next_due']=None
            if calls>=case['call_budget']:
                state.update(status='CALL_BUDGET',terminal_tick=now)
                blocked.append(client); denials.append(dict(tick=now,client=client))
                continue
            if state['attempts']>0:
                state['retries_used']+=1
                state['retries_remaining']-=1
            calls+=1; state['attempts']+=1
            admitted=len(accepted)<fixture['capacity_per_tick']
            if admitted:accepted.append(client)
            started.append(client)
            state.update(status='RUNNING',in_flight_finish=now+1)
            attempts.append(dict(client=client,ordinal=state['attempts'],start=now,finish=now+1,
                                 accepted=admitted,outcome='SUCCESS' if admitted else 'OVERLOADED'))
        ticks.append(dict(tick=now,completed=completed,candidates=candidates,started=started,
                          accepted=accepted,budget_denied=blocked,calls_used=calls,
                          budget_remaining=case['call_budget']-calls,
                          retries_used=sum(s['retries_used'] for s in clients.values()),
                          effects=sum(s['effects'] for s in clients.values()),
                          clients=copy.deepcopy(list(clients.values()))))
    final=list(clients.values())
    # The fixed contract ends by t7. This is not a general horizon policy.
    assert all(s['status'] in ('SUCCEEDED','RETRY_EXHAUSTED','CALL_BUDGET') for s in final)
    summary=dict(calls=calls,retries=sum(s['retries_used'] for s in final),
                 effects=sum(s['effects'] for s in final),duplicate_effects=sum(max(0,s['effects']-1) for s in final),
                 succeeded=sum(s['status']=='SUCCEEDED' for s in final),
                 not_succeeded=sum(s['status']!='SUCCEEDED' for s in final),
                 unfinished=sum(s['terminal_tick'] is None for s in final),
                 retry_exhausted=sum(s['status']=='RETRY_EXHAUSTED' for s in final),
                 call_budget=sum(s['status']=='CALL_BUDGET' for s in final),
                 budget_remaining=case['call_budget']-calls,
                 peak_all_starts=max(len(t['started']) for t in ticks),
                 peak_retry_starts=max(sum(e['start']==t['tick'] and e['ordinal']>1 for e in attempts) for t in ticks),
                 last_terminal_tick=max(s['terminal_tick'] for s in final))
    return dict(id=case['id'],attempts=attempts,budget_denials=denials,ticks=ticks,
                clients=copy.deepcopy(final),summary=summary)


def calculate(fixture):
    # All cases and types are validated before any client state is created.
    if not identical(fixture,FIXTURE):raise InvalidInput()
    return {'cases':[_simulate(c,fixture) for c in fixture['cases']]}
