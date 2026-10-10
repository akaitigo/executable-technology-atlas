"""Read-only saved evidence checker. Only explicit --seal-evidence changes bindings."""
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
 cases=json.loads((ROOT/'cases.json').read_text());raw=json.loads((ROOT/'evidence/raw.json').read_text());assert len(cases)==len(raw)==10
 snapshots=0
 for i,(c,row) in enumerate(zip(cases,raw)):
  assert row['id']==c['id'] and row['input']==c['input'];r=row['result']
  if i<7:
   assert r['input']==c['input'] and row['oracle']==check(r)
   snapshots+=row['oracle']['reader_states']
   for e in r['events']:
    if 'path' not in e:continue
    for obj in (e['path'],e['held_reader'],e['candidate']):
     if obj is None:continue
     data=bytes.fromhex(obj['hex']);assert len(data)==obj['length'] and hashlib.sha256(data).hexdigest()==obj['sha256']
  else:assert r==run(c['input']) and r['status']=='rejected' and r['temp_created'] is False
 assert not list(ROOT.glob('.owned-*')),'owned temp remains; do not remove unrelated files'
 assert cases[5]['input']['old']=='' and len(cases[5]['input']['new'])==1024
 mutants=[]
 m=copy.deepcopy(raw[0]['result']);next(e for e in m['events'] if e['event']=='after_replace')['held_reader']=next(e for e in m['events'] if e['event']=='after_replace')['path'];mutants.append(m)
 m=copy.deepcopy(raw[1]['result']);next(e for e in m['events'] if e['event']=='after_exception')['path']['length']=4;mutants.append(m)
 m=copy.deepcopy(raw[2]['result']);next(e for e in m['events'] if e['event']=='partial_overwrite')['path']['sha256']='0'*64;mutants.append(m)
 m=copy.deepcopy(raw[1]['result']);m['committed']=True;mutants.append(m)
 m=copy.deepcopy(raw[0]['result']);m['cleanup']['temp_removed']=False;mutants.append(m)
 m=copy.deepcopy(raw[0]['result']);m['durability_proven']=True;mutants.append(m)
 for m in mutants:
  try:check(m)
  except AssertionError:continue
  raise AssertionError('oracle accepted falsified reader/lifecycle evidence')
 base={'mode':'atomic-abort','old':'old','new':'new','cut':1}
 invalid=[None,{},dict(base,cut=-1),dict(base,cut=4),dict(base,cut=1.0),dict(base,cut=True),dict(base,old='é'),dict(base,new='x'*1025),dict(base,new=None),dict(base,path='../outside'),dict(base,mode='fsck'),dict(base,mode='atomic-commit',cut=1)]
 assert all(run(s)['status']=='rejected' and run(s)['temp_created'] is False for s in invalid)
 for topic,target in [('replace','runner.py'),('verify','checker.py'),('timeline','index.html'),('sources','SOURCES.md')]:assert route(topic)=={'status':'supported','target':target} and (ROOT/target).is_file()
 for topic in ('block-cow','power-loss','raid','repair','mount','kernel-driver','backup','unknown'):assert route(topic)['status']=='unsupported'
 links=0
 for f in list(ROOT.rglob('*.md'))+[ROOT/'index.html',ROOT/'document.html']:
  text=f.read_text();refs=re.findall(r'\]\(([^)]+)\)',text) if f.suffix=='.md' else re.findall(r'(?:href|src)=["\']([^"\']+)',text)
  for ref in refs:
   if ref.startswith(('https://','http://','#')):continue
   parsed=urlsplit(ref);target=(f.parent/parsed.path).resolve()
   assert target==ROOT or ROOT in target.parents,('outside module link',ref)
   assert target.exists(),(f.name,ref)
   for value in parse_qs(parsed.query).get('file',[]):assert (ROOT/value).is_file(),('viewer source missing',value)
   links+=1
 for name in ('README.md','index.html'):
  text=(ROOT/name).read_text()
  for word in ('前提','仕組み','実務','限界','COVERAGE.md','SOURCES.md','durability'):assert word in text,(name,word)
 for word in ('次1','次2','次3','次4','CoW','multiwriter','fsync','未教材'):assert word in (ROOT/'COVERAGE.md').read_text(),word
 meta=json.loads((ROOT/'evidence/run.json').read_text());assert meta['durability_proven'] is False
 assert meta['input_sha256']==digest(ROOT/'cases.json')
 for p,h in meta['source_sha256'].items():assert digest(ROOT/p)==h,('stale source',p)
 for p,h in meta['artifact_sha256'].items():assert digest(ROOT/'evidence'/p)==h,('stale artifact',p)
 assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'artifact drift'
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
 return {'status':'passed','saved_cases':10,'actual_file_cases':7,'independent_reader_snapshots':snapshots,'falsified_evidence_rejected':len(mutants),'additional_input_rejections':len(invalid),'skill_routes':'4 supported / 8 unsupported','local_links':links,'binding':'input/source/raw/reader SVG/artifacts matched','cleanup':'no owned temp remains / held readers closed / server closed','durability_proven':False,'subject_complete':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal-evidence',action='store_true');a=p.parse_args()
 if a.seal_evidence:(ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),ensure_ascii=False,indent=2)+'\n');print('explicit artifact binding sealed; observation time preserved')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False));raise SystemExit(1)
