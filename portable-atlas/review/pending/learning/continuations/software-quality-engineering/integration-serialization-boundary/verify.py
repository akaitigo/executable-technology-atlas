# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,datetime,platform
from pathlib import Path
from model import evaluate
from oracle import H,check,configs
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def semantic(r):
 if r['status']=='REFUSED_INPUT':return dict(inputs=r['inputs'],status=r['status'],attempts=r['attempts'],unit=r['unit'],receiver_process=r['receiver_process'])
 return dict(inputs=r['inputs'],status=r['status'],fixture_id=r['fixture_id'],domain=r['domain'],wire_utf8=r['wire_utf8'],wire_hex=r['wire_hex'],unit={k:v for k,v in r['unit']['result'].items() if k!='pid'},unit_exit=r['unit']['exit_status'],attempts=[{k:a[k] for k in ['attempt','fixture_id','request_hex','request_utf8','request_headers','http_status','response_hex','response_utf8','response','outcome']} for a in r['attempts']],receiver_exit=r['receiver_process']['exit_status'],receiver_closed=r['receiver_process']['owned_child_closed'],receiver_records=[{k:v for k,v in x.items() if k not in ['started_utc','ended_utc']} for x in r['receiver_process']['final']['records']])
def exercise():
 assert H['fixed_before_implementation'];rows=[]
 for c in configs():r=evaluate(c);check(r);rows.append(r)
 base=configs()[0];bad=[None,[],True,{},dict(base,extra=1),dict(base,delay_ms=True),dict(base,delay_ms=1000.0),dict(base,delay_ms=1),dict(base,delay_ms='1000'),dict(base,serializer=[]),dict(base,serializer={}),dict(base,serializer='unknown'),dict(base,receiver=[]),dict(base,receiver={}),dict(base,receiver='unknown')];refused=[]
 for c in bad:
  r=evaluate(c);assert r['status']=='REFUSED_INPUT' and r['attempts']==[] and r['unit'] is None and r['receiver_process'] is None;refused.append(r)
 names=['unit-pass-implies-e2e','wrong-wire-type','wrong-unit','hide-rejected-attempt','http200-implies-match','receiver-wire-disagrees','fixture-ID-changed','leaked-receiver'];killed=[]
 for name in names:
  r=copy.deepcopy(rows[3]);a=r['attempts'][0]
  if name=='unit-pass-implies-e2e':a['outcome']='MATCH'
  elif name=='wrong-wire-type':r['wire_utf8']=H['fixtures'][0]['normal_wire']
  elif name=='wrong-unit':a['response']['accepted_delay_ms']=1000
  elif name=='hide-rejected-attempt':r=copy.deepcopy(rows[2]);r['attempts']=r['attempts'][:1]
  elif name=='http200-implies-match':a['http_status']=400
  elif name=='receiver-wire-disagrees':r['receiver_process']['final']['records'][0]['request_hex']='00'
  elif name=='fixture-ID-changed':a['fixture_id']='F2000'
  else:r['receiver_process']['owned_child_closed']=False
  try:check(r)
  except AssertionError:killed.append(name)
  else:raise AssertionError('mutant accepted')
 return dict(rows=rows,refused=refused,mutants=killed)
def main():
 o=R/'observations';raw=o/'attempt-01.json';rc=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(rc.read_text());assert old['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(rc.read_bytes());rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ['receipt.json','read-only-proof.json']}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(x) for x in new['rows']]==[semantic(x) for x in old['rows']] and [semantic(x) for x in new['refused']]==[semantic(x) for x in old['refused']] and new['mutants']==old['mutants'];receipt=json.loads(rc.read_text());assert not receipt['ui_pending'] and receipt['source_hashes']==sources() and receipt['raw_sha256']==sha(raw)
  for f,h in receipt['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for x in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(x[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','attempts','units']) and not x['open']
  assert len(qa['links'])==13 and all(x['chars']>0 and x['status'].startswith('READ_COMPLETE') for x in qa['links']);assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==8
  for obs,expected in zip(b['rows'],old['rows']):assert obs['semantic']==semantic(expected) and obs['unit_pid']!=obs['receiver_pid'] and obs['receiver_port']>0
 print('PASS: 8 finite conditions x2 actual HTTP requests / pure units / 15 refusals / 8 mutants; unit pass and HTTP200 do not imply semantic match')
if __name__=='__main__':main()
