# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,datetime,platform
from pathlib import Path
from cases import configs,FIXTURES
from model import evaluate
from motion import valid_physics,calculate
from area_oracle import expected
from oracle import check,equal,projection
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def semantic(x):return {k:v for k,v in x.items() if k not in ['started_utc','ended_utc','environment']}
def exercise():
 rows=[];decimal_rows=[]
 for c in configs():x=evaluate(c);check(x);rows.append(x);decimal_rows.append(dict(inputs=c,expected=expected(FIXTURES[c['fixture']],c['mode'],c['h'])))
 base=configs()[0];bad=[None,[],True,{},dict(base,extra=1),dict(base,fixture=[]),dict(base,fixture='unknown'),dict(base,mode=[]),dict(base,mode='unknown'),dict(base,h=True),dict(base,h='0.5'),dict(base,h=0),dict(base,h=-.5),dict(base,h=.25),dict(base,h={})];refused=[]
 for c in bad:
  x=evaluate(c);assert x['status']=='REFUSED_INPUT' and x['rows']==[] and x['events']==[];refused.append(x)
 spec=dict(v=2,tau=.5,a=2,obstacle_m=2,horizon_s=3,h=.5)
 phys=[dict(spec,v=-1),dict(spec,tau=-1),dict(spec,a=0),dict(spec,a=-1),dict(spec,obstacle_m=-1),dict(spec,horizon_s=-1),dict(spec,h=0),dict(spec,h=-1),dict(spec,v=True),dict(spec,tau='0.5'),dict(spec,v=float('nan')),dict(spec,a=float('inf')),dict(spec,tau=-float('inf')),dict(spec,extra=1),{k:v for k,v in spec.items() if k!='a'}];physical=[]
 for p in phys:
  assert not valid_physics(p)
  try:calculate(p,'delayed')
  except ValueError as e:physical.append(dict(input_repr=repr(p),accepted=False,simulation_executed=False,reason=str(e)))
  else:raise AssertionError('invalid physics executed')
 names=['omit-delay-distance','touch-is-clear','sample-scan-only-contact','reverse-after-stop','future-is-observed','known-distance-implies-stopped','v0-waits-delay','instant-has-inertia'];killed=[]
 def case(f,m='delayed'):return copy.deepcopy(next(x for x in rows if x['inputs']==dict(fixture=f,mode=m,h=.5)))
 for name in names:
  x=case('delay-touch')
  if name=='omit-delay-distance':x['stop_distance_m']=1
  elif name=='touch-is-clear':x['contact_classification']='NO_CONTACT_IN_MODEL'
  elif name=='sample-scan-only-contact':x=case('between-samples');x['first_contact_time_s']=1
  elif name=='reverse-after-stop':x['rows'][-1]['v_mps']=-1
  elif name=='future-is-observed':x=case('delay-window');x['event_status']='EVENT_IN_WINDOW'
  elif name=='known-distance-implies-stopped':x=case('braking-window');x['horizon_motion']='STOPPED_BY_HORIZON'
  elif name=='v0-waits-delay':x=case('rest-clear');x['stop_time_s']=1
  else:x=case('delay-touch','instant');x['stop_distance_m']=1
  try:check(x)
  except AssertionError:killed.append(name)
  else:raise AssertionError('mutant accepted: '+name)
 for a,b in zip(rows[::2],rows[1::2]):
  assert a['stop_distance_m']==b['stop_distance_m'] and a['first_contact_time_s']==b['first_contact_time_s']
  for x in b['rows']:assert x==next(y for y in a['rows'] if y['t']==x['t'])
 return dict(rows=rows,decimal_area_oracle_70=decimal_rows,refused=refused,physical_refused=physical,mutants=killed)
def main():
 o=R/'observations';raw=o/'attempt-01.json';rc=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str)+'\n');rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(rc.read_text());assert old['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(rc.read_bytes());rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ['receipt.json','read-only-proof.json']}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(x) for x in new['rows']]==[semantic(x) for x in old['rows']] and new['refused']==old['refused'] and new['physical_refused']==old['physical_refused'] and new['mutants']==old['mutants'];assert json.loads(json.dumps(new['decimal_area_oracle_70'],default=str))==old['decimal_area_oracle_70'];receipt=json.loads(rc.read_text());assert not receipt['ui_pending'] and receipt['source_hashes']==sources() and receipt['raw_sha256']==sha(raw)
  for f,h in receipt['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for x in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(x[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','trace']) and not x['open']
  assert len(qa['links'])==11 and all(x['chars']>0 and x['status'].startswith('READ_COMPLETE') for x in qa['links']);assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==60
  for obs,want in zip(b['rows'],old['rows']):
   equal(obs['projection'],projection(want));assert len(obs['comparisons'])==3
   for cmp in obs['comparisons']:equal(cmp,projection(next(x for x in old['rows'] if x['inputs']==cmp['inputs'])))
 print('PASS: 60 finite conditions / 15 config + 15 physics refusals / 8 mutants; Decimal area + analytical event oracle; h only changes display samples')
if __name__=='__main__':main()
