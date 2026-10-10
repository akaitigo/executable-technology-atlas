"""Explicit-only finite model observation writer; no Windows API execution."""
import argparse,datetime,hashlib,html,json,platform
from pathlib import Path
from parser import analyze
from oracle import expected,parity_vectors
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observe():
 cases=json.loads((ROOT/'cases.json').read_text());rows=[]
 for c in cases:
  result=analyze(c['input']);h=expected(c['id']);row=dict(c,result=result,oracle=h);rows.append(row)
  matched=result['status']==c['expect'] and (result['variants']['subset']['args']==h['args'] if result['status']=='accepted' else (result['reason'] if result['phase']=='input' else result['variants']['subset']['fault']['reason'])==h['reject_reason'])
  if not matched:(ROOT/'evidence/failed-observation.json').write_text(json.dumps(row,indent=2)+'\n');raise RuntimeError('manual table mismatch: '+c['id'])
 matrix=[]
 for c in parity_vectors():
  result=analyze(c['input']);assert result['status']=='accepted' and result['variants']['subset']['args']==c['args'],c['id'];matrix.append(dict(c,result=result))
 raw=ROOT/'evidence/raw.json';raw.write_text(json.dumps(rows,ensure_ascii=True,indent=2)+'\n');(ROOT/'evidence/parity-matrix.json').write_text(json.dumps(matrix,indent=2)+'\n')
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="610"><rect width="1100" height="610" fill="#f4f8f7"/><g font-family="sans-serif"><text x="25" y="35" font-size="24">Python quoting subset model / NOT native Windows execution</text>']
 row=rows[0]
 for n,t in enumerate(row['result']['variants']['subset']['trace']):
  y=75+n*31;s=t['after'];label=f'{n} {repr(t["char"])}: q={s["quoted"]} pending={s["pending_backslashes"]} current={repr(s["current"])} emitted={s["args"]}'
  svg.append(f'<text x="25" y="{y}" font-size="16">{html.escape(label)}</text>')
 svg.append('<text x="25" y="540" font-size="16">Manual expected tail args: [a b c, d, e] / naive split: 5 pieces</text><text x="25" y="575" font-size="14">Generated diagram; not IAB screenshot. argv[0], Unicode, adjacent quote rules excluded.</text></g></svg>');(ROOT/'evidence/quote-trace.svg').write_text(''.join(svg))
 meta={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'system':platform.system(),'machine':platform.machine(),'python':platform.python_version()},'input_sha256':sha(ROOT/'cases.json'),'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and 'evidence' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts},'artifact_sha256':{p.name:sha(p) for p in (raw,ROOT/'evidence/parity-matrix.json',ROOT/'evidence/quote-trace.svg')},'execution':'actual Python finite subset model only','oracle':'manual literal table and closed-form parity vectors, no parser import','unrun':['Windows API/CommandLineToArgvW/CRT','Windows VM/native process/CreateProcess','argv0/full commandline/UTF16/shell/security/GUI'], 'scope':'ASCII argument tail <=128char, balanced/adjacent restricted; subset refusal not Windows refusal'}
 (ROOT/'evidence/run.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps({'status':'observed','saved_cases':len(rows),'parity_vectors':len(matrix),'Windows_API':'not executed'}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-evidence',action='store_true');a=p.parse_args()
 if a.write_evidence:observe()
 else:print('read-only: observations unchanged; use explicit --write-evidence when requested')
