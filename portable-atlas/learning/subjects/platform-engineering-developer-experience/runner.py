import argparse,datetime,hashlib,json,platform,re,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def load(n):return json.loads((ROOT/n).read_text())
def validate_config(c):
    k=load('contract.json')
    if type(c) is not dict or set(c)!=set(k['configKeys']):raise ValueError('config-keys')
    n=c['name']
    if type(n) is not str:raise ValueError('invalid-name')
    if '/' in n or '\\' in n or n in ('.','..'):raise ValueError('path-escape')
    if not re.fullmatch('[a-z][a-z0-9-]{0,19}',n):raise ValueError('invalid-name')
    if c['owner'] not in k['owners']:raise ValueError('invalid-owner')
    if c['kind'] not in k['kinds']:raise ValueError('invalid-kind')
    if type(c['schemaVersion']) is not int or c['schemaVersion']!=2:raise ValueError('invalid-schema')
def render(c,v):
    validate_config(c);t=load('templates.json')
    if str(v) not in t:raise ValueError('unsupported-template')
    return {p:s.format(**c) for p,s in t[str(v)].items()}
def safe_target(root,relative):
    if type(relative) is not str or not relative or '\\' in relative:raise ValueError('path-escape')
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts:raise ValueError('path-escape')
    target=(root/p).resolve()
    if root.resolve() not in target.parents:raise ValueError('path-escape')
    return target
def write_tree(root,tree):
    targets=[(safe_target(root,p),s) for p,s in tree.items()]
    for p,s in targets:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def read_tree(root):return {p.relative_to(root).as_posix():p.read_text(encoding='utf-8') for p in sorted(root.rglob('*')) if p.is_file()}
def file_hashes(tree):return {p:hashlib.sha256(s.encode()).hexdigest() for p,s in sorted(tree.items())}
def validate_tree(c,tree):
    e=render(c,2);missing=sorted(set(e)-set(tree));extra=sorted(set(tree)-set(e));changed=sorted(p for p in set(e)&set(tree) if e[p]!=tree[p]);meta=[]
    try:
        m=json.loads(tree.get('project.json',''))
        for k in ('schemaVersion','templateVersion'):
            if type(m.get(k)) is not int or m[k]!=2:meta.append(k)
    except (ValueError,AttributeError):meta.append('invalid-project-json')
    assert sorted(e)==load('contract.json')['requiredFiles']
    return {'valid':not(missing or extra or changed or meta),'missing':missing,'extra':extra,'changed':changed,'metadataDrift':meta,'expectedFileHashes':file_hashes(e),'actualFileHashes':file_hashes(tree)}
def cycle(case,folder):
    cases=load('fixture.json')['cases']
    if case not in cases:raise ValueError('unsupported-case')
    inp=cases[case];c=inp['config'];folder=Path(folder);start=time.perf_counter_ns();trace=[]
    def event(p):trace.append({'phase':p,'elapsedNs':time.perf_counter_ns()-start,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    event('validate-input');base={'case':case,'input':inp,'inputDigest':digest(inp),'environment':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()}}
    try:tree=render(c,inp['templateVersion'])
    except ValueError as e:return dict(base,status='rejected',reason=str(e),tree={},repeatTree={},filesWritten=0,trace=trace)
    write_tree(folder/'first',tree);event('render-first');write_tree(folder/'repeat',render(c,inp['templateVersion']));event('render-repeat');repeat=read_tree(folder/'repeat');before=read_tree(folder/'first');fault=inp['fault']
    if fault=='schema':p=folder/'first/project.json';p.write_text(p.read_text().replace('"schemaVersion":2','"schemaVersion":1'))
    elif fault=='tamper':p=folder/'first/README.md';p.write_text(p.read_text()+'DRIFT\n')
    elif fault=='missing':(folder/'first/src/main.py').unlink()
    elif fault=='extra':(folder/'first/extra.txt').write_text('unexpected\n')
    event('inject-fault');actual=read_tree(folder/'first');report=validate_tree(c,actual);event('validate-contract')
    return dict(base,status='valid' if report['valid'] else 'drift',reason=None,tree=actual,repeatTree=repeat,preFaultFileHashes=file_hashes(before),repeatFileHashes=file_hashes(repeat),deterministicRender=before==repeat,report=report,filesWritten=len(before)+len(repeat),trace=trace)
def run(case):
    work=ROOT/'observations/work';work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fixture-',dir=work) as folder:return cycle(case,folder)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=list(load('fixture.json')['cases']),default='cedar');a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))
