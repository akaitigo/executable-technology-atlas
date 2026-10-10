import argparse,hashlib,json,platform,sys,time
from datetime import datetime,timezone
from pathlib import Path
from runner import run
from oracle import check
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'evidence' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts}
def fd_diagram(raw):
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="480" viewBox="0 0 1000 480" role="img" aria-label="実入力に基づくFD lifecycle図"><rect width="1000" height="480" fill="white"/><text x="20" y="32" font-size="20">実parent/child data pipe — checkpointと終端 (生成図、captureではない)</text>']
 for i,row in enumerate([raw[0],raw[3],raw[4]]):
  r=row['result'];y=75+i*125;refs=int(r['input']['mode']!='close');eof=any(e['event']=='eof' for e in r['child_events'])
  for x,w,fill in [(20,290,'#eef3f5'),(390,180,'#ddeee7'),(660,315,'#eef3f5')]:out.append('<rect x="%d" y="%d" width="%d" height="100" rx="10" fill="%s"/>'%(x,y,w,fill))
  texts=[(35,y+25,'%s parent PID %s'%(row['id'],r['parent_pid'])),(35,y+52,'write %s closed / dup %s refs=%s'%(r['fds']['parent_write'],r['fds']['parent_duplicate_write'],refs)),(35,y+79,'bounded timeout=%s'%r['bounded_timeout']),(405,y+35,'data pipe'),(405,y+63,'last writer close'),(675,y+25,'child PID %s read FD %s'%(r['child_pid'],r['fds']['child_read'])),(675,y+52,'EOF=%s / exit=%s'%(eof,r['returncode'])),(675,y+79,'cleanup: child reaped / FD closed')]
  for x,yy,t in texts:out.append('<text x="%d" y="%d" font-size="14">%s</text>'%(x,yy,t))
  out.append('<path d="M315 %dH385 M575 %dH655" stroke="#3e737d" stroke-width="3"/>'%(y+50,y+50))
 return '\n'.join(out+['</svg>'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-evidence',action='store_true');a=p.parse_args()
 if not a.write_evidence:print('read-only: explicit --write-evidence required');sys.exit(0)
 raw=[];stamp=datetime.now(timezone.utc).isoformat();start=time.monotonic_ns()
 for c in json.loads((ROOT/'cases.json').read_text()):
  r=run(c['input']);item=dict(c,result=r)
  raw.append(item)
  try:
   if r['status']=='observed':item['oracle']=check(r)
   elif r['status']!='rejected':raise RuntimeError(r['failure'])
  except Exception as error:
   (ROOT/'evidence/failed-observation.json').write_text(json.dumps({'observed_at_utc':stamp,'source_sha256':sources(),'raw':raw,'failure':str(error)},ensure_ascii=False,indent=2)+'\n')
   raise RuntimeError('observation verification failed; preserved in evidence/failed-observation.json')
 ev=ROOT/'evidence';(ev/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');(ev/'fd-lifecycle.svg').write_text(fd_diagram(raw))
 meta={'observed_at_utc':stamp,'ended_at_utc':datetime.now(timezone.utc).isoformat(),'duration_ns':time.monotonic_ns()-start,'environment':{'system':platform.system(),'release':platform.release(),'machine':platform.machine(),'python':platform.python_version()},'command':'python3 -B observe.py --write-evidence','input_sha256':digest(ROOT/'cases.json'),'source_sha256':sources(),'artifact_sha256':{p:digest(ev/p) for p in ('raw.json','fd-lifecycle.svg')},'executed':'actual owned subprocess / os.pipe / os.dup / os.read / os.close / SIGTERM / wait','clock_contract':'mono_ns is process-local elapsed; wall_ns timeline display approximate; no cross-process mono ordering proof','unrun':['kernel modification','VM','host settings','internal kernel tracing','scheduler latency/throughput benchmark','Linux/Windows runtime','nonblocking and SIGPIPE tests']}
 (ev/'run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':'observed','cases':len(raw),'actual_children':sum(x['result']['status']=='observed' for x in raw),'all_children_reaped':all(x['result'].get('cleanup',{}).get('child_reaped',True) for x in raw)},ensure_ascii=False))
