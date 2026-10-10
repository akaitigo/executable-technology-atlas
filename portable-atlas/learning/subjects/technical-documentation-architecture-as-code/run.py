import sys
sys.dont_write_bytecode=True
import argparse,json
from model import SCENARIOS,experiment
p=argparse.ArgumentParser();p.add_argument('--scenario',choices=SCENARIOS,default='baseline'); a=p.parse_args()
print(json.dumps(experiment(a.scenario),ensure_ascii=False,indent=2))
