import argparse,datetime,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 if not args.record:return subprocess.run([sys.executable,'checker.py'],env=env).returncode
 id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-interval');result=subprocess.run([sys.executable,'experiment.py'],capture_output=True,text=True,env=env)
 folder=ROOT/'observations'/id;folder.mkdir(parents=True,exist_ok=False)
 (folder/'command.json').write_text(json.dumps({'argv':['python3','experiment.py'],'stdin':None,'stdout':result.stdout,'stderr':result.stderr,'exit':result.returncode},ensure_ascii=False,indent=2)+'\n')
 if result.returncode:return result.returncode
 raw=json.loads(result.stdout);names=['experiment.py','runner.py','checker.py','contracts.json','expected-table.json','sources.json','coverage.json','route.py','README.md','index.html','app.js','styles.css','skills/atlas-interval-input-version-reuse/SKILL.md']+[str(f.relative_to(ROOT)) for f in sorted((ROOT/'fixtures').glob('*.json'))]
 raw.update({'run_id':id,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':{n:sha(ROOT/n) for n in names}})
 for n in ['contracts.json','expected-table.json']+names[13:]:
  dest=folder/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes())
 (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 (folder/'artifact-index.json').write_text(json.dumps({'excludes_self':True,'files':{str(f.relative_to(folder)):sha(f) for f in sorted(folder.rglob('*')) if f.is_file()}},indent=2)+'\n')
 (ROOT/'observation-data.js').write_text('window.INTERVAL_OBSERVATION='+json.dumps(raw,ensure_ascii=False)+';\n');print(json.dumps({'run_id':id,'cases':len(raw['rows']),'modes':4,'exit':0}));return 0
if __name__=='__main__':sys.exit(main())
