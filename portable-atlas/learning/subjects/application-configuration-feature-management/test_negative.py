import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;source=ROOT/json.loads((ROOT/'current.json').read_text())['directory']
def tree():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file()}
before=tree();p=subprocess.run([sys.executable,'checker.py'],cwd=ROOT,text=True,capture_output=True);assert p.returncode==0 and before==tree(),'read-only failed';results=[{'test':'default checker read-only','passed':True}]
for name,key,change in [('winning-config','task-over-env',lambda v:v['config'].update(timeout_ms=2000)),('provenance','task-over-env',lambda v:v['provenance']['timeout_ms'].update(layer='env-input')),('bucket','defaults',lambda v:v['actors'][0].update(bucket=2711)),('truthiness-observation','truthiness-bug',lambda v:v['config'].update(flag_enabled=False)),('hide-secret-refusal','unknown-secret-field',lambda v:v.update(errors=[]))]:
    folder=Path(tempfile.mkdtemp(prefix='oracle-negative-',dir=ROOT))
    try:
        shutil.copytree(source,folder,dirs_exist_ok=True);target=folder/key/'result.json';v=json.loads(target.read_text());change(v);target.write_text(json.dumps(v));p=subprocess.run([sys.executable,'checker.py','--oracle',folder.name],cwd=ROOT,text=True,capture_output=True);assert p.returncode!=0,name+' accepted';results.append({'test':name,'passed':True,'detected':p.stderr.strip()})
    finally:shutil.rmtree(folder)
assert before==tree(),'original changed';print(json.dumps({'passed':True,'tests':results}))
