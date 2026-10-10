"""Read-only actual children, literal owner tables, UI resets and stale responses."""
import json,hashlib,re,datetime,argparse,copy
from pathlib import Path
from oracle import validate,project,TABLE,FIXTURE
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def compact(x):return json.dumps(x,separators=(',',':'))
def cleared(x):
 assert x['answer']=='' and not x['answer_open'] and x['answer_hidden'] and x['comparison']=='未比較'
 assert x['result']==x['attempt']==x['status']=='未実行' and x['rows']==[] and x['final']=='未計算'
def observed(x,r,literal):
 if literal is None:
  assert x['rows']==[] and x['final']=='未計算' and x['answer']=='' and x['answer_hidden'] and not x['answer_open'];return
 cells=[[json.loads(c) for c in row] for row in x['rows']]
 assert cells==[[row['step'],row['event'],*vector] for row,vector in zip(r['timeline'],literal)] and len(cells)==len(literal)
 assert json.loads(x['final'])==r['final'] and not x['answer_hidden'] and x['answer']
 p=literal[-1];assert '今回の最終process '+str(p[0])+' / alive '+compact(p[1])+' / A '+compact(p[2])+' / B '+compact(p[3])+'。' in x['answer']
 if r['status']=='NORMAL':assert '正常契約:' in x['answer']
 else:assert '故障mode:' in x['answer'] and '正常契約:' not in x['answer']
def business(x):return {k:v for k,v in x.items() if k not in ['held_meta','held_payload','ignored','release_disabled']}
def custom_validate(raw):
 table=load('custom-oracle.json');assert [a['id'] for a in raw['attempts']]==[c['id'] for c in table['cases']]
 for c,a in zip(table['cases'],raw['attempts']):
  assert a['command']==['python3','-B','runner.py','--case',c['case'],'--events-json',compact(c['events'])] and a['exit']==0 and not a['stderr'];r=json.loads(a['stdout']);fixture=copy.deepcopy(next(x for x in FIXTURE['cases'] if x['id']==c['case']));fixture['events']=c['events'];assert r['input']==fixture and r['case']==c['case'] and r['status']==c['status'] and r['reason']==''
  assert [project(row) for row in r['timeline']]==c['rows'] and r['final']==r['timeline'][-1]
  assert datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
def verify_qa(raw,custom,q=None):
 if q is None:q=load('evidence/iab-qa-case-results.json')
 assert q['tab_closed'] and not q['console'] and list(q['cases'])==[r['case'] for r in raw['cases']]
 for r in raw['cases']:
  x=q['cases'][r['case']];assert json.loads(x['result'])==r;observed(x,r,TABLE['expected'][r['case']]['rows']);assert r['status'] in x['comparison'] and x['po']=='ownerとviewを分ける' and x['ps']=='画面別stateを比較'
  a=json.loads(x['attempt']);assert a['http_status']==200 and a['delay_ms']==0 and datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
 assert set(q['inputs'])=={'owner寿命の予想','状態値の予想','event JSON上書き（空欄は条件fixture）'}
 for name,pair in q['inputs'].items():
  b,a=pair['before'],pair['after'];assert b['answer_open'] and b['answer'] and b['status']=='NORMAL';cleared(a)
  assert a['po']==('新しいowner予想' if name=='owner寿命の予想' else b['po']) and a['ps']==('新しいstate予想' if name=='状態値の予想' else b['ps']) and a['events']==('[{"op":"rotate","target":"A"}]' if name.startswith('event') else b['events'])
 assert q['before_condition_reset']['answer_open']
 for key in ['condition_reset','button_reset']:
  x=q[key];cleared(x);assert x['po']==x['ps']==x['events']==''
 for key in ['success_before_refusal','success_before_failure']:assert q[key]['answer_open'] and q[key]['status']=='NORMAL'
 x=q['success_then_refusal'];assert x['status']=='INPUT_REFUSED: EVENT_JSON' and x['po']=='拒否ならowner未計算' and x['ps']=='正常答えなし' and x['po'] in x['comparison'] and x['ps'] in x['comparison'];observed(x,json.loads(x['result']),None)
 x=q['success_then_failure'];assert x['status'].startswith('EXECUTION_FAILURE');observed(x,json.loads(x['result']),None)
 held=json.loads(q['old_received']['held_payload']);assert held['data']['result']==raw['cases'][1] and held['data']['attempt']['http_status']==200
 b,a=q['latest_before_release'],q['latest_after_release'];assert b['case']==a['case']=='recreate-b' and json.loads(a['final'])['owners']['B']==dict(owner='p1:B:3',view_generation=1,state=0);assert business(b)==business(a) and b['ignored']=='旧応答破棄: 0' and a['ignored']=='旧応答破棄: 1' and a['held_payload']=='' and a['release_disabled']
 held=json.loads(q['input_old_received']['held_payload']);assert held['data']['result']==raw['cases'][1]
 b,a=q['input_before_release'],q['input_after_release'];cleared(b);cleared(a);assert business(b)==business(a) and a['events']=='[]' and a['ignored']=='旧応答破棄: 1'
 table=load('custom-oracle.json');assert list(q['custom'])==[c['id'] for c in table['cases']]
 for c,attempt in zip(table['cases'],custom['attempts']):
  r=json.loads(attempt['stdout']);x=q['custom'][c['id']];assert json.loads(x['result'])==r and json.loads(x['events'])==c['events'] and x['answer_open'];observed(x,r,c['rows'])
 for n,body in q['documents'].items():assert (ROOT/n).read_text()==body,n
 p=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/p['raw']).read_text()
def saved(pointer):
 p=load(pointer);assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw'])
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 return p,r
def check(binding=True):
 p,r=saved('evidence/current.json');cp,custom=saved('evidence/custom-current.json');result=validate(r);custom_validate(custom)
 assert len(r['attempts'])==21
 for a,c in zip(r['attempts'],r['cases']):
  assert a['case']==c['case'] and a['command']==['python3','-B','runner.py','--case',c['case']] and json.loads(a['stdout'])==c and not a['stderr'];assert a['exit']=={'NORMAL':0,'FAULT_GLOBAL_LEAK':0,'FAULT_DEAD_REUSE':0,'INPUT_REFUSED':2,'EXECUTION_FAILURE':1}[c['status']]
  assert datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
 verify_qa(r,custom)
 for n in ['lifetime','verify','compare','sources']:assert route(n)['status']=='supported' and (ROOT/route(n)['target']).exists()
 for n in ['android','compose','savedstatehandle','sdk-install','process-kill']:assert route(n)['status']=='unsupported'
 assert 'sleep(' not in (ROOT/'producer.py').read_text()+(ROOT/'server.py').read_text()+(ROOT/'ui.js').read_text()
 links=0
 for n in ['README.md','SOURCES.md','EXPECTATIONS.md','index.html','skills/atlas-screen-owner-lifetime/SKILL.md']:
  text=(ROOT/n).read_text();targets=re.findall(r'\]\(([^)]+)\)',re.sub(r'`[^`]*`','',text)) if n.endswith('.md') else re.findall(r'href="([^"]+)"',text)
  for t in targets:
   if t.startswith('https://') or t.startswith('#'):continue
   t=t.split('?file=')[1] if '?file=' in t else t.split('#')[0]
   if not binding and t=='evidence/binding.json':continue
   assert ((ROOT/n).parent/t).exists(),t;links+=1
 if binding:
  q=load('evidence/ui-qa.json');assert q['status']=='passed' and q['raw_sha256']==p['sha256'] and q['custom_raw_sha256']==cp['sha256'] and q['owned_cleanup']
  for n,h in q['capture_sha256'].items():assert sha(ROOT/n)==h
  assert load('evidence/binding.json')['files']==inventory()
 return dict(status='passed',**result,actual_child_attempts=25,actual_browser_cases=25,custom_literal_rows=6,local_links=links,raw=p['raw'],custom_raw=cp['raw'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record-binding',action='store_true');a=p.parse_args()
 if a.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check()))
