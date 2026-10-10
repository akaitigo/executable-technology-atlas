"""Read-only raw, literal rows, actual UI count/table and stale-result checks."""
import json,hashlib,argparse,re,datetime
from pathlib import Path
from oracle import validate,TABLE
from route import route
ROOT=Path(__file__).resolve().parent
NAMES=['arrived','accepted','dropped','processed','lost','pending']
COLS=['tick','queue','arrived','accepted','dropped','processed','lost','completions']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def cleared(x):
 assert x['answer']=='' and not x['answer_open'] and x['answer_hidden'] and x['comparison']=='未比較'
 assert x['result']==x['attempt']==x['status']=='未実行' and x['rows']==[] and x['counts']==dict.fromkeys(NAMES,'—')
def observed(x,e):
 if e['counts'] is None:assert x['counts']==dict.fromkeys(NAMES,'—') and x['rows']==[]
 else:
  assert x['counts']=={k:str(v) for k,v in e['counts'].items()}
  assert [[json.loads(cell) for cell in row] for row in x['rows']]==[[r[k] for k in COLS] for r in e['timeline']]
def business(x):return {k:v for k,v in x.items() if k not in ['held_meta','held_payload','ignored','release_disabled']}
def verify_qa(raw,q=None):
 if q is None:q=load('evidence/iab-qa-case-results.json')
 assert q['tab_closed'] and not q['console'] and list(q['cases'])==[r['case'] for r in raw['cases']]
 for r in raw['cases']:
  x=q['cases'][r['case']];e=TABLE['expected'][r['case']];assert json.loads(x['result'])==r
  observed(x,e);assert r['status'] in x['comparison'] and x['pd']=='dropと受入後喪失を分ける' and x['pc']=='受入と完了は別'
  a=json.loads(x['attempt']);assert a['delay_ms']==0 and a['http_status']==200 and datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
  if r['status']=='EXECUTION_FAILURE':assert x['answer']=='' and x['answer_hidden'] and not x['answer_open']
  else:assert x['answer'] and not x['answer_hidden']
  if r['status']=='INPUT_REFUSED':assert r['reason'] in x['answer']
  if r['counts'] is not None:
   from editable import answer_check
   answer_check(x,r)
 assert set(q['prediction_controls'])=={'drop/喪失の予想','処理完了の予想'}
 for name,pair in q['prediction_controls'].items():
  b,a=pair['before'],pair['after'];assert b['answer_open'] and b['answer'] and b['status']=='NORMAL';cleared(a)
  if name=='drop/喪失の予想':assert a['pd']=='新しいdrop予想' and a['pc']==b['pc']
  else:assert a['pc']=='新しい完了予想' and a['pd']==b['pd']
 assert q['before_condition_reset']['answer_open']
 for name in ['condition_reset','button_reset']:
  x=q[name];cleared(x);assert x['pd']==x['pc']==x['events']==''
 for name in ['success_before_refusal','success_before_failure']:assert q[name]['answer_open'] and q[name]['status']=='NORMAL'
 x=q['success_then_refusal'];assert x['status']=='INPUT_REFUSED: EVENT_JSON' and x['answer_open'] and x['pd']=='拒否なら未計算' and x['pc']=='完了なし' and x['pd'] in x['comparison'] and x['pc'] in x['comparison'];assert json.loads(x['result'])['counts'] is None;observed(x,dict(counts=None))
 x=q['success_then_failure'];assert x['status'].startswith('EXECUTION_FAILURE') and not x['answer_open'] and x['answer_hidden'] and x['answer']=='';observed(x,dict(counts=None))
 held=json.loads(q['old_response_received']['held_payload']);assert held['data']['result']==raw['cases'][0];assert q['old_response_received']['status']=='未実行' and '受信済: capacity2' in q['old_response_received']['held_meta'];assert held['data']['attempt']['http_status']==200
 b,a=q['latest_before_release'],q['latest_after_release'];assert b['case']==a['case']=='capacity3' and b['counts']['processed']=='3' and b['ignored']=='旧応答破棄: 0' and a['ignored']=='旧応答破棄: 1';assert business(a)==business(b) and a['release_disabled'] and a['held_payload']==''
 held=json.loads(q['prediction_old_received']['held_payload']);assert held['data']['result']==raw['cases'][0]
 b,a=q['prediction_before_release'],q['prediction_after_release'];cleared(b);cleared(a);assert business(a)==business(b) and a['pd']=='受信後の新予想' and a['ignored']=='旧応答破棄: 1'
 for file,body in q['documents'].items():assert (ROOT/file).read_text()==body,file
 pointer=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/pointer['raw']).read_text()
def check(binding=True):
 p=load('evidence/current.json');assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw'])
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(r);assert len(r['attempts'])==18
 for a,c in zip(r['attempts'],r['cases']):
  assert a['case']==c['case'] and a['command']==['python3','-B','runner.py','--case',c['case']] and json.loads(a['stdout'])==c and not a['stderr'];assert a['exit']=={'NORMAL':0,'FAULT_OVERWRITE':0,'INPUT_REFUSED':2,'EXECUTION_FAILURE':1}[c['status']]
  assert datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
 verify_qa(r)
 from editable import check as editable_check
 editable_check()
 for n in ['offload','verify','compare','sources']:assert route(n)['status']=='supported' and (ROOT/route(n)['target']).exists()
 for n in ['real-irq','smp','memory-order','wcet','safety']:assert route(n)['status']=='unsupported'
 assert 'sleep(' not in (ROOT/'producer.py').read_text()+(ROOT/'server.py').read_text()+(ROOT/'ui.js').read_text()
 links=0
 for n in ['README.md','SOURCES.md','EXPECTATIONS.md','index.html','skills/atlas-isr-offload-queue/SKILL.md']:
  text=(ROOT/n).read_text();targets=re.findall(r'\]\(([^)]+)\)',re.sub(r'`[^`]*`','',text)) if n.endswith('.md') else re.findall(r'href="([^"]+)"',text)
  for target in targets:
   if target.startswith('https://') or target.startswith('#'):continue
   target=target.split('?file=')[1] if '?file=' in target else target.split('#')[0]
   if not binding and target=='evidence/binding.json':continue
   assert ((ROOT/n).parent/target).exists(),target;links+=1
 if binding:
  q=load('evidence/ui-qa.json');assert q['status']=='passed' and q['raw_sha256']==p['sha256'] and q['owned_cleanup']
  for n,h in q['capture_sha256'].items():assert sha(ROOT/n)==h
  assert load('evidence/binding.json')['files']==inventory()
 return dict(status='passed',**result,actual_child_attempts=18,actual_browser_cases=18,local_links=links,raw=p['raw'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record-binding',action='store_true');a=p.parse_args()
 if a.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check()))
