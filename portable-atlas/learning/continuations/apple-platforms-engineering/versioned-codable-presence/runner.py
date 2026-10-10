"""Explicit Swift execution; tmp compiler outputs never in user caches."""
import datetime,hashlib,json,os,pathlib,platform,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
SOURCES=['main.swift','runner.py','fixtures.json','hand-oracle.json']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def binding():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}
class SwiftSession:
    def __init__(self):
        self.temp=tempfile.TemporaryDirectory(prefix='atlas-codable-',dir='/private/tmp');self.path=pathlib.Path(self.temp.name);self.binary=self.path/'lesson';self.env=os.environ.copy();self.env['TMPDIR']=str(self.path);self.env['CLANG_MODULE_CACHE_PATH']=str(self.path/'module-cache');self.env['SWIFT_MODULECACHE_PATH']=str(self.path/'module-cache')
        cmd=['swiftc','main.swift','-module-cache-path',str(self.path/'module-cache'),'-o',str(self.binary)]
        started=utc();p=subprocess.run(cmd,cwd=ROOT,env=self.env,capture_output=True,text=True)
        clean=lambda s:s.replace(str(self.path),'OWN_TMP').replace(str(ROOT),'.')
        version=subprocess.run(['swiftc','--version'],capture_output=True,text=True)
        self.compile=dict(utc=started,command=['swiftc','main.swift','-module-cache-path','OWN_TMP/module-cache','-o','OWN_TMP/lesson'],exit=p.returncode,stdout=clean(p.stdout),stderr=clean(p.stderr),toolchain=version.stdout,toolchain_exit=version.returncode,binary_sha256=hashlib.sha256(self.binary.read_bytes()).hexdigest() if p.returncode==0 else None,tmp_scope='own /private/tmp ephemeral directory',source_binding=binding())
    def run(self,cases):
        fixtures=json.loads((ROOT/'fixtures.json').read_text());requests=[dict(case=n,**fixtures[n]) for n in cases];started=utc()
        if self.compile['exit']!=0:return dict(utc=started,compile=self.compile,result=dict(status='EXECUTION_FAILURE',phase='compile',error='SwiftCompileFailure'),source_binding=binding())
        p=subprocess.run([str(self.binary)],input=json.dumps(requests),cwd=ROOT,env=self.env,capture_output=True,text=True)
        attempt=dict(command=['OWN_TMP/lesson'],exit=p.returncode,stdout=p.stdout,stderr=p.stderr.replace(str(self.path),'OWN_TMP').replace(str(ROOT),'.'),input_requests=requests,binary_sha256=self.compile['binary_sha256'])
        if p.returncode!=0:return dict(utc=started,compile=self.compile,attempt=attempt,result=dict(status='EXECUTION_FAILURE',phase='process',error='SwiftProcessFailure'),source_binding=binding())
        values=json.loads(p.stdout)
        return {n:dict(case=n,utc=started,runtime=dict(python=platform.python_version(),os=platform.system(),machine=platform.machine()),fixture=fixtures[n],compile=self.compile,attempt=attempt,result=v,source_binding=binding()) for n,v in zip(cases,values)}
    def close(self):self.temp.cleanup();return not self.path.exists()
def execute(cases):
    session=SwiftSession()
    try:result=session.run(cases)
    finally:clean=session.close()
    if 'result' in result:result['owned_compile_tmp_cleaned']=clean
    else:
        for v in result.values():v['owned_compile_tmp_cleaned']=clean
    return result
if __name__=='__main__':
    if sys.argv[1:]==['--record']:
        result=execute(list(json.loads((ROOT/'fixtures.json').read_text())));d=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');d.mkdir();(d/'raw.json').write_text(json.dumps(result,indent=2)+'\n');print(d.relative_to(ROOT));sys.exit(0 if 'result' not in result else 1)
    elif len(sys.argv)==3 and sys.argv[1]=='--case':
        result=execute([sys.argv[2]]);print(json.dumps(result.get(sys.argv[2],result),indent=2))
    else:raise SystemExit('Use --case FIXED_CASE for actual compile/run; explicit --record to save')
