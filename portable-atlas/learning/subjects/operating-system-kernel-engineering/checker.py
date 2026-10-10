"""Read-only saved-observation verifier. Explicit sealing only updates artifact binding."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from oracle import check
from runner import run
from route import route
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings():return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='integrity.json' and '__pycache__' not in p.parts}
def verify():
 cases=json.loads((ROOT/'cases.json').read_text());raw=json.loads((ROOT/'evidence/raw.json').read_text())
 assert len(cases)==len(raw)==8
 children=[]
 for i,(c,row) in enumerate(zip(cases,raw)):
  assert row['id']==c['id'] and row['input']==c['input']
  r=row['result']
  if i<5:
   assert r['input']==c['input'] and row['oracle']==check(r)
   assert r['timeline']==sorted(r['parent_events']+r['child_events'],key=lambda e:e['wall_ns'])
   assert [json.loads(line) for line in r['raw_child_stdout'].splitlines()]==r['child_events']
   assert r['end_mono_ns']>=r['start_mono_ns']
   assert len(r['cleanup']['closed_parent_fds'])==len(set(r['cleanup']['closed_parent_fds']))
   children.append(r['child_pid'])
  else:
   assert r==run(c['input']) and r['status']=='rejected' and r['child_pid'] is None
 assert len(children)==len(set(children))
 assert len(cases[2]['input']['payload'])==512
 assert raw[1]['oracle']['received_bytes']==0 and raw[2]['oracle']['received_bytes']==512
 # Independent oracle should reject falsified lifecycle/payload/ownership evidence.
 mutants=[]
 m=copy.deepcopy(raw[3]['result']);m['bounded_timeout']=False;mutants.append(m)
 m=copy.deepcopy(raw[3]['result']);next(e for e in m['parent_events'] if e['event']=='writer_refs_checkpoint')['parent_write_refs']=0;mutants.append(m)
 m=copy.deepcopy(raw[4]['result']);m['child_events'].append(dict(event='eof'));mutants.append(m)
 m=copy.deepcopy(raw[0]['result']);m['child_pid']=m['parent_pid'];mutants.append(m)
 m=copy.deepcopy(raw[0]['result']);m['cleanup']['parent_open_fds']=1;mutants.append(m)
 m=copy.deepcopy(raw[0]['result']);next(e for e in m['child_events'] if e['event']=='data')['hex']='00';mutants.append(m)
 for m in mutants:
  try:check(m)
  except AssertionError:continue
  raise AssertionError('oracle accepted falsified lifecycle')
 base={'mode':'close','payload':'','timeout_ms':200}
 invalid=[None,{},dict(base,timeout_ms=99),dict(base,timeout_ms=501),dict(base,timeout_ms=200.0),dict(base,payload='é'),dict(base,payload='x'*513),dict(base,payload=None),dict(base,pid=1),dict(base,mode='shell'),dict(base,mode='leak-signal',payload='x')]
 assert all(run(x)['status']=='rejected' and run(x)['child_pid'] is None for x in invalid)
 for topic,target in [('pipe','runner.py'),('verify','checker.py'),('fd-diagram','index.html'),('sources','SOURCES.md')]:
  assert route(topic)=={'status':'supported','target':target} and (ROOT/target).is_file()
 for topic in ('kernel-patch','vm','scheduler','memory','filesystem','driver','external-pid','unknown'):assert route(topic)['status']=='unsupported'
 links=0
 for f in list(ROOT.rglob('*.md'))+[ROOT/'index.html']:
  text=f.read_text();refs=re.findall(r'\]\(([^)]+)\)',text) if f.suffix=='.md' else re.findall(r'(?:href|src)=["\']([^"\']+)',text)
  for ref in refs:
   if ref.startswith(('https://','http://','#')):continue
   parsed=urlsplit(ref)
   target=(f.parent/parsed.path).resolve()
   if parsed.query:
    for value in parse_qs(parsed.query).get('file',[]):assert (ROOT/value).is_file(),('viewer source missing',value)
   assert ROOT==target or ROOT in target.parents,('outside module link',ref)
   assert target.exists(),(f.name,ref)
   links+=1
 for name in ('README.md','index.html'):
  text=(ROOT/name).read_text()
  for word in ('前提','仕組み','実務','限界','SOURCES.md','COVERAGE.md'):assert word in text,(name,word)
 for word in ('次1','次2','次3','次4','scheduler','VM','filesystem','未教材'):
  assert word in (ROOT/'COVERAGE.md').read_text(),word
 meta=json.loads((ROOT/'evidence/run.json').read_text())
 assert meta['input_sha256']==digest(ROOT/'cases.json')
 for p,h in meta['source_sha256'].items():assert digest(ROOT/p)==h,('stale source',p)
 for p,h in meta['artifact_sha256'].items():assert digest(ROOT/'evidence'/p)==h,('stale artifact',p)
 assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'artifact drift'
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text())
 assert qa['status']=='passed' and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
 return {'status':'passed','saved_cases':8,'actual_owned_children':5,'all_children_reaped':True,'independent_lifecycle_mutations_rejected':len(mutants),'additional_input_rejections':len(invalid),'normal_unsupported_routes':'4 / 8','local_links':links,'binding':'input/source/raw/FD SVG/artifacts matched','UI_QA':'actual IAB observation/capture and cleanup recorded','subject_complete':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal-evidence',action='store_true');a=p.parse_args()
 if a.seal_evidence:
  (ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),ensure_ascii=False,indent=2)+'\n');print('explicit artifact binding sealed; observation time unchanged')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False));raise SystemExit(1)
