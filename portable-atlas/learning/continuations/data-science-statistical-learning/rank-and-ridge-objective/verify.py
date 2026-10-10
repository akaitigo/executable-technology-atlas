# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import argparse,copy,hashlib,json,platform,sqlite3,subprocess,datetime
from pathlib import Path
from model import run,objective
from oracle import check,check_candidate
R=Path(__file__).resolve().parent
SOURCES=['fixture.json','hand-oracle.json','model.py','oracle.py','verify.py','route.py','serve.py','index.html','source.html','README.md','VERIFICATION.md','sources.json','coverage.json','skills/rank-ridge/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {s:digest(R/s) for s in SOURCES}
def calculate():
 f=json.loads((R/'fixture.json').read_text());hand=json.loads((R/'hand-oracle.json').read_text());results={c['id']:run(c) for c in f['cases']}
 for c in f['cases']:check(c,results[c['id']],hand)
 candidates=[]
 for c in f['cases'][:4]:
  for a in range(-3,4):
   for b in range(-3,4):
    value=objective(c,[a,b]);check_candidate(c,[a,b],value);candidates.append(dict(case=c['id'],coef=[a,b],result=value))
 invalid=[];base=f['cases'][0]
 for field,value in [('lambda_value',-1),('lambda_value',5),('lambda_value',True),('lambda_value','1'),('lambda_value',0.5),('X',[]),('X',[[1],[2]]),('X',[[True,0],[0,1]]),('X',[[6,0],[0,1]]),('X',[[0,0],[0,0]]),('X',[[1.0,0],[0,1]]),('y',[]),('y',[True,3]),('y',[21,3]),('y',[2.0,3]),('y',[2,3,4]),('fault','bad')]:
  c=copy.deepcopy(base);c[field]=value;result=run(c);assert result['status']=='REFUSED_INPUT' and result['solution'] is None;invalid.append(dict(field=field,value=value,result=result))
 mutations=[]
 for label,name,field in [('wrong-coefficient','independent-ols','coef'),('ridge-as-ols','independent-ridge','coef'),('rank-faked','correlated-ols','rank_x'),('nonunique-as-failure','correlated-ols','status'),('penalty-erased','correlated-ridge','penalty'),('failure-as-success','execution-failure','status')]:
  c=next(c for c in f['cases'] if c['id']==name);result=copy.deepcopy(results[name])
  if field=='status':result['status']='EXECUTION_FAILURE' if name=='correlated-ols' else 'UNIQUE'
  elif field=='coef':result['solution']['coef']=['2','3'] if name=='independent-ridge' else ['2','4']
  elif field=='rank_x':result['solution'][field]=2
  else:result['solution'][field]='0'
  try:check(c,result,hand)
  except AssertionError:mutations.append(dict(label=label,rejected=True))
  else:raise AssertionError('mutation accepted '+label)
 return dict(results=results,candidates=candidates,invalid=invalid,mutations=mutations)
def main():
 p=argparse.ArgumentParser();p.add_argument('--record');p.add_argument('--seal-record',action='store_true');a=p.parse_args();computed=calculate();attempt=R/'observations'/'attempt-01'
 if a.record:
  assert a.record=='attempt-01' and not attempt.exists(),'only unused attempt-01'
  attempt.mkdir();raw=dict(command=['python3','-B','verify.py','--record','attempt-01'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,system=platform.system(),machine=platform.machine()),inputs=json.loads((R/'fixture.json').read_text()),source_hashes=hashes(),exit_status=0,**computed)
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
  qa=json.loads((R/'observations'/'ui-qa.json').read_text());assert qa['passed'] and len(qa['cases'])==7
  for case in qa['cases']:
   result=computed['results'][case['scenario']];assert case['status'].startswith(result['status']) and case['solution']==result['solution']
   if result['status']=='EXECUTION_FAILURE':assert case['answer']=='' and case['result']=='EXECUTION_FAILURE: 前の比較・正常答えを破棄'
  fixtures=json.loads((R/'fixture.json').read_text())['cases']
  for case in qa['cases']:
   c=next(c for c in fixtures if c['id']==case['scenario']);assert case['inputs']==dict(X=c['X'],y=c['y'],lambda_value=c['lambda_value'])
   if computed['results'][case['scenario']]['status']=='REFUSED_INPUT':assert case['answer']=='' and case['solution'] is None and case['selected']=='解と点の表示を破棄'
  assert len(qa['points'])==8
  for p in qa['points']:
   c=next(c for c in fixtures if c['id']==p['scenario']);s=computed['results'][p['scenario']]['solution'];i=p['row'];assert p['X']==c['X'][i] and p['y']==c['y'][i] and p['predicted']==s['predicted'][i] and p['residual']==s['residuals'][i]
  assert [p['scenario'] for p in qa['transitions']]==['negative-lambda','execution-failure','independent-ridge']
  for p in qa['transitions'][:2]:assert p['answer']=='' and p['selected']=='解と点の表示を破棄'
  assert qa['transitions'][2]['answer']==qa['cases'][1]['answer']
  assert [x['prediction'] for x in qa['prediction_changes']]==['nonunique','same','unique','']
  for x in qa['prediction_changes']:assert x['result']=='' and x['answer']==''
  for x in qa['refusals']:assert x['prediction']=='unique' and x['result']=='予想と一致' and x['answer']==qa['cases'][0]['answer']
  assert len(qa['refusals'])==3 and qa['condition_reset_count']==7 and len(qa['links'])==7
  assert not qa['resources']['cleanup_pending'] and qa['resources']['own_tab_closed'] and qa['resources']['own_server_exit']==0 and not qa['resources']['own_port_listening']
  assert qa['resources']['protected_before']==qa['resources']['protected_after']
 print('PASS: 7 exact scenarios; 196 objective identities; 17 invalid inputs; 6 mutation rejections')
if __name__=='__main__':main()
