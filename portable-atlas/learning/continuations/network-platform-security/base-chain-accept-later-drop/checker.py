import copy,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,collect,digest,snapshot
def verify(rows):
 for row in rows:
  r=row['run'];assert r['result']==row['expected'],row['id'];assert r['exit']==(2 if row['expected']['status']=='input_refusal' else 0);assert not r['stderr']
def main():
 before=snapshot();rows=collect()['rows'];verify(rows)
 # Negative controls perturb outputs independently; oracle must catch every mutant.
 mutations=[]
 for name,idx,key,value in [('wrong-final',0,'final','accept'),('visited-after-drop',3,'trace',['chain service priority=10']),('json-order',6,'trace',['chain service priority=10']),('bool-accepted',13,'status','observed'),('missing-last-drop',0,'trace',['final drop'])]:
  m=copy.deepcopy(rows)
  if key=='status':m[idx]['run']['result'][key]=value
  else:m[idx]['run']['result']['normal'][key]=value
  try:verify(m)
  except AssertionError:mutations.append(name)
  else:raise AssertionError('mutant survived '+name)
 js=ROOT/'observation-data.js'
 if js.exists():
  raw=json.loads(js.read_text().split('=',1)[1].rstrip(';\n'));verify(raw['rows']);assert {n:digest(ROOT/n) for n in SOURCES}==raw['source_digests']
  folder=ROOT/'observations'/raw['run_id'];assert json.loads((folder/'raw.json').read_text())==raw
  index=json.loads((folder/'artifact-index.json').read_text());assert all(digest(folder/n)==h for n,h in index['files'].items())
  assert (folder/'expected-table.json').read_bytes()==(ROOT/'expected-table.json').read_bytes()
 assert before==snapshot(),'checker mutated unit'
 print(json.dumps({'passed':len(rows),'mutants_rejected':mutations,'read_only':True}));return 0
if __name__=='__main__':sys.exit(main())
