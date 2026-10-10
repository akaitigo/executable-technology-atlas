import argparse,json
from pathlib import Path
from parser import analyze
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input-json');a=p.parse_args()
 try:spec=json.loads(a.input_json) if a.input_json is not None else json.loads((ROOT/'cases.json').read_text())[0]['input'];out=analyze(spec)
 except (ValueError,TypeError):out={'status':'rejected','phase':'input','reason':'input_json','variants':{}}
 print(json.dumps(out,ensure_ascii=True,indent=2));raise SystemExit(0 if out['status']=='accepted' else 2)
