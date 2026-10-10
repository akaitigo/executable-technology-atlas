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
  r=evaluate({k:h[k] for k in ['budget','critical_required','variant']});check(r);rows.append(r)
 base=dict(budget=3,critical_required=True,variant='upper');bad=[]
 inputs=[{**base,k:v} for k,v in [('budget',True),('budget',3.0),('budget',-1),('budget',6),('critical_required','true'),('critical_required',0),('critical_required',None),('variant',[]),('variant',{}),('variant',None),('variant',7),('variant',True),('variant','unknown'),('extra',1)]]+[[],None,False]
 for c in inputs:
  r=evaluate(c);assert r['status']=='REFUSED_INPUT' and r['greedy'] is None and r['optimal'] is None and r['subsets']==[];bad.append(r)
 sample=next(r for r in rows if r['inputs']==base);mutants=[]
 for name in ['double-count-overlap','over-budget','ignore-critical','greedy-is-optimal','not-run-is-pass','miss-is-detected','tie-wrong','score-is-probability']:
  r=copy.deepcopy(sample)
  if name=='double-count-overlap':r['subsets'][3]['score']=29
  elif name=='over-budget':r['optimal']=copy.deepcopy(next(x for x in rows if x['inputs']==dict(budget=4,critical_required=True,variant='upper'))['optimal'])
  elif name=='ignore-critical':r=copy.deepcopy(next(x for x in rows if x['inputs']==dict(budget=1,critical_required=True,variant='upper')));r['status']='MODEL_COMPLETE';r['optimal']=dict(selected=['T4'],cost=1,covered=['C'],score=6,valid=True)
  elif name=='greedy-is-optimal':r['optimal']=r['greedy'];r['score_gap']=0
  elif name=='not-run-is-pass':r['greedy_execution'][0]['status']='NO_DIFFERENCE_DETECTED'
  elif name=='miss-is-detected':r['greedy_execution'][1]['checks'][0]['outcome']='DETECTED'
  elif name=='tie-wrong':r=copy.deepcopy(next(x for x in rows if x['inputs']==dict(budget=4,critical_required=True,variant='upper')));r['optimal']['selected']=['T2','T3']
  else:r['score_is_probability']=True
  try:check(r)
  except AssertionError:mutants.append(name)
  else:raise AssertionError('mutant accepted')
 return dict(rows=rows,refused=bad,mutants=mutants)
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def main():
 o=R/'observations';raw=o/'attempt-01.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  rc=json.loads(receipt.read_text());assert rc['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(v) for v in new['rows']]==[semantic(v) for v in old['rows']] and [semantic(v) for v in new['refused']]==[semantic(v) for v in old['refused']] and new['mutants']==old['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for v in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(v[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','greedy_trace','subsets','execution']) and not v['open']
  assert len(qa['links'])==9 and all(v['chars']>0 and v['status'].startswith('READ_COMPLETE') for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==48
  for observed,expected in zip(b['rows'],old['rows']):assert observed==projection(expected,observed['started_utc'],observed['ended_utc'])
 print('PASS: 48 finite cases / 16 subsets each / 17 refusals / 8 mutants; real Python boundary probes; impact not probability/quality')
def projection(r,start=None,end=None):
 return dict(inputs=r['inputs'],status=r['status'],started_utc=start or r['started_utc'],ended_utc=end or r['ended_utc'],greedy=r['greedy'],optimal=r['optimal'],score_gap=r['score_gap'],chosen=[s['chosen'] for s in r['greedy_trace']],subsets=r['subsets'],greedy_execution=r['greedy_execution'],optimal_execution=r['optimal_execution'])
if __name__=='__main__':main()
