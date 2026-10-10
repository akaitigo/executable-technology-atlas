"""Saved child raw, independent oracle and actual IAB checks; normal read-only."""
import json,hashlib,re,argparse,datetime
from pathlib import Path
from oracle import validate
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def verify_qa(raw):
 q=load('evidence/iab-qa-case-results.json');assert q['tab_closed'] and not q['console'];assert list(q['cases'])==[c['case'] for c in raw['cases']]
 for r in raw['cases']:
  x=q['cases'][r['case']];assert json.loads(x['result'])==r and r['status'] in x['comparison']
  assert x['pc']=='外側yを保つ？' and x['pv']=='safeはfree y';attempt=json.loads(x['attempt']);assert attempt['delay_ms']==0 and attempt['http_status']==200
  assert datetime.datetime.fromisoformat(attempt['ended_utc'])>=datetime.datetime.fromisoformat(attempt['started_utc'])
  if r['status']=='NORMAL':
   assert not x['hidden'];assert x['display']['safe-value']==str(r['safe']['value']) and x['display']['naive-value']==str(r['naive']['value'])
   for mode in ['safe','naive']:assert x['display'][mode+'-free']=='{'+', '.join(r[mode]['free'])+'}'
  else:
   assert all(v=='—' for v in x['display'].values())
   if r['status']=='EXECUTION_FAILURE':assert x['hidden'] and not x['answer']
   else:assert not x['hidden'] and r['reason'] in x['answer']
 x=q['cases']['capture'];assert x['display']['safe-ast']=='λv0.y' and x['display']['naive-ast']=='λy.y'
 x=q['cases']['fresh-free-collision'];assert x['display']['safe-ast']=='λv1.(y + v0)'
 old=q['before_prediction_reset'];a=q['value_prediction_reset'];b=q['free_prediction_reset'];assert not old['hidden']
 assert a['pc']=='新しい結果予想' and a['pv']==old['pv'] and b['pc']==a['pc'] and b['pv']=='新しい自由名予想'
 for x in [a,b,q['condition_reset'],q['button_reset']]:
  assert x['hidden'] and not x['answer'] and x['comparison']=='未比較' and x['result']==x['attempt']==x['status']=='未実行' and all(v=='—' for v in x['display'].values())
 for key in ['condition_reset','button_reset']:assert q[key]['pc']==q[key]['pv']==q[key]['ast']==''
 assert q['success_before_refusal']['status']==q['success_before_failure']['status']=='NORMAL'
 x=q['success_then_refusal'];assert x['status']=='INPUT_REFUSED: AST_JSON' and x['pc']=='拒否なら値なし' and x['pv']=='拒否理由を見る' and x['pc'] in x['comparison'] and x['pv'] in x['comparison'] and 'AST_JSON' in x['answer'] and all(v=='—' for v in x['display'].values())
 x=q['success_then_failure'];assert x['status'].startswith('EXECUTION_FAILURE') and x['hidden'] and not x['answer'] and all(v=='—' for v in x['display'].values())
 a=q['latest_before_old_response'];b=q['latest_after_old_response'];assert a['ignored']=='0' and b['ignored']=='1'
 for key in a:
  if key!='ignored':assert a[key]==b[key],key
 assert b['case']=='closed-replacement' and b['display']['safe-value']==b['display']['naive-value']=='9' and json.loads(b['attempt'])['delay_ms']==0
 for file,body in q['documents'].items():assert (ROOT/file).read_text()==body,file
 pointer=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/pointer['raw']).read_text()
def check(binding=True):
 p=load('evidence/current.json');assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw'])
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(r);assert len(r['attempts'])==len(r['cases'])
 for attempt,c in zip(r['attempts'],r['cases']):
  assert attempt['case']==c['case'] and attempt['command']==['python3','-B','runner.py','--case',c['case']] and json.loads(attempt['stdout'])==c and not attempt['stderr'];assert attempt['exit']=={'NORMAL':0,'INPUT_REFUSED':2,'EXECUTION_FAILURE':1}[c['status']]
  assert datetime.datetime.fromisoformat(attempt['ended_utc'])>=datetime.datetime.fromisoformat(attempt['started_utc'])
 verify_qa(r)
 for t in ['substitution','verify','compare','sources']:assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ['type-safety','general-language','proof','performance','security']:assert route(t)['status']=='unsupported'
 links=0
 for n in ['README.md','EXPECTATIONS.md','SOURCES.md','index.html','skills/atlas-capture-substitution/SKILL.md']:
  s=(ROOT/n).read_text();base=(ROOT/n).parent;targets=re.findall(r'\]\(([^)]+)\)',re.sub(r'`[^`]*`','',s)) if n.endswith('.md') else re.findall(r'href="([^"]+)"',s)
  for t in targets:
   if t.startswith('https://') or t.startswith('#'):continue
   t=t.split('?file=')[1] if '?file=' in t else t.split('#')[0]
   if not binding and t=='evidence/binding.json':continue
   assert (base/t).exists(),t;links+=1
 if binding:
  q=load('evidence/ui-qa.json');assert q['status']=='passed' and q['raw_sha256']==p['sha256'] and q['owned_cleanup']
  for n,h in q['capture_sha256'].items():assert sha(ROOT/n)==h
  assert load('evidence/binding.json')['files']==inventory()
 return dict(status='passed',**result,actual_child_attempts=len(r['attempts']),local_links=links,raw=p['raw'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record-binding',action='store_true');args=a.parse_args()
 if args.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check()))
