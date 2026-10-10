# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,datetime,hashlib
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parent;H=json.loads((R/'hand-oracle.json').read_text())
def check_model(r):
 x=r['inputs'];e=next(v for v in H['cases'] if v['case']==x['case'] and v['timeout_ms']==x['timeout_ms'] and v['window_ms']==x['window_ms']);assert r['mode']=='DETERMINISTIC_MODEL' and r['status']=='MODEL_COMPLETE'
 assert r['counts']==dict(issued=6,client_received=e['success'],client_timeout=e['timeout'],pending=e['pending'],server200_attempts=e['server_seen'])
 m=r['metrics'];assert m['deadline_confirmed_ratio']==str(Fraction(e['success'],6)) and m['deadline_upper_ratio']==str(Fraction(e['success']+e['pending'],6))
 assert m['client_received200_ratio']==m['server_attempt200_ratio']=='1' and m['received_latency_stats']==e['received_stats'] and m['all_observed_wait_stats']==e['wait_stats'] and m['full_response_latency_stats'] is None
 assert r['censored_ids']==e['censored_ids'] and len(r['trace'])==6
 for i,t in enumerate(r['trace']):
  good=i<e['success'];censored=not good;outcome='RECEIVED_200' if good else 'CLIENT_TIMEOUT' if e['timeout'] else 'PENDING_AT_WINDOW'
  assert t==dict(request_id=H['request_ids'][i],arrival_ms=0,planned_server_delay_ms=H['delays'][x['case']][i],server200_generated_by_window=i<e['server_seen'],server_attempt_status=200 if i<e['server_seen'] else None,client_outcome=outcome,client_received_status=200 if good else None,observed_wait_ms=e['wait'][i],response_latency_ms=H['delays'][x['case']][i] if good else None,right_censored=censored)
 assert r['python']=='3.9.6'
def dt(s):return datetime.datetime.fromisoformat(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_actual(folder,initial=False):
 r=json.loads((folder/'raw.json').read_text());assert r['mode']=='ACTUAL_LOOPBACK_HTTP' and r['status']=='OBSERVED' and r['python']=='3.9.6' and r['system']=='Darwin' and r['machine']=='arm64'
 assert r['owned_server_exit']==0 and r['owned_server_stopped'] and r['protected_listeners_no_actions']
 for f,h in r['source_hashes'].items():
  p=R/f
  if initial and f in ('http_client.py','actual_http.py'):p=R/'observations'/('http-client-initial.py' if f=='http_client.py' else 'actual-http-initial.py')
  if not initial and f=='actual_http.py':p=R/'observations/harness-attempt02.py'
  assert sha(p)==h
 assert r['server_events']==[json.loads(line) for line in (folder/'server.jsonl').read_text().splitlines()]
 clients=r['clients'];assert [c['request_id'] for c in clients]==['qe-fast-01','qe-timeout-01']
 assert len({r['ready']['pid'],clients[0]['pid'],clients[1]['pid']})==3
 for c in clients:
  assert c['timeout_s']==2.0 and c['observed_wait_ms']==(c['end_monotonic_ns']-c['start_monotonic_ns'])/1e6
  events=[e for e in r['server_events'] if e['request_id']==c['request_id']];assert [e['event'] for e in events[:2]]==['ARRIVED','GENERATED_200_SEND_ATTEMPT'] and events[1]['status']==200 and not events[1]['client_receipt_proven']
  assert events[-1]['event'] in ('WRITE_RETURNED','SEND_ERROR') and all(e['pid']==r['ready']['pid'] for e in events)
  assert dt(c['started_utc'])<=dt(events[0]['utc'])<dt(events[1]['utc'])<=dt(events[-1]['utc'])
  if c['request_id']=='qe-fast-01':assert c['outcome']=='RECEIVED_200' and c['client_received_status']==200 and c['client_received200'] and c['body']['request_id']==c['request_id'] and c['observed_wait_ms']<2000
  else:
   assert c['outcome']==('CLIENT_TRANSPORT_ERROR' if initial else 'CLIENT_TIMEOUT') and c['error_class'] in ('timeout','TimeoutError') and not c['client_received200'] and c['client_received_status'] is None and c['body'] is None
   assert 1900<=c['observed_wait_ms']<=3000 and dt(c['ended_utc'])<dt(events[1]['utc']) and events[0]['delay_ms']==2200
 return r
