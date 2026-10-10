import sys
sys.dont_write_bytecode=True
import argparse,datetime,hashlib,json,platform,re
from html.parser import HTMLParser
import model,oracle
R=model.ROOT
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(o):return hashlib.sha256(o if isinstance(o,bytes) else o.encode()).hexdigest()
assert model.SOURCES==oracle.LOCATORS
assert sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
def call_projection(row):return [[c['request'],c['start'],c['finish'],c['return']['ok']] for c in row['calls']]
def projection(row):
 return {'protectedCalls':row['protected']['callCount'],'badCalls':row['bad']['callCount'],'finalState':row['protected']['finalState'],'protectedFinish':row['protected']['virtualFinish'],'badFinish':row['bad']['virtualFinish'],'outcomes':[r['outcome'] for r in row['protected']['requests']],'transitions':row['protected']['transitions'],'protectedTrace':row['protected']['traceSha256'],'badTrace':row['bad']['traceSha256']}
def compare(row):
 inp=row['input'];args=[inp[k] for k in ('threshold','cooldown','retries','deadline','budget','recovery')];e=oracle.expected(*args);b=oracle.bad_expected(inp['recovery']);r=row['protected'];bad=row['bad']
 assert call_projection(r)==e['calls']
 reqs=[[x['request'],x['arrival'],x['start'],x['finish'],x['outcome'],x['stateAfter'],x['failureCount'],x['openUntil']] for x in r['requests']]
 assert reqs==e['requests'] and r['transitions']==e['transitions']
 for key in ('callCount','finalState','virtualFinish'):assert r[key]==e[key]
 assert call_projection(bad)==b['calls'] and bad['callCount']==b['callCount'] and bad['virtualFinish']==b['virtualFinish'] and [x['outcome'] for x in bad['requests']]==b['outcomes']
 assert r['callCount']<=inp['budget'] and bad['callCount']<=24
 for name in ('protected','bad'):
  result=row[name];assert result['traceSha256']==sha(canonical({k:result[k] for k in ('requests','transitions','calls')}))
  assert result['callCount']==len(result['calls']) and len(result['requests'])==8
  for c in result['calls']:
   assert c['finish']==c['start']+1
   assert c['return']['value']==('fixed-ok' if c['return']['ok'] else 'fixed-failure')
  if name=='protected':
   for req in result['requests']:
    calls=[c for c in result['calls'] if c['request']==req['request']]
    assert len(calls)<=inp['retries']+1 and all(c['finish']<=req['absoluteDeadline'] for c in calls)
    for event in req['events']:
     if event['kind']=='retry-wait':assert event['finish']-event['start']==event['delay'] and event['delay'] in (1,2)
 row['oracle']=e;row['badOracle']=b;row['inputSha256']=sha(canonical(inp));row['rawSha256']=sha(canonical({'protected':r,'bad':bad}));return row
rows=[]
for threshold in (1,2):
 for cooldown in (1,3):
  for retries in (0,1,2):
   for deadline in (0,1,5):
    for budget in (1,16):
     for recovery in ('4','8','never'):rows.append(compare(model.experiment(threshold,cooldown,retries,deadline,budget,recovery)))
# Hand timeline: call0 fails at1, wait1, call2 fails at3→open until6;
# probe6 fails at7→open until10; probe10 succeeds at11→closed.
hand=[]
default=compare(model.experiment());assert default['protected']['callCount']==6 and default['bad']['callCount']==16
assert [x['at'] for x in default['protected']['transitions']]==[3,6,7,10,11]
assert [(x['from'],x['to']) for x in default['protected']['transitions']]==[('closed','open'),('open','half-open'),('half-open','open'),('open','half-open'),('half-open','closed')];hand.append(default)
bound=compare(model.experiment(1,3,0,1,16,'never'));assert bound['protected']['callCount']==4 and bound['bad']['callCount']==24
assert [x['start'] for x in bound['protected']['calls']]==[0,4,8,12];hand.append(bound)
zero=compare(model.experiment(deadline=0));assert zero['protected']['callCount']==0 and all(x['outcome']=='deadline-rejected' for x in zero['protected']['requests']);hand.append(zero)
one=compare(model.experiment(budget=1));assert one['protected']['callCount']==1 and all(x['outcome']=='budget-rejected' for x in one['protected']['requests']);hand.append(one)
rejects=[]
for index,values in [(0,[0,4,True,1.0]),(1,[0,5,True]),(2,[-1,3,False]),(3,[-1,6,True]),(4,[0,17,True]),(5,['live-service',8])]:
 for v in values:
  args=[2,3,1,5,16,'8'];args[index]=v
  try:model.experiment(*args)
  except ValueError as e:rejects.append({'input':args,'error':str(e)})
  else:raise AssertionError(args)
faults=[]
# Actual altered executions against the same expected policy, not fabricated status.
never=model.experiment(1,3,0,1,16,'never');assert never['bad']['callCount']>never['protected']['callCount'];faults.append({'fault':'unbounded retry policy, capped by independent teaching budget','raw':never['bad'],'expectedCalls':4,'detected':True})
wrong=model.experiment(2,4,1,5,16,'8');assert wrong['protected']['transitions']!=default['oracle']['transitions'];faults.append({'fault':'cooldown one tick late','raw':wrong['protected'],'expectedTransitions':default['oracle']['transitions'],'detected':True})
wrong=model.experiment(budget=16);assert wrong['protected']['callCount']>one['oracle']['callCount'];faults.append({'fault':'shared budget ignored/refilled','raw':wrong['protected'],'expectedCalls':1,'detected':True})
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if 'id'in d:self.ids.append(d['id'])
  if t=='a' and 'href'in d:self.links.append(d['href'])
page=Page();page.feed((R/'index.html').read_text());assert len(page.ids)==len(set(page.ids))
for key in ['prediction','threshold','cooldown','retries','deadline','budget','recovery','run','transitions','requests','bad-flow','raw','answer','roadmap']:assert key in page.ids
readme=(R/'README.md').read_text();html=(R/'index.html').read_text()
for url in oracle.LOCATORS.values():assert url in readme and url in html
for marker in ['routing','resilience','protocol','observability','TLS','jitter']:assert marker in readme and marker in html
for link in re.findall(r'\]\(([^)]+)\)',readme)+page.links:
 if link.startswith(('https://','#')):continue
 if a.record and link.startswith('evidence/') and not (R/link).exists():continue
 target=(R/link.split('#')[0]).resolve();assert target.is_relative_to(R) and target.exists(),link
ui=None
if (R/'evidence/ui-qa.json').exists():
 ui=json.loads((R/'evidence/ui-qa.json').read_text());assert ui['status']=='passed' and len(ui['rows'])==10
 for observed in ui['rows']:
  if observed['status']=='input-rejected':
   assert observed['staleTraceCleared'] is True
   try:model.experiment(*observed['input'])
   except ValueError:pass
   else:raise AssertionError('UI rejection mismatch')
  else:
   pr=projection(compare(model.experiment(*observed['input'])));assert observed['projection']==pr and observed['projectionSha256']==sha(canonical(pr))
run={'schema':1,'executedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'command':'python3 -B check.py --record','timeModel':'integer virtual ticks, no wall-clock wait or service communication','measurements':{'cases':rows,'hand':hand,'inputRejects':rejects,'faults':faults},'sourceBinding':oracle.LOCATORS}
if a.record:(R/'evidence/run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
else:
 saved=json.loads((R/'evidence/run.json').read_text());assert saved['measurements']==run['measurements'] and saved['sourceBinding']==run['sourceBinding']
files={str(f.relative_to(R)):sha(f.read_bytes()) for f in sorted(R.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f!=R/'evidence/bindings.json'}
if a.record:(R/'evidence/bindings.json').write_text(json.dumps({'schema':1,'sha256':files,'sourceBinding':oracle.LOCATORS},ensure_ascii=False,indent=2)+'\n')
else:assert json.loads((R/'evidence/bindings.json').read_text())['sha256']==files
print(json.dumps({'status':'passed' if ui else 'core-passed-ui-pending','transitionTimeComparisons':len(rows),'handCases':len(hand),'inputRejects':len(rejects),'intentionalFaults':len(faults),'maxBadCalls':max(x['bad']['callCount'] for x in rows),'roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files),'actualIABRows':len(ui['rows']) if ui else 0,'mode':'record' if a.record else 'read-only'}))
