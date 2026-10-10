"""Tamper disposable copies; verify the default checker does not write."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT/json.loads((ROOT/'current.json').read_text())['directory']
def tree(): return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file()}
before=tree(); good=subprocess.run([sys.executable,'checker.py'],cwd=ROOT,capture_output=True,text=True); assert good.returncode==0 and before==tree(),'checker changed originals'
results=[{'test':'default checker read-only','passed':True}]
for name,file,change in [('amount','normal/after-1/output.csv',lambda s:s.replace('250','251')),('quarantine','normal/after-1/quarantine.json',lambda s:'[]\n'),('schema','normal/after-1/schema.json',lambda s:s.replace('integer','string',1)),('failure-pointer','publish-failure-after-success/after-2/current.json',lambda s:s.replace('generation','changed'))]:
    folder=Path(tempfile.mkdtemp(prefix='oracle-negative-',dir=ROOT))
    try:
        shutil.copytree(source,folder,dirs_exist_ok=True); target=folder/file; target.write_text(change(target.read_text()))
        result=subprocess.run([sys.executable,'checker.py','--oracle',folder.name],cwd=ROOT,capture_output=True,text=True)
        assert result.returncode!=0,name+' tamper accepted'
        results.append({'test':name,'passed':True,'detected':result.stderr.strip()})
    finally: shutil.rmtree(folder)
assert before==tree(),'negative tests changed original'
print(json.dumps({'passed':True,'tests':results}))
