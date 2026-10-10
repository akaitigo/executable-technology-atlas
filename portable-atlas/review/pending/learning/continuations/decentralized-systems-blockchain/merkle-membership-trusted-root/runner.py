"""Default readonly; --record creates a fresh UTC observation, never overwrites."""
import datetime,hashlib,json,platform,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
SOURCES=['calculate.py','runner.py','checker.py','contracts.json','hand-oracle.json','expected-table.json','sources.json','README.md','COVERAGE.md','server.py','index.html','app.js','styles.css','route.py','skills/atlas-merkle-membership-trusted-root/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(ROOT)):(digest(p),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def run(text):
 p=subprocess.run([sys.executable,'-B','calculate.py'],input=text,text=True,capture_output=True,cwd=ROOT)
 return {'argv':['python3','-B','calculate.py'],'stdin':text,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode,'result':json.loads(p.stdout)}
def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];data={'run_id':datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-merkle'),'engine':'hashlib SHA256 finite ordered membership','python':platform.python_version(),'rows':[{**r,'run':run(r['input_json'])} for r in rows],'source_digests':{n:digest(ROOT/n) for n in SOURCES}}
 assert before==snapshot()
 if '--record' in sys.argv:
  target=ROOT/'observations'/data['run_id'];target.mkdir(parents=True)
  (target/'raw.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  for n in ['calculate.py','contracts.json','hand-oracle.json','expected-table.json']:(target/n).write_bytes((ROOT/n).read_bytes())
  (target/'artifact-index.json').write_text(json.dumps({'excludes_self':True,'files':{p.name:digest(p) for p in target.iterdir() if p.is_file()}},indent=2)+'\n')
  (ROOT/'observation-data.js').write_text('window.MERKLE_OBSERVATION='+json.dumps(data,ensure_ascii=False)+';\n')
  print(json.dumps({'recorded':data['run_id'],'rows':len(rows)}))
 else:print(json.dumps({'rows':len(data['rows']),'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
