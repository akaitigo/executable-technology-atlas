import pathlib,json,hashlib,tempfile,shutil,sys
sys.dont_write_bytecode=True
from checker import check
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
 names=['premature-global-max','unseen-as-zero','watermark-regression','close-boundary-strict','late-grace-lost','end-included','drop-normalized','failure-normal-window']
 for name in names:
  with tempfile.TemporaryDirectory(prefix='watermark-negative-owned-') as td:
   root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());cs={c['id']:c for c in d['cases']};c=cs['min-complete'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout'])
   if name=='premature-global-max':o['trace'][2]['watermark']=18;o['trace'][2]['finalizedNow']=[0];o['trace'][2]['windows'][0].update(finalized=True,finalizedStep=3);o['summary']['windows'][0]['finalizedStep']=3
   elif name=='unseen-as-zero':c=cs['unseen-partition'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['trace'][0]['watermark']=0;o['summary']['watermark']=18
   elif name=='watermark-regression':o['trace'][3]['watermark']=-2;o['summary']['watermark']=-2
   elif name=='close-boundary-strict':c=cs['deadline-boundary'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['trace'][6]['finalizedNow']=[];o['summary']['windows'][0].update(finalized=False,finalizedStep=None)
   elif name=='late-grace-lost':c=cs['grace-late-update'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['summary']['windows'][0]['sum']=3;o['summary']['windows'][0]['ids'].remove('e5');o['summary']['accepted'].remove('e5');o['summary']['dropped']=['e5'];o['summary']['lateAccepted']=[]
   elif name=='end-included':c=cs['no-grace-boundary'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['trace'][2]['windowStart']=0;o['summary']['windows'][0]['sum']+=3;o['summary']['windows'][0]['ids'].append('e3')
   elif name=='drop-normalized':c=cs['max-fault'];o=json.loads(c['stdout']);a=json.loads(c['auditStdout']);o['summary']['accepted'].append('e4');o['summary']['dropped']=[];o['summary']['windows'][0]['sum']=7;o['summary']['windows'][0]['ids'].append('e4');a['maxFaultLoss']=[]
   else:c=cs['execution-failure'];c['exitCode']=0;c['stderr']='';a['outcome']='OBSERVED'
   c['stdout']=json.dumps(o)+'\n';a['summary']=o['summary'];c['auditStdout']=json.dumps(a)+'\n';c['auditCommand']['inputRaw']=json.dumps({k:c[k] for k in ['inputRaw','argv','startedUtc','endedUtc','exitCode','stdout','stderr']});c['auditCommand']['stdout']=c['auditStdout'];c['auditCommand']['stderr']=c['auditStderr'];refresh(root,d)
   try:check(root)
   except (AssertionError,ValueError,KeyError,TypeError):out.append({'test':name,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralOrPrefixOracleRejected':True})
   else:raise AssertionError(name+' accepted')
 assert before==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':out},indent=2))
if __name__=='__main__':main()
