"""Read-only oracle: fixed literals, no producer import, decoder or cache logic."""
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
FIELDS=['status','pc','a','steps','trace','diagnostic']
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def verify(raw):
 table=json.loads((ROOT/'expected-table.json').read_text());contracts=json.loads((ROOT/'contracts.json').read_text());assert len(raw['rows'])==len(table['rows'])==10
 assert {r['id'] for r in raw['rows']}=={e['id'] for e in table['rows']}
 for r,c in zip(raw['rows'],contracts['cases']):
  e=next(e for e in table['rows'] if e['id']==r['id'])
  assert r['id']==e['id']==c['id'] and r['input']==c['input'] and r['prewarm']==c['prewarm']
  for mode in ['fetch','invalidate','stale']:
   v=r['variants'][mode];assert {k:v[k] for k in FIELDS}==e[mode],(r['id'],mode,'literal trace')
   if e[mode]['status']=='input':assert v['memory'] is None and not v['cache_events'] and not v['decoded_blocks'];continue
   mem=c['input']['program']+[0]*(256-len(c['input']['program']))
   # Apply only literal handwritten changes; no instruction semantics are interpreted.
   for step in e[mode]['trace']:
    for addr,old,new in step[6]:assert mem[addr]==old;mem[addr]=new
   assert v['memory']==mem,(r['id'],mode,'full memory')
   if mode=='fetch':assert not v['cache_events'] and not v['store_events'] and not v['decoded_blocks'];continue
   for b in v['decoded_blocks']:
    if b['start'] in c['prewarm'] and b==v['decoded_blocks'][c['prewarm'].index(b['start'])]:assert b['addresses']==table.get('prewarm_overrides',{}).get(r['id'],{}).get(str(b['start']),table['prewarm_blocks'][str(b['start'])]['addresses'])
   if e['store']['write'] is None:assert not v['store_events']
   else:
    ev=v['store_events'];assert len(ev)==1 and ev[0]['write']==e['store']['write'] and ev[0]['overlaps']==e['store']['evicted']
    assert ev[0]['evicted']==(e['store']['evicted'] if mode=='invalidate' else [])
    assert ev[0]['kept']==(e['store']['kept'] if mode=='invalidate' else sorted(e['store']['kept']+e['store']['evicted']))
  assert r['variants']['fetch']['trace']==r['variants']['invalidate']['trace']
 return True

def main():
 before=snapshot();p=subprocess.run([sys.executable,str(ROOT/'experiment.py')],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));assert p.returncode==0 and not p.stderr
 raw=json.loads(p.stdout);verify(raw)
 mutants=[]
 for name in ['stale-a','missing-eviction','unrelated-eviction','wrap-address','refusal-as-halt']:
  x=copy.deepcopy(raw)
  if name=='stale-a':x['rows'][0]['variants']['stale']['a']=7
  elif name=='missing-eviction':x['rows'][0]['variants']['invalidate']['store_events'][0]['evicted']=[]
  elif name=='unrelated-eviction':x['rows'][3]['variants']['invalidate']['store_events'][0]['evicted'].append(20)
  elif name=='wrap-address':x['rows'][5]['variants']['invalidate']['store_events'][0]['write']=256
  else:x['rows'][6]['variants']['fetch']['status']='halt'
  try:verify(x)
  except AssertionError:mutants.append(name)
  else:raise AssertionError('negative control accepted: '+name)
 pointer=ROOT/'observation-data.js'
 run_id=None
 if pointer.exists():
  saved=json.loads(pointer.read_text().removeprefix('window.STORE_OBSERVATION=').strip().removesuffix(';'));verify(saved);run_id=saved['run_id'];folder=ROOT/'observations'/run_id
  assert json.loads((folder/'raw.json').read_text())==saved
  for n,d in saved['source_digests'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d,n
  index=json.loads((folder/'artifact-index.json').read_text())
  for n,d in index['files'].items():assert hashlib.sha256((folder/n).read_bytes()).hexdigest()==d,n
 assert snapshot()==before
 print(json.dumps({'status':'passed','cases':10,'variants':30,'negative_controls_rejected':mutants,'run_id':run_id,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))
if __name__=='__main__':main()
