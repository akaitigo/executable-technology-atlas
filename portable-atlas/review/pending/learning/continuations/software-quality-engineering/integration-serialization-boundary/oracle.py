# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
H=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def configs():return [dict(delay_ms=f['delay_ms'],serializer=c['serializer'],receiver=c['receiver']) for f in H['fixtures'] for c in H['cases']]
def check(r):
 c=r['inputs'];f=next(x for x in H['fixtures'] if x['delay_ms']==c['delay_ms']);h=next(x for x in H['cases'] if x['serializer']==c['serializer'] and x['receiver']==c['receiver']);wire=f['normal_wire'] if c['serializer']=='normal' else f['fault_wire'];accepted=f['delay_ms'] if h['accepted']=='original' else f['coerced'] if h['accepted']=='coerced' else None
 assert r['status']=='HTTP_ATTEMPTS_RECORDED' and r['fixture_id']==f['fixture_id'] and r['domain']=={'fixture_id':f['fixture_id'],'delay_ms':f['delay_ms']} and r['wire_utf8']==wire and r['wire_hex']==wire.encode().hex();u=r['unit'];w=u['result'];assert u['exit_status']==0 and json.loads(u['stdout'])==w and w['success'] and w['tests_run']==2 and w['failures']==w['errors']==w['skipped']==0 and w['fixture_id']==f['fixture_id'] and w['delay_ms']==f['delay_ms'] and w['receiver']==c['receiver'] and '\nOK\n' in u['stderr']
 p=r['receiver_process'];assert p['exit_status']==0 and p['owned_child_closed'] and p['stderr']=='' and p['final']['closed'] and p['startup']['pid']==p['final']['pid'] and p['startup']['pid']!=w['pid'] and json.loads(p['final_stdout'])==p['final'];assert len(r['attempts'])==len(p['final']['records'])==2
 expected={'fixture_id':f['fixture_id'],'status':'ACCEPTED' if accepted is not None else 'REFUSED_CONTRACT','accepted_delay_ms':accepted}
 for number,(a,record) in enumerate(zip(r['attempts'],p['final']['records']),1):
  assert a['attempt']==number and a['fixture_id']==f['fixture_id'] and a['request_hex']==record['request_hex']==wire.encode().hex() and a['request_utf8']==wire and a['request_headers']=={'Content-Type':'application/json','Content-Length':str(len(wire.encode()))} and a['http_status']==record['http_status']==h['http_status'] and a['outcome']==h['outcome'];assert a['response']==expected and json.loads(a['response_utf8'])==expected and a['response_hex']==record['response_hex']==a['response_utf8'].encode().hex() and record['accepted_delay_ms']==accepted and record['fixture_id']==f['fixture_id']
