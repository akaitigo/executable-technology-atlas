"""Read-only by default. Explicit sealing binds files; never replaces execution provenance."""
import argparse, hashlib, itertools, json, re
from pathlib import Path
from model import step
from runner import run
from oracle import transition, trace
from route import route
ROOT=Path(__file__).resolve().parent

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bindings():
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='integrity.json' and '__pycache__' not in p.parts and p.suffix not in ('.pyc',)}
def verify():
    count=0; mutant_witnesses=0
    for q,prev,edge,en,rst in itertools.product(range(4),range(4),range(2),range(2),range(2)):
        e=dict(t=0,edge=edge,en=en,rst=rst)
        assert step(q,prev,e)==transition(q,prev,e), ('sync',q,prev,e)
        assert step(q,prev,e,'async')==transition(q,prev,e,True)
        mutant_witnesses+=step(q,prev,e,'next-state-bug')!=transition(q,prev,e)
        count+=1
    assert mutant_witnesses==16
    cases=json.loads((ROOT/'cases.json').read_text())
    raw=json.loads((ROOT/'evidence/raw.json').read_text())
    assert len(raw)==len(cases)
    for c,saved in zip(cases,raw):
        out=run(c['input'])
        assert saved==dict(id=c['id'],input=c['input'],result=out),c['id']
        assert out['status']==c['expect'],c['id']
        if out['status']=='accepted':
            for v,async_mode in [('sync',False),('async',True)]:
                assert [[r['q'],r['prev']] for r in out['traces'][v]]==trace(c['input']['events'],async_mode),c['id']
    normal=raw[0]['result']['traces']; pulse=raw[1]['result']['traces']
    assert (normal['sync'][4]['q'],normal['sync'][4]['prev'])==(0,3)
    assert normal['next-state-bug'][4]['prev']==0
    assert pulse['sync'][2]['q']==1 and pulse['async'][2]['q']==0
    assert pulse['sync'][4]['q']==2 and pulse['async'][4]['q']==1
    invalid=[None,{'events':None},{'events':[dict(t=-1,edge=1,en=1,rst=0)]}, {'events':[dict(t=10001,edge=1,en=1,rst=0)]}, {'events':[dict(t=0.5,edge=1,en=1,rst=0)]},{'events':[dict(t=0,edge=2,en=1,rst=0)]},{'events':[dict(t=0,edge=1,en=1.0,rst=0)]},{'events':[dict(t=0,edge=1,en=1,rst=0,extra=0)]},{'events':[dict(t=0,edge=1,en=1)]}]
    assert all(run(x)['status']=='rejected' for x in invalid)
    for topic,target in [('counter','runner.py'),('verify','checker.py'),('waveform','index.html'),('sources','SOURCES.md')]:
        assert route(topic)=={'status':'supported','target':target}
        assert (ROOT/target).is_file()
    for topic in ('synthesis','timing','cdc','axi','hls','hardware','install','unknown'):
        assert route(topic)['status']=='unsupported'
    # Check bounded README/coverage/skill Markdown and HTML local resource links.
    links=0
    for f in list(ROOT.rglob('*.md'))+[ROOT/'index.html']:
        text=f.read_text()
        refs=re.findall(r'\]\(([^)]+)\)',text) if f.suffix=='.md' else re.findall(r'(?:href|src)=["\']([^"\']+)',text)
        for ref in refs:
            if ref.startswith(('https://','http://','#')): continue
            target=(f.parent/ref.split('#')[0]).resolve()
            assert ROOT==target or ROOT in target.parents, ('outside module link',ref)
            assert target.exists(), (f.name,ref)
            links+=1
    for f in ('README.md','index.html'):
        text=(ROOT/f).read_text()
        for token in ('前提','仕組み','実務','限界','COVERAGE.md','SOURCES.md'):
            assert token in text,(f,token)
    coverage=(ROOT/'COVERAGE.md').read_text()
    for token in ('次1','次2','次3','次4','CDC','AXI','STA','未教材','UG901','UG903'):
        assert token in coverage,token
    meta=json.loads((ROOT/'evidence/run.json').read_text())
    assert meta['input_sha256']==digest(ROOT/'cases.json')
    for p,h in meta['source_sha256'].items(): assert digest(ROOT/p)==h, ('stale source',p)
    for p,h in meta['artifact_sha256'].items(): assert digest(ROOT/'evidence'/p)==h, ('stale artifact',p)
    assert json.loads((ROOT/'evidence/integrity.json').read_text())==bindings(),'integrity drift'
    qa=json.loads((ROOT/'evidence/ui-qa.json').read_text())
    assert qa['status']=='passed' and qa['server_cleanup']=='owned process exited; scoped listener inventory empty'
    return {'status':'passed','single_step_states':count,'variants_vs_independent_table':['sync','async'],'mutant_witnesses':mutant_witnesses,'saved_cases':len(cases),'extra_rejections':len(invalid),'skill_routes':'4 supported / 8 unsupported','local_links':links,'provenance':'input/source/raw/waveform/artifact digest matched','UI_QA':'saved IAB observations; capture status recorded','subject_completion':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--seal-evidence',action='store_true'); a=p.parse_args()
    if a.seal_evidence:
        (ROOT/'evidence/integrity.json').write_text(json.dumps(bindings(),ensure_ascii=False,indent=2)+'\n')
        print('explicit artifact binding sealed; run timestamp preserved')
    try: print(json.dumps(verify(),ensure_ascii=False,indent=2))
    except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:
        print(json.dumps({'status':'failed','reason':str(e)},ensure_ascii=False)); raise SystemExit(1)
