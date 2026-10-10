"""Read-only actual HTTP evidence and independent SQL checks; explicit binding separate."""
import json,hashlib,argparse,re
from pathlib import Path
from oracle import validate
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def check(binding=True):
 p=load('evidence/current.json');assert sha(ROOT/p['raw'])==p['sha256'];r=load(p['raw']);assert r['fixture']==load('fixture.json')
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(r)
 for t in ['http','verify','compare','sources']:assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ['framework','tls','concurrency','chunked','after-send']:assert route(t)['status']=='unsupported'
 links=0
 for n in ['README.md','SOURCES.md','EXPECTATIONS.md','index.html','skills/atlas-wsgi-boundaries/SKILL.md']:
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
