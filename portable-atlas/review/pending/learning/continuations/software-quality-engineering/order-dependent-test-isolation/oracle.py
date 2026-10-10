# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
H=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def check(r):
 h=next(x for x in H['cases'] if all(r['inputs'][k]==x[k] for k in ['isolation','order']));assert r['status']=='ATTEMPTS_RECORDED' and r['actual_unittest_executed'];assert len(r['attempts'])==2;pids=[]
 for number,a in enumerate(r['attempts'],1):
  w=a['worker'];assert a['attempt']==number and a['status']=='WORKER_FINISHED' and a['exit_status']==h['exit'];assert json.loads(a['stdout'])==w;assert w['isolation']==h['isolation'] and w['order']==h['order'] and w['tests_run']==2 and w['errors']==w['skipped']==0 and w['failures']==len(h['failed']) and w['success']==(h['exit']==0) and w['final_state']==h['final_state'];assert [[row[k] for k in H['row_fields']] for row in w['trace']]==h['rows'];assert [x['test'] for x in w['trace'] if x['outcome']=='FAIL']==h['failed'];assert type(w['pid']) is int and w['pid']>0;pids.append(w['pid']);assert 'Ran 2 tests' in a['stderr']
  if h['exit']:assert 'AssertionError: 8 != 10' in a['stderr'] and 'FAILED (failures=1)' in a['stderr'] and 'test_default' in a['stderr']
  else:assert '\nOK\n' in a['stderr'] and 'FAILED' not in a['stderr']
 assert len(set(pids))==2
