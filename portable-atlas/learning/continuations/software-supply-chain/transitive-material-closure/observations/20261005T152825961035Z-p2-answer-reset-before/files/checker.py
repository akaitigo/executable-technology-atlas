import copy,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):return sha(p.read_bytes())
def snapshot():return {str(p.relative_to(ROOT)):(digest(p),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def check(raw):
 table=json.loads((ROOT/'expected-table.json').read_text());expected={r['id']:r for r in table['rows']};literal={n:bytes.fromhex(h) for n,h in table['literal_materials'].items()};base={n:sha(literal[n]) for n in ['root','A','B']}
 assert json.loads((ROOT/'fixtures/baseline-materials.json').read_text())==base
 assert len(raw['rows'])==8 and {r['id'] for r in raw['rows']}==set(expected)
 for row in raw['rows']:
  e=expected[row['id']];assert row['reachable']==e['reachable']
  assert row['normal']['decision']==e['normal'] and row['normal']['reason']==e['normal_reason'] and row['faulty']['decision']==e['faulty']
  assert row['status']==('execution-error' if e['category']=='error' else 'expected-refusal' if e['category']=='refused' else 'observed')
  if e['mismatched'] is not None:assert row['normal']['mismatched']==e['mismatched']
  if e['missing'] is not None:assert row['normal']['missing']==e['missing'] and row['normal']['extra']==[]
  if e['artifact_literal'] is None:
   assert row['artifact'] is None and row['declared'] is None
   expected_materials=['A'] if e['category']=='error' else []
  else:
   b=bytes.fromhex(table['literal_artifacts'][e['artifact_literal']]);a=row['artifact'];assert a=={'hex':b.hex(),'ascii':b.decode('ascii'),'sha256':sha(b),'size':len(b)}
   assert row['direct_names']==['A'] and row['faulty']['reason']=='direct-name-match'
   expected_materials=e['reachable']
   declaration={n:base[n] for n in ['root','A']} if e['category'] in ['undeclared','closure'] else dict(base,B=sha(literal['B-new'])) if e['category']=='changed' else base
   assert row['declared']==declaration
  assert set(row['materials'])==set(expected_materials)
  for n,v in row['materials'].items():
   b=literal['B-new'] if n=='B' and row['id'] in ['B-changed','changed-undeclared'] else literal[n]
   assert v=={'sha256':sha(b),'size':len(b),'hex':b.hex()}
  events=[t['event'] for t in row['trace']]
  if row['artifact']:
   assert events.count('material-read')==len(expected_materials) and events.index('artifact-built')<events.index('consumer-check')
  else:assert 'artifact-built' not in events and 'consumer-check' not in events
 return True

def main():
 before=snapshot();raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.MATERIAL_OBSERVATION=').strip().removesuffix(';'));folder=ROOT/'observations'/raw['run_id'];assert raw==json.loads((folder/'raw.json').read_text())
 c=json.loads((folder/'command.json').read_text());assert c['exit']==0 and c['stderr']=='' and json.loads(c['stdout'])['rows']==raw['rows']
 for n,h in raw['source_digests'].items():assert digest(ROOT/n)==h,n
 for n,h in json.loads((folder/'artifact-index.json').read_text())['files'].items():assert digest(folder/n)==h,n
 check(raw)
 table=json.loads((ROOT/'expected-table.json').read_text());expect={r['id']:r for r in table['rows']}
 for row in raw['rows']:
  p=folder/row['id']/'artifact.bin'
  if row['artifact']:assert p.read_bytes()==bytes.fromhex(table['literal_artifacts'][expect[row['id']]['artifact_literal']])
  else:assert not p.exists()
 controls=[]
 for label,case,field,value in [('hide-B-change','B-changed','normal',{'decision':'allow','reason':'all-materials-match','mismatched':[]}),('omit-reach-B','B-undeclared','reachable',['A','root']),('missing-material-hidden','B-undeclared','normal',{'decision':'allow','reason':'all-materials-match','mismatched':[]}),('cycle-as-observed','cycle','status','observed'),('error-as-artifact','read-failure','artifact',{'hex':'00','ascii':'x','sha256':'0','size':1})]:
  bad=copy.deepcopy(raw);next(r for r in bad['rows'] if r['id']==case)[field]=value
  try:check(bad)
  except (AssertionError,KeyError,TypeError):controls.append(label)
  else:raise AssertionError('escaped:'+label)
 from route import route
 assert all(route(t)['status']=='supported' for t in ['material-closure','B-change','undeclared-B','graph-closure','unknown-node','cycle','read-failure'])
 assert all(route(t)['status']=='unsupported' for t in ['slsa-level','signature','resolver','sbom'])
 assert snapshot()==before
 print(json.dumps({'status':'passed','run_id':raw['run_id'],'build_observed':5,'prebuild_refusals':2,'execution_errors':1,'normal_decisions':{'allow':1,'deny':1,'refuse':5,'error':1},'negative_controls_detected':controls,'oracle':'fixed reachable sets and literal artifact/material bytes; no graph traversal or producer import','skill_routes':'7 supported / 4 exclusions; structure only, model unrun','read_only_files':len(before),'hash_mtime_equal':True}));return 0
if __name__=='__main__':sys.exit(main())
