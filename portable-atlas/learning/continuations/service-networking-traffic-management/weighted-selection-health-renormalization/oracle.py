# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,datetime
from pathlib import Path
# Literal pre-implementation tables only; no runner, solver, bucket construction or health predicate.
HAND=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def check(case,r):
 e=HAND['expected'][case];assert r['inputs']==dict(zip(['a','b','ha','hb','slot','fault','fail'],HAND['inputs'][case]))
 assert r['status']==e['status'] and r['candidates']==e['candidates'] and r['bounds']==e['bounds'] and r['total']==e['total']
 assert [t['selected'] for t in r['trace']]==e['picks'] and [t['outcome'] for t in r['trace']]==e['outcomes']
 assert [t['slot'] for t in r['trace']]==list(range(len(e['picks'])))
 assert [t['healthy'] for t in r['trace']]==([True,False,False,False] if case=='late-health-fault' else [True]*len(e['picks']))
 for k in ['reason','error_class','error_message']:
  if k in e:assert r[k]==e[k]
  else:assert k not in r
 if case=='failure':assert r['attempted_slot']==0
 assert r['python']=='3.9.6' and datetime.datetime.fromisoformat(r['started_utc'])<=datetime.datetime.fromisoformat(r['ended_utc'])
