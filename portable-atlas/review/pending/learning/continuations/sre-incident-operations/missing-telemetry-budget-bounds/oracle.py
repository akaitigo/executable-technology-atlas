# Enumerate all missing outcomes; custom integer ratios, no model/Fraction import.
import json,sys,itertools,math,functools
def rat(n,d=1):
 assert d!=0
 if d<0:n,d=-n,-d
 g=math.gcd(n,d);return (n//g,d//g)
def show(a):return str(a[0]) if a[1]==1 else str(a[0])+'/'+str(a[1])
def sub(a,b):return rat(a[0]*b[1]-b[0]*a[1],a[1]*b[1])
def div(a,b):return rat(a[0]*b[1],a[1]*b[0])
def cmp(a,b):return (a[0]*b[1]>b[0]*a[1])-(a[0]*b[1]<b[0]*a[1])
def extremes(values):
 sorted_values=sorted(values,key=functools.cmp_to_key(cmp));return dict(lower=show(sorted_values[0]),upper=show(sorted_values[-1]))
def check(r,x,literal=None):
 if literal and 'status' in literal:assert r==literal;return
 eligible={l['id'] for l in x['ledger'] if l['eligible']};excluded=sorted({l['id'] for l in x['ledger']}-eligible);ontime={o['id']:o for o in x['observations'] if o['arrived_tick']<=x['cutoff']};good=sorted(i for i in eligible if i in ontime and ontime[i]['result']=='good');bad=sorted(i for i in eligible if i in ontime and ontime[i]['result']=='bad');unknown=sorted(eligible-set(good)-set(bad));g,b,u,n=len(good),len(bad),len(unknown),len(eligible);s=g+b;target=rat(x['target']['num'],x['target']['den']);allowed=rat(n*(x['target']['den']-x['target']['num']),x['target']['den']);possibilities=list(itertools.product([0,1],repeat=u));badcounts=[b+u-sum(v) for v in possibilities];slis=[rat(g+sum(v),n) for v in possibilities] if n else None;remainders=[sub(allowed,rat(v)) for v in badcounts];burns=[div(rat(v),allowed) for v in badcounts] if n and allowed[0]>0 else None
 decision='NO_ELIGIBLE' if not n else 'CERTAIN_MET' if all(cmp(v,target)>=0 for v in slis) else 'CERTAIN_MISSED' if all(cmp(v,target)<0 for v in slis) else 'INDETERMINATE';seen=rat(g,s) if s else None;reason='NO_ELIGIBLE' if not n else 'ZERO_BUDGET' if allowed[0]==0 else 'DEFINED';rows=[dict(id=l['id'],eligible=l['eligible'],state='EXCLUDED' if not l['eligible'] else 'GOOD' if l['id'] in good else 'BAD' if l['id'] in bad else 'UNKNOWN',arrived_tick=ontime[l['id']]['arrived_tick'] if l['id'] in ontime else None) for l in sorted(x['ledger'],key=lambda l:l['id'])]
 expected=dict(status='OBSERVED',target=show(target),cutoff=x['cutoff'],counts=dict(eligible=n,good=g,bad=b,unknown=u,seen=s,excluded=len(excluded)),groups=dict(good=good,bad=bad,unknown=unknown,excluded=excluded),lateIDs=sorted(o['id'] for o in x['observations'] if o['arrived_tick']>x['cutoff']),rows=rows,seenOnlySLI=show(seen) if seen is not None else None,seenOnlyVerdict='NO_SEEN' if seen is None else 'MET' if cmp(seen,target)>=0 else 'MISSED',allowedBudget=show(allowed),badBounds=dict(lower=min(badcounts),upper=max(badcounts)),sliBounds=extremes(slis) if slis else None,remainingBounds=extremes(remainders),burnBounds=extremes(burns) if burns else None,burnReason=reason,decision=decision,ledgerCompleteAssumed=True,productionGuarantee='UNCONFIRMED',approval='UNCONFIRMED',clock='synthetic cutoff; no real collector');assert r==expected
 if literal:
  assert [n,g,b,u]==literal['counts']
  for k in ['seenOnlySLI','allowedBudget','decision','burnReason']:assert r[k]==literal[k],k
  for k in ['sliBounds','remainingBounds','burnBounds']:assert ([r[k]['lower'],r[k]['upper']] if r[k] else None)==literal[k],k
if __name__=='__main__':
 a=json.loads(sys.stdin.read());check(a['result'],a['input']);print(json.dumps(dict(status='passed',independent=True)))
