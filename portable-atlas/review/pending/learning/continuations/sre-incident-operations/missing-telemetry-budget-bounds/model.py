import json,sys
from fractions import Fraction
class Refused(Exception):pass
def exact(x,k,reason):
 if not isinstance(x,dict) or set(x)!=set(k):raise Refused(reason)
def integer(x,lo,hi,reason):
 if type(x)!=int or not lo<=x<=hi:raise Refused(reason)
def validate(x):
 exact(x,['target','cutoff','ledger','observations'],'FIELDS');exact(x['target'],['num','den'],'TARGET');integer(x['target']['den'],1,10,'TARGET');integer(x['target']['num'],0,x['target']['den'],'TARGET');integer(x['cutoff'],0,10,'CUTOFF')
 if not isinstance(x['ledger'],list) or len(x['ledger'])>6:raise Refused('LEDGER')
 ids=set()
 for row in x['ledger']:
  exact(row,['id','eligible'],'LEDGER')
  if not isinstance(row['id'],str) or row['id'] not in list('ABCDEF') or row['id'] in ids or type(row['eligible'])!=bool:raise Refused('LEDGER')
  ids.add(row['id'])
 if not isinstance(x['observations'],list) or len(x['observations'])>6:raise Refused('OBSERVATION')
 seen=set()
 for o in x['observations']:
  exact(o,['id','result','arrived_tick'],'OBSERVATION')
  if not isinstance(o['id'],str) or o['id'] not in ids or o['id'] in seen or o['result'] not in ['good','bad']:raise Refused('OBSERVATION')
  seen.add(o['id']);integer(o['arrived_tick'],0,10,'ARRIVAL')
def bounds(a,b):return dict(lower=str(a),upper=str(b))
def process(x):
 validate(x);obs={o['id']:o for o in x['observations'] if o['arrived_tick']<=x['cutoff']};late=sorted(o['id'] for o in x['observations'] if o['arrived_tick']>x['cutoff']);groups=dict(good=[],bad=[],unknown=[],excluded=[]);rows=[]
 for l in sorted(x['ledger'],key=lambda l:l['id']):
  o=obs.get(l['id']);state='excluded' if not l['eligible'] else o['result'] if o else 'unknown';groups[state].append(l['id']);rows.append(dict(id=l['id'],eligible=l['eligible'],state=state.upper(),arrived_tick=o['arrived_tick'] if o else None))
 g,b,u=map(lambda k:len(groups[k]),['good','bad','unknown']);n=g+b+u;s=g+b;target=Fraction(x['target']['num'],x['target']['den']);q=n*(1-target);seen=Fraction(g,s) if s else None;sli=bounds(Fraction(g,n),Fraction(g+u,n)) if n else None;remaining=bounds(q-b-u,q-b);burn=bounds(Fraction(b,n)/(1-target),Fraction(b+u,n)/(1-target)) if n and target<1 else None
 decision='NO_ELIGIBLE' if not n else 'CERTAIN_MET' if Fraction(g,n)>=target else 'CERTAIN_MISSED' if Fraction(g+u,n)<target else 'INDETERMINATE';reason='NO_ELIGIBLE' if not n else 'ZERO_BUDGET' if target==1 else 'DEFINED'
 return dict(status='OBSERVED',target=str(target),cutoff=x['cutoff'],counts=dict(eligible=n,good=g,bad=b,unknown=u,seen=s,excluded=len(groups['excluded'])),groups=groups,lateIDs=late,rows=rows,seenOnlySLI=str(seen) if seen is not None else None,seenOnlyVerdict='NO_SEEN' if seen is None else 'MET' if seen>=target else 'MISSED',allowedBudget=str(q),badBounds=dict(lower=b,upper=b+u),sliBounds=sli,remainingBounds=remaining,burnBounds=burn,burnReason=reason,decision=decision,ledgerCompleteAssumed=True,productionGuarantee='UNCONFIRMED',approval='UNCONFIRMED',clock='synthetic cutoff; no real collector')
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read())
  if '--fail' in sys.argv:raise RuntimeError('injected bounds evaluator error')
  out=process(x);code=0
 except (Refused,json.JSONDecodeError) as e:out=dict(status='INPUT_REFUSED',reason=str(e) if isinstance(e,Refused) else 'JSON');code=2
 except Exception as e:out=dict(status='EXECUTION_FAILURE',reason=type(e).__name__);code=1
 print(json.dumps(out));sys.exit(code)
