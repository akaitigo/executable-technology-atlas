"""Read-only independent fixed-table verification, with negative controls."""
import copy,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(ROOT)):(sha(p),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def check(raw):
 table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']}
 assert len(raw['rows'])==11 and {r['id'] for r in raw['rows']}==set(expected)
 for row in raw['rows']:
  e=expected[row['id']]
  for mode in ['normal','faulty']:
   r=row[mode];assert r['status']==e['status'] and r['reason']==e['reason']
   assert r['adopted_version']==e['adopted'] and r['candidate_label']==('v2' if e['status']=='accepted' else 'v3')
   assert r['validated_candidate_version']==e['validated'] and r['immutable_mutation_blocked'] is True
   for name in ['request']:
    if e[mode] is None:assert r[name] is None
    else:
     assert r[name]['tuple']==e[mode]['tuple'] and r[name]['field_versions']==e[mode]['field_versions']
     if mode=='normal':assert r[name]['request_snapshot']==e[mode]['field_versions'][0] and r[name]['tuple']==table['version_tuples'][r[name]['request_snapshot']]
   if e['status']=='execution-error':assert r['next_request'] is None
   else:assert r['next_request']['tuple']==[2000,4] and r['next_request']['field_versions']==['v2','v2']
   t=r['trace']; assert t[0]=={'event':'json-read','fixture':'v1.json'}
   commits=[i for i,x in enumerate(t) if x['event'] in ['reference-swap','field-write']]
   validated=[i for i,x in enumerate(t) if x['event']=='validated']
   assert all(any(t[j]['version']==t[i]['version'] and j<i for j in validated) for i in commits)
   assert len(commits)==(1 if mode=='normal' else 2)
   assert all(t[i]['version']=='v2' for i in commits)
   if e['status']!='accepted':
    terminal=[x for x in t if x['event'] in ['rejected','execution-error']];assert len(terminal)==1 and terminal[0]['reason']==e['reason'] and terminal[0]['retained']=='v2'
    assert not any(x.get('version')=='v3' and x['event'] in ['reference-swap','field-write'] for x in t)
   if row['id']=='between-reads':
    reads=[i for i,x in enumerate(t) if x['event']=='field-read'];assert reads[0]<commits[0]<reads[1]
   if row['id']=='before-commit':
    reads=[i for i,x in enumerate(t) if x['event']=='field-read']
    if mode=='normal':assert reads[1]<commits[0]
    else:assert commits[0]<reads[0]<reads[1]<commits[1]
 return True

def main():
 before=snapshot();text=(ROOT/'observation-data.js').read_text();raw=json.loads(text.removeprefix('window.RELOAD_OBSERVATION=').strip().removesuffix(';'))
 folder=ROOT/'observations'/raw['run_id'];assert raw==json.loads((folder/'raw.json').read_text())
 command=json.loads((folder/'command.json').read_text());assert command['exit']==0 and command['stderr']=='' and json.loads(command['stdout'])['rows']==raw['rows']
 for name,h in raw['source_digests'].items():assert sha(ROOT/name)==h,name
 index=json.loads((folder/'artifact-index.json').read_text())['files']
 for name,h in index.items():assert sha(folder/name)==h,name
 check(raw);controls=[]
 for label,case,mode,field,value in [('hide-mixed','between-reads','faulty','request',{'tuple':[1000,2],'field_versions':['v1','v1'],'request_snapshot':None}),('false-adopt','bad-type','normal','adopted_version','v3'),('refusal-as-accepted','bad-syntax','normal','status','accepted'),('error-as-answer','read-failure','normal','request',{'tuple':[2000,4],'field_versions':['v2','v2'],'request_snapshot':'v2'}),('mutable-snapshot','before-reload','normal','immutable_mutation_blocked',False)]:
  bad=copy.deepcopy(raw);r=next(r for r in bad['rows'] if r['id']==case);r[mode][field]=value
  try:check(bad)
  except AssertionError:controls.append(label)
  else:raise AssertionError('negative control escaped:'+label)
 from route import route
 assert all(route(x)['status']=='supported' for x in ['atomic-reload','last-known-good','between-reads','partial-window','json-refusal','read-failure'])
 assert all(route(x)['status']=='unsupported' for x in ['remote-provider','os-config','distributed-reload','durability'])
 assert snapshot()==before
 print(json.dumps({'status':'passed','run_id':raw['run_id'],'accepted':4,'expected_refusals':6,'execution_errors':1,'negative_controls_detected':controls,'read_only_file_count':len(before),'hash_mtime_equal':True,'oracle':'fixed tuple/version table; producer not imported','skill_routes':'6 supported / 4 unsupported; structural only, model unrun'}));return 0
if __name__=='__main__':sys.exit(main())
