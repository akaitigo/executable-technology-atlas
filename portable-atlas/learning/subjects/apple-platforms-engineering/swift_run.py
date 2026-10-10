"""Explicit actual compile/run, task-owned temporary output/cache cleanup."""
import datetime,hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def execute(cases):
 # Build/cache/temp are module-owned; no package install or toolchain change.
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();tmp_name=None;result=None
 with tempfile.TemporaryDirectory(prefix='.swift-task-',dir=ROOT) as name:
  tmp=Path(name);tmp_name=tmp.name;cache=tmp/'cache';cache.mkdir();env=dict(os.environ);env.update(TMPDIR=str(tmp),CLANG_MODULE_CACHE_PATH=str(cache),SWIFT_MODULECACHE_PATH=str(cache))
  binary=tmp/'lesson';cmd=['xcrun','swiftc','Lesson.swift','-module-cache-path',str(cache),'-o',str(binary)]
  compile_result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
  def sanitized(text):return text.replace(str(ROOT),'<module>').replace(str(tmp),'<owned-build>')
  log={'started_at_utc':started,'compiler_command':['xcrun','swiftc','Lesson.swift','-module-cache-path','<owned-build>/cache','-o','<owned-build>/lesson'],'compile_exit_code':compile_result.returncode,'compile_stdout':sanitized(compile_result.stdout),'compile_stderr':sanitized(compile_result.stderr)}
  if compile_result.returncode:raise RuntimeError(json.dumps(log))
  binary_hash=hashlib.sha256(binary.read_bytes()).hexdigest()
  payload=json.dumps([{'id':c['id'],'json':c['json']} for c in cases],ensure_ascii=True)
  run_result=subprocess.run([str(binary)],input=payload,cwd=ROOT,env=env,capture_output=True,text=True,timeout=10)
  log.update(run_exit_code=run_result.returncode,run_stdout=run_result.stdout,run_stderr=sanitized(run_result.stderr),binary_sha256=binary_hash,stdin_sha256=hashlib.sha256(payload.encode()).hexdigest())
  if run_result.returncode:raise RuntimeError(json.dumps(log))
  result=(json.loads(run_result.stdout),log)
 result[1].update(finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),build_cache_cleanup=not (ROOT/tmp_name).exists(),remaining_owned_build_dirs=sorted(p.name for p in ROOT.glob('.swift-task-*')))
 return result
