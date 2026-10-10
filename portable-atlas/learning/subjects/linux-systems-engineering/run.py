import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser();p.add_argument('--mode',default='004');p.add_argument('--principal',default='owner');p.add_argument('--operation',default='read');p.add_argument('--kind',default='file');p.add_argument('--security',default='none');a=p.parse_args()
try:
    d=experiment(a.mode,a.principal,a.operation,a.kind,a.security);print(json.dumps(d,ensure_ascii=False,indent=2));sys.exit(2 if d['protected']['status']=='rejected' else 0)
except ValueError as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
