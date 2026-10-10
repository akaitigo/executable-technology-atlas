import hashlib,json,os,platform,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Runtime:
 def __enter__(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='swift-wire-owned-');self.path=Path(self.tmp.name);self.binary=self.path/'wire'
  version=subprocess.run(['swiftc','--version'],capture_output=True,text=True);self.identity={'compiler':'swiftc','version_stdout':version.stdout,'version_stderr':version.stderr,'version_exit':version.returncode,'host':platform.system(),'arch':platform.machine()}
  argv=['swiftc',str(ROOT/'Wire.swift'),'-module-cache-path',str(self.path/'cache'),'-o',str(self.binary)]
  p=subprocess.run(argv,capture_output=True,text=True,timeout=120);self.compile={'argv':['swiftc','Wire.swift','-module-cache-path','$OWNED_TMP/cache','-o','$OWNED_TMP/wire'],'stdout':p.stdout.replace(str(ROOT),'$UNIT').replace(str(self.path),'$OWNED_TMP'),'stderr':p.stderr.replace(str(ROOT),'$UNIT').replace(str(self.path),'$OWNED_TMP'),'exit':p.returncode}
  if p.returncode:self.tmp.cleanup();raise RuntimeError(json.dumps(self.compile))
  self.identity['binary_sha256']=hashlib.sha256(self.binary.read_bytes()).hexdigest();return self
 def run(self,text):
  p=subprocess.run([str(self.binary)],input=text,capture_output=True,text=True,timeout=5)
  return {'argv':['$OWNED_TMP/wire'],'stdin':text,'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode,'result':json.loads(p.stdout)}
 def __exit__(self,*args):self.tmp.cleanup();self.cleaned=not self.path.exists()
def produce():
 c=json.loads((ROOT/'contracts.json').read_text())
 with Runtime() as rt:rows=[dict(id=x['id'],label=x['label'],input_json=x['input_json'],**rt.run(x['input_json'])) for x in c['cases']];raw={'identity':rt.identity,'compile':rt.compile,'rows':rows}
 raw['owned_tmp_cleaned']=rt.cleaned;return raw
if __name__=='__main__':print(json.dumps(produce(),ensure_ascii=False))
