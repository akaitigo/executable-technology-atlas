"""Read-only finite checker. Only --seal-evidence updates artifact bindings."""
import argparse,copy,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from emulator import analyze,execute
from oracle import expected,ADD_TABLE,SUCCESSOR,ADVANCE_TWO
from route import route
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings():return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='integrity.json' and '__pycache__' not in p.parts}
def verify():
 cases=json.loads((ROOT/'cases.json').read_text());raw=json.loads((ROOT/'evidence/raw.json').read_text());assert len(cases)==len(raw)==14
 executed=0
 for c,row in zip(cases,raw):
  assert row['id']==c['id'] and row['input']==c['input'] and row['expect']==c['expect'];r=analyze(c['input'])
  assert row['result']==r and r['status']==c['expect'],c['id']
  if r['phase']=='execution':
   executed+=1;assert row['oracle']==expected(c['input'])
   assert {k:v for k,v in r['variants']['correct'].items() if k!='memory_sha256'}==row['oracle']
   h=hashlib.sha256(bytes(r['memory'])).hexdigest()
   for v in r['variants'].values():assert v['memory_sha256']==h and v['steps']<=c['input']['budget']
 hand=json.loads((ROOT/'handtrace.json').read_text())
 for index,key in [(0,'wrap-branch'),(2,'pc-wrap')]:
  projected=[dict(pc_before=t['before']['pc'],a_before=t['before']['a'],op=t['op'],pc_after=t['after']['pc'],a_after=t['after']['a'],taken=t['taken']) for t in raw[index]['result']['variants']['correct']['trace']]
  assert projected==hand[key]['correct']
 assert raw[0]['result']['variants']['naive-unbounded']['state']==hand['wrap-branch']['naive_final'] and raw[0]['result']['variants']['naive-unbounded']['steps']==hand['wrap-branch']['naive_steps']
 assert raw[2]['result']['variants']['naive-unbounded']['fault']['reason']==hand['pc-wrap']['naive_fault']
 assert raw[3]['result']['variants']['correct']['state']==hand['operand-wrap']['normal_final'] and raw[3]['result']['variants']['naive-unbounded']['fault']['reason']==hand['operand-wrap']['naive_fault']
 add_checked=0
 for a in range(256):
  for imm in range(256):
   out=execute({'program':[32,imm,255],'pc':0,'a':a,'budget':2})
   assert out['status']=='halted' and out['state']=={'pc':2,'a':ADD_TABLE[a][imm]}
   add_checked+=1
 fetch_checked=jz_checked=0
 for pc in range(256):
  mem=[0]*256;mem[pc]=16;mem[SUCCESSOR[pc]]=42;mem[ADVANCE_TWO[pc]]=255
  out=execute({'program':mem,'pc':pc,'a':0,'budget':2});assert out['state']=={'pc':ADVANCE_TWO[pc],'a':42} and out['status']=='halted';fetch_checked+=1
  for a in (0,1):
   mem=[0]*256;mem[pc]=48;mem[SUCCESSOR[pc]]=123
   out=execute({'program':mem,'pc':pc,'a':a,'budget':1})
   assert out['trace'][0]['after']=={'pc':123 if a==0 else ADVANCE_TWO[pc],'a':a} and out['trace'][0]['taken']==(a==0)
   jz_checked+=1
 illegal=0
 for opcode in range(256):
  if opcode in (16,32,48,255):continue
  out=execute({'program':[opcode],'pc':0,'a':0,'budget':1});assert out['fault']['reason']=='illegal_opcode' and out['steps']==0;illegal+=1
 # Altered execution traces must fail the independent table/handtrace comparison.
 mutants=[]
 m=copy.deepcopy(raw[0]['result']['variants']['correct']);m['trace'][1]['after']['a']=256;mutants.append((m,raw[0]['oracle']))
 m=copy.deepcopy(raw[0]['result']['variants']['correct']);m['trace'][2]['taken']=False;mutants.append((m,raw[0]['oracle']))
 m=copy.deepcopy(raw[2]['result']['variants']['correct']);m['trace'][0]['after']['pc']=256;mutants.append((m,raw[2]['oracle']))
 m=copy.deepcopy(raw[10]['result']['variants']['correct']);m['fault']=None;mutants.append((m,raw[10]['oracle']))
 for m,o in mutants:assert {k:v for k,v in m.items() if k!='memory_sha256'}!=o
 base={'program':[255],'pc':0,'a':0,'budget':1}
 invalid=[None,{},dict(base,program=[]),dict(base,program=[255]*257),dict(base,program=[True]),dict(base,program=[1.0]),dict(base,pc=-1),dict(base,pc=256),dict(base,a=True),dict(base,budget=0),dict(base,budget=65),dict(base,budget=1.0),dict(base,path='../vm.img')]
 assert all(analyze(s)['phase']=='input' and analyze(s)['variants']=={} for s in invalid)
 for topic,target in [('emulator','runner.py'),('verify','checker.py'),('register-memory','index.html'),('sources','SOURCES.md')]:assert route(topic)=={'status':'supported','target':target} and (ROOT/target).is_file()
 for topic in ('vm-boot','hypervisor','isolation','jit','devices','migration','real-isa','unknown'):assert route(topic)['status']=='unsupported'
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
  for word in ('前提','仕組み','実務','限界','COVERAGE.md','SOURCES.md','SPEC.md'):assert word in text,(name,word)
 for word in ('次1','次2','次3','次4','JIT','hypervisor','isolation','未教材'):assert word in (ROOT/'COVERAGE.md').read_text(),word
 meta=json.loads((ROOT/'evidence/run.json').read_text());assert meta['input_sha256']==digest(ROOT/'cases.json')
 for p,h in meta['source_sha256'].items():assert digest(ROOT/p)==h,('stale source',p)
 for p,h in meta['artifact_sha256'].items():assert digest(ROOT/'evidence'/p)==h,('stale artifact',p)
 assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'artifact drift'
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
 return {'status':'passed','saved_cases':14,'execution_cases':executed,'independent_ADD_pairs':add_checked,'PC_operand_positions':fetch_checked,'JZ_taken_not_taken':jz_checked,'illegal_opcodes_rejected':illegal,'falsified_traces_rejected':len(mutants),'additional_input_rejections':len(invalid),'skill_routes':'4 supported / 8 unsupported','local_links':links,'binding':'input/source/raw/register SVG/artifacts matched','subject_complete':False,'VM_boot_isolation':'not executed'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal-evidence',action='store_true');a=p.parse_args()
 if a.seal_evidence:(ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),ensure_ascii=False,indent=2)+'\n');print('explicit artifact binding sealed; observation time preserved')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False));raise SystemExit(1)
