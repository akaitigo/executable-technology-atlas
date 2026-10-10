# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import argparse,copy,hashlib,json,platform,sqlite3,subprocess,datetime
from pathlib import Path
from model import run,validate
from oracle import check,TICKS
R=Path(__file__).resolve().parent
SOURCES=['fixture.json','model.py','oracle.py','verify.py','route.py','serve.py','index.html','source.html','README.md','VERIFICATION.md','sources.json','coverage.json','skills/as-of-history/SKILL.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {s:digest(R/s) for s in SOURCES}
def calculate():
 f=json.loads((R/'fixture.json').read_text());results={c['id']:run(c) for c in f['cases']}
 for name,result in results.items():check(name,result)
 base=f['cases'][0];ticks=[]
 for t,v in enumerate(TICKS):
  c=copy.deepcopy(base);c['orders']=[['probe','c1',t,1]];result=run(c);o=result['orders'][0]
  assert o['versions']==([] if v is None else [v]) and o['classification']==('GAP' if v is None else 'MATCHED')
  ticks.append(dict(tick=t,result=result))
 invalid=[]
 for label,field,value in [('negative-time','time',-1),('large-time','time',21),('bool-time','time',True),('negative-amount','amount',-1),('bool-amount','amount',False),('duplicate-order','duplicate',None),('duplicate-version','version',None),('unknown-method','method','bad'),('empty-orders','orders',[]),('reverse-interval','interval',None)]:
  c=copy.deepcopy(base)
  if field=='time':c['orders'][0][2]=value
  elif field=='amount':c['orders'][0][3]=value
  elif field=='duplicate':c['orders'].append(c['orders'][0][:])
  elif field=='version':c['versions'][1][0]=1
  elif field=='interval':c['versions'][0][3:]=[11,10]
  else:c[field]=value
  result=run(c);assert result['status']=='REFUSED_INVALID_INPUT' and result['aggregate'] is None
  invalid.append(dict(label=label,result=result))
 mutations=[]
 for label,name,change in [('latest-pollution','boundary','aggregate'),('missing-order','boundary','remove'),('wrong-version','boundary','version'),('gap-erased','gap','aggregate'),('overlap-success','overlap','status'),('failure-normalized','execution-failure','status')]:
  result=copy.deepcopy(results[name])
  if change=='aggregate':result['aggregate']={'south':150}
  elif change=='remove':result['orders'].pop()
  elif change=='version':result['orders'][0]['versions']=[2]
  else:result['status']='OK'
  try:check(name,result)
  except AssertionError:mutations.append(dict(label=label,rejected=True))
  else:raise AssertionError('mutation accepted '+label)
 return dict(results=results,ticks=ticks,invalid=invalid,mutations=mutations)
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
  qa=json.loads((R/'observations'/'ui-qa.json').read_text());assert qa['passed'] and len(qa['cases'])==7 and len(qa['prediction_changes'])==4 and len(qa['refusals'])==3
  for case in qa['cases']:
   result=computed['results'][case['scenario']]
   assert json.loads(case['rows'])==result['rows'] and case['status'].startswith(result['status'])
   if result['status']=='OK':assert json.loads(case['aggregate'].split(': ',1)[1])==result['aggregate']
   else:assert case['aggregate']=='集計: 採用不可' and case['answer']=='正常な答えは出せない。拒否理由と生結果を確認する。' and case['result'].startswith(result['status'])
  assert [x['prediction'] for x in qa['prediction_changes']]==['latest','retain','history','']
  for x in qa['prediction_changes']:assert x['result']=='' and x['answer']=='' and json.loads(x['selected'])==computed['results']['boundary']['orders'][1]
  for x in qa['refusals']:assert x['prediction']=='history' and x['result']=='予想と一致' and x['answer']==qa['cases'][0]['answer'] and json.loads(x['selected'])==computed['results']['boundary']['orders'][1]
  assert qa['condition_changes']==dict(tested=7,prediction='',result='',answer='',position='0')
  assert not qa['resources']['cleanup_pending'] and qa['resources']['own_tab_closed'] and qa['resources']['own_server_exit']==0 and not qa['resources']['own_port_listening']
  assert qa['resources']['protected_before']==qa['resources']['protected_after']
  assert len(qa['links'])==6 and all(x['length']>100 for x in qa['links'])
  assert len(qa['captures'])==4 and all(not x['saved'] and x['path'] is None and x['hash'] is None for x in qa['captures'])
 print('PASS: 7 SQL scenarios; 21 tick boundaries; 10 invalid inputs; 6 mutation rejections')
if __name__=='__main__':main()
