import argparse,datetime,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args();env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 if not args.record:return subprocess.run([sys.executable,'checker.py'],env=env).returncode
 id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-material');p=subprocess.run([sys.executable,'experiment.py'],capture_output=True,text=True,env=env);folder=ROOT/'observations'/id;folder.mkdir(parents=True,exist_ok=False)
 (folder/'command.json').write_text(json.dumps({'argv':['python3','experiment.py'],'stdin':None,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode},ensure_ascii=False,indent=2)+'\n')
 if p.returncode:return p.returncode
 raw=json.loads(p.stdout);names=['experiment.py','runner.py','checker.py','contracts.json','expected-table.json','sources.json','coverage.json','route.py','README.md','index.html','app.js','styles.css','skills/atlas-transitive-material-closure/SKILL.md']+[str(f.relative_to(ROOT)) for f in sorted((ROOT/'fixtures').iterdir()) if f.is_file()]
 raw.update({'run_id':id,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':{n:digest(ROOT/n) for n in names}})
 for n in ['contracts.json','expected-table.json']+names[13:]:
  dest=folder/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/n).read_bytes())
 for row in raw['rows']:
  if row['artifact']:
   dest=folder/row['id']/'artifact.bin';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(bytes.fromhex(row['artifact']['hex']))
 (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
 (folder/'artifact-index.json').write_text(json.dumps({'excludes_self':True,'files':{str(f.relative_to(folder)):digest(f) for f in sorted(folder.rglob('*')) if f.is_file()}},indent=2)+'\n')
 (ROOT/'observation-data.js').write_text('window.MATERIAL_OBSERVATION='+json.dumps(raw,ensure_ascii=False)+';\n');print(json.dumps({'run_id':id,'rows':8,'artifact_files':5,'exit':0}));return 0
if __name__=='__main__':sys.exit(main())
