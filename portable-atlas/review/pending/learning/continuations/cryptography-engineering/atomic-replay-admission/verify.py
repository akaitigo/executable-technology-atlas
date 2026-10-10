import sys
sys.dont_write_bytecode=True
import argparse,json,hashlib,copy,itertools
from pathlib import Path
from admission import run,SCHEDULES,validate,authenticated
from fixtures import FIXTURES
from oracle import expected,HAND_COUNTS,ORDERS,mac
from threads import witness,environment
R=Path(__file__).resolve().parent
SOURCE=['CONTRACT.md','admission.py','fixtures.py','oracle.py','threads.py','verify.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assert_row(row,f,i):
 e=expected(f,i);assert row['accepted_count']==e['accepted_count']==HAND_COUNTS[f['id']][i]
 assert row['seen']==e['seen']
 assert [s['event'] for s in row['trace']]==['initial']+ORDERS[i]
 assert len(row['trace'])==(5 if i<6 else 3)
 final=row['trace'][-1]
 for n,r in zip('AB',f['requests']):
  state=final['requests'][n]
  assert state['authenticated']==e['authenticated'][n]
  assert state['status']==('invalid_mac' if not e['authenticated'][n] else 'accepted' if e['accepted'][n] else 'replay')
  if not e['authenticated'][n]:assert all(s['requests'][n]['cached_absent'] is None for s in row['trace'])
 for before,after in zip(row['trace'],row['trace'][1:]):
  assert set(before['seen'])<=set(after['seen'])
  assert after['accepted_count']-before['accepted_count'] in (0,1)
  if set(after['seen'])!=set(before['seen']):
   n=after['event'][0];assert after['requests'][n]['authenticated'] and after['requests'][n]['status']=='accepted'
def guards():
 cases=[]
 def add(name,change):
  f=copy.deepcopy(FIXTURES[0]);change(f);cases.append((name,f))
 add('extra_fixture',lambda f:f.update(extra=1))
 add('requests_tuple',lambda f:f.update(requests=tuple(f['requests'])))
 add('one_request',lambda f:f.update(requests=f['requests'][:1]))
 add('seen_tuple',lambda f:f.update(seen=()))
 add('seen_duplicate',lambda f:f.update(seen=['X','X']))
 add('seen_over16',lambda f:f.update(seen=['X'+str(i) for i in range(17)]))
 add('seen_bad_id',lambda f:f.update(seen=['é']))
 for name,value in [('id_empty',''),('id17','A'*17),('id_unicode','π'),('id_nul','A\0'),('id_bool',True)]:add(name,lambda f,v=value:f['requests'][0].update(id=v))
 for name,value in [('payload_bool',False),('payload65','a'*65),('payload66_utf8','π'*33),('payload_surrogate','\ud800')]:add(name,lambda f,v=value:f['requests'][0].update(payload=v))
 for name,value in [('tag_short','0'*63),('tag_upper','A'*64),('tag_bool',True)]:add(name,lambda f,v=value:f['requests'][0].update(tag=v))
 add('extra_request',lambda f:f['requests'][0].update(extra=1))
 out=[]
 for name,f in cases:
  try:run(f,'split-2')
  except ValueError as exc:out.append(dict(name=name,rejected=True,error=str(exc)))
  else:raise AssertionError(name)
 for value in ('unknown',True,None):
  try:run(FIXTURES[0],value)
  except ValueError as exc:out.append(dict(name='schedule_'+str(value),rejected=True,error=str(exc)))
  else:raise AssertionError('bad schedule')
 return out
def mutants():
 source=(R/'admission.py').read_text()
 changes=[
 ('ignore_mac',"return hmac.compare_digest(actual,r['tag'])","return True"),
 ('check_always_absent',"s['cached_absent']=s['id'] not in seen","s['cached_absent']=True"),
 ('forget_remember',"seen.add(s['id']);count+=1","count+=1"),
 ('count_replays',"s['status']='accepted' if s['cached_absent'] else 'replay'","count+=1; s['status']='accepted' if s['cached_absent'] else 'replay'"),
 ('split_rechecks',"if s['cached_absent']:seen.add(s['id']);count+=1\n  snapshot(event)","if s['id'] not in seen:seen.add(s['id']);count+=1\n  snapshot(event)"),
 ('omit_id_from_mac',"r['id'].encode('ascii')+b'\\0'+r['payload'].encode('utf-8')","r['payload'].encode('utf-8')")]
 out=[]
 for name,old,new in changes:
  assert old in source,name
  ns={};exec(compile(source.replace(old,new),'mutant-'+name,'exec'),ns)
  kills=[]
  for f in FIXTURES:
   for i,s in enumerate(SCHEDULES):
    try:assert_row(ns['run'](f,s),f,i)
    except AssertionError:kills.append(f['id']+'/'+s)
  assert kills,name
  out.append(dict(name=name,killed_by=kills))
 return out
def check():
 # Exhaustive permutations independently establish that exactly 6 legal split orders exist.
 legal=[list(p) for p in itertools.permutations(['Ac','Aw','Bc','Bw']) if p.index('Ac')<p.index('Aw') and p.index('Bc')<p.index('Bw')]
 assert sorted(legal)==sorted(ORDERS[:6])
 rows=[]
 for f in FIXTURES:
  assert all(authenticated(r)==mac(r) for r in f['requests'])
  for i,s in enumerate(SCHEDULES):
   row=run(f,s);assert_row(row,f,i);rows.append(row)
 return dict(rows=rows,guards=guards(),mutants=mutants())
def validate_threads(data):
 assert len(data['rows'])==14
 for w in data['rows']:
  f=next(f for f in FIXTURES if f['id']==w['fixture']);i=1 if w['mode']=='split' else 6
  assert w['status']=='passed' and not w['alive_threads'] and not w['errors']
  assert w['accepted_count']==HAND_COUNTS[f['id']][i] and w['seen']==expected(f,i)['seen']
  assert len(w['results'])==2
  if w['mode']=='split':
   checks=[e for e in w['events'] if e['event']=='check'];writes=[j for j,e in enumerate(w['events']) if e['event']=='remember']
   assert len(checks)==2
   if writes:assert max(j for j,e in enumerate(w['events']) if e['event']=='check')<min(writes)
  elif f['id'] in ('same','payload','boundary'):
   assert sorted(e['cached_absent'] for e in w['events'] if e['event']=='check')==[False,True]
 failure=data['intentional_failure'];assert failure['status']=='failed' and not failure['alive_threads'] and failure['accepted_count']==0
 assert len(failure['errors'])==2 and all(e['type']=='BrokenBarrierError' for e in failure['errors'])
 return True
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--record');ap.add_argument('--seal-record',action='store_true');a=ap.parse_args()
 data=check()
 if a.record:
  out=R/'observations'/a.record;out.mkdir(parents=True,exist_ok=False)
  raw=dict(environment=environment(),source_hashes={n:sha(R/n) for n in SOURCE},**data)
  (out/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
  t=dict(environment=environment(),rows=[witness(f,m) for f in FIXTURES for m in ('split','atomic')],intentional_failure=witness(FIXTURES[0],'split',broken=True))
  (out/'threads.json').write_text(json.dumps(t,ensure_ascii=False,indent=2)+'\n');validate_threads(t)
 elif a.seal_record:
  hashes={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}
  (R/'observations/receipt.json').write_text(json.dumps(dict(hashes=hashes,ui_pending=False),indent=2)+'\n')
 else:
  raw=json.loads((R/'observations/attempt-01/raw.json').read_text());assert data['rows']==raw['rows'] and data['guards']==raw['guards'] and data['mutants']==raw['mutants']
  for n,h in raw['source_hashes'].items():assert sha(R/n)==h
  validate_threads(json.loads((R/'observations/attempt-01/threads.json').read_text()))
 print(json.dumps(dict(status='passed',rows=len(data['rows']),guards=len(data['guards']),mutants=len(data['mutants']),scope='finite unit only')))
