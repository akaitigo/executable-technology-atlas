import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
SOURCES=['Wire.swift','runtime.py','checker.py','runner.py','server.py','README.md','contracts.json','expected-table.json','sources.json','coverage.json','route.py','index.html','app.js','styles.css','skills/atlas-swift-character-scalar-wire-units/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if len(sys.argv)==1:return subprocess.run([sys.executable,str(ROOT/'checker.py')],env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')).returncode
 if sys.argv[1:]!=['--record']:raise SystemExit('use runner.py [--record]')
 id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-swift');folder=ROOT/'observations'/id;folder.mkdir(parents=True,exist_ok=False)
 p=subprocess.run([sys.executable,str(ROOT/'runtime.py')],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 (folder/'command.json').write_text(json.dumps({'argv':['python3','runtime.py'],'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode},ensure_ascii=False,indent=2)+'\n')
 if p.returncode:return p.returncode
 raw=json.loads(p.stdout);raw.update(run_id=id,source_digests={n:digest(ROOT/n) for n in SOURCES})
 for n in ['contracts.json','expected-table.json','Wire.swift']:(folder/n).write_bytes((ROOT/n).read_bytes())
 (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');(folder/'artifact-index.json').write_text(json.dumps({'excludes_self':True,'files':{str(f.relative_to(folder)):digest(f) for f in sorted(folder.rglob('*')) if f.is_file()}},indent=2)+'\n')
 (ROOT/'observation-data.js').write_text('window.SWIFT_OBSERVATION='+json.dumps(raw,ensure_ascii=False)+';\n');print(json.dumps({'run_id':id,'cases':13,'owned_tmp_cleaned':raw['owned_tmp_cleaned'],'exit':0}));return 0
if __name__=='__main__':sys.exit(main())
