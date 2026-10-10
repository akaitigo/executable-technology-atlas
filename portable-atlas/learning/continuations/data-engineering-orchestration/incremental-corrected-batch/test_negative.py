#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,sys,tempfile
sys.dont_write_bytecode=True
import checker
ROOT=pathlib.Path(__file__).resolve().parent
def fp():return {str(p):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def main():
 run=ROOT/(ROOT/'CURRENT').read_text().strip();before=fp();checker.check(run);assert before==fp();out=[{'test':'read-only SHA256+mtime_ns','passed':True}]
 for kind in ['missing-c','retained-b','wrong-sum','false-refusal-success','replay-reprocessed','wrong-order','wrong-version']:
  with tempfile.TemporaryDirectory(prefix='incremental-negative-') as td:
   temp=pathlib.Path(td)/'run';shutil.copytree(run,temp);d=json.loads((temp/'result.json').read_text());a=d['cases'][2]['attempts'][0];o=a['observation']
   if kind=='missing-c':o['after']=[['a',110],['d',400]];o['count']=2;o['sum']=510
   if kind=='retained-b':o['after']=[['a',110],['b',200],['c',300],['d',400]];o['count']=4;o['sum']=1010
   if kind=='wrong-sum':o['sum']=811
   if kind=='false-refusal-success':a=d['cases'][3]['attempts'][0];o=a['observation'];a['exitCode']=0;o['exitCode']=0;o['reason']=None
   if kind=='replay-reprocessed':a=d['cases'][2]['attempts'][1];o=a['observation'];o['actions'][0]['action']='upsert'
   if kind=='wrong-order':a=d['cases'][6]['attempts'][0];o=a['observation'];o['events']=list(reversed(o['events']));o['order']=[e['eventId'] for e in o['events']]
   if kind=='wrong-version':o['events'][0]['sourceVersion']=99
   if kind in ['wrong-order','wrong-version']:
    caseName='same-key-order' if kind=='wrong-order' else 'keyed'
    inp=temp/caseName/'batch-0.json';inp.write_text(json.dumps(o['events']));a['inputSha256']=hashlib.sha256(inp.read_bytes()).hexdigest()
   # raw stdout と result の派生表・artifact indexを整合してから独立oracleに渡す。
   for c in d['cases']:
    for rec in c['attempts']:
     rec['stdout']=json.dumps(rec['observation'])+'\n';(temp/c['id']/('stdout-'+str(rec['index'])+'.json')).write_text(rec['stdout'])
   (temp/'result.json').write_text(json.dumps(d));(temp/'stdout.json').write_text(json.dumps(d)+'\n')
   art={str(p.relative_to(temp)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in temp.rglob('*') if p.is_file() and p.name!='artifacts.json'};(temp/'artifacts.json').write_text(json.dumps(art))
   try:checker.check(temp)
   except AssertionError as e:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejection':str(e)})
   else:raise AssertionError('accepted '+kind)
 assert before==fp();print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
