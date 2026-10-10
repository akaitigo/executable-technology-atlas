"""Read-only Swift evidence verification. --seal-evidence explicitly updates bindings."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from oracle import expected,projection,VARIANTS
from matrix import cases as matrix_cases
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='integrity.json' and '__pycache__' not in p.parts}
def verify():
 cases=json.loads((ROOT/'cases.json').read_text());raw=json.loads((ROOT/'evidence/raw.json').read_text());matrix=json.loads((ROOT/'evidence/matrix.json').read_text());assert len(cases)==len(raw)==18 and len(matrix)==160
 comparisons=0
 for inputs,rows in [(cases,raw),(matrix_cases(),matrix)]:
  for c,r in zip(inputs,rows):
   assert c['id']==r['id'] and c['json']==r['json'] and len(c['json'].encode())<=4096
   for v in VARIANTS:
    oracle=expected(c['json'],v);assert oracle==r['oracle'][v];assert projection(r['variants'][v])==projection(oracle),(c['id'],v);comparisons+=1
    if r['variants'][v]['status']=='rejected':assert r['variants'][v]['error']['kind'] in ('keyNotFound','valueNotFound','typeMismatch','dataCorrupted')
 hand=json.loads((ROOT/'hand-oracle.json').read_text());byid={r['id']:r for r in raw}
 for key,h in hand.items():
  if type(h)!=dict:continue
  variants=byid[key]['variants'];normal=variants['normal'];assert normal['status']==h['normal'],key
  for field in ('note','age'):
   if field in h:assert normal['profile'][field]==h[field]
  for v,label in [('normal','normal'),('eager-optional','eager')]:
   if label+'_kind' in h:assert variants[v]['error']['kind']==h[label+'_kind'] and variants[v]['error']['coding_path']==h[label+'_path']
  for field in ('name','note'):
   if 'defaulting_'+field in h:assert variants['defaulting']['profile'][field]==h['defaulting_'+field]
 # Actual counterexamples to false schema rules, independent from error formatting.
 mutants=[]
 for id,variant in [('optional-missing','eager-optional'),('optional-null','eager-optional'),('required-missing','defaulting'),('age-string','defaulting'),('age-bool','defaulting'),('note-wrong-type','defaulting'),('int8-overflow','defaulting')]:
  actual=byid[id]['variants'];assert projection(actual[variant])!=projection(expected(byid[id]['json'],'normal'));mutants.append(id)
 m=copy.deepcopy(byid['int8-max']['variants']['normal']);m['profile']['age']=128;assert projection(m)!=projection(expected(byid['int8-max']['json']))
 for topic,target in [('codable','runner.py'),('verify','checker.py'),('json-diagram','index.html'),('sources','SOURCES.md')]:assert route(topic)=={'status':'supported','target':target} and (ROOT/target).is_file()
 for topic in ('ios-simulator','device','sdk-install','signing','swiftui','actors','permissions','unknown'):assert route(topic)['status']=='unsupported'
 links=0
 for f in list(ROOT.rglob('*.md'))+[ROOT/'index.html',ROOT/'document.html']:
  txt=f.read_text();refs=re.findall(r'\]\(([^)]+)\)',txt) if f.suffix=='.md' else re.findall(r'(?:href|src)=["\']([^"\']+)',txt)
  for ref in refs:
   if ref.startswith(('http://','https://','#')):continue
   parsed=urlsplit(ref);target=(f.parent/parsed.path).resolve();assert target==ROOT or ROOT in target.parents,('outside module',ref);assert target.exists(),(f.name,ref)
   for value in parse_qs(parsed.query).get('file',[]):assert (ROOT/value).is_file(),value
   links+=1
 for name in ('README.md','index.html'):
  txt=(ROOT/name).read_text()
  for word in ('前提','仕組み','実務','限界','COVERAGE.md','SOURCES.md','SPEC.md'):assert word in txt,(name,word)
 for word in ('次1','次2','次3','次4','ARC','SwiftUI','未教材'):assert word in (ROOT/'COVERAGE.md').read_text(),word
 log=json.loads((ROOT/'evidence/swift-execution.json').read_text());assert log['compile_exit_code']==log['run_exit_code']==0 and log['build_cache_cleanup'] and log['remaining_owned_build_dirs']==[]
 assert len(log['binary_sha256'])==64;live=json.loads(log['run_stdout']);assert len(live)==178
 for recorded,r in zip(raw+matrix,live):assert recorded['id']==r['id'] and recorded['json']==r['json'] and recorded['variants']==r['variants']
 assert not list(ROOT.glob('.swift-task-*')),'owned build/cache remain'
 meta=json.loads((ROOT/'evidence/run.json').read_text());assert meta['input_sha256']==sha(ROOT/'cases.json') and meta['build_cache_cleanup'] and meta['remaining_owned_build_dirs']==[]
 for p,h in meta['source_sha256'].items():assert sha(ROOT/p)==h,('source drift',p)
 for p,h in meta['artifact_sha256'].items():assert sha(ROOT/'evidence'/p)==h,('artifact drift',p)
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['raw_sha256']==sha(ROOT/'evidence/raw.json') and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
 assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'integrity drift'
 return dict(status='passed',actual_Swift_cases=18,actual_field_matrix_cases=160,independent_variant_comparisons=comparisons,actual_counterexamples=len(mutants),falsified_profile_rejected=1,skill_routes='4 supported / 8 unsupported',local_links=links,build_cache_cleanup=True,checker_mode='saved actual Swift evidence verified; no recompile or evidence rewrite',binding='input/source/stdout/raw/diagram/artifacts matched',subject_complete=False,iOS_device_simulator='not executed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal-evidence',action='store_true');a=p.parse_args()
 if a.seal_evidence:(ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),ensure_ascii=False,indent=2)+'\n');print('explicit binding sealed; Swift observation time preserved')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False));raise SystemExit(1)
