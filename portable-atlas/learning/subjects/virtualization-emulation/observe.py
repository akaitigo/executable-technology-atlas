import argparse,hashlib,json,platform,sys,time
from pathlib import Path
from datetime import datetime,timezone
from emulator import analyze
from oracle import expected
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'evidence' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts}
def diagram(r):
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="390" viewBox="0 0 1000 390" role="img" aria-label="wrap branch register比較"><rect width="1000" height="390" fill="white"/><text x="20" y="30" font-size="21">実Tiny8 trace — A / PC / opcode（生成図、captureではない）</text>']
 for vi,name in enumerate(('correct','naive-unbounded')):
  y=65+vi*150;out.append('<text x="20" y="%d" font-size="17">%s</text>'%(y,name))
  for i,row in enumerate(r['variants'][name]['trace']):
   x=20+i*192
   out.append('<rect x="%d" y="%d" width="175" height="90" rx="10" fill="%s"/>'%(x,y+12,'#dfeee6' if vi==0 else '#f7e5db'))
   out.append('<text x="%d" y="%d" font-size="15">%d: %s</text>'%(x+12,y+36,i,row['op']))
   out.append('<text x="%d" y="%d" font-size="17">A=%d PC=%d</text>'%(x+12,y+67,row['after']['a'],row['after']['pc']))
   out.append('<text x="%d" y="%d" font-size="13">JZ %s</text>'%(x+12,y+88,row['taken']))
 out.append('<text x="20" y="370" font-size="14">correct: 4step A0 / naive: 5step A99 / 両variant有限budget / 実VM・hypervisor・isolationは未実証</text>')
 return '\n'.join(out+['</svg>'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-evidence',action='store_true');a=p.parse_args()
 if not a.write_evidence:print('read-only: explicit --write-evidence required');sys.exit(0)
 raw=[];stamp=datetime.now(timezone.utc).isoformat();start=time.monotonic_ns()
 for c in json.loads((ROOT/'cases.json').read_text()):
  r=analyze(c['input']);item=dict(c,result=r);raw.append(item)
  try:
   assert r['status']==c['expect']
   if r['phase']=='execution':
    item['oracle']=expected(c['input']);assert {k:v for k,v in r['variants']['correct'].items() if k!='memory_sha256'}==item['oracle']
  except Exception as e:
   (ROOT/'evidence/failed-observation.json').write_text(json.dumps({'observed_at_utc':stamp,'source_sha256':sources(),'raw':raw,'failure':str(e)},ensure_ascii=False,indent=2)+'\n');raise RuntimeError('verification failed; evidence/failed-observation.json preserved')
 ev=ROOT/'evidence';(ev/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');(ev/'register-trace.svg').write_text(diagram(raw[0]['result']))
 meta={'observed_at_utc':stamp,'ended_at_utc':datetime.now(timezone.utc).isoformat(),'duration_ns':time.monotonic_ns()-start,'environment':{'system':platform.system(),'release':platform.release(),'machine':platform.machine(),'python':platform.python_version()},'command':'python3 -B observe.py --write-evidence','input_sha256':digest(ROOT/'cases.json'),'source_sha256':sources(),'artifact_sha256':{p:digest(ev/p) for p in ('raw.json','register-trace.svg')},'executed':'Python stdlib Tiny8 interpreter; both correct and width-omission variant bounded','ISA':'author-defined SPEC.md, no real ISA compatibility claim','unrun':['hypervisor','real VM boot','guest/host isolation','real CPU instruction compatibility','JIT/native codegen','devices/interrupt/MMU','cycle/performance measurement','QEMU/KVM/HVF execution']}
 (ev/'run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'observed','cases':len(raw),'input_accepted_for_execution':sum(x['result']['phase']=='execution' for x in raw),'all_variants_bounded':True}))
