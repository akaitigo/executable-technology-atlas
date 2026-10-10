import sys
sys.dont_write_bytecode=True
import argparse,copy,datetime,hashlib,json,platform,re
from html.parser import HTMLParser
import model,oracle
R=model.ROOT
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
assert model.SOURCES==oracle.LOCATORS
assert json.loads((R/'telemetry.json').read_text())==oracle.BASE
assert sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
def compare(row):
    inp=row['input'];e=oracle.expected(inp['capacity'],inp['policy'],inp['order'],inp['copies'],inp['sensor'])
    for k in ('retained','dropped','rejected'):assert row['queue'][k]==e[k]
    assert [t['after'] for t in row['queue']['trace'][:8]]==e['queueTimeline']
    assert row['queue']['afterReconnect']==[] and row['queue']['trace'][-1]['after']==[]
    assert all(len(t['after'])<=inp['capacity'] for t in row['queue']['trace'])
    assert row['deliveries']==e['deliveries']
    assert row['protected']['accepted']==e['accepted'] and row['protected']['latest']==e['latest']
    assert [t['decision'] for t in row['protected']['trace']]==e['reasons']
    assert [t['latest'] for t in row['protected']['trace']]==e['latestTimeline']
    assert row['naive']['accepted']==e['deliveries'] and row['naive']['latest']==e['naiveLatest']
    for name in ('protected','naive'):
        result=row[name];assert result['traceSha256']==sha(canonical(result['trace']))
        assert result['counts']=={label:sum(t['decision']==label for t in result['trace']) for label in ('accept','duplicate','stale')}
    assert row['queue']['traceSha256']==sha(canonical(row['queue']['trace']))
    row['oracle']=e;row['inputSha256']=sha(canonical(inp));row['rawSha256']=sha(canonical({'queue':row['queue'],'protected':row['protected'],'naive':row['naive']}));return row
rows=[]
for capacity in range(1,7):
 for policy in ('drop-oldest','reject-newest'):
  for order in ('forward','reverse'):
   for copies in range(1,4):
    for sensor in ('valid','invalid-sensor'):rows.append(compare(model.experiment(capacity,policy,order,copies,sensor)))
hand=[]
for expected in oracle.HAND:
 row=compare(model.experiment(*expected['input']));r=row['protected'];n=row['naive'];assert r['counts']['accept']==expected['protectedCount'] and n['counts']['accept']==expected['naiveCount'];assert r['counts']['duplicate']==expected['duplicates'] and r['counts']['stale']==expected['stale'];assert {d:v['seq'] for d,v in r['latest'].items()}==expected['latestSeq'];assert {d:v['seq'] for d,v in n['latest'].items()}==expected['naiveSeq'];hand.append(row)
boundary=model.receive([{'device':'a','seq':1,'raw':0},{'device':'a','seq':99,'raw':1000}],'protected');assert boundary['counts']['accept']==2 and boundary['latest']['a']['raw']==1000
rejects=[]
for args in [(0,'drop-oldest','reverse',2,'valid'),(7,'drop-oldest','reverse',2,'valid'),(True,'drop-oldest','reverse',2,'valid'),(1.0,'drop-oldest','reverse',2,'valid'),(6,'persist-all','reverse',2,'valid'),(6,'drop-oldest','random',2,'valid'),(6,'drop-oldest','reverse',0,'valid'),(6,'drop-oldest','reverse',4,'valid'),(6,'drop-oldest','reverse',True,'valid'),(6,'drop-oldest','reverse',2.0,'valid'),(6,'drop-oldest','reverse',2,'real-sensor')]:
 try:model.experiment(*args)
 except ValueError as e:rejects.append({'input':list(args),'error':str(e)})
 else:raise AssertionError(args)
for field,value in [('device','c'),('device',1),('seq',0),('seq',100),('seq',True),('seq',1.5),('raw',-1),('raw',1001),('raw',True),('raw',1.0),('raw','100')]:
 record={'device':'a','seq':1,'raw':100};record[field]=value
 try:model.validate_record(record)
 except ValueError as e:rejects.append({'input':record,'error':str(e)})
 else:raise AssertionError(record)
for record in [{},{'device':'a','seq':1,'raw':100,'extra':1}]:
 try:model.validate_record(record)
 except ValueError as e:rejects.append({'input':record,'error':str(e)})
 else:raise AssertionError(record)
base=compare(model.experiment());faults=[]
for mode in ('fault-global-key','fault-no-monotonic'):
 raw=model.receive(base['deliveries'],mode)
 assert raw['accepted']!=base['oracle']['accepted'] or raw['latest']!=base['oracle']['latest']
 faults.append({'fault':mode,'deliveries':base['deliveries'],'raw':raw,'expectedLatest':base['oracle']['latest'],'expectedAccepted':base['oracle']['accepted'],'detected':True})
wrong=model.experiment(6,'drop-oldest','forward',1,'valid');e=oracle.expected(1,'drop-oldest','forward',1,'valid');assert wrong['queue']['retained']!=e['retained'];faults.append({'fault':'capacity ignored: uses 6 instead of requested 1','rawQueue':wrong['queue'],'expectedRetained':e['retained'],'detected':True})
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if 'id'in d:self.ids.append(d['id'])
  if t=='a' and 'href'in d:self.links.append(d['href'])
page=Page();page.feed((R/'index.html').read_text());assert len(page.ids)==len(set(page.ids))
for key in ['prediction','capacity','policy','order','copies','sensor','run','queue-flow','protected-flow','naive-flow','raw','answer','roadmap']:assert key in page.ids
readme=(R/'README.md').read_text();html=(R/'index.html').read_text()
for url in oracle.LOCATORS.values():assert url in readme and url in html
for marker in ['transport','durability','identity','lifecycle','epoch','QoS']:assert marker in readme and marker in html
for link in re.findall(r'\]\(([^)]+)\)',readme)+page.links:
 if link.startswith(('https://','#')):continue
 if a.record and link.startswith('evidence/') and not (R/link).exists():continue
 target=(R/link.split('#')[0]).resolve();assert target.is_relative_to(R) and target.exists(),link
def projection(row):
 return {'retained':[f"{r['device']}:{r['seq']}" for r in row['queue']['retained']],'dropped':len(row['queue']['dropped']),'rejected':len(row['queue']['rejected']),'protectedCounts':row['protected']['counts'],'naiveCounts':row['naive']['counts'],'latest':row['protected']['latest'],'naiveLatest':row['naive']['latest'],'queueTrace':row['queue']['traceSha256'],'protectedTrace':row['protected']['traceSha256'],'naiveTrace':row['naive']['traceSha256']}
ui=None
if (R/'evidence/ui-qa.json').exists():
 ui=json.loads((R/'evidence/ui-qa.json').read_text());assert ui['status']=='passed' and len(ui['rows'])==10
 for observed in ui['rows']:
  if observed['status']=='input-rejected':
   assert observed['staleTraceCleared'] is True
   try:model.experiment(*observed['input'])
   except ValueError:pass
   else:raise AssertionError('UI input rejection mismatch')
  else:
   pr=projection(compare(model.experiment(*observed['input'])));assert observed['projection']==pr;assert observed['projectionSha256']==sha(canonical(pr))
run={'schema':1,'executedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),'machine':platform.machine()},'command':'python3 -B check.py --record','measurements':{'cases':rows,'hand':hand,'recordBoundary':boundary,'inputRejects':rejects,'faults':faults},'sourceBinding':oracle.LOCATORS,'fixtureSha256':sha((R/'telemetry.json').read_bytes())}
if a.record:(R/'evidence/run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
else:
 saved=json.loads((R/'evidence/run.json').read_text());assert saved['measurements']==run['measurements'] and saved['sourceBinding']==run['sourceBinding'] and saved['fixtureSha256']==run['fixtureSha256']
files={str(f.relative_to(R)):sha(f.read_bytes()) for f in sorted(R.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f!=R/'evidence/bindings.json'}
if a.record:(R/'evidence/bindings.json').write_text(json.dumps({'schema':1,'sha256':files,'sourceBinding':oracle.LOCATORS},ensure_ascii=False,indent=2)+'\n')
else:assert json.loads((R/'evidence/bindings.json').read_text())['sha256']==files
print(json.dumps({'status':'passed' if ui else 'core-passed-ui-pending','timelineComparisons':len(rows),'handCases':len(hand),'recordBoundaryCases':2,'inputRejects':len(rejects),'intentionalFaults':len(faults),'roadmapLocalLinksSourceBinding':'passed','digestFiles':len(files),'actualIABRows':len(ui['rows']) if ui else 0,'mode':'record' if a.record else 'read-only'}))
