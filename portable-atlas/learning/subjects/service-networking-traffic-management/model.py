"""virtual timeのみ。固定callable、serial request、有限breaker/retry。"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ARRIVALS=list(range(0,16,2));HARD_CALL_LIMIT=24
SOURCES={'breaker':'https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker','retry':'https://learn.microsoft.com/en-us/azure/architecture/patterns/retry','envoy':'https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking'}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
def validate(threshold,cooldown,retries,deadline,budget,recovery):
    for label,v,lo,hi in [('threshold',threshold,1,3),('cooldown',cooldown,1,4),('retries',retries,0,2),('deadline',deadline,0,5),('budget',budget,1,16)]:
        if type(v)is not int or not lo<=v<=hi:raise ValueError(f'{label} integer {lo}..{hi}')
    if recovery not in ('4','8','never'):raise ValueError('unsupported recovery fixture')
class FixedService:
    def __init__(self,recovery):self.recovery=recovery;self.calls=[]
    def __call__(self,request,start):
        if len(self.calls)>=HARD_CALL_LIMIT:raise ValueError('hard call limit')
        success=self.recovery!='never' and start>=int(self.recovery)
        raw={'request':request,'start':start,'finish':start+1,'return':{'ok':success,'value':'fixed-ok' if success else 'fixed-failure'}}
        self.calls.append(raw);return success

def simulate(threshold,cooldown,retries,deadline,budget,recovery,mode):
    service=FixedService(recovery);now=0;state='closed';failures=0;until=None;transitions=[];requests=[]
    for req,arrival in enumerate(ARRIVALS):
        now=max(now,arrival);start=now;events=[];attempt=0;outcome=None
        while outcome is None: # bad retry also stops at the independent hard call limit
            if len(service.calls)>=HARD_CALL_LIMIT:outcome='hard-limit';break
            if mode=='protected':
                if state=='open':
                    if now<until:outcome='open-rejected';break
                    transitions.append({'at':now,'from':'open','to':'half-open','reason':'cooldown-elapsed'});state='half-open'
                if len(service.calls)>=budget:outcome='budget-rejected';break
                if now+1>arrival+deadline:outcome='deadline-rejected';break
            before=state;ok=service(req,now);now+=1
            events.append({'kind':'call','attempt':attempt,'at':now-1,'finish':now,'ok':ok,'state':before})
            if mode=='protected':
                if ok:
                    failures=0
                    if state=='half-open':transitions.append({'at':now,'from':'half-open','to':'closed','reason':'probe-success'});state='closed'
                else:
                    failures+=1
                    if state=='half-open' or failures>=threshold:
                        transitions.append({'at':now,'from':state,'to':'open','reason':'probe-failure' if state=='half-open' else 'failure-threshold'});state='open';until=now+cooldown
            if ok:outcome='success'
            elif mode=='protected' and state=='open':outcome='failure-open'
            elif mode=='protected' and attempt>=retries:outcome='retry-limit'
            else:
                wait=2**attempt if mode=='protected' else 0
                events.append({'kind':'retry-wait','start':now,'finish':now+wait,'delay':wait});now+=wait;attempt+=1
        requests.append({'request':req,'arrival':arrival,'start':start,'finish':now,'absoluteDeadline':arrival+deadline,'outcome':outcome,'stateAfter':state,'failureCount':failures,'openUntil':until,'events':events})
    return {'mode':mode,'requests':requests,'transitions':transitions,'calls':service.calls,'callCount':len(service.calls),'finalState':state,'virtualFinish':now,'traceSha256':digest({'requests':requests,'transitions':transitions,'calls':service.calls})}
def experiment(threshold=2,cooldown=3,retries=1,deadline=5,budget=16,recovery='8'):
    validate(threshold,cooldown,retries,deadline,budget,recovery)
    inputs=dict(zip(('threshold','cooldown','retries','deadline','budget','recovery'),(threshold,cooldown,retries,deadline,budget,recovery)))
    return {'input':inputs,'arrivals':ARRIVALS,'hardCallLimit':HARD_CALL_LIMIT,'protected':simulate(threshold,cooldown,retries,deadline,budget,recovery,'protected'),'bad':simulate(threshold,cooldown,retries,deadline,budget,recovery,'bad-retry-storm')}
