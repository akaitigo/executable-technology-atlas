"""Read-only validation of saved actual OS evidence against a literal independent oracle."""
import json,hashlib,argparse,re
from pathlib import Path
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text())
def inventory():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def check(binding=True):
 p=load('evidence/current.json');r=load('evidence/'+p['raw']);o=load('oracle.json');assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];assert r['exit_code']==0
 assert r['fixture']==load('fixture.json')
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert r['environment']['system']=='Darwin';assert r['environment']['allocation_granularity']>1
 assert [m['mode'] for m in r['modes']]==list(o['modes'])
 for m in r['modes']:
  e=m['events'];x=o['modes'][m['mode']];assert m['pid']==r['environment']['pid'];assert m['offset']==0 and m['length']==4
  assert len(e)==8;assert e[0]['requested_bytes']=='AAAA' and 'file_bytes' not in e[0];assert e[1]['event']=='file_flush_before_map' and e[1]['file_bytes']=='AAAA'
  assert (e[2]['mapping_bytes'],e[2]['observer_bytes'],e[2]['file_bytes'])==('AAAA',)*3
  assert m['write_outcome']==x['write_outcome']
  for k,j in [('mapping_bytes','after_mapping'),('observer_bytes','after_observer'),('file_bytes','after_file')]:
   assert e[3][k]==x[j];assert e[4][k]==x[j]
  if 'exception_type' in x:assert m['exception']['type']==x['exception_type'] and e[3]['event']=='write_refused'
  else:assert e[3]['event']=='write_succeeded'
  assert e[4]['flush_outcome']=='succeeded' and e[4]['flush_return'] is None
  assert e[5]['mapping_closed'] and not e[5]['file_object_closed'] and not e[5]['observer_closed']
  assert e[6]['observer_closed'] and not e[6]['file_object_closed'];assert e[7]['file_object_closed']
  assert m['final_file_bytes']==x['after_close_file'] and all(m['cleanup'].values())
 assert [b['id'] for b in r['boundaries']]==list(o['boundaries'])
 for b in r['boundaries']:
  assert b['pid']==r['environment']['pid'];assert b['outcome']=='refused' and b['exception']['type']==o['boundaries'][b['id']]
  assert b['initial']==b['final_file_bytes']=='AAAA' and all(b['cleanup'].values())
 assert [(b['offset'],b['length']) for b in r['boundaries']]==[(1,1),(0,5),(0,4),(0,4)]
 assert r['outcomes']==dict(writes_succeeded=2,writes_refused=1,boundary_refusals=4,unexpected_acceptances=0,execution_failures=0)
 assert r['durability_proven'] is False and r['physical_COW_pages']==r['pagefaults']=='not measured' and r['crossprocess']=='not executed'
 for t in ['visibility','verify','timeline','sources']:assert route(t)['status']=='supported' and (ROOT/route(t)['target']).is_file()
 for t in ['pagefault','cow-pages','crossprocess','power-loss','linux']:assert route(t)['status']=='unsupported'
 links=0
 for file in ['index.html','README.md','SOURCES.md','EXPECTATIONS.md']:
  s=(ROOT/file).read_text()
  targets=re.findall(r'\]\(([^)]+)\)',s) if file.endswith('.md') else re.findall(r'href="([^"]+)"',s)
  for t in targets:
   if t.startswith('https://') or t.startswith('#'):continue
   if '?file=' in t:t=t.split('?file=')[1]
   else:t=t.split('#')[0]
   if not binding and t=='evidence/binding.json':continue
   assert (ROOT/t).exists(),t;links+=1
 if binding:
  q=load('evidence/ui-qa.json');assert q['status']=='passed' and q['raw_sha256']==p['sha256'] and q['owned_cleanup']==True
  for n,h in q['capture_sha256'].items():assert sha(ROOT/n)==h
  assert load('evidence/binding.json')['files']==inventory()
 return dict(status='passed',actual_modes=3,writes_succeeded=2,writes_refused=1,boundary_refusals=4,local_links=links,raw=p['raw'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record-binding',action='store_true');args=a.parse_args()
 if args.record_binding:
  check(False);(ROOT/'evidence/binding.json').write_text(json.dumps(dict(files=inventory()),indent=2)+'\n')
 print(json.dumps(check(),ensure_ascii=False))
