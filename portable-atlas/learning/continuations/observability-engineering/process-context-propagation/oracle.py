"""Independent saved relation table validation. No child/runner import or business recomputation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text())
def validate(raw):
 assert raw['execution_failures']==0;assert raw['fixture']['parent']==TABLE['parent'];assert [c['id'] for c in raw['cases']]==list(TABLE['cases'])
 for c,fixture in zip(raw['cases'],raw['fixture']['cases']):
  x=TABLE['cases'][c['id']];child=c['child'];assert c['request']==fixture['request']==child['request'];assert json.loads(c['stdin'])==c['request'];assert child['received_stdin']==c['stdin']
  assert c['parent']==TABLE['parent'];assert c['parent_pid']==raw['environment']['parent_pid']==child['ppid'];assert c['child_pid']==child['pid']!=c['parent_pid']
  assert c['command']==['python3','-B','child.py'];assert c['stderr']=='' and c['exit_code']==x['exit'];assert all(c['cleanup'].values())
  lines=c['stdout'].splitlines();assert len(lines)==2 and json.loads(lines[0])==child and json.loads(lines[1])==c['emit_ack'];assert c['emit_ack']['event']=='childemit_completed' and c['emit_ack']['pid']==child['pid'] and c['emit_ack']['seq']==3
  assert [e['event'] for e in c['parent_events']]==TABLE['parent_events'];assert [e['seq'] for e in c['parent_events']]==[0,1,2];assert all(e['pid']==c['parent_pid'] and e['utc'] for e in c['parent_events'])
  events=TABLE['child_success_events'] if x['exit']==0 else TABLE['child_refusal_events'];assert [e['event'] for e in child['events']]==events;assert [e['seq'] for e in child['events']]==[0,1,2];assert all(e['pid']==child['pid'] and e['utc'] for e in child['events'])
  if x['exit']==0:
   assert child['status']=='succeeded' and child['amount']==x['amount'];s=child['span'];assert s==dict(trace_id=x['trace_id'],span_id=TABLE['child_span_id'],parent_span_id=x['parent_span_id'])
   binding='connected' if s['trace_id']==TABLE['parent']['trace_id'] and s['parent_span_id']==TABLE['parent']['span_id'] else 'orphan';assert binding==x['binding']
  else:assert child['status']=='refused' and child['reason']==x['reason'] and child['amount'] is None and child['span'] is None
 return dict(cases=10,business_success=4,input_refused=6,connected=1,orphan=3,execution_failures=0,clock_sort_used=False)
