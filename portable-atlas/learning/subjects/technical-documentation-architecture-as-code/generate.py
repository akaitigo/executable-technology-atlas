import sys
sys.dont_write_bytecode=True
import argparse,json
from model import ROOT,generate
p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
artifacts,manifest=generate(json.loads((ROOT/'contract.json').read_text()),(ROOT/'api.py').read_bytes())
if a.write:
    for name,raw in artifacts.items(): (ROOT/'generated'/name).write_text(raw)
    (ROOT/'generated/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
else: print(json.dumps({'artifacts':artifacts,'manifest':manifest},ensure_ascii=False,indent=2))
