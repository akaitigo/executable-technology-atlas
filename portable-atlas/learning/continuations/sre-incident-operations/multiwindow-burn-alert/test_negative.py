#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,sys,tempfile
sys.dont_write_bytecode=True
import checker
ROOT=pathlib.Path(__file__).resolve().parent
def fp():return {str(p):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def main():
 run=ROOT/(ROOT/'CURRENT').read_text().strip();before=fp();checker.check(run);assert before==fp();out=[{'test':'read-only SHA256 + mtime_ns','passed':True}]
 for kind in ['short-only-as-and','wrong-long-fraction','wrong-denominator','boundary-100-included','missing-failed-id','empty-as-false','refusal-as-success']:
  with tempfile.TemporaryDirectory(prefix='burn-negative-') as td:
   temp=pathlib.Path(td)/'run';shutil.copytree(run,temp);d=json.loads((temp/'result.json').read_text());c=d['cases'][1];o=c['observation']
   if kind=='short-only-as-and':o['and']=True
   if kind=='wrong-long-fraction':o['windows']['long']['burn']=[4,1];o['windows']['long']['burnText']='4';o['windows']['long']['overThreshold']=True
   if kind=='wrong-denominator':o['windows']['short']['denominator']=100
   if kind=='boundary-100-included':c=d['cases'][4];o=c['observation'];o['windows']['long']['eventIds'].append(100);o['windows']['long']['failedIds'].append(100);o['windows']['long']['denominator']=4;o['windows']['long']['failures']=4
   if kind=='missing-failed-id':o['windows']['short']['failedIds'].pop()
   if kind=='empty-as-false':c=d['cases'][5];c['observation']['and']=False
   if kind=='refusal-as-success':c=d['cases'][8];c['exitCode']=0;c['observation']['reason']=None
   for rec in d['cases']:
    rec['stdout']=json.dumps(rec['observation'])+'\n';(temp/rec['id']/'stdout.json').write_text(rec['stdout'])
   (temp/'result.json').write_text(json.dumps(d));(temp/'stdout.json').write_text(json.dumps(d)+'\n')
   artifacts={str(p.relative_to(temp)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in temp.rglob('*') if p.is_file() and p.name!='artifacts.json'};(temp/'artifacts.json').write_text(json.dumps(artifacts))
   try:checker.check(temp)
   except AssertionError as e:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejection':str(e)})
   else:raise AssertionError('accepted '+kind)
 assert before==fp();print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
