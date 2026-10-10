"""独立request-level transition/time oracle。modelもcallableもimportしない。"""
LOCATORS={'breaker':'https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker','retry':'https://learn.microsoft.com/en-us/azure/architecture/patterns/retry','envoy':'https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking'}
def expected(threshold,cooldown,retries,deadline,budget,recovery):
    clock=0;status='closed';count=0;unlock=None;failureRun=0;calls=[];requests=[];transitions=[]
    # Each request has pre-enumerated candidate slots. A request never retries
    # after reaching the threshold; half-open permits only a single probe.
    for rid,arrival in enumerate((0,2,4,6,8,10,12,14)):
        clock=arrival if clock<arrival else clock;requestStart=clock;reason=None
        if status=='open' and clock>=unlock:
            transitions.append({'at':clock,'from':'open','to':'half-open','reason':'cooldown-elapsed'});status='half-open'
        if status=='open':reason='open-rejected'
        for slot in range(retries+1):
            if reason:break
            if count==budget:reason='budget-rejected';break
            if clock>=arrival+deadline:reason='deadline-rejected';break # duration exactly one tick
            previous=status;success=recovery!='never' and clock>=int(recovery)
            calls.append([rid,clock,clock+1,success]);count+=1;clock+=1
            if success:
                failureRun=0;reason='success'
                if previous=='half-open':transitions.append({'at':clock,'from':'half-open','to':'closed','reason':'probe-success'});status='closed'
            else:
                failureRun+=1
                trip=previous=='half-open' or failureRun>=threshold
                if trip:
                    transitions.append({'at':clock,'from':previous,'to':'open','reason':'probe-failure' if previous=='half-open' else 'failure-threshold'});status='open';unlock=clock+cooldown;reason='failure-open'
                elif slot==retries:reason='retry-limit'
                else:clock+= (1,2,4)[slot]
        requests.append([rid,arrival,requestStart,clock,reason,status,failureRun,unlock])
    return {'calls':calls,'requests':requests,'transitions':transitions,'callCount':count,'finalState':status,'virtualFinish':clock}
def bad_expected(recovery):
    # Closed form per request: fill consecutive unit slots until recovery or
    # remaining global hard cap 24; no breaker, deadline, budget or wait.
    clock=0;calls=[];outcomes=[]
    for rid,arrival in enumerate((0,2,4,6,8,10,12,14)):
        clock=max(clock,arrival);start=clock;remaining=24-len(calls)
        duration=remaining if recovery=='never' else min(remaining,max(1,int(recovery)-clock+1))
        for tick in range(clock,clock+duration):calls.append([rid,tick,tick+1,recovery!='never' and tick>=int(recovery)])
        clock+=duration;outcomes.append('success' if duration and calls[-1][3] else 'hard-limit')
    return {'calls':calls,'callCount':len(calls),'virtualFinish':clock,'outcomes':outcomes}
