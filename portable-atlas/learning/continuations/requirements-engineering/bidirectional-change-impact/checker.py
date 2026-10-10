"""Saved raw, literal/matrix oracle and actual IAB evidence; normal mode read-only."""
import json,hashlib,re,argparse
from pathlib import Path
from oracle import validate
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def verify_qa(raw):
 q=load('evidence/iab-qa-case-results.json');assert q['tab_closed'] and not q['console']
 assert list(q['cases'])==[c['case'] for c in raw['cases']]
 for r in raw['cases']:
  x=q['cases'][r['case']];assert json.loads(x['result'])==r
  assert x['pc']=='対象枝のみ' and x['pv']=='欠落なら不完全' and r['status'] in x['comparison']
  if r['status']=='EXECUTION_FAILURE':assert x['hidden'] and not x['answer']
  else:assert not x['hidden'] and x['answer']
  if r['status']=='TRACE_INCOMPLETE':assert 'trace不完全' in x['answer'] and '影響なし・完全traceとは判断しない' in x['answer']
 old=q['before_prediction_reset'];a=q['reach_prediction_reset'];b=q['links_prediction_reset']
 assert not old['hidden'] and json.loads(old['result'])['status']=='NORMAL'
 assert a['pc']=='新到達予想' and a['pv']==old['pv'] and b['pc']==a['pc'] and b['pv']=='新逆link予想'
 for x in [a,b]:assert x['comparison']=='未比較' and x['result']=='未実行' and x['hidden'] and x['answer']=='' and x['case']==old['case']
 for key in ['condition_reset','button_reset']:
  x=q[key];assert x['pc']==x['pv']==x['start']==x['answer']=='' and x['hidden'] and x['comparison']=='未比較' and x['result']=='未実行'
 x=q['override_refused'];r=json.loads(x['result']);assert r['status']=='INPUT_REFUSED' and r['reason']=='UNKNOWN_ID' and r['input']['start']=='T-UNKNOWN' and not r['reachable']
 assert x['pc']=='IDは未知なら拒否' and x['pv']=='拒否理由を見る' and x['pc'] in x['comparison'] and x['pv'] in x['comparison'] and 'UNKNOWN_ID' in x['answer']
 for file,body in q['documents'].items():assert (ROOT/file).read_text()==body,file
 pointer=load('evidence/current.json');assert q['raw_document']==(ROOT/'evidence'/pointer['raw']).read_text()
 assert q['final_raw_link']['tab_closed'] and q['final_raw_link']['body']==q['raw_document']
def check(binding=True):
 p=load('evidence/current.json');assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];r=load('evidence/'+p['raw'])
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(r);verify_qa(r)
 for t in ['impact','verify','compare','sources']:assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ['approval','validation','product-graph','performance','safety']:assert route(t)['status']=='unsupported'
 links=0
 for n in ['README.md','EXPECTATIONS.md','SOURCES.md','index.html','skills/atlas-bidirectional-impact/SKILL.md']:
  s=(ROOT/n).read_text();base=(ROOT/n).parent;targets=re.findall(r'\]\(([^)]+)\)',s) if n.endswith('.md') else re.findall(r'href="([^"]+)"',s)
  for t in targets:
   if t.startswith('https://') or t.startswith('#'):continue
   t=t.split('?file=')[1] if '?file=' in t else t.split('#')[0]
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
