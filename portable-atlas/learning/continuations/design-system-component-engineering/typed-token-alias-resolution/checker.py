"""Saved actual child attempts and independently read computed style; read-only by default."""
import json,hashlib,re,argparse,datetime
from pathlib import Path
from oracle import validate,TABLE
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
BASE=dict(a='rgb(240, 240, 240)',b='rgb(240, 240, 240)',focus='rgb(20, 30, 40)',positive='rgb(240, 240, 240)')
def cleared(x):
 assert x['answer']=='' and not x['answer_open'] and x['answer_hidden'] and x['comparison']=='未比較'
 assert x['result']==x['attempt']==x['status']=='未実行' and x['ui_computed']=='未測定' and x['css_display']==x['applied_css']=='' and x['computed']==BASE and not any(x['properties'].values())
def verify_qa(raw,q=None):
 if q is None:q=load('evidence/iab-qa-case-results.json')
 assert q['tab_closed'] and not q['console'] and list(q['cases'])==[c['case'] for c in raw['cases']]
 for r in raw['cases']:
  x=q['cases'][r['case']];e=TABLE['expected'][r['case']];assert json.loads(x['result'])==r and r['status'] in x['comparison'];assert x['computed']==e['computed']
  assert x['pc']=='参照先のRGB' and x['pv']=='A/B/focus連動';attempt=json.loads(x['attempt']);assert attempt['delay_ms']==0 and attempt['http_status']==200 and datetime.datetime.fromisoformat(attempt['ended_utc'])>=datetime.datetime.fromisoformat(attempt['started_utc'])
  if r['css'] is not None:
   assert x['applied_css']==x['css_display']==r['css'] and json.loads(x['ui_computed'])==x['computed'] and not x['answer_hidden'] and x['answer']
   if r['status']=='NORMAL':
    assert '現在の参照先へ連動' in x['answer'] and 'green参照ならgreen値を使う' in x['answer'] and 'blue変更はA/B/focusへ連動' not in x['answer']
   props=e['properties'].copy()
   if r['status']=='FAULT_UNRESOLVED_CSS':props.update({'semantic-action':'','semantic-focus':'','semantic-positive':''})
   assert x['properties']==props
  else:
   assert x['css_display']==x['applied_css']=='' and x['ui_computed']=='未測定' and not any(x['properties'].values())
   if r['status']=='EXECUTION_FAILURE':assert x['answer']=='' and x['answer_hidden'] and not x['answer_open']
   else:assert not x['answer_hidden'] and r['reason'] in x['answer']
 assert set(q['prediction_controls'])=={'CSS値の予想','利用先色の予想'}
 for name,pair in q['prediction_controls'].items():
  before,after=pair['before'],pair['after'];assert before['answer_open'] and before['answer'] and not before['answer_hidden'] and before['status']=='NORMAL';cleared(after)
  if name=='CSS値の予想':assert after['pc']=='新しいCSS予想' and after['pv']==before['pv']
  else:assert after['pv']=='新しい利用先予想' and after['pc']==before['pc']
 assert q['before_condition_reset']['answer_open'] and q['before_condition_reset']['answer']
 for key in ['condition_reset','button_reset']:
  x=q[key];cleared(x);assert x['pc']==x['pv']==x['tokens']==''
 for key in ['success_before_refusal','success_before_failure']:assert q[key]['status']=='NORMAL' and q[key]['answer_open']
 x=q['success_then_refusal'];assert x['status']=='INPUT_REFUSED: TOKEN_JSON' and x['pc']=='拒否ならCSSなし' and x['pv']=='色を残さない' and x['pc'] in x['comparison'] and x['pv'] in x['comparison'] and 'TOKEN_JSON' in x['answer'];assert x['answer_open'] and x['applied_css']=='' and x['computed']==BASE and json.loads(x['result'])['css'] is None
 x=q['success_then_failure'];assert x['status'].startswith('EXECUTION_FAILURE') and x['answer']=='' and not x['answer_open'] and x['answer_hidden'] and x['applied_css']=='' and x['computed']==BASE
 for file,body in q['documents'].items():assert (ROOT/file).read_text()==body,file
 pointer=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/pointer['raw']).read_text()
def check(binding=True):
 p=load('evidence/current.json');assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw'])
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(r);assert len(r['attempts'])==len(r['cases'])
 for attempt,c in zip(r['attempts'],r['cases']):
  assert attempt['case']==c['case'] and attempt['command']==['python3','-B','runner.py','--case',c['case']] and json.loads(attempt['stdout'])==c and not attempt['stderr'];assert attempt['exit']=={'NORMAL':0,'FAULT_UNRESOLVED_CSS':0,'INPUT_REFUSED':2,'EXECUTION_FAILURE':1}[c['status']]
  assert datetime.datetime.fromisoformat(attempt['ended_utc'])>=datetime.datetime.fromisoformat(attempt['started_utc'])
 verify_qa(r)
 for t in ['tokens','verify','compare','sources']:assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ['full-dtcg','brand','package','accessibility','performance']:assert route(t)['status']=='unsupported'
 links=0
 for n in ['README.md','EXPECTATIONS.md','SOURCES.md','index.html','skills/atlas-typed-color-alias/SKILL.md']:
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
 return dict(status='passed',**result,actual_child_attempts=len(r['attempts']),actual_browser_cases=len(r['cases']),local_links=links,raw=p['raw'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record-binding',action='store_true');args=a.parse_args()
 if args.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check()))
