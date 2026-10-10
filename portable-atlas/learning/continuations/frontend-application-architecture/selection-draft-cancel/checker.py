"""Read-only saved evidence check; explicit artifact binding is separate."""
import json,hashlib,re,argparse
from pathlib import Path
from oracle import validate
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def verify_qa():
 q=load('evidence/iab-qa-case-results.json')
 assert q['tab_closed'] and not q['console']
 old=q['compared'];a=q['canonical_prediction_reset'];b=q['view_prediction_reset']
 assert old['comparison']!='未比較' and not old['hidden']
 assert a['pc']=='新しい正本予想' and a['pv']==old['pv']
 assert b['pc']==a['pc'] and b['pv']=='新しい表示予想'
 for x in [a,b]:
  assert x['comparison']=='未比較' and x['hidden'] and x['answer']==''
  for key in ['a','b','drafts','editor','url']:assert x[key]==old[key]
 x=q['condition_reset'];assert x['pc']==x['pv']==x['answer']=='' and x['hidden'] and x['comparison']=='未比較' and x['mode']=='shared' and x['editor']=='Alpha' and json.loads(x['drafts'])==dict(byId={},shared=None)
 for case,reason in [('unknown_refused','UNKNOWN_ID'),('blank_refused','INVALID_TEXT')]:
  x=q[case];assert x['status']=='INPUT_REFUSED: '+reason and x['a']=='Alpha' and x['b']=='Beta' and x['editor']=='Alpha' and x['pc']=='拒否ならAlpha/Beta' and x['pv']=='Alpha' and reason in x['answer'] and 'INPUT_REFUSED' in x['comparison']
 assert q['cancel_b']['editor']=='Beta' and q['cancel_b']['b']=='Beta'
 assert q['save_b']['a']=='Alpha' and q['save_b']['b']==q['save_b']['editor']=='Beta saved'
 for case in ['execution_failure','failure_persists']:
  x=q[case];assert x['hidden'] and x['answer']=='' and x['status'].startswith('EXECUTION_FAILURE') and x['comparison'].startswith('EXECUTION_FAILURE')
 assert q['failure_reset']['status']=='OK' and q['failure_reset']['pc']==q['failure_reset']['pv']=='' and q['failure_reset']['hidden']
 assert q['stale_history']['status']=='INPUT_REFUSED: STALE_HISTORY'
 for file,body in q['documents'].items():assert (ROOT/file).read_text()==body,file
 p=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/p['raw']).read_text()
def check(binding=True):
 p=load('evidence/current.json');assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw']);assert r['fixture']==load('fixture.json')
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(r)
 verify_qa()
 for t in ['draft','verify','edit','sources']:assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ['react','router','persistence','undo','performance']:assert route(t)['status']=='unsupported'
 links=0
 for n in ['README.md','EXPECTATIONS.md','SOURCES.md','index.html','skills/atlas-selection-draft/SKILL.md']:
  s=(ROOT/n).read_text();base=(ROOT/n).parent;targets=re.findall(r'\]\(([^)]+)\)',s) if n.endswith('.md') else re.findall(r'href="([^"]+)"',s)
  for t in targets:
   if t.startswith('https://') or t.startswith('#'):continue
   if '?file=' in t:t=t.split('?file=')[1]
   else:t=t.split('#')[0]
   if not binding and t=='evidence/binding.json':continue
   assert (base/t).exists(),t;links+=1
 if binding:
  q=load('evidence/ui-qa.json');assert q['status']=='passed' and q['raw_sha256']==p['sha256'] and q['owned_cleanup']
  for n,h in q['capture_sha256'].items():assert sha(ROOT/n)==h
  assert load('evidence/binding.json')['files']==inventory()
 return dict(status='passed',**result,local_links=links,raw=p['raw'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record-binding',action='store_true');args=a.parse_args()
 if args.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check()))
