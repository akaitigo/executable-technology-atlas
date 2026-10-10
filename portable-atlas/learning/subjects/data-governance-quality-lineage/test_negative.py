import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;source=ROOT/json.loads((ROOT/'current.json').read_text())['directory']
def tree():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file()}
before=tree();p=subprocess.run([sys.executable,'checker.py'],cwd=ROOT,text=True,capture_output=True);assert p.returncode==0 and before==tree(),'checker wrote originals';results=[{'test':'default checker read-only','passed':True}]
for name,key,mutation in [('hide-violation','nonnull',lambda v:v.update(violations=[])),('aggregate','normal',lambda v:v['output'][0].update(amount_sum=101)),('hide-cycle','cycle',lambda v:v.update(graph_errors=[])),('stale-output','source-change',lambda v:v.update(output=[{'category':'c1','amount_sum':100,'class':'public','product_rows':[1]}])),('column-lineage','normal',lambda v:v['column_lineage'][5].update(sources=['validated.class']))]:
    folder=Path(tempfile.mkdtemp(prefix='oracle-negative-',dir=ROOT))
    try:
        shutil.copytree(source,folder,dirs_exist_ok=True);target=folder/key/'result.json';v=json.loads(target.read_text());mutation(v);target.write_text(json.dumps(v));p=subprocess.run([sys.executable,'checker.py','--oracle',folder.name],cwd=ROOT,text=True,capture_output=True);assert p.returncode!=0,name+' accepted';results.append({'test':name,'passed':True,'detected':p.stderr.strip()})
    finally:shutil.rmtree(folder)
assert before==tree(),'original changed';print(json.dumps({'passed':True,'tests':results}))
