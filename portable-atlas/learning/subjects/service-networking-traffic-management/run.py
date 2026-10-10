import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser()
for name,default in [('threshold',2),('cooldown',3),('retries',1),('deadline',5),('budget',16)]:p.add_argument('--'+name,type=int,default=default)
p.add_argument('--recovery',default='8');a=p.parse_args()
try:print(json.dumps(experiment(a.threshold,a.cooldown,a.retries,a.deadline,a.budget,a.recovery),ensure_ascii=False,indent=2))
except ValueError as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
