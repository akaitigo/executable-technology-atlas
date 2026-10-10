"""Only explicit --write-evidence compiles/runs Swift and updates evidence."""
import argparse,datetime,hashlib,html,json,platform,subprocess
from pathlib import Path
from swift_run import execute
from oracle import expected,projection,VARIANTS
from matrix import cases as matrix_cases
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observe():
 cases=json.loads((ROOT/'cases.json').read_text());matrix=matrix_cases();allrows,log=execute(cases+matrix)
 for c,r in zip(cases+matrix,allrows):
  assert r['id']==c['id'] and r['json']==c['json'];r['oracle']={v:expected(c['json'],v) for v in VARIANTS}
  if any(projection(r['variants'][v])!=projection(r['oracle'][v]) for v in VARIANTS):
   (ROOT/'evidence/failed-observation.json').write_text(json.dumps({'row':r,'log':log},ensure_ascii=False,indent=2)+'\n');raise RuntimeError('oracle mismatch: '+c['id'])
 rows=allrows[:len(cases)];(ROOT/'evidence/matrix.json').write_text(json.dumps(allrows[len(cases):],ensure_ascii=False,indent=2)+'\n')
 raw=ROOT/'evidence/raw.json';raw.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(ROOT/'evidence/swift-execution.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="680"><rect width="1080" height="680" fill="#f5f8fb"/><g font-family="sans-serif"><text x="25" y="35" font-size="23">Actual Swift Codable: normal / eager optional / try? defaulting</text>']
 for n,r in enumerate(rows):
  y=70+n*30;svg.append(f'<text x="25" y="{y}" font-size="15">{html.escape(r["id"])}</text>')
  for x,v in zip((355,575,820),VARIANTS):
   o=r['variants'][v];label=o['status'] if not o['error'] else o['error']['kind'];color='#226650' if o['status']=='accepted' else '#9a523c';svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="14">{html.escape(label)}</text>')
 svg.append('<text x="25" y="645" font-size="14">Generated diagram from actual Swift outputs; not IAB screenshot / iOS app execution</text></g></svg>');(ROOT/'evidence/decode-matrix.svg').write_text(''.join(svg))
 version=subprocess.run(['swift','--version'],capture_output=True,text=True,timeout=10)
 meta={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'system':platform.system(),'machine':platform.machine(),'python':platform.python_version(),'swift_version':version.stdout.strip(),'swift_version_exit':version.returncode},'input_sha256':sha(ROOT/'cases.json'),'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'evidence' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts},'artifact_sha256':{p.name:sha(p) for p in (raw,ROOT/'evidence/swift-execution.json',ROOT/'evidence/matrix.json',ROOT/'evidence/decode-matrix.svg')},'actual':'Foundation JSONDecoder compiled/run with existing xcrun swiftc on Darwin arm64','oracle':'Python JSON/type rules compare status/profile; Swift diagnostics kept raw, not universalized','build_cache_cleanup':log['build_cache_cleanup'],'remaining_owned_build_dirs':log['remaining_owned_build_dirs'],'unrun':['iOS/iPadOS/watchOS/tvOS/visionOS runtime','UI app/Xcode project/device/simulator','SwiftUI/UIKit/AppKit/actor concurrency/ARC/ABI/signing/security/performance']}
 (ROOT/'evidence/run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'observed','actual_swift_cases':len(rows),'variant_comparisons':len(allrows)*3,'matrix_cases':len(matrix),'build_cache_cleanup':log['build_cache_cleanup']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-evidence',action='store_true');a=p.parse_args()
 if a.write_evidence:observe()
 else:print('read-only: saved Swift observations unchanged; actual compile/run requires --write-evidence')
