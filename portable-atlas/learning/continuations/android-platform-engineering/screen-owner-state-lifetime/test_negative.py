"""Read-only literal corruption, UI stale-answer and finite input probes."""
import json,copy
from pathlib import Path
from oracle import validate
from checker import verify_qa,custom_validate
from producer import run,validate as input_check,FIXTURE,Refused
ROOT=Path(__file__).resolve().parent
def load(n):return json.loads((ROOT/n).read_text())
def checks():
 r=load('evidence/'+load('evidence/current.json')['raw']);custom=load('evidence/'+load('evidence/custom-current.json')['raw']);qa=load('evidence/iab-qa-case-results.json');rejected=[]
 for name in ['rotation_changes_owner','rotation_resets_state','finish_keeps_owner','recreate_keeps_old_state','death_keeps_owner','global_leak_hidden','dead_reuse_hidden']:
  x=copy.deepcopy(r)
  if name=='rotation_changes_owner':x['cases'][1]['timeline'][1]['owners']['B']['owner']='p1:B:3'
  if name=='rotation_resets_state':x['cases'][1]['timeline'][1]['owners']['B']['state']=0
  if name=='finish_keeps_owner':x['cases'][2]['timeline'][1]['owners']['B']=copy.deepcopy(x['cases'][2]['timeline'][0]['owners']['B'])
  if name=='recreate_keeps_old_state':x['cases'][3]['timeline'][2]['owners']['B']['state']=1
  if name=='death_keeps_owner':x['cases'][4]['timeline'][1]['owners']=copy.deepcopy(x['cases'][4]['timeline'][0]['owners'])
  if name=='global_leak_hidden':x['cases'][9]['timeline'][1]['owners']['A']['state']=2
  if name=='dead_reuse_hidden':x['cases'][10]['timeline'][2]['owners']['B']['owner']='p1:B:3'
  try:validate(x)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 for name in ['ui_wrong_owner','input_old_details_open','old_response_applied','custom_fixed_answer']:
  q=copy.deepcopy(qa)
  if name=='ui_wrong_owner':q['cases']['rotate-b']['rows'][1][5]='["p1:B:3",2,1]'
  if name=='input_old_details_open':q['inputs']['event JSON上書き（空欄は条件fixture）']['after']['answer_open']=True
  if name=='old_response_applied':q['latest_after_release']['final']=q['cases']['rotate-b']['final']
  if name=='custom_fixed_answer':q['custom']['global-empty']['answer']=q['cases']['global-leak']['answer']
  try:verify_qa(r,custom,q)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 probes=[]
 for name,events,reason in [('event_bool',False,'EVENTS_TYPE'),('event_string',['rotate'],'EVENT_FIELDS'),('op_bool',[dict(op=True,target='B')],'OP'),('null_screen',[dict(op='rotate',target=None)],'TARGET'),('screen_on_death',[dict(op='death',target='B')],'TARGET')]:
  x=run('initial',json.dumps(events));assert x['status']=='INPUT_REFUSED' and x['reason']==reason and x['timeline'] is None and x['final'] is None;probes.append(name)
 x=copy.deepcopy(FIXTURE['cases'][0]);x['mode']='unknown'
 try:input_check(x)
 except Refused as e:assert str(e)=='MODE';probes.append('mode_unknown')
 else:raise AssertionError('mode')
 assert run('unknown')['reason']=='UNKNOWN_CASE' and run('initial','{bad')['reason']=='EVENT_JSON'
 taps=[dict(op='tap',target='A')]*7;assert run('initial',json.dumps(taps))['final']['owners']['A']['state']==9
 assert run('initial',json.dumps(taps+[taps[0]]))['reason']=='STATE_RANGE'
 events=[dict(op='finish',target='B'),dict(op='death',target=None),dict(op='restart',target=None),dict(op='create',target='B')];x=run('dead-owner-reuse',json.dumps(events));assert x['final']['owners']['B']==dict(owner='p2:B:1',view_generation=1,state=0)
 return dict(mutants_rejected=rejected,input_probes=probes,unknown_and_json_refused=True,tap9_boundary=True,death_clears_fault_cache=True)
if __name__=='__main__':print(json.dumps(checks()))
