import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;source=ROOT/json.loads((ROOT/'current.json').read_text())['directory']
def tree():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file()}
before=tree();p=subprocess.run([sys.executable,'checker.py'],cwd=ROOT,text=True,capture_output=True);assert p.returncode==0 and before==tree(),'read-only failed';results=[{'test':'default checker read-only','passed':True}]
for name,key,kind in [('generated-bytes','cold','bytes'),('toolchain-key','toolchain-change','tool'),('dependency-binding','dependency-same-mtime','dep'),('false-cache-hit','source-same-mtime-content','hit'),('hide-cycle','cycle','error')]:
    folder=Path(tempfile.mkdtemp(prefix='oracle-negative-',dir=ROOT))
    try:
        shutil.copytree(source,folder,dirs_exist_ok=True);i=2 if key in ('toolchain-change','dependency-same-mtime','source-same-mtime-content') else 1;state=folder/key/f'attempt-{i}';target=state/'result.json';v=json.loads(target.read_text())
        if kind=='bytes':(state/'bundle.bin').write_bytes(b'wrong\n')
        elif kind=='tool':v['actions'][0]['key_payload']['toolchain']='toy-1'
        elif kind=='dep':v['actions'][0]['input_bindings']['suffix.txt']['digest']='sha256:wrong'
        elif kind=='hit':v['actions'][0]['cache']='hit'
        else:v['errors']=[]
        if kind!='bytes':target.write_text(json.dumps(v))
        p=subprocess.run([sys.executable,'checker.py','--oracle',folder.name],cwd=ROOT,text=True,capture_output=True);assert p.returncode!=0,name+' accepted';results.append({'test':name,'passed':True,'detected':p.stderr.strip()})
    finally:shutil.rmtree(folder)
assert before==tree(),'original changed';print(json.dumps({'passed':True,'tests':results}))
