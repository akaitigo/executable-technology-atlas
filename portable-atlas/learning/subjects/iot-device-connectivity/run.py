import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser();p.add_argument('--capacity',type=int,default=6);p.add_argument('--policy',default='drop-oldest');p.add_argument('--order',default='reverse');p.add_argument('--copies',type=int,default=2);p.add_argument('--sensor',default='valid');a=p.parse_args()
try:print(json.dumps(experiment(a.capacity,a.policy,a.order,a.copies,a.sensor),ensure_ascii=False,indent=2))
except ValueError as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
