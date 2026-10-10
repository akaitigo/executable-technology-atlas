"""Explicit task-owned RAM export; --record alone persists QA artifacts."""
import argparse,datetime,hashlib,json,platform,sys,urllib.request,urllib.error
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
def snapshot():return {str(p.relative_to(ROOT)):[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns] for p in ROOT.rglob('*') if p.is_file()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,required=True);p.add_argument('--directory',required=True);p.add_argument('--record',action='store_true');a=p.parse_args()
 q=(ROOT/a.directory).resolve();assert q.parent==ROOT/'qa' and q.is_dir();base='http://127.0.0.1:'+str(a.port)+'/'
 def get(path):
  with urllib.request.urlopen(base+path,timeout=5) as f:return f.status,f.read()
 before=snapshot();health=json.loads(get('api/health')[1]);rows=[]
 for path in ['view/readme','view/calculate','view/checker','view/hand','view/coverage','view/parent-readme','view/skill','view/fixed-raw','view/not-listed']:
  try:status,body=get(path)
  except urllib.error.HTTPError as e:status=e.code
  rows.append({'path':path,'status':status})
 fixed=json.loads((ROOT/'expected-table.json').read_text())['rows'];setup=[]
 for i,row in enumerate([fixed[0],fixed[-1]]):
  req=urllib.request.Request(base+'measure',data=json.dumps({'input_json':row['input_json'],'revision':-i-1}).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=5) as f:setup.append(json.load(f))
 export=json.loads(get('api/export')[1]);assert before==snapshot()
 if a.record:
  (q/'memory-receipts.json').write_text(json.dumps(export,ensure_ascii=False,indent=2)+'\n')
  (q/'http-links.json').write_text(json.dumps({'rows':rows,'health_before_setup':health,'total':len(export['requests']),'ui_post_count':sum(x['revision']>=0 for x in export['requests']),'unit_sha_mtime_unchanged_during_GET_POST_export':True,'parent_reference_sha256':hashlib.sha256((ROOT/'../../../subjects/decentralized-systems-blockchain/README.md').read_bytes()).hexdigest()},indent=2)+'\n')
  (q/'memory-http-check.json').write_text(json.dumps({'mode':'memory-only','unit_sha_mtime_unchanged':True,'requests':setup},ensure_ascii=False,indent=2)+'\n')
  (q/'toolchain.json').write_text(json.dumps({'python':platform.python_version(),'installed':False,'hash_backend':'hashlib SHA256 plus system OpenSSL','actual_IAB':True},indent=2)+'\n')
 print(json.dumps({'receipts':len(export['requests']),'UI_POST':sum(x['revision']>=0 for x in export['requests']),'setup':2,'sha_mtime_unchanged':True,'recorded':a.record}))
if __name__=='__main__':main()
