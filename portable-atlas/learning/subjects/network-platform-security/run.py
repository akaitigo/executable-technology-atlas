import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser();p.add_argument('--source',default='10.0.0.130');p.add_argument('--protocol',default='tcp');p.add_argument('--port',type=int,default=443);p.add_argument('--order',default='deny-first');a=p.parse_args()
try:print(json.dumps(experiment(a.source,a.protocol,a.port,a.order),ensure_ascii=False,indent=2))
except ValueError as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
