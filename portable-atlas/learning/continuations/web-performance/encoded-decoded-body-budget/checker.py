"""Independent actual HTTP bytes and actual Browser ResourceTiming; read-only."""
import json,hashlib,copy,datetime,argparse,re
from urllib.parse import urlparse
from pathlib import Path
from oracle import validate,validate_wire,TABLE,FIXTURE
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def compact(x):return json.dumps(x,separators=(',',':'))
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def cleared(x):
 assert x['answer']=='' and not x['answer_open'] and x['answer_hidden'] and x['comparison']=='未比較' and x['result']==x['status']=='未実行'
 assert x['encoded']==x['decoded']==x['used']=='—' and x['accepted']=='未判定' and x['body']=='body未取得'
def business(x):return {k:v for k,v in x.items() if k not in ['held_meta','held_payload','ignored','release_disabled']}
def browser_wire(b,c,port):
 u=urlparse(b['url']);assert u.scheme=='http' and u.hostname=='127.0.0.1' and u.port==port and u.query=='request='+b['request_id']
 assert b['same_origin'] and b['cache_mode']=='no-store' and b['request_id']==b['response_request_id'];s=b['receipt'];assert s['request_id']==b['request_id'] and s['http_status']==b['http_status']
 body=bytes.fromhex(s['body_hex']);assert len(body)==s['body_bytes']==s['bytes_written']==int(b['content_length'])
 assert hashlib.sha256(body).hexdigest()==s['body_sha256']==b['body_sha256'] and s['content_encoding']==b['content_encoding']
 assert datetime.datetime.fromisoformat(b['ended_utc'].replace('Z','+00:00'))>=datetime.datetime.fromisoformat(b['started_utc'].replace('Z','+00:00'))
 if c['variant']=='http-failure':
  assert b['http_status']==500 and body==b'injected HTTP failure' and b['decoded_hex']==body.hex() and b['decoded_bytes']==len(body) and u.path=='/body/error';return
 expected_hex=TABLE['plain_hex' if c['encoding']=='plain' else 'gzip_hex'];expected_size=3 if c['encoding']=='plain' else 23
 assert u.path=='/body/'+c['encoding'] and b['http_status']==200 and s['body_hex']==expected_hex and s['body_bytes']==expected_size and b['decoded_hex']==TABLE['decoded_hex'] and b['decoded_bytes']==3
 e=b['observed_entry'];assert e and e['name']==b['url'] and e['entryType']=='resource' and e['initiatorType']=='fetch' and e['encodedBodySize']==expected_size and e['decodedBodySize']==3
 assert b['lookup_injected_missing']==(c['variant']=='timing-missing')
 assert b['lookup_name']==b['url']+('-missing' if c['variant']=='timing-missing' else '')
 assert b['lookup_entry']==(None if c['variant']=='timing-missing' else e)
def answer_check(x,r,e):
 assert '実encoded '+str(e['encoded'])+' bytes / decoded '+str(e['decoded'])+' bytes。現budget '+str(r['input']['budget'])+' bytes' in x['answer']
 assert 'の'+str(e['used'])+' bytesを比較し、'+('受入' if e['accepted'] else '拒否')+'。' in x['answer']
 if r['input']['policy']=='decoded-fault':assert 'encoded budgetの正しい比較は'+str(e['encoded'])+' <= '+str(r['input']['budget'])+'で'+('受入' if e['encoded']<=r['input']['budget'] else '拒否')+'。' in x['answer']
def observed(x,r,e):
 assert r['status']==e['status'] and r['reason']==e.get('reason','') and r['used']==e['used'] and r['accepted'] is e['accepted']
 assert r['measurement']==(None if e['encoded'] is None else dict(encoded=e['encoded'],decoded=e['decoded']))
 if e['encoded'] is None:assert x['encoded']==x['decoded']==x['used']=='—' and x['accepted']=='未判定' and x['answer']=='' and not x['answer_open'] and x['answer_hidden'];return
 assert x['encoded']==str(e['encoded']) and x['decoded']==str(e['decoded']) and x['used']==str(e['used']) and x['accepted']==('受入' if e['accepted'] else '拒否')
 assert not x['answer_hidden'] and x['body']=='実decode済body: 616263 / 3 bytes';answer_check(x,r,e)
def custom_validate(raw):
 table=load('custom-oracle.json');assert [a['id'] for a in raw['attempts']]==[c['id'] for c in table['cases']]
 for c,a in zip(table['cases'],raw['attempts']):
  assert a['command']==['python3','-B','runner.py','--case',c['case'],'--port',str(raw['port']),'--input-json',compact(c['input'])] and a['exit']==0 and not a['stderr'];x=json.loads(a['stdout']);r=x['result'];base=copy.deepcopy(next(k for k in FIXTURE['cases'] if k['id']==c['case']));base.update(c['input']);assert r['input']==base and r['case']==c['case'];validate_wire(x['wire'],base['encoding']);e=c['expected'];assert r['status']==e['status'] and r['measurement']==dict(encoded=e['encoded'],decoded=e['decoded']) and r['used']==e['used'] and r['accepted'] is e['accepted']
def verify_qa(raw,custom,q=None):
 if q is None:q=load('evidence/iab-qa-case-results.json')
 assert q['tab_closed'] and not q['console'] and list(q['cases'])==[c['id'] for c in FIXTURE['cases']]
 urls=[]
 for c in FIXTURE['cases']:
  x=q['cases'][c['id']];d=json.loads(x['result']);r=d['result'];e=TABLE['expected'][c['id']];assert r['case']==c['id'];observed(x,r,e)
  assert r['status'] in x['comparison'] and x['pz']=='bodyは3/23、decode3' and x['pd']=='encodedで境界比較'
  if e['status']=='INPUT_REFUSED':assert d['browser'] is None
  else:assert r['input']==c;browser_wire(d['browser'],c,raw['port']);urls.append(d['browser']['url'])
 assert len(set(urls))==11
 assert set(q['inputs'])=={'encoded/decodedの予想','budget判定の予想','条件JSON上書き（空欄はfixture）'}
 for name,pair in q['inputs'].items():
  b,a=pair['before'],pair['after'];assert b['answer_open'] and b['answer'] and b['status']=='NORMAL';cleared(a)
  assert a['pz']==('新しいsize予想' if name=='encoded/decodedの予想' else b['pz']) and a['pd']==('新しいbudget予想' if name=='budget判定の予想' else b['pd']) and a['input_json']==('{"encoding":"gzip","budget":4,"policy":"encoded","variant":"normal"}' if name.startswith('条件JSON') else b['input_json'])
 assert q['before_condition_reset']['answer_open']
 for name in ['condition_reset','button_reset']:
  x=q[name];cleared(x);assert x['pz']==x['pd']==x['input_json']==''
 for name in ['success_before_refusal','success_before_missing','success_before_failure']:assert q[name]['answer_open'] and q[name]['status']=='NORMAL'
 x=q['success_then_refusal'];assert x['status']=='INPUT_REFUSED: INPUT_JSON' and x['pz']=='拒否なら未測定' and x['pd']=='正常答えなし' and x['pz'] in x['comparison'] and x['pd'] in x['comparison'];assert not x['answer_open'] and x['answer']=='' and x['answer_hidden']
 for name,case in [('success_then_missing','timing-missing'),('success_then_failure','http-failure')]:
  x=q[name];d=json.loads(x['result']);observed(x,d['result'],TABLE['expected'][case]);browser_wire(d['browser'],d['result']['input'],raw['port'])
 h=json.loads(q['old_received']['held_payload']);assert h['data']['result']['case']=='gzip8' and h['data']['result']['measurement']==dict(encoded=23,decoded=3);browser_wire(h['data']['browser'],h['data']['result']['input'],raw['port'])
 b,a=q['latest_before_release'],q['latest_after_release'];assert b['case']==a['case']=='gzip23' and a['accepted']=='受入' and business(a)==business(b) and b['ignored']=='旧結果破棄: 0' and a['ignored']=='旧結果破棄: 1' and a['held_payload']=='' and a['release_disabled']
 b,a=q['input_before_release'],q['input_after_release'];cleared(b);cleared(a);assert business(a)==business(b) and a['input_json']=='{"encoding":"plain","budget":3,"policy":"encoded","variant":"normal"}' and a['ignored']=='旧結果破棄: 1'
 table=load('custom-oracle.json');assert list(q['custom'])==[c['id'] for c in table['cases']]
 for c,attempt in zip(table['cases'],custom['attempts']):
  r=json.loads(attempt['stdout'])['result'];x=q['custom'][c['id']];d=json.loads(x['result']);assert d['result']==r and json.loads(x['input_json'])==c['input'] and x['answer_open'];observed(x,r,c['expected']);browser_wire(d['browser'],r['input'],raw['port'])
 for n,body in q['documents'].items():assert (ROOT/n).read_text()==body,n
 p=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/p['raw']).read_text()
def saved(pointer):
 p=load(pointer);assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw'])
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 return p,r
def check(binding=True):
 p,r=saved('evidence/current.json');cp,custom=saved('evidence/custom-current.json');result=validate(r);custom_validate(custom);assert len(r['attempts'])==16
 for a,c,x in zip(r['attempts'],FIXTURE['cases'],r['cases']):
  assert a['case']==c['id'] and a['command']==['python3','-B','runner.py','--case',c['id'],'--port',str(r['port'])] and json.loads(a['stdout'])==x and not a['stderr'];assert a['exit']==(2 if c['id'] in ['budget-negative','budget-bool','budget-large','encoding-unknown','policy-unknown'] else 3 if c['variant']=='timing-missing' else 1 if c['variant']=='http-failure' else 0)
  assert datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
 verify_qa(r,custom)
 failed=load('evidence/run-20261005T153826-caa9bf68.json');assert sum(x['result']['status']=='EXECUTION_FAILURE' and 'PermissionError' in x['result']['reason'] and x['wire'] is None for x in failed['cases'])==11 and len(failed['cases'])==16
 manifest=load('revisions/initial-lookup-injection/snapshot-manifest.json')
 for n,h in manifest.items():assert sha(ROOT/'revisions/initial-lookup-injection'/n)==h,n
 for task in ['body-budget','verify','compare','sources']:assert route(task)['status']=='supported' and (ROOT/route(task)['target']).exists()
 for task in ['wire-total','latency','cache-cdn','web-vitals','cross-origin']:assert route(task)['status']=='unsupported'
 links=0
 for n in ['README.md','SOURCES.md','EXPECTATIONS.md','index.html','skills/atlas-body-size-budget/SKILL.md']:
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
 return dict(status='passed',**result,actual_child_attempts=20,actual_browser_cases=20,actual_browser_body_fetches=15,local_links=links,raw=p['raw'],custom_raw=cp['raw'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record-binding',action='store_true');a=p.parse_args()
 if a.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check()))
