import sys
sys.dont_write_bytecode=True
import argparse,json
from model import experiment
p=argparse.ArgumentParser()
for name,default in [('reuse','warm'),('lifetime','process-local'),('duplicates','duplicates'),('payload','normal'),('error','none')]:p.add_argument('--'+name,default=default)
a=p.parse_args()
try:print(json.dumps(experiment(a.reuse,a.lifetime,a.duplicates,a.payload,a.error),ensure_ascii=False,indent=2))
except ValueError as e:print(json.dumps({'status':'rejected','error':str(e)}));sys.exit(2)
