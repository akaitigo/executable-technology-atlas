"""Read-only byte/timing/budget corruption rejection, no live connection required."""
import json,copy
from pathlib import Path
from oracle import validate
from checker import verify_qa
from producer import prepare,resolve,decide
ROOT=Path(__file__).resolve().parent
def load(n):return json.loads((ROOT/n).read_text())
def checks():
 r=load('evidence/'+load('evidence/current.json')['raw']);c=load('evidence/'+load('evidence/custom-current.json')['raw']);qa=load('evidence/iab-qa-case-results.json');rejected=[]
 for name in ['encoded_as_decoded','wrong_gzip_hex','wrong_decode','boundary23_refused','fault_as_normal']:
  x=copy.deepcopy(r)
  if name=='encoded_as_decoded':x['cases'][1]['wire']['body_bytes']=3;x['cases'][1]['result']['measurement']['encoded']=3
  if name=='wrong_gzip_hex':x['cases'][1]['wire']['body_hex']='00'*23
  if name=='wrong_decode':x['cases'][1]['wire']['decoded_hex']='616264'
  if name=='boundary23_refused':x['cases'][3]['result']['accepted']=False
  if name=='fault_as_normal':x['cases'][2]['result']['status']='NORMAL'
  try:validate(x)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 for name in ['fabricated_browser_encoded','receipt_not_response','stale_input_answer','old_result_applied','custom_budget8_answer','missing_lookup_forged_as_present']:
  q=copy.deepcopy(qa)
  if name=='fabricated_browser_encoded':d=json.loads(q['cases']['gzip8']['result']);d['browser']['observed_entry']['encodedBodySize']=3;q['cases']['gzip8']['result']=json.dumps(d)
  if name=='receipt_not_response':d=json.loads(q['cases']['gzip8']['result']);d['browser']['receipt']['request_id']='0'*32;q['cases']['gzip8']['result']=json.dumps(d)
  if name=='stale_input_answer':q['inputs']['条件JSON上書き（空欄はfixture）']['after']['answer_open']=True
  if name=='old_result_applied':q['latest_after_release']['accepted']='拒否'
  if name=='missing_lookup_forged_as_present':d=json.loads(q['cases']['timing-missing']['result']);d['browser']['lookup_entry']=d['browser']['observed_entry'];q['cases']['timing-missing']['result']=json.dumps(d)
  if name=='custom_budget8_answer':q['custom']['fault23-match']['answer']=q['cases']['gzip-decoded-fault']['answer']
  try:verify_qa(r,c,q)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 base=dict(encoding='gzip',budget=8,policy='encoded',variant='normal');probes=[]
 for name,value,reason in [('array',[],'INPUT_FIELDS'),('missing',dict(encoding='gzip'),'INPUT_FIELDS'),('extra',dict(base,extra=1),'INPUT_FIELDS'),('float',dict(base,budget=8.5),'BUDGET'),('null',dict(base,budget=None),'BUDGET'),('variant',dict(base,variant='unknown'),'VARIANT')]:
  x=prepare('gzip8',json.dumps(value));assert x['status']=='INPUT_REFUSED' and x['reason']==reason;probes.append(name)
 assert prepare('unknown')['reason']=='UNKNOWN_CASE' and prepare('plain8','{bad')['reason']=='INPUT_JSON'
 c=resolve('gzip8')
 for m in [None,dict(encoded=0,decoded=3),dict(encoded=True,decoded=3),dict(encoded=23,decoded=0)]:assert decide(c,m)['status']=='UNSUPPORTED_TIMING' and decide(c,m)['accepted'] is None
 assert decide(c,dict(encoded=24,decoded=3))['reason']=='BODY_SIZE_MISMATCH'
 return dict(mutants_rejected=rejected,input_probes=probes,missing_zero_bool_timing_not_success=True,unknown_and_json_refused=True)
if __name__=='__main__':print(json.dumps(checks()))
