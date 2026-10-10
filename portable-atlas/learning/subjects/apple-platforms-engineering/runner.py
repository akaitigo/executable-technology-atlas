"""Read-only saved Swift result or independent JSON prediction; explicit live option."""
import argparse,json
from pathlib import Path
from oracle import expected,VARIANTS
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',default='optional-missing');p.add_argument('--json');p.add_argument('--run-swift',action='store_true');a=p.parse_args()
 if a.json is not None:
  if len(a.json.encode('utf-8'))>4096:print(json.dumps({'status':'rejected','phase':'input','reason':'JSON text exceeds lesson4096byte bound'}));raise SystemExit(2)
  cases=[{'id':'custom','json':a.json}]
 else:
  allcases=json.loads((ROOT/'cases.json').read_text());cases=[c for c in allcases if c['id']==a.case]
  if not cases:print(json.dumps({'status':'unsupported','reason':'unknown fixed case'}));raise SystemExit(2)
 if a.run_swift:
  from swift_run import execute
  rows,log=execute(cases);out={'mode':'actual Swift compile/run','row':rows[0],'cleanup':log['build_cache_cleanup']}
 elif a.json is not None:out={'mode':'independent Python prediction; Swift not run','row':{'id':'custom','json':a.json,'variants':{v:expected(a.json,v) for v in VARIANTS}}}
 else:
  row=next(r for r in json.loads((ROOT/'evidence/raw.json').read_text()) if r['id']==a.case);out={'mode':'saved actual Swift observation, read-only','row':row}
 print(json.dumps(out,ensure_ascii=True,indent=2));raise SystemExit(0 if out['row']['variants']['normal']['status']=='accepted' else 2)
