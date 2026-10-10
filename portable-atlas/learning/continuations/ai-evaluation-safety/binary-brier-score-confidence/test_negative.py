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
 for name in ['mean-zero','sample-loss-hidden','wrong-square','strict-threshold','accuracy-as-brier','refusal-normal-score','json-normal-score','fault-certified']:
  with tempfile.TemporaryDirectory(prefix='brier-negative-owned-') as td:
   root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());cs={c['id']:c for c in d['cases']};c=cs['moderate'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout'])
   if name=='mean-zero':o['summary']['reportedBrier']='0';a['probabilityBrier']='0';a['reportedBrier']='0'
   elif name=='sample-loss-hidden':o['samples'][0]['squaredError']='0';a['samples'][0]['probabilitySquaredError']='0';a['samples'][0]['reportedSquaredError']='0'
   elif name=='wrong-square':o['samples'][0]['squaredError']='2/5';a['samples'][0]['probabilitySquaredError']='2/5'
   elif name=='strict-threshold':c=cs['threshold50'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['samples'][0]['class']=0;a['samples'][0]['class']=0
   elif name=='accuracy-as-brier':o['summary']['reportedBrier']='1';a['probabilityBrier']='1';a['reportedBrier']='1'
   elif name in ['refusal-normal-score','json-normal-score']:
    c=cs['refused-empty' if name=='refusal-normal-score' else 'execution-failure'];c['exitCode']=0;c['stderr']='';a.update(outcome='OBSERVED',probabilityBrier='0',reportedBrier='0',correct=2)
   else:c=cs['threshold-fault-moderate'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);a['reportedScoreValid']=True
   c['stdout']=json.dumps(o)+'\n';c['auditStdout']=json.dumps(a)+'\n';c['auditCommand']['inputRaw']=json.dumps({k:c[k] for k in ['inputRaw','argv','startedUtc','endedUtc','exitCode','stdout','stderr']});c['auditCommand']['stdout']=c['auditStdout'];c['auditCommand']['stderr']=c['auditStderr'];refresh(root,d)
   try:check(root)
   except (AssertionError,ValueError,KeyError,TypeError):out.append({'test':name,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralOrIntegerOracleRejected':True})
   else:raise AssertionError(name+' accepted')
 assert before==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':out},indent=2))
if __name__=='__main__':main()
