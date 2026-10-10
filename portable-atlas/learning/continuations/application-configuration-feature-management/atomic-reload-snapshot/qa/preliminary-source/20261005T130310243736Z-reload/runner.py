import argparse,datetime,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
 if not args.record:return subprocess.run([sys.executable,'checker.py'],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')).returncode
 run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-reload')
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');p=subprocess.run([sys.executable,'experiment.py'],capture_output=True,text=True,env=env)
 folder=ROOT/'observations'/run_id;folder.mkdir(parents=True,exist_ok=False)
 command={'argv':['python3','experiment.py'],'stdin':None,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode}
 (folder/'command.json').write_text(json.dumps(command,ensure_ascii=False,indent=2)+'\n')
 if p.returncode:return p.returncode
 raw=json.loads(p.stdout)
 source_names=['experiment.py','runner.py','checker.py','contracts.json','expected-table.json','sources.json','README.md','index.html','app.js','styles.css','route.py','skills/atlas-atomic-reload-snapshot/SKILL.md']+[str(f.relative_to(ROOT)) for f in sorted((ROOT/'fixtures').glob('*.json'))]
 raw.update({'run_id':run_id,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':{n:sha(ROOT/n) for n in source_names}})
 for name in ['contracts.json','expected-table.json']+source_names[12:]:
  dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
 (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 (folder/'artifact-index.json').write_text(json.dumps({'excludes_self':True,'files':{str(f.relative_to(folder)):sha(f) for f in sorted(folder.rglob('*')) if f.is_file()}},indent=2)+'\n')
 (ROOT/'observation-data.js').write_text('window.RELOAD_OBSERVATION='+json.dumps(raw,ensure_ascii=False)+';\n')
 print(json.dumps({'run_id':run_id,'rows':len(raw['rows']),'exit':0}));return 0
if __name__=='__main__':sys.exit(main())
