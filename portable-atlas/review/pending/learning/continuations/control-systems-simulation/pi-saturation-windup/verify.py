# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,datetime,platform
from pathlib import Path
from cases import configs
from model import evaluate
from controller import step
from decimal_oracle import expected
from oracle import HAND,check,check_probe,equal
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def semantic(x):return {k:v for k,v in x.items() if k not in ['started_utc','ended_utc','environment']}
def projection(x):return dict(inputs=x['inputs'],status=x['status'],metrics=x['metrics'],point_count=len(x['rows']))
def exercise():
 rows=[];decimal_rows=[]
 for c in configs():x=evaluate(c);check(x);rows.append(x);a,b=expected(c);decimal_rows.append(dict(inputs=c,rows=a,metrics=b))
 base=configs()[0];bad=[None,[],True,{},dict(base,extra=1),dict(base,h=True),dict(base,h='0.25'),dict(base,h=0),dict(base,h=.3),dict(base,h=[]),dict(base,ki=True),dict(base,ki=1.0),dict(base,ki=2),dict(base,mode=[]),dict(base,mode='unknown')];refused=[]
 for c in bad:
  x=evaluate(c);assert x['status']=='REFUSED_INPUT' and x['rows']==[] and x['metrics'] is None;refused.append(x)
 probes=[]
 for p in HAND['conditional_probes_h05_ki1']:
  x=step(p['y'],p['z'],p['r'],.5,'conditional',1);check_probe(x,p);probes.append(dict(input=p,actual=x))
 names=['new-z-used-for-request','new-y-used-for-integral','wrong-error-sign','ignore-actuator-clip','ignore-equality-stop','invent-terminal-input','unsettled-is-zero','hide-reexit'];killed=[]
 for name in names:
  x=copy.deepcopy(rows[3])
  if name=='new-z-used-for-request':x['rows'][0]['u_requested']+=1
  elif name=='new-y-used-for-integral':x['rows'][0]['z_next']=.25*(4-x['rows'][0]['y_next'])
  elif name=='wrong-error-sign':x['rows'][0]['e']=-4
  elif name=='ignore-actuator-clip':x['rows'][0]['u_actual']=4
  elif name=='invent-terminal-input':x['rows'][-1]['u_requested']=0
  elif name=='unsettled-is-zero':x['metrics']['settled_time']=0
  elif name=='hide-reexit':x=copy.deepcopy(rows[5]);x['metrics']['reexit_times']=[]
  else:
   x=copy.deepcopy(probes[1]['actual']);x['integral_stopped']=False
   try:check_probe(x,probes[1]['input'])
   except AssertionError:killed.append(name);continue
   raise AssertionError('equality mutant accepted')
  try:check(x)
  except AssertionError:killed.append(name)
  else:raise AssertionError('mutant accepted: '+name)
 # P has no integral output contribution; saturated and conditional y/u agree.
 for offset in [0,6]:
  assert [x['y'] for x in rows[offset+2]['rows']]==[x['y'] for x in rows[offset+4]['rows']]
  assert [x['u_actual'] for x in rows[offset+2]['rows']]==[x['u_actual'] for x in rows[offset+4]['rows']]
 return dict(rows=rows,decimal_oracle_70=decimal_rows,refused=refused,probes=probes,mutants=killed)
def main():
 o=R/'observations';raw=o/'attempt-01.json';rc=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str)+'\n');rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(rc.read_text());assert old['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(rc.read_bytes());rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ['receipt.json','read-only-proof.json']}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(x) for x in new['rows']]==[semantic(x) for x in old['rows']] and new['refused']==old['refused'] and new['probes']==old['probes'] and new['mutants']==old['mutants'];assert json.loads(json.dumps(new['decimal_oracle_70'],default=str))==old['decimal_oracle_70'];receipt=json.loads(rc.read_text());assert not receipt['ui_pending'] and receipt['source_hashes']==sources() and receipt['raw_sha256']==sha(raw)
  for f,h in receipt['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for x in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(x[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','trace']) and not x['open']
  assert len(qa['links'])==11 and all(x['chars']>0 and x['status'].startswith('READ_COMPLETE') for x in qa['links']);assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==12
  for obs,want in zip(b['rows'],old['rows']):
   equal(obs['projection'],projection(want))
   assert len(obs['comparisons'])==3
   for cmp in obs['comparisons']+[obs['p_control']]:equal(cmp,projection(next(x for x in old['rows'] if x['inputs']==cmp['inputs'])))
 print('PASS: 12 finite PI/P conditions / 15 config refusals / 9 boundary probes / 8 mutants; all states matched Decimal70 and initial hand steps')
if __name__=='__main__':main()
