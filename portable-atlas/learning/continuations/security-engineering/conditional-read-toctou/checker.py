import copy,hashlib,json,sqlite3,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(ROOT)):(digest(p),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def check(raw,folder):
 table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']};specs={r['id']:r for r in json.loads((ROOT/'contracts.json').read_text())['cases']};actors={'actor-alpha':'alpha','actor-beta':'beta'}
 assert len(raw['rows'])==10 and {r['id'] for r in raw['rows']}==set(expected)
 for r in raw['rows']:
  e=expected[r['id']];s=specs[r['id']]
  assert r['before_rows']==[['doc1','alpha','ALPHA SYNTHETIC',1]] and r['after_rows']==e['final_rows']
  assert r['check_allowed']==e['check_allowed'] and r['normal']==e['normal'] and r['faulty']==e['faulty']
  assert r['status']==('expected-refusal' if e['category']=='refused' else 'execution-error' if e['category']=='error' else 'observed') and r['owned_tmp_cleaned'] is True
  con=sqlite3.connect((folder/r['id']/'state.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
  try:
   stored=con.execute('SELECT id,tenant,payload,revision FROM resources ORDER BY id').fetchall();assert [list(x) for x in stored]==e['final_rows']
   if e['direct_sql_reference'] is not None:
    result=con.execute('SELECT payload,tenant FROM resources WHERE tenant = ? AND id = ?',(actors[s['actor']],s['resource'])).fetchall();assert [list(x) for x in result]==e['direct_sql_reference']
  finally:con.close()
  sql=[x for x in r['trace'] if x['event']=='sql'];assert len(sql)==(0 if e['category']=='refused' else 2+e['faulty']['attempts'])
  for event in sql:assert event['transaction_before'] is False and event['transaction_during'] is True and event['exit']==(1 if e['category']=='error' and event['phase']!='check' else 0)
  endings=[x for x in r['trace'] if x['event'] in ['commit','rollback']];assert all(x['transaction_after'] is False for x in endings)
  if e['category']=='refused':assert not any(x['event'] in ['mutation','sql'] for x in r['trace'])
  if s['change'] is not None and e['category']!='refused':
   check_end=next(i for i,x in enumerate(r['trace']) if x['event']=='commit' and x['connection']=='reader' and x['phase']=='check')
   change_end=next(i for i,x in enumerate(r['trace']) if x['event']=='commit' and x['connection']=='writer')
   read=next(i for i,x in enumerate(r['trace']) if x['event']=='sql' and x['phase']=='conditional-read')
   assert change_end<check_end<read if s['schedule']=='before-check' else check_end<change_end<read
 return True

def main():
 before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.TOCTOU_OBSERVATION=').strip().removesuffix(';'));folder=ROOT/'observations'/raw['run_id'];assert raw==json.loads((folder/'raw.json').read_text())
 c=json.loads((folder/'command.json').read_text());assert c['exit']==0 and c['stderr']=='' and json.loads(c['stdout'])['rows']==raw['rows']
 for n,h in raw['source_digests'].items():assert digest(ROOT/n)==h,n
 for n,h in json.loads((folder/'artifact-index.json').read_text())['files'].items():assert digest(folder/n)==h,n
 check(raw,folder);controls=[]
 for label,case,mode,field,value in [('conditional-leak','move-after-check','normal','payload','BETA SYNTHETIC'),('hide-id-only-leak','move-after-check','faulty','payload',None),('old-check-authoritative','beta-after-check','normal','decision','deny'),('refusal-as-allow','unknown-actor','normal','decision','allow'),('error-as-payload','sql-error','normal','payload','ALPHA SYNTHETIC')]:
  bad=copy.deepcopy(raw);next(r for r in bad['rows'] if r['id']==case)[mode][field]=value
  try:check(bad,folder)
  except AssertionError:controls.append(label)
  else:raise AssertionError('escaped:'+label)
 from route import route
 assert all(route(t)['status']=='supported' for t in ['conditional-read','toctou-gap','check-before-change','payload-update','late-allow','unknown-actor','sql-error'])
 assert all(route(t)['status']=='unsupported' for t in ['authentication','parallel-race','full-revocation','product-certification'])
 assert snapshot()==before
 print(json.dumps({'status':'passed','run_id':raw['run_id'],'observed':6,'input_refusals':3,'sql_execution_errors':1,'sqlite_snapshots':10,'independent_oracle':'fixed literal rows/interleavings/decisions plus separate read-only direct SQL; producer not imported','negative_controls_detected':controls,'all_owned_tmp_cleaned':True,'skill_routes':'7 supported / 4 exclusions; structural only, model unrun','read_only_files':len(before),'all_hash_mtime_equal':True}));return 0
if __name__=='__main__':sys.exit(main())
