"""Explicit-only observation writer; default invocation is read-only."""
import argparse,datetime,hashlib,json,platform,html
from pathlib import Path
from model import analyze
from oracle import expected
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observe():
 cases=json.loads((ROOT/'cases.json').read_text());rows=[]
 for c in cases:
  result=analyze(c['input']);o={v:expected(c['input'],v) for v in ('serialized','ephemeral')} if result['phase']=='execution' else {}
  row=dict(c,result=result,oracle=o);rows.append(row)
  if result['status']!=c['expect'] or result.get('variants')!=o:
   (ROOT/'evidence/failed-observation.json').write_text(json.dumps(row,indent=2));raise RuntimeError('independent oracle mismatch: '+c['id'])
 raw=ROOT/'evidence/raw.json';raw.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 data=rows[0];normal=data['result']['variants']['serialized'];bad=data['result']['variants']['ephemeral'];svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="510" viewBox="0 0 1000 510"><rect width="1000" height="510" fill="#f5f9f7"/><g font-family="sans-serif"><text x="25" y="32" font-size="21">Generated model trace: rotation / saved state vs ephemeral</text>']
 for n,event in enumerate(data['input']['events']):
  y=64+n*31;a=normal['trace'][n]['after'];b=bad['trace'][n]['after'];label=f'{n} {event}: I{a["instance"]} P{a["process"]} {a["stage"]}'
  svg.append(f'<text x="25" y="{y}" font-size="15">{html.escape(label)}</text><text x="560" y="{y}" fill="#276b51">saved counter={a["counter"]}</text><text x="790" y="{y}" fill="#985648">ephemeral={b["counter"]}</text>')
 svg.append('<text x="25" y="495" font-size="13">Python finite model only; not Android capture / SDK execution</text></g></svg>');(ROOT/'evidence/counter-trace.svg').write_text(''.join(svg))
 meta={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'system':platform.system(),'machine':platform.machine(),'python':platform.python_version()},'input_sha256':sha(ROOT/'cases.json'),'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'evidence' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts},'artifact_sha256':{p.name:sha(p) for p in (raw,ROOT/'evidence/counter-trace.svg')},'scope':'finite model actual Python execution, MAX32 events / counter0..9','unrun':['Android SDK/device/emulator','Android callbacks/Bundle/OS kill','ViewModel/Compose/IPC/permissions/security/performance'],'assumptions':['save only when explicit event supplied','available snapshot input conditional; never guaranteed after process death','JSON codec author-defined, not Bundle']}
 (ROOT/'evidence/run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'observed','cases':len(rows),'execution_cases':len([r for r in rows if r['result']['phase']=='execution'])}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-evidence',action='store_true');a=p.parse_args()
 if a.write_evidence:observe()
 else:print('read-only: observations unchanged; use explicit --write-evidence when requested')
