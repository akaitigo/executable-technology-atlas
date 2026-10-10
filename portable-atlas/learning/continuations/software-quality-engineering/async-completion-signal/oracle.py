"""Independent hand event/value/TAP relation checks; no producer imports."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text())
def validate(raw):
 assert raw['execution_failures']==0;assert raw['fixture']['initial_value']==0 and raw['fixture']['updated_value']==raw['fixture']['assert_expected']==1
 assert [c['id'] for c in raw['cases']]==list(TABLE['cases'])
 for c,f in zip(raw['cases'],raw['fixture']['cases']):
  x=TABLE['cases'][c['id']];assert c['input']==f;assert c['exit_code']==x['exit'];assert c['stderr']=='';assert c['child_reaped'] and c['streams_closed'] and c['temp_removed'];assert c['copied_source_sha256']==raw['source_sha256']['case.test.mjs'];assert c['test_runner_pid']!=c['test_file_pid']
  assert c['command']==['node','--test','--test-reporter=tap','case.test.mjs'];assert c['env']==dict(ATLAS_SCHEDULE=f['schedule'],ATLAS_VARIANT=f['variant'])
  events=c['events'];assert [e['event'] for e in events]==x['events'];assert [e['seq'] for e in events]==list(range(len(events)));assert all(e['pid']==c['test_file_pid'] for e in events)
  parsed=[]
  for line in c['stdout'].splitlines():
   if line.startswith('# ATLAS_EVENT '):parsed.append(json.loads(line[len('# ATLAS_EVENT '):]))
  assert parsed==events;assert 'TAP version 13' in c['stdout'] and '# tests 1' in c['stdout'] and '# cancelled 0' in c['stdout'];assert '/Users/' not in c['stdout']
  if 'refusal' in x:
   assert events[0]['reason']==x['refusal'];assert 'exitCode: 2' in c['stdout'] and "code: 'ERR_TEST_FAILURE'" in c['stdout'];assert not any(e['event'].startswith('assert_') for e in events)
  else:
   read=next(e for e in events if e['event']=='assert_read');assert read['value']==x['assert_value'] and read['expected']==1;last=events[-1];assert last['value']==x['final_value'] and last['work_settled'] and last['gate_released'];assert next(e for e in events if e['event']=='update_waiting')['value']==0;assert next(e for e in events if e['event']=='value_updated')['value']==1
   if x['assertion']=='failed':
    e=next(e for e in events if e['event']=='assert_failed');assert e['code']=='ERR_ASSERTION' and e['actual']==0 and e['expected']==1;assert 'not ok 1 - same assertion body' in c['stdout'] and "code: 'ERR_ASSERTION'" in c['stdout'] and '# pass 0' in c['stdout'] and '# fail 1' in c['stdout']
   else:assert 'ok 1 - same assertion body' in c['stdout'] and 'not ok' not in c['stdout'] and '# pass 1' in c['stdout'] and '# fail 0' in c['stdout']
 return dict(cases=5,assertion_pass=3,expected_assertion_fail=1,input_refusals=1,unexpected_execution_failures=0,both_awaited_schedules_pass=True)
