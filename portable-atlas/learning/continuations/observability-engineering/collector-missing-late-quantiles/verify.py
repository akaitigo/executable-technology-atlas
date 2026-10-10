# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,platform,datetime
from pathlib import Path
from model import evaluate
from oracle import H,check
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert H['fixed_before_implementation'];rows=[]
 for h in H['cases']:
  r=evaluate({k:h[k] for k in ['scenario','cutoff_ms','threshold_ms']});check(r);rows.append(r)
 bad=[];base=dict(scenario='full',cutoff_ms=2400,threshold_ms=800)
 for k,v in [('scenario','unknown'),('scenario',[]),('scenario',{}),('scenario',None),('scenario',7),('scenario',True),('cutoff_ms',True),('cutoff_ms',2400.0),('cutoff_ms',-1),('cutoff_ms',3000),('threshold_ms',False),('threshold_ms',800.0),('threshold_ms',0),('extra',1)]:
  r=evaluate({**base,k:v});assert r['status']=='REFUSED_INPUT' and r['collector'] is None and r['teaching_oracle'] is None;bad.append(r)
 sample=next(r for r in rows if r['inputs']==dict(scenario='missing-high',cutoff_ms=4500,threshold_ms=800));mutants=[]
 for name in ['impute-zero','seen-denominator-six','empty-is-zero','pending-as-missing','missing-quality-failure','p50-interpolate','tail-mean-p95','oracle-leak']:
  r=copy.deepcopy(sample);c=r['collector']
  if name=='impute-zero':c['trace'][-1]['latency_ms']=0
  elif name=='seen-denominator-six':c['seen_good_ratio']='2/3'
  elif name=='empty-is-zero':
   r=copy.deepcopy(rows[0]);r['collector']['seen_stats']={'n':0,'mean_ms':'0','p50_ms':0,'p95_ms':0}
  elif name=='pending-as-missing':
   r=copy.deepcopy(next(x for x in rows if x['inputs']==dict(scenario='missing-high',cutoff_ms=4000,threshold_ms=800)));r['collector']['trace'][-1]['state']='CONFIRMED_MISSING'
  elif name=='missing-quality-failure':c['registered_good_upper']=c['registered_good_lower']
  elif name=='p50-interpolate':c['seen_stats']['p50_ms']=300
  elif name=='tail-mean-p95':c['seen_stats']['p95_ms']=375
  else:c['full_population_stats']=r['teaching_oracle']['stats']
  try:check(r)
  except AssertionError:mutants.append(name)
  else:raise AssertionError('mutant accepted')
 return dict(rows=rows,refused=bad,mutants=mutants)
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def main():
 o=R/'observations';raw=o/'attempt-01.json';rcfile=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,real_collector_executed=False);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');rcfile.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  rc=json.loads(rcfile.read_text());assert rc['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(rcfile.read_bytes());rcfile.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(v) for v in new['rows']]==[semantic(v) for v in old['rows']] and [semantic(v) for v in new['refused']]==[semantic(v) for v in old['refused']] and new['mutants']==old['mutants'];rc=json.loads(rcfile.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for v in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(v[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','trace','teacher']) and not v['open']
  assert len(qa['links'])==9 and all(v['chars']>0 and v['status'].startswith('READ_COMPLETE') for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==50
  for row,expected in zip(b['rows'],old['rows']):assert row==projection(expected,row['started_utc'],row['ended_utc'])
 print('PASS: 50 finite cases / 14 refusals / 8 mutants; collector unknown stays null, teaching oracle separate; no real collector')
def projection(r,start=None,end=None):
 c=r['collector'];return dict(inputs=r['inputs'],status=r['status'],started_utc=start or r['started_utc'],ended_utc=end or r['ended_utc'],collector=c,oracle_stats=r['teaching_oracle']['stats'],oracle_good=r['teaching_oracle']['good'],oracle_ratio=r['teaching_oracle']['good_ratio'],bias=r['teaching_bias_seen_minus_ledger'])
if __name__=='__main__':main()
