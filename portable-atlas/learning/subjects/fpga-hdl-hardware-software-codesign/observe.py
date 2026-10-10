"""Only --write-evidence mutates provenance. Does not install or invoke missing tools."""
import argparse, hashlib, json, platform, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
from runner import run
ROOT=Path(__file__).resolve().parent
SOURCE_FILES=['model.py','oracle.py','runner.py','cases.json','rtl/counter.v','rtl/tb.v','SOURCES.md']
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def waveform(rows):
    colors={'sync':'#117a65','next-state-bug':'#b03a2e','async':'#2471a3'}
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="380" viewBox="0 0 1000 380" role="img" aria-label="モデルevent波形">','<rect width="1000" height="380" fill="#fff"/>','<text x="20" y="26" font-size="17">Pythonモデルevent波形 — arbitrary t / post-event / clock levelではない</text>']
    for vi,v in enumerate(colors):
        for si,sig in enumerate(('q','prev')):
            y=75+vi*90+si*35
            out.append('<text x="10" y="%s" font-size="13">%s %s</text>'%(y,v,sig))
            data=rows['traces'][v]
            for i,e in enumerate(data):
                x=160+i*110
                out.append('<path d="M%d %d h100" stroke="%s" stroke-width="3"/>'%(x,y-e[sig]*5,colors[v]))
                out.append('<text x="%d" y="%d" font-size="13">%d</text>'%(x+30,y-8-e[sig]*5,e[sig]))
                if vi==2 and si==1: out.append('<text x="%d" y="355" font-size="13">t=%d</text>'%(x,e['t']))
    return '\n'.join(out+['</svg>'])

def observe():
    cases=json.loads((ROOT/'cases.json').read_text())
    raw=[dict(id=c['id'],input=c['input'],result=run(c['input'])) for c in cases]
    stamp=datetime.now(timezone.utc).isoformat()
    return raw, {'observed_at_utc':stamp,'environment':{'system':platform.system(),'release':platform.release(),'machine':platform.machine(),'python':platform.python_version()}, 'input_sha256':digest(ROOT/'cases.json'), 'source_sha256':{p:digest(ROOT/p) for p in SOURCE_FILES}, 'tool_availability':{'iverilog':bool(shutil.which('iverilog')),'verilator':bool(shutil.which('verilator')),'vvp':bool(shutil.which('vvp'))},'executed':'Python clocked state transition model', 'rtl_simulation':'not executed; no iverilog/verilator on observed PATH', 'unrun':['synthesis','timing closure','hardware','CDC safety','HW/SW integration'],'command':'python3 -B observe.py --write-evidence','input_units':'arbitrary t, event-based, edge inputs settled before rising event'}
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--write-evidence',action='store_true'); a=p.parse_args()
    if not a.write_evidence:
        print('read-only: explicit --write-evidence required to refresh observations'); sys.exit(0)
    raw,meta=observe()
    ev=ROOT/'evidence'
    (ev/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
    (ev/'waveform.svg').write_text(waveform(raw[0]['result']))
    meta['artifact_sha256']={p:digest(ev/p) for p in ('raw.json','waveform.svg')}
    (ev/'run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'observed','cases':len(raw),'executed':meta['executed'],'tools':meta['tool_availability']}))
