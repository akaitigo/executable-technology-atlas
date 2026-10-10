import datetime,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
SOURCES=['oracle.py','evaluator.py','runner.py','checker.py','server.py','contracts.json','expected-table.json','sources.json','coverage.json','route.py','README.md','index.html','app.js','styles.css','skills/atlas-ready-valid-stalled-payload/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(ROOT)):[digest(p),p.stat().st_mtime_ns] for p in ROOT.rglob('*') if p.is_file()}
def run(text):
 p=subprocess.run([sys.executable,'-B',str(ROOT/'evaluator.py')],input=text,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 return {'argv':['python3','-B','evaluator.py'],'stdin':text,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode,'result':json.loads(p.stdout)}
def collect():
 return {'engine':'Python ideal clock edge model','python':platform.python_version(),'rows':[dict(row,run=run(row['input_json'])) for row in json.loads((ROOT/'expected-table.json').read_text())['rows']]}
def main():
 if len(sys.argv)==1:
  before=snapshot();p=subprocess.run([sys.executable,'-B',str(ROOT/'checker.py')]);assert before==snapshot(),'normal runner mutated unit';return p.returncode
 if sys.argv[1:]!=['--record']:raise SystemExit('runner.py [--record]')
 rid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-ready');folder=ROOT/'observations'/rid;folder.mkdir(parents=True,exist_ok=False)
 raw=collect();raw.update(run_id=rid,source_digests={n:digest(ROOT/n) for n in SOURCES})
 for n in ['expected-table.json','contracts.json','evaluator.py']:
  with (folder/n).open('xb') as f:f.write((ROOT/n).read_bytes())
 with (folder/'raw.json').open('x') as f:json.dump(raw,f,ensure_ascii=False,indent=2);f.write('\n')
 with (folder/'artifact-index.json').open('x') as f:json.dump({'excludes_self':True,'files':{str(p.relative_to(folder)):digest(p) for p in folder.iterdir() if p.is_file() and p.name!='artifact-index.json'}},f,indent=2)
 (ROOT/'observation-data.js').write_text('window.READY_OBSERVATION='+json.dumps(raw,ensure_ascii=False)+';\n')
 print(json.dumps({'run_id':rid,'cases':len(raw['rows'])}));return 0
if __name__=='__main__':sys.exit(main())
