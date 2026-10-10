# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,platform
from pathlib import Path
from model import run,stats
from oracle import H,check_model,check_actual
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert H['fixed_before_implementation'];rows=[]
 for e in H['cases']:
  r=run(e['case'],e['timeout_ms'],e['window_ms']);check_model(r);rows.append(r)
 refused=[]
 for a in [('slow',True,2500),('slow',-1,2500),('slow',1.5,2500),('unknown',2000,2500),('slow',3000,2500),('slow',2000,True),('slow',2000,0)]:
  r=run(*a);assert r['status']=='REFUSED_INPUT' and r['trace']==[] and 'metrics' not in r;refused.append(r)
 assert stats([100]*19+[2200])['p95_ms']==100 and max([100]*19+[2200])==H['nearest_rank_caveat']['p100_ms']
 mutants=[];base=rows[3]
 for name in ['denominator','timeout-received','censored-as-latency','received-mean','p95-mean','pending-erased']:
  r=copy.deepcopy(rows[2] if name=='pending-erased' else base)
  if name=='denominator':r['metrics']['deadline_confirmed_ratio']='1'
  elif name=='timeout-received':r['trace'][-1]['client_received_status']=200
  elif name=='censored-as-latency':r['trace'][-1]['response_latency_ms']=2000
  elif name=='received-mean':r['metrics']['received_latency_stats']['mean_ms']='2650/3'
  elif name=='p95-mean':r['metrics']['received_latency_stats']['p95_ms']=660
  else:r['counts']['pending']=0
  try:check_model(r)
  except AssertionError:mutants.append(name)
  else:raise AssertionError('mutant accepted')
 check_actual(R/'observations/http-attempt-01',True);check_actual(R/'observations/http-attempt-02')
 return rows,refused,mutants
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def main():
 o=R/'observations';raw=o/'model-attempt-01.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();rows,refused,mutants=exercise();raw.write_text(json.dumps(dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),source_hashes=sources(),rows=rows,refused=refused,mutants=mutants,actual_http_reexecuted=False),ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  rc=json.loads(receipt.read_text());assert rc['ui_pending'] and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;rows,refused,mutants=exercise();data=json.loads(raw.read_text());assert [semantic(r) for r in rows]==[semantic(r) for r in data['rows']] and [semantic(r) for r in refused]==[semantic(r) for r in data['refused']] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['transport_no_normal_answer']
  for v in qa['prediction_changes']+qa['condition_changes']:assert all(v[k]=='' for k in ['answer','body','comparison','raw','trace','summary']) and not v['open']
  assert [v['prediction'] for v in qa['prediction_changes']]==['same','different','unknown',''] and len(qa['links'])==11 and all(v['chars']>0 and not v['read_failure'] for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  for r in json.loads((o/'browser-model-cases.json').read_text())['rows']:check_model(r)
 print('PASS: 12 deterministic model cases / 7 refusals / 6 mutants; 2 actual HTTP attempts, separate processes, UTC-ID join; actual HTTP not reexecuted')
if __name__=='__main__':main()
