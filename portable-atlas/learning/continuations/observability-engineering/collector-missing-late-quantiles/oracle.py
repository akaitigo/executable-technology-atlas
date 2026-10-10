# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
H=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def check(r):
 assert r['mode']=='SYNTHETIC_MEMORY_ONLY' and r['status']=='MODEL_COMPLETE'
 cfg=r['inputs'];h=next(v for v in H['cases'] if all(v[k]==cfg[k] for k in cfg));c=r['collector'];t=r['teaching_oracle']
 for k in ['seen_ids','counts','seen_stats','known_good','seen_good_ratio','registered_good_lower','registered_good_upper']:assert c[k]==h[k],k
 assert c['full_population_stats'] is None and c['imputed_values']==[] and len(c['trace'])==6
 assert t['label']=='OMNISCIENT_TEACHING_FIXTURE_NOT_COLLECTOR' and t['stats']==h['oracle_stats'] and t['good']==h['oracle_good'] and t['good_ratio']==h['oracle_good_ratio']
 assert r['teaching_bias_seen_minus_ledger']==h['bias']
 schedule=H['schedules'][cfg['scenario']]
 for i,(actual,source) in enumerate(zip(c['trace'],H['ledger'])):
  rid=source['request_id'];assert actual['request_id']==rid and actual['issued_ms']==source['issued_ms']
  seen=rid in h['seen_ids'];missing=not seen and h['counts']['confirmed_missing']>0
  assert actual['state']==('SEEN' if seen else ('CONFIRMED_MISSING' if missing else 'PENDING'))
  assert actual['latency_ms']==(source['teaching_latency_ms'] if seen else None)
  assert actual['arrival_ms']==(schedule['arrivals_ms'][i] if seen else None)
  assert actual['loss_notice_ms']==(schedule['loss_notice_ms'][i] if missing else None)
  assert t['ledger'][i]==dict(request_id=rid,issued_ms=source['issued_ms'],latency_ms=source['teaching_latency_ms'],scheduled_arrival_ms=schedule['arrivals_ms'][i],scheduled_final_loss_notice_ms=schedule['loss_notice_ms'][i])
 return True
