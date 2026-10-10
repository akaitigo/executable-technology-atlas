import base64,datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
QA=ROOT/'qa/20261005T172306318700Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['answer','attempt','classification','normal','physical','run','state','trace']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden']
 assert not any(s[n] for n in ['answer_open','trace_open','physical_open'])
def opened(s):assert all(s[n] for n in ['answer_open','trace_open','physical_open'])
def actual(raw,oracle):
 run=raw['run'];r=run['result'];assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
 assert run['stdin']==raw['input_json'] and json.loads(run['stdout'])==r and run['stderr']==''
 if oracle.get('status')=='observed':
  assert run['exit']==0 and r['summary']==oracle
  assert r['handles_closed'] is True and r['temporary_cleanup'] is True
  assert r['trace'][0]['sql']=='PRAGMA journal_mode=WAL' and r['trace'][0]['rows']==[['wal']]
  header=bytes.fromhex(r['db_header_hex']);assert header[:16]==b'SQLite format 3\0' and header[18:20]==bytes([2,2])
  assert r['wal']['bytes']>32 and len(bytes.fromhex(r['wal']['header_hex']))==32
  b=base64.b64decode(r['closed_db_base64'],validate=True);assert b[:16]==b'SQLite format 3\0' and hashlib.sha256(b).hexdigest()==r['closed_db_sha256']
  errors=[x for x in r['trace'] if x['return_code']]
  if oracle['upgrade_code']:
   assert len(errors)==1 and errors[0]['extended_code']==oracle['upgrade_code'] and errors[0]['primary_code']==5 and errors[0]['state']==oracle['attempt_state']
  else:assert not errors
 else:
  assert run['exit']==2 and r['status']=='input_refusal' and r['summary'] is None and r['temporary_cleanup']=='not-created' and r['code']==oracle['code']
 return r

def display(s,oracle):
 raw=load(ROOT/s['raw']);assert raw['input_json']==s['input'];r=actual(raw,oracle)
 assert s['initial_run']=='20261005T172259397385Z-wal' and not s['results_hidden']
 if r['status']=='observed':
  o=r['summary'];assert json.loads(s['normal'])=={'recovery_before':o['recovery_before'],'final':o['final_row'],'recovery_done':o['recovery_done']}
  assert json.loads(s['attempt'])=={'first':o['first_row'],'after_attempt':o['after_attempt_row'],'code':o['upgrade_code'],'name':o['upgrade_name']}
  assert json.loads(s['state'])=={'attempt':o['attempt_state'],'final':o['final_state'],'tmp_cleanup':True,'handles_closed':True}
  assert json.loads(s['physical'])=={n:r[n] for n in ['engine','db_header_hex','wal','closed_db_sha256']}
  assert json.loads(s['trace'])==r['trace'] and not s['answer_hidden']
  for n in ['schedule','initial','writer','delta','busy_ms']:assert str(o['input'][n]) in s['answer']
  for word in [str(o['upgrade_code']),o['upgrade_name'],str(o['final_row']),'tmp cleanup=true','773 SQLITE_BUSY_TIMEOUT']:assert word in s['answer']
  category=o['category']
 else:
  assert s['answer_hidden'] and s['answer']=='' and json.loads(s['trace'])==raw['run'];category='input'
 expected='予想未選択' if not s['prediction'] else ('予想と一致' if s['prediction']==category else '予想と不一致')
 assert expected in s['message'],(expected,s['message'])
 return r

def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits}
 assert len(e['matrix'])==65 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['', 'stale','busy','success','input']}
 for x in e['matrix']:assert x['state']['input']==fixed[x['id']]['input_json'];display(x['state'],fixed[x['id']]['expected'])
 assert len(e['resets'])==18
 for x in e['resets']:
  opened(x['before']);empty(x['after'])
  if x['kind']=='prediction':assert x['after']['prediction']==x['new_value'] and x['after']['input']==x['before']['input']
  else:assert x['after']['scenario']==x['new_value'] and x['after']['prediction']=='' and x['after']['input']==fixed[x['new_value']]['input_json']
 assert len(e['edited'])==10
 for x,o in zip(e['edited'],edits):
  assert {n:x[n] for n in ['id','input_json','expected']}==o;opened(x['before']);empty(x['reset']);assert x['reset']['input']==o['input_json'];display(x['state'],o['expected'])
 assert len(e['stale'])==3 and {x['kind'] for x in e['stale']}=={'prediction','scenario','input'}
 for x in e['stale']:
  empty(x['reset']);empty(x['after']);assert x['reset']==x['after'];assert (datetime.datetime.fromisoformat(x['checked_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['started_utc'].replace('Z','+00:00'))).total_seconds()>=.6
 opened(e['host_before']);display(e['host_before'],fixed['stale']['expected']);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert len(e['captures'])==3
 for x in e['captures']:
  b=(QA/x['path']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000
  display(x['state'],oracle[x['state']['input']]);assert x['state']['scroll_width']<=x['state']['width']
  if x['path'].startswith('mobile'):assert x['state']['width']==390
 reqs=list((ROOT/'observations'/e['preview_id']/'requests').glob('*.json'));assert len(reqs)==113
 for p in reqs:
  r=load(p);assert r['request_id']==p.stem;actual(r,oracle[r['input_json']])
 start=load(ROOT/'observations'/e['preview_id']/'server-start.json');assert start['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
 assert load(ROOT/'observations'/e['preview_id']/'server-stop.json')['server_closed']
 fixedraw=load(ROOT/'observations'/e['run_id']/'raw.json');assert fixedraw['source_digests']==start['source_digests']
 for r in fixedraw['rows']:
  out=r['run']['result'];assert out['summary']==r['expected'] if out['status']=='observed' else out['code']==r['expected']['code']
  if out['status']=='observed':assert (ROOT/'observations'/e['run_id']/(r['id']+'.closed.sqlite')).read_bytes()==base64.b64decode(out['closed_db_base64'])
 links=load(QA/'http-links.json');assert links['old_coverage_exists']
 for x in links['rows']:assert x['status']==(404 if x['path'].startswith('../') else 200)
 for x in e['links']:
  if not x['href'].startswith('https:'):assert (ROOT/x['href']).is_file()
 assert all(x['closed'] and x['not_bypassed'] and x['status']=='blocked' and 'ERR_BLOCKED_BY_CLIENT' in x['error'] for x in e['navigation'])
 assert e['viewport_reset'] and e['cleanup']['owned_server_stopped']
 cleanup=load(QA/'cleanup.json');assert cleanup['protected_ports_untouched'] and cleanup['viewport_reset'] and cleanup['owned_oracle_helper_removed']
 assert not cleanup['ports_after']['49301']['listening'] and not cleanup['ports_after']['49458']['listening']
 assert cleanup['ports_after']['53478']['listening'] and cleanup['ports_after']['60285']['listening']
 assert set(cleanup['owned_tabs_closed'])=={'42','43','44','45'}
 assert [x['path'] for x in e['captures']]==['desktop-busy-snapshot.jpg','mobile-general-busy.jpg','mobile-input-refusal.jpg']
 assert json.loads(e['captures'][0]['state']['attempt'])['code']==517 and json.loads(e['captures'][1]['state']['attempt'])['code']==5 and e['captures'][2]['state']['answer_hidden']
 if (QA/'artifact-index.json').exists():
  index=load(QA/'artifact-index.json');assert index['excludes_self'] and index['excludes_future_verification']
  for name,sha in index['files'].items():assert digest(ROOT/name)==sha
 t=load(ROOT/'qa/toolchain.json');assert not t['installed'] and not t['private_python_handle_used'] and all(t['native_public_apis'].values()) and t['wrapper_error_attributes']['sqlite_errorcode'] is False and t['wrapper_error_attributes']['sqlite_errorname'] is False
 assert before==snapshot(),'QA mutated unit'
 print(json.dumps({'matrix':65,'select_resets':18,'edited':10,'stale':3,'requests':113,'captures':3,'host_failure':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
