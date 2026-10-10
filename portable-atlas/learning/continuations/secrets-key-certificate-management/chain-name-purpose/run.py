import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser();p.add_argument('--case',default='wrong-san');p.add_argument('--mode',default='offline');a=p.parse_args()
try:print(json.dumps(experiment(a.case,a.mode),ensure_ascii=False,indent=2))
except (ValueError,RuntimeError) as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
