import argparse,json
from pathlib import Path
from experiment import execute,validate
ROOT=Path(__file__).resolve().parent
def run(spec):
 try:validate(spec)
 except ValueError as e:return {'status':'rejected','error':str(e),'temp_created':False}
 return execute(spec)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input-json');a=p.parse_args()
 try:
  spec=json.loads(a.input_json) if a.input_json is not None else json.loads((ROOT/'cases.json').read_text())[0]['input']
  r=run(spec)
 except json.JSONDecodeError:r={'status':'rejected','error':'invalid JSON','temp_created':False}
 print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(2 if r['status']=='rejected' else 1 if r['status']=='error' else 0)
