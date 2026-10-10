import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'expected-table.json').read_text())
def snapshot():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def verify_row(row):
 e=next(e for e in TABLE['rows'] if e['input_json']==row['stdin']);r=row['result']
 for k,v in e['expected'].items():assert r[k]==v,(e['id'],k)
 assert json.loads(row['stdout'])==r and row['stderr']=='' and row['exit']==(2 if e['category']=='input' else 0)
 if e['category']!='input':assert json.loads(r['encoded_json'])==json.loads(e['input_json'])
 return e

def main():
 before=snapshot();p=subprocess.run([sys.executable,str(ROOT/'runtime.py')],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));assert p.returncode==0 and not p.stderr
 raw=json.loads(p.stdout);assert raw['compile']['exit']==0 and raw['owned_tmp_cleaned'] and len(raw['rows'])==13
 for row in raw['rows']:verify_row(row)
 rejected=[]
 for name in ['character-for-scalar','normalized-decomposed','wrong-utf16','hidden-rejection','invented-refusal-value']:
  x=copy.deepcopy(raw['rows'][{'character-for-scalar':3,'normalized-decomposed':1,'wrong-utf16':2,'hidden-rejection':3,'invented-refusal-value':11}[name]])
  if name=='character-for-scalar':x['result']['decoded']['scalar']=3
  elif name=='normalized-decomposed':x['result']['redecoded']['codepoints']=[233]
  elif name=='wrong-utf16':x['result']['decoded']['utf16']=3
  elif name=='hidden-rejection':x['result']['normal']['accepted']=True
  else:x['result']['decoded']={'character':0}
  try:verify_row(x)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name)
 saved=ROOT/'observation-data.js';run_id=None
 if saved.exists():
  obs=json.loads(saved.read_text().removeprefix('window.SWIFT_OBSERVATION=').strip().removesuffix(';'));run_id=obs['run_id'];assert json.loads((ROOT/'observations'/run_id/'raw.json').read_text())==obs
  for row in obs['rows']:verify_row(row)
  for n,d in obs['source_digests'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d,n
  idx=json.loads((ROOT/'observations'/run_id/'artifact-index.json').read_text())
  for n,d in idx['files'].items():assert hashlib.sha256((ROOT/'observations'/run_id/n).read_bytes()).hexdigest()==d,n
 assert snapshot()==before
 print(json.dumps({'status':'passed','cases':13,'negative_controls_rejected':rejected,'owned_tmp_cleaned':raw['owned_tmp_cleaned'],'run_id':run_id,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))
if __name__=='__main__':main()
