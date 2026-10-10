"""Read-only finite quoting checker; only --seal-evidence updates bindings."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from parser import analyze
from oracle import expected,parity_vectors
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='integrity.json' and '__pycache__' not in p.parts}
def trace_check(v,text):
 trace=v['trace'];assert len(trace)<=len(text)+1
 for i,t in enumerate(trace):
  assert t['index']==i and t['char']==(text[i] if i<len(text) else '<EOF>')
  if i:assert t['before']==trace[i-1]['after']
  s=t['after']
  if 'pending_backslashes' in s:assert 0<=s['pending_backslashes']<=len(text) and type(s['quoted']) is bool
  assert all(type(a) is str for a in s['args'])
 if v['status']=='accepted':assert trace[-1]['char']=='<EOF>' and trace[-1]['after']['args']==v['args']
def verify():
 cases=json.loads((ROOT/'cases.json').read_text());raw=json.loads((ROOT/'evidence/raw.json').read_text());assert len(cases)==len(raw)==21
 executed=witnesses=0
 for c,row in zip(cases,raw):
  assert all(c[k]==row[k] for k in c);r=analyze(c['input']);h=expected(c['id']);assert r==row['result'] and r['status']==c['expect'] and h==row['oracle'] and h['tail']==c['input']['tail']
  if r['phase']=='input':assert r['reason']==h['reject_reason'] and r['variants']=={};continue
  executed+=1;normal=r['variants']['subset'];bad=r['variants']['simple-split']
  for v in (normal,bad):trace_check(v,c['input']['tail'])
  if r['status']=='accepted':
   assert normal['args']==h['args'];witnesses+=normal['args']!=bad['args']
  else:assert normal['args'] is None and normal['fault']['reason']==h['reject_reason']
 vectors=parity_vectors();matrix=json.loads((ROOT/'evidence/parity-matrix.json').read_text());assert len(matrix)==len(vectors)==39
 for c,row in zip(vectors,matrix):
  assert all(c[k]==row[k] for k in c);r=analyze(c['input']);assert r==row['result'] and r['status']=='accepted' and r['variants']['subset']['args']==c['args']
  for v in r['variants'].values():trace_check(v,c['input']['tail'])
  # Neutral exterior separators do not alter an argument tail. This is not full argv0 behavior.
  padded=analyze({'tail':'\t '+c['input']['tail']+' \t'});assert padded['status']=='accepted' and padded['variants']['subset']['args']==c['args']
 # False odd/even and empty-argument expectations must fail manual/closed-form oracles.
 m=copy.deepcopy(raw[3]['result']['variants']['subset']['args']);m[0]=m[0].replace('"','');assert m!=expected('odd-three-slashes')['args']
 m=copy.deepcopy(raw[4]['result']['variants']['subset']['args']);m[0]='a'+('\\'*4)+'b c';assert m!=expected('even-four-slashes')['args']
 assert []!=expected('empty-argument')['args']
 invalid=[None,{}, {'tail':False},{'tail':3},{'tail':[]},{'tail':'a','command':'external'},{'tail':'x'*129},{'tail':'a\r'},{'tail':'a\v'},{'tail':'a\x7f'},{'tail':'😀'},{'tail':'\0'}]
 assert all(analyze(s)['phase']=='input' and analyze(s)['variants']=={} for s in invalid)
 assert len(raw[14]['result']['variants']['subset']['trace'])==129
 for topic,target in [('quoting','runner.py'),('verify','checker.py'),('character-trace','index.html'),('sources','SOURCES.md')]:assert route(topic)=={'status':'supported','target':target} and (ROOT/target).is_file()
 for topic in ('windows-api','vm','crt','argv0','unicode','powershell','process','unknown'):assert route(topic)['status']=='unsupported'
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
  for word in ('前提','仕組み','実務','限界','COVERAGE.md','SOURCES.md','SPEC.md','実Windows','未実行'):assert word in txt,(name,word)
 for word in ('次1','次2','次3','次4','COM','security','未教材'):assert word in (ROOT/'COVERAGE.md').read_text(),word
 meta=json.loads((ROOT/'evidence/run.json').read_text());assert meta['input_sha256']==sha(ROOT/'cases.json')
 for p,h in meta['source_sha256'].items():assert sha(ROOT/p)==h,('source drift',p)
 for p,h in meta['artifact_sha256'].items():assert sha(ROOT/'evidence'/p)==h,('artifact drift',p)
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['raw_sha256']==sha(ROOT/'evidence/raw.json') and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
 assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'integrity drift'
 return dict(status='passed',saved_cases=21,execution_cases=executed,closed_form_parity_vectors=39,neutral_tail_separator_checks=39,actual_simple_split_counterexamples=witnesses,falsified_expectations_rejected=3,additional_input_rejections=len(invalid),max128_trace_rows=129,skill_routes='4 supported / 8 unsupported',local_links=links,binding='input/source/raw/parity matrix/diagram/artifacts matched',subject_complete=False,Windows_API_CRT_VM='not executed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal-evidence',action='store_true');a=p.parse_args()
 if a.seal_evidence:(ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),indent=2)+'\n');print('explicit binding sealed; observation time preserved')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False));raise SystemExit(1)
