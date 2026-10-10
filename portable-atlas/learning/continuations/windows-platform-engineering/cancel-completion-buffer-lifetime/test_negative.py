import pathlib,json,hashlib,tempfile,shutil,sys
sys.dont_write_bytecode=True
from checker import check,audit
R=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fp():return {p.relative_to(R).as_posix():(sha(p),p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
def refresh(root,d):
 run=root/(root/'CURRENT').read_text().strip()
 for c in d['cases']:
  f=run/c['id'];(f/'stdout.txt').write_text(c['stdout']);(f/'stderr.txt').write_text(c['stderr']);(f/'input.txt').write_text(c['inputRaw']);(f/'audit-stdout.txt').write_text(c['auditStdout']);(f/'audit-stderr.txt').write_text(c['auditStderr']);(f/'command.json').write_text(json.dumps(c,indent=2)+'\n');(f/'audit-command.json').write_text(json.dumps(c['auditCommand'],indent=2)+'\n')
 raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw);(run/'artifacts.json').write_text(json.dumps({'files':{p.relative_to(run).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'}},indent=2)+'\n')
def main():
 before=fp();out=[]
 for name in ['cancel-as-complete','guard-reuse-allowed','generation-reset','interference-hidden','aborted-payload-write','failure-normal-state']:
  with tempfile.TemporaryDirectory(prefix='cancel-negative-owned-') as td:
   root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());cs={c['id']:c for c in d['cases']};c=cs['guarded-success'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout'])
   if name=='cancel-as-complete':o['trace'][1]['state']['operationA'].update(pending=False,status='aborted')
   elif name=='guard-reuse-allowed':o['trace'][2]['result']='REUSE_ALLOWED';o['summary']['reuseAllowed']=True
   elif name=='generation-reset':c=cs['variable-generation4'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['summary']['buffer']['generation']=2
   elif name=='interference-hidden':c=cs['fault-success'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['summary']['interference']=False
   elif name=='aborted-payload-write':c=cs['fault-aborted'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['summary']['buffer']['payload']='A-result'
   else:c=cs['execution-failure'];c['exitCode']=0;c['stderr']='';a['outcome']='OBSERVED'
   c['stdout']=json.dumps(o)+'\n';a['summary']=o['summary'];c['auditStdout']=json.dumps(a)+'\n';c['auditCommand']['inputRaw']=json.dumps({k:c[k] for k in ['inputRaw','argv','startedUtc','endedUtc','exitCode','stdout','stderr']});c['auditCommand']['stdout']=c['auditStdout'];c['auditCommand']['stderr']=c['auditStderr'];refresh(root,d)
   try:check(root)
   except (AssertionError,ValueError,KeyError,TypeError):out.append({'test':name,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralOrOrderOracleRejected':True})
   else:raise AssertionError(name+' accepted')
 assert before==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':out},indent=2))
if __name__=='__main__':main()
