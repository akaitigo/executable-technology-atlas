import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;source=ROOT/json.loads((ROOT/'current.json').read_text())['directory']
def tree():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file()}
before=tree();p=subprocess.run([sys.executable,'checker.py'],cwd=ROOT,text=True,capture_output=True);assert p.returncode==0 and before==tree(),'read-only failed';results=[{'test':'default checker read-only','passed':True}]
for name,key,change in [('wrong-peer-sum','peers',lambda v:v['observations'][0]['rows'][0].update(total=10)),('missing-peer-id','peers',lambda v:v['observations'][0]['rows'][0].update(frame_ids=[1])),('null-to-zero','null-amounts',lambda v:v['observations'][0]['rows'][0].update(total=0)),('order-contract','peers',lambda v:v['observations'][0].update(sql=v['observations'][0]['sql'].replace('ORDER BY sort_key)','ORDER BY sort_key,id)'))),('invalid-frame-success','invalid-start-end',lambda v:v['observations'][0].update(outcome='rows',error=None))]:
    folder=Path(tempfile.mkdtemp(prefix='oracle-negative-',dir=ROOT))
    try:
        shutil.copytree(source,folder,dirs_exist_ok=True);target=folder/key/'result.json';v=json.loads(target.read_text());change(v)
        # Keep all raw/derived copies consistent so detection reaches the independent oracle.
        for observation in v['observations']:
            for row in observation['rows']:
                row['frame_ids_raw']=','.join(map(str,row['frame_ids']))
            observation['raw_rows']=[[row[c] for c in observation['columns']] for row in observation['rows']]
        target.write_text(json.dumps(v))
        trace_path=folder/key/'trace.json';trace=json.loads(trace_path.read_text());position=0
        for i,event in enumerate(trace):
            if event['event']=='query-observed':trace[i]={'event':'query-observed',**v['observations'][position]};position+=1
        trace_path.write_text(json.dumps(trace))
        cmd_path=folder/key/'command.json';cmd=json.loads(cmd_path.read_text());cmd['stdout']=''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in trace);cmd['stdout_digest']='sha256:'+hashlib.sha256(cmd['stdout'].encode()).hexdigest();cmd_path.write_text(json.dumps(cmd))
        p=subprocess.run([sys.executable,'checker.py','--oracle',folder.name],cwd=ROOT,text=True,capture_output=True);assert p.returncode!=0,name+' accepted';results.append({'test':name,'passed':True,'detected':p.stderr.strip()})
    finally:shutil.rmtree(folder)
assert before==tree(),'original changed';print(json.dumps({'passed':True,'tests':results}))
