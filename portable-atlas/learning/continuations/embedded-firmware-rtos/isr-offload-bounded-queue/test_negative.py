"""Finite corruption rejection, no files changed."""
import json,copy
from pathlib import Path
from oracle import validate
from checker import verify_qa
from producer import run,validate as input_check,Refused,FIXTURE
ROOT=Path(__file__).resolve().parent
def checks():
 p=json.loads((ROOT/'evidence/current.json').read_text());raw=json.loads((ROOT/'evidence'/p['raw']).read_text());qa=json.loads((ROOT/'evidence/iab-qa-case-results.json').read_text());rejected=[]
 for name in ['drop_as_accepted','early_complete','accepted_means_completed','hide_overwrite','retain_dropped','capacity0_as_refusal']:
  r=copy.deepcopy(raw)
  if name=='drop_as_accepted':r['cases'][0]['timeline'][2]['accepted'].append(2)
  if name=='early_complete':r['cases'][0]['timeline'][3]['completions']['0']=2
  if name=='accepted_means_completed':r['cases'][2]['counts']['processed']=3
  if name=='hide_overwrite':r['cases'][2]['timeline'][2]['lost']=[]
  if name=='retain_dropped':r['cases'][0]['timeline'][2]['queue'].append(2)
  if name=='capacity0_as_refusal':r['cases'][4]['status']='INPUT_REFUSED'
  try:validate(r)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 for name in ['wrong_ui_count','wrong_ui_tick','old_details_open','old_response_applied','prediction_old_answer']:
  q=copy.deepcopy(qa)
  if name=='wrong_ui_count':q['cases']['slot-overwrite']['counts']['processed']='3'
  if name=='wrong_ui_tick':q['cases']['capacity2']['rows'][3][7]='{"0":2}'
  if name=='old_details_open':q['prediction_controls']['drop/喪失の予想']['after']['answer_open']=True
  if name=='old_response_applied':q['latest_after_release']['result']=q['cases']['capacity2']['result']
  if name=='prediction_old_answer':q['prediction_after_release']['answer']='受入3件なので完了3件'
  try:verify_qa(raw,q)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 from editable import verify_ui as editable_verify,validate as editable_validate
 ep=json.loads((ROOT/'evidence/editable-current.json').read_text());er=json.loads((ROOT/'evidence'/ep['raw']).read_text());eq=json.loads((ROOT/'evidence/editable-iab.json').read_text())
 q=copy.deepcopy(eq);q['cases']['slot-empty']['answer']='受入3件でも完了は1件、ID0/1喪失、ID2tick3'
 try:editable_verify(er,q)
 except AssertionError:rejected.append('empty_slot_fixed_default_answer')
 else:raise AssertionError('accepted default answer for empty')
 q=copy.deepcopy(eq);q['cases']['queue-one']['answer']=eq['cases']['queue-three']['answer']
 try:editable_verify(er,q)
 except AssertionError:rejected.append('one_queue_default_answer')
 else:raise AssertionError('accepted default answer for one')
 r=copy.deepcopy(er);c=json.loads(r['attempts'][1]['stdout']);c['timeline'][3]['completions']={'2':3};r['attempts'][1]['stdout']=json.dumps(c)
 try:editable_validate(r)
 except AssertionError:rejected.append('editable_one_wrong_completion_ID')
 else:raise AssertionError('accepted wrong ID')
 probes=[]
 for name,field,value,reason in [('mode','mode','unknown','MODE'),('slot-cap','capacity',1,'MODE_CAPACITY'),('id-range','events',[{'id':3,'tick':0}],'EVENT_ID'),('event-shape','events',[0],'EVENT_FIELDS'),('event-length','events',[{}, {}, {}, {}],'EVENTS_TYPE')]:
  c=copy.deepcopy(FIXTURE['cases'][2] if name=='slot-cap' else FIXTURE['cases'][0]);c[field]=value
  try:input_check(c)
  except Refused as e:assert str(e)==reason;probes.append(name)
  else:raise AssertionError(name)
 assert run('unknown')['reason']=='UNKNOWN_CASE' and run('capacity2','{bad')['reason']=='EVENT_JSON'
 assert run('capacity2','[]')['counts']['arrived']==0
 return dict(mutants_rejected=rejected,boundary_probes=probes,unknown_and_bad_json_refused=True,custom_empty_normal=True)
if __name__=='__main__':print(json.dumps(checks()))
