import copy,json,sys
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,collect,digest,snapshot
def verify(rows):
 for row in rows:
  run=row['run'];r=run['result'];e=row['expected'];assert {k:r.get(k) for k in e}==e,row['id'];assert run['exit']==(2 if e['status']=='input_refusal' else 0);assert not run['stderr'];assert json.loads(run['stdout'])==r
  if e['status']=='observed':
   assert r['copy_before_ascii']==r['original_ascii'] and r['original_unchanged'] and r['temporary_cleanup']
   assert r['file_trace'][1]=='shutil.copyfile original.txt -> copy.txt';assert [a['input'] for a in r['ledger_trace']]==json.loads(row['input_json'])['handoffs']
def main():
 before=snapshot();rows=collect()['rows'];verify(rows);caught=[]
 for name,idx,key,value in [('hash-only-approval',2,'normal',{'pass':True,'decision':'integrity-match','claim':'synthetic copy and ledger only'}),('missed-one-byte',1,'copy_after_sha256',rows[0]['expected']['original_sha256']),('missed-sequence',3,'ledger_errors',[]),('wrong-evidence-id',4,'ledger_consistent',True),('false-authenticity',0,'authenticity_proven',True)]:
  m=copy.deepcopy(rows);m[idx]['run']['result'][key]=value
  try:verify(m)
  except AssertionError:caught.append(name)
  else:raise AssertionError('mutant survived '+name)
 js=ROOT/'observation-data.js'
 if js.exists():
  raw=json.loads(js.read_text().split('=',1)[1].rstrip(';\n'));verify(raw['rows']);assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  d=ROOT/'observations'/raw['run_id'];assert json.loads((d/'raw.json').read_text())==raw;idx=json.loads((d/'artifact-index.json').read_text());assert 'artifact-index.json' not in idx['files'];assert all(digest(d/n)==h for n,h in idx['files'].items());assert (d/'expected-table.json').read_bytes()==(ROOT/'expected-table.json').read_bytes()
 assert before==snapshot();print(json.dumps({'fixed_cases':len(rows),'mutants_rejected':caught,'all_tmp_cleaned':True,'read_only':True}));return 0
if __name__=='__main__':sys.exit(main())
