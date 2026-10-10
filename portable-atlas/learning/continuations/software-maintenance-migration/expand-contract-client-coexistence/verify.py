# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import argparse,copy,hashlib,json,platform,sqlite3,subprocess,datetime
from pathlib import Path
from model import run,cents,text
from oracle import check,observe,AMOUNTS,SCHEMA
R=Path(__file__).resolve().parent
SOURCES=['fixture.json','model.py','oracle.py','verify.py','route.py','serve.py','index.html','source.html','README.md','VERIFICATION.md','sources.json','coverage.json','skills/expand-contract/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {s:digest(R/s) for s in SOURCES}
def calculate():
 f=json.loads((R/'fixture.json').read_text());results={c['id']:run(c,observe) for c in f['cases']}
 for name,result in results.items():check(name,result)
 for name in ['bridge','active-guard','contract']:
  trace=results[name]['trace'];statement="UPDATE money SET amount_text='20.00',amount_cents=2000 WHERE id=1";i=trace.index(statement)
  assert trace[i-1:i+2]==['BEGIN ',statement,'COMMIT']
 failure=results['execution-failure']['trace'];statement="UPDATE money SET amount_text='20.00' WHERE id=1";i=failure.index(statement)
 assert failure[i-1:i+2]==['BEGIN ',statement,'ROLLBACK']
 amounts=[]
 for s,n in AMOUNTS:
  assert cents(s)==n and text(n)==s;amounts.append(dict(text=s,cents=n))
 invalid=[]
 for value in ['1.005','01.20','-1.00','10000.00','1.0','1e2','NaN','１２.３０',None,True]:
  c=copy.deepcopy(f['cases'][6]);c['amount']=value;result=run(c,observe);assert result['status']=='REFUSED_INVALID_AMOUNT';check('invalid-amount',result);invalid.append(dict(value=value,result=result))
 for value in [-1,1000000,True,1.5,'1230']:
  try:text(value)
  except ValueError:invalid.append(dict(cent=value,refused=True))
  else:raise AssertionError('invalid cent accepted')
 for value in [None,'true',1]:
  c=copy.deepcopy(f['cases'][4]);c['retired']=value;result=run(c,observe);assert result['status']=='REFUSED_INVALID_INPUT' and result['phases']==[];invalid.append(dict(retired=value,result=result))
 mutations=[]
 for label,name,field in [('wrong-cent','backfill','cent'),('old-column-kept','contract','schema'),('stale-guard','old-write-fault','guard'),('active-guard-allowed','active-guard','guard'),('failure-normal','execution-failure','status'),('old-client-success','contract','old')]:
  result=copy.deepcopy(results[name])
  if field=='cent':result['phases'][-1]['direct']['rows'][0][2]=1231
  elif field=='schema':result['phases'][-1]['direct']['schema']=SCHEMA['expand']
  elif field=='guard':result['guard']['allowed']=True
  elif field=='status':result['status']='OK'
  else:result['phases'][-1]['clients']['old']['status']='OK'
  try:check(name,result)
  except AssertionError:mutations.append(dict(label=label,rejected=True))
  else:raise AssertionError('mutation accepted '+label)
 return dict(results=results,amounts=amounts,invalid=invalid,mutations=mutations)
def main():
 p=argparse.ArgumentParser();p.add_argument('--record');p.add_argument('--seal-record',action='store_true');a=p.parse_args();computed=calculate();attempt=R/'observations'/'attempt-02'
 if a.record:
  assert a.record=='attempt-02' and not attempt.exists(),'only unused attempt-02'
  attempt.mkdir();raw=dict(command=['python3','-B','verify.py','--record','attempt-02'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,system=platform.system(),machine=platform.machine()),inputs=json.loads((R/'fixture.json').read_text()),source_hashes=hashes(),exit_status=0,**computed)
  (attempt/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
  (R/'observations'/'data.js').write_text('window.EVIDENCE='+json.dumps(computed,ensure_ascii=False)+';\n')
  (R/'observations'/'receipt.json').write_text(json.dumps(dict(source_hashes=hashes(),artifacts={str(x.relative_to(R)):digest(x) for x in [attempt/'raw.json',R/'observations'/'data.js']},ui_pending=True),indent=2)+'\n')
 elif a.seal_record:
  receipt=R/'observations'/'receipt.json';old=json.loads(receipt.read_text());assert old['ui_pending']
  (R/'observations'/'initial-receipt.json').write_bytes(receipt.read_bytes())
  qa=R/'observations'/'ui-qa.json';assert json.loads(qa.read_text())['passed']
  receipt.write_text(json.dumps(dict(source_hashes=hashes(),artifacts={str(x.relative_to(R)):digest(x) for x in R.rglob('*') if x.is_file() and str(x.relative_to(R)).startswith('observations/') and x.name not in ('receipt.json','read-only-proof.json')},ui_pending=False,sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
 else:
  raw=json.loads((attempt/'raw.json').read_text());assert {k:raw[k] for k in computed}==computed
  receipt=json.loads((R/'observations'/'receipt.json').read_text());assert receipt['source_hashes']==hashes() and not receipt['ui_pending']
  for s,h in receipt['artifacts'].items():assert digest(R/s)==h,s
  initial=json.loads((R/'observations'/'initial-receipt.json').read_text());assert raw['source_hashes']==initial['source_hashes']
  for s,h in initial['artifacts'].items():assert digest(R/s)==h,s
  qa=json.loads((R/'observations'/'ui-qa.json').read_text());assert qa['passed'] and len(qa['cases'])==8
  for case in qa['cases']:
   result=computed['results'][case['scenario']];assert case['status'].startswith(result['status'])
   assert case['guard']==result['guard']
   if result['status']=='EXECUTION_FAILURE':assert case['answer']=='' and case['result']=='EXECUTION_FAILURE: 前の比較・正常答えを破棄'
  assert len(qa['stages'])==33
  for stage in qa['stages']:
   p=computed['results'][stage['scenario']]['phases'][stage['position']];o=stage['observed']
   assert stage['phase']==p['phase'] and o['schema']==p['direct']['schema'] and o['rows']==p['direct']['rows']
   for client in ['old','new']:assert o[client]==p['clients'][client]['status'] and o[client+'_rows']==p['clients'][client]['rows']
  assert qa['failure_after_normal_comparison']==dict(condition_reset=True,result='EXECUTION_FAILURE: 前の比較・正常答えを破棄',answer='')
  assert [x['prediction'] for x in qa['prediction_changes']]==['contract','refuse','coexist','']
  for x in qa['prediction_changes']:assert x['result']=='' and x['answer']==''
  for x in qa['refusals']:assert x['prediction']=='coexist' and x['result']=='予想と一致' and x['answer']==qa['cases'][2]['answer']
  assert len(qa['refusals'])==3 and qa['condition_reset_count']==8 and len(qa['links'])==6
  assert not qa['resources']['cleanup_pending'] and qa['resources']['own_tab_closed'] and qa['resources']['own_server_exit']==0 and not qa['resources']['own_port_listening']
  assert qa['resources']['protected_before']==qa['resources']['protected_after']
 print('PASS: 8 SQLite scenarios / 33 phases; 5 exact amount pairs; 18 invalid inputs; 6 mutation rejections')
if __name__=='__main__':main()
