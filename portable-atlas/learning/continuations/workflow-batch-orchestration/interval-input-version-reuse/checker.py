import copy,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
MODES=['normal','drop-interval','drop-digest','latest-lookup']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(ROOT)):(digest(p),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def canonical_sha(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def check(raw):
 table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']};specs={r['id']:r for r in json.loads((ROOT/'contracts.json').read_text())['cases']}
 assert len(raw['rows'])==15 and {r['id'] for r in raw['rows']}==set(expected)
 totals={table['literal_digests'][k]:v for k,v in table['literal_totals'].items()}
 for row in raw['rows']:
  e=expected[row['id']];s=specs[row['id']];assert set(row['modes'])==set(MODES)
  for mode,r in row['modes'].items():
   assert r['status']==e['status'] and r['reason']==e['reason']
   assert r['request']=={'interval':s['interval'],'selector':s['selector']}
   if e['status']!='success':
    assert r['value'] is None and r['artifact'] is None and r['task_calls']==0 and r['cache_before']==r['cache_after']
    assert r['trace'][-1]['event']==('execution-error' if e['status']=='execution-error' else 'refused')
    continue
   x=e['modes'][mode];resolved=r['resolved_input'];assert r['value']==x['value'] and r['cache_hit']==x['hit'] and r['task_calls']==x['calls']
   assert resolved['version_label']==x['selected'] and resolved['input_sha']==x['input_sha']
   assert resolved['values']=={'a':[2,3],'b':[2,8],'c':[7]}[next(k for k,v in table['literal_digests'].items() if v==x['input_sha'])]
   assert resolved['raw_file_sha']==digest(ROOT/'fixtures'/resolved['fixture'])
   binding={'task':'sum-demo-v1','interval':x['artifact_interval'],'input_sha':x['artifact_input_sha']};a=r['artifact'];assert a['body']['binding']==binding and a['body']['value']==x['value']
   assert a['body']['value']==totals[binding['input_sha']] and a['body']['count']==(1 if binding['input_sha']==table['literal_digests']['c'] else 2)
   assert a['artifact_sha']==canonical_sha(a['body']) and r['reused_binding_matches_request']==x['binding_matches']
   key=['sum-demo-v1',x['input_sha']] if mode=='drop-interval' else ['sum-demo-v1',s['interval']] if mode=='drop-digest' else ['sum-demo-v1',s['interval'],x['input_sha']]
   assert r['cache_key']==key
   events=[t['event'] for t in r['trace']];assert events.index('resolved-input')<events.index('cache-lookup')
   assert events[-1]==('cache-reuse' if x['hit'] else 'task-compute')
   if x['hit']:assert r['cache_before']==r['cache_after']
   else:assert len(r['cache_after'])==len(r['cache_before'])+1
 return True

def main():
 before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.INTERVAL_OBSERVATION=').strip().removesuffix(';'));folder=ROOT/'observations'/raw['run_id']
 assert raw==json.loads((folder/'raw.json').read_text());c=json.loads((folder/'command.json').read_text());assert c['exit']==0 and c['stderr']=='' and json.loads(c['stdout'])['rows']==raw['rows']
 for n,h in raw['source_digests'].items():assert digest(ROOT/n)==h,n
 for n,h in json.loads((folder/'artifact-index.json').read_text())['files'].items():assert digest(folder/n)==h,n
 check(raw);controls=[]
 for label,case,mode,field,value in [('hide-digest-collision','new-version','drop-digest','value',10),('hide-interval-binding','same-input-new-interval','drop-interval','reused_binding_matches_request',True),('latest-as-pinned','latest-changed-explicit-v1','latest-lookup','value',5),('false-cache-hit','new-interval','normal','cache_hit',True),('corrupt-cache-as-success','corrupt-cache','normal','status','success'),('error-as-value','read-failure','normal','value',5)]:
  bad=copy.deepcopy(raw);next(r for r in bad['rows'] if r['id']==case)['modes'][mode][field]=value
  try:check(bad)
  except (AssertionError,TypeError):controls.append(label)
  else:raise AssertionError('escaped:'+label)
 from route import route
 assert all(route(t)['status']=='supported' for t in ['pinned-rerun','new-version','new-interval','same-label','artifact-binding','latest-drift','refusal','read-failure'])
 assert all(route(t)['status']=='unsupported' for t in ['airflow-runtime','calendar','distributed-storage','external-effects'])
 assert snapshot()==before
 print(json.dumps({'status':'passed','run_id':raw['run_id'],'success_cases':9,'expected_refusals':5,'execution_errors':1,'modes':4,'negative_controls_detected':controls,'oracle':'fixed literal totals, version/interval binding, hit table; producer not imported','skill_routes':'8 supported / 4 exclusions; structural only, model unrun','read_only_files':len(before),'all_hash_mtime_equal':True}));return 0
if __name__=='__main__':sys.exit(main())
