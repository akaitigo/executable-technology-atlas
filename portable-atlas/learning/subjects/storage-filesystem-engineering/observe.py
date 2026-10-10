import argparse,hashlib,json,platform,sys,time
from datetime import datetime,timezone
from pathlib import Path
from runner import run
from oracle import check
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'evidence' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts}
def diagram(raw):
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="440" viewBox="0 0 1000 440" role="img" aria-label="実reader最終snapshot比較"><rect width="1000" height="440" fill="white"/><text x="20" y="30" font-size="21">実reader snapshot — length / SHA prefix（生成図、captureではない）</text>']
 for i,row in enumerate(raw[:3]):
  es=row['result']['events'];last=[e for e in es if 'path' in e][-1];y=65+i*120
  out.append('<text x="20" y="%d" font-size="16">%s</text>'%(y,row['id']))
  for x,name,obj in [(20,'target path',last['path']),(350,'held reader',last['held_reader']),(680,'new.tmp',last['candidate'])]:
   out.append('<rect x="%d" y="%d" width="300" height="85" rx="10" fill="%s"/>'%(x,y+10,'#f5e8dc' if i==2 else '#e3efeb'))
   out.append('<text x="%d" y="%d" font-size="15">%s length=%s</text>'%(x+15,y+35,name,obj['length'] if obj else 'none'))
   out.append('<text x="%d" y="%d" font-size="14">SHA: %s</text>'%(x+15,y+65,obj['sha256'][:18] if obj else 'none'))
 out.append('<text x="20" y="435" font-size="13">全temp cleanup済 / fsync call-return ≠ power-loss durability proof / application write-new ≠ physical block CoW</text>')
 return '\n'.join(out+['</svg>'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-evidence',action='store_true');a=p.parse_args()
 if not a.write_evidence:print('read-only: explicit --write-evidence required');sys.exit(0)
 raw=[];stamp=datetime.now(timezone.utc).isoformat();start=time.monotonic_ns()
 for c in json.loads((ROOT/'cases.json').read_text()):
  r=run(c['input']);item=dict(c,result=r);raw.append(item)
  try:
   if r['status']=='observed':item['oracle']=check(r)
   elif r['status']!='rejected':raise RuntimeError(r['unexpected'])
  except Exception as e:
   (ROOT/'evidence/failed-observation.json').write_text(json.dumps({'observed_at_utc':stamp,'source_sha256':sources(),'raw':raw,'failure':str(e)},ensure_ascii=False,indent=2)+'\n');raise RuntimeError('verification failed; evidence/failed-observation.json preserved')
 ev=ROOT/'evidence';(ev/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');(ev/'reader-states.svg').write_text(diagram(raw))
 meta={'observed_at_utc':stamp,'ended_at_utc':datetime.now(timezone.utc).isoformat(),'duration_ns':time.monotonic_ns()-start,'environment':{'system':platform.system(),'release':platform.release(),'machine':platform.machine(),'python':platform.python_version()},'command':'python3 -B observe.py --write-evidence','input_sha256':digest(ROOT/'cases.json'),'source_sha256':sources(),'artifact_sha256':{p:digest(ev/p) for p in ('raw.json','reader-states.svg')},'executed':'owned TemporaryDirectory / actual file writes, flush, fsync, os.replace, held/path reader snapshots, cleanup','durability_proven':False,'unrun':['power-loss/crash durability','F_FULLFSYNC/device cache persistence','physical block CoW or filesystem type detection','continuous concurrent readers/multiwriter','metadata/ACL preservation','cross-filesystem EXDEV','Linux/Windows runtime','real disk errors']}
 (ev/'run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'observed','cases':len(raw),'actual_file_cases':sum(x['result']['status']=='observed' for x in raw),'all_owned_temp_removed':all(x['result'].get('cleanup',{}).get('temp_removed',True) for x in raw)}))
