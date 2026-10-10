"""Read-only verification; --seal-evidence alone changes artifact bindings."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from model import analyze,decode,Refused
from oracle import expected,TOKENS
from route import route
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings():return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='integrity.json' and '__pycache__' not in p.parts}
def verify():
 cases=json.loads((ROOT/'cases.json').read_text());raw=json.loads((ROOT/'evidence/raw.json').read_text());assert len(cases)==len(raw)==17
 executed=0
 for c,row in zip(cases,raw):
  assert all(row[k]==c[k] for k in c);r=analyze(c['input']);assert row['result']==r and r['status']==c['expect'],c['id']
  if r['phase']=='execution':
   executed+=1
   for v in ('serialized','ephemeral'):assert row['oracle'][v]==expected(c['input'],v)==r['variants'][v],(c['id'],v)
   for v in r['variants'].values():assert v['steps']<=32
 hand=json.loads((ROOT/'handtrace.json').read_text());byid={r['id']:r for r in raw}
 for key,h in hand.items():
  if not isinstance(h,dict):continue
  r=byid[key]['result']['variants'];normal=r['serialized'];bad=r['ephemeral']
  assert normal['state']['counter']==h['normal_final_counter'] and bad['state']['counter']==h['ephemeral_final_counter'],key
  for k,field in [('final_instance','instance'),('final_process','process')]:
   if k in h:assert normal['state'][field]==h[k]
  if 'event_count' in h:assert normal['steps']==h['event_count'] and normal['trace'][h['recreated_step']]['after']['counter']==h['counter_after_create']
  if 'death_step' in h:assert normal['trace'][h['death_step']]['callback']==h['death_callback'] and normal['trace'][h['death_step']]['after']['alive']==False
 # All12 candidate events at each reachable stage for every counter0..9.
 boot=['create','start','resume'];bg=['pause','stop'];ops=('create','start','resume','tap','pause','stop','save','destroy_rotate','process_death','finish','restart','drop_saved');prefixes=[[]]
 for n in range(10):
  b=boot+['tap']*n
  prefixes.extend([b,b+['pause'],b+bg,b+bg+['save','destroy_rotate'],b+bg+['save','process_death'],b+bg+['save','finish'],b+bg+['save','destroy_rotate','create'],b+bg+['save','destroy_rotate','create','start']])
 transition_checks=0
 for prefix in prefixes:
  for op in ops:
   spec={'saved':None,'events':prefix+[op]};r=analyze(spec)
   for v in ('serialized','ephemeral'):assert r['variants'][v]==expected(spec,v);transition_checks+=1
 for n,token in enumerate(TOKENS):assert decode(token)==n
 bad_saved=['{broken','[]','null','{}','{"counter":3}', '{"version":1,"counter":true}','{"version":true,"counter":1}','{"version":2,"counter":1}','{"version":1,"counter":-1}','{"version":1,"counter":10}','{"version":1,"counter":1.0}','{"version":1,"counter":2,"counter":3}','{"version":1,"counter":1,"extra":0}',' '*129,'{"version":1,"counter":{"version":1}}',chr(0xd800)]
 for token in bad_saved:
  spec={'saved':token,'events':['create']};r=analyze(spec)
  for v in ('serialized','ephemeral'):assert r['variants'][v]==expected(spec,v) and r['variants'][v]['status']=='rejected' and r['variants'][v]['steps']==0
 invalid=[None,{}, {'saved':False,'events':['create']},{'saved':None,'events':[]},{'saved':None,'events':['create']*33},{'saved':None,'events':[True]},{'saved':None,'events':['sdk-install']},{'saved':None,'events':'create'},{'saved':None,'events':['create'],'device':'external'}]
 assert all(analyze(s)['phase']=='input' and analyze(s)['variants']=={} for s in invalid)
 # Maximum event bound and counter bound: meaningful accepted/refused witnesses.
 spec={'saved':None,'events':boot+(['pause','resume']*14)+['pause']};r=analyze(spec);assert len(spec['events'])==32 and r['status']=='accepted'
 mutants=[]
 m=copy.deepcopy(byid['rotation-restore']['oracle']['serialized']);m['state']['counter']=0;mutants.append((m,byid['rotation-restore']['oracle']['serialized']))
 m=copy.deepcopy(byid['process-death-with-snapshot']['oracle']['serialized']);m['trace'][8]['callback']='onDestroy';mutants.append((m,byid['process-death-with-snapshot']['oracle']['serialized']))
 m=copy.deepcopy(byid['rotation-restore']['oracle']['serialized']);m['state']['instance']=1;mutants.append((m,byid['rotation-restore']['oracle']['serialized']))
 m=copy.deepcopy(byid['stale-snapshot']['oracle']['serialized']);m['state']['counter']=2;mutants.append((m,byid['stale-snapshot']['oracle']['serialized']))
 m=copy.deepcopy(byid['finish-cold-launch']['oracle']['serialized']);m['state']['saved']=TOKENS[2];mutants.append((m,byid['finish-cold-launch']['oracle']['serialized']))
 assert all(m!=o for m,o in mutants)
 for topic,target in [('lifecycle','runner.py'),('verify','checker.py'),('diagram','index.html'),('sources','SOURCES.md')]:assert route(topic)=={'status':'supported','target':target} and (ROOT/target).is_file()
 for topic in ('sdk-install','device','emulator','apk','permissions','os-kill','compose','unknown'):assert route(topic)['status']=='unsupported'
 links=0
 for f in list(ROOT.rglob('*.md'))+[ROOT/'index.html',ROOT/'document.html']:
  txt=f.read_text();refs=re.findall(r'\]\(([^)]+)\)',txt) if f.suffix=='.md' else re.findall(r'(?:href|src)=["\']([^"\']+)',txt)
  for ref in refs:
   if ref.startswith(('https://','http://','#')):continue
   parsed=urlsplit(ref);target=(f.parent/parsed.path).resolve();assert target==ROOT or ROOT in target.parents,('outside module',ref);assert target.exists(),(f.name,ref)
   for value in parse_qs(parsed.query).get('file',[]):assert (ROOT/value).is_file(),('viewer source missing',value)
   links+=1
 for name in ('README.md','index.html'):
  txt=(ROOT/name).read_text()
  for word in ('前提','仕組み','実務','限界','COVERAGE.md','SOURCES.md','SPEC.md'):assert word in txt,(name,word)
 for word in ('次1','次2','次3','次4','IPC','ViewModel','未教材'):assert word in (ROOT/'COVERAGE.md').read_text(),word
 meta=json.loads((ROOT/'evidence/run.json').read_text());assert meta['input_sha256']==digest(ROOT/'cases.json')
 for p,h in meta['source_sha256'].items():assert digest(ROOT/p)==h,('stale source',p)
 for p,h in meta['artifact_sha256'].items():assert digest(ROOT/'evidence'/p)==h,('stale artifact',p)
 assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'artifact drift'
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
 return dict(status='passed',saved_cases=17,execution_cases=executed,independent_transition_variant_checks=transition_checks,canonical_save_tokens=10,invalid_saved_states=len(bad_saved),additional_input_rejections=len(invalid),falsified_traces_rejected=len(mutants),event32_boundary='passed',skill_routes='4 supported / 8 unsupported',local_links=links,binding='input/source/raw/diagram/artifacts matched',subject_complete=False,Android_SDK_device_emulator='not executed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal-evidence',action='store_true');a=p.parse_args()
 if a.seal_evidence:(ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),ensure_ascii=False,indent=2)+'\n');print('explicit artifact binding sealed; observation time preserved')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False));raise SystemExit(1)
