import argparse,json
from pathlib import Path
from emulator import analyze
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input-json');a=p.parse_args()
 try:
  spec=json.loads(a.input_json) if a.input_json is not None else json.loads((ROOT/'cases.json').read_text())[0]['input']
  r=analyze(spec)
 except json.JSONDecodeError:r={'status':'rejected','phase':'input','error':'invalid JSON','variants':{}}
 print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(2 if r['status']=='rejected' else 0)
