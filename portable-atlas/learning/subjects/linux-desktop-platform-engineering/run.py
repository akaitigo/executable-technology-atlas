import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser();p.add_argument('--case',default='quoted');p.add_argument('--selection',default='spaces');p.add_argument('--launch',default='argv-model');a=p.parse_args()
try:
    d=experiment(a.case,a.selection,a.launch);print(json.dumps(d,ensure_ascii=False,indent=2));sys.exit(2 if d['protected']['status']=='rejected' else 0)
except ValueError as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
